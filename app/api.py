from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import os
import uuid
import tempfile
from mangum import Mangum
from app.utils import upload_to_s3, detect_faces, clear_s3_bucket, is_liveness_detected, analyze_movement

app = FastAPI()

@app.post("/upload/")
async def upload_image(file: UploadFile = File(...)):
    try:
        # Salvar o arquivo temporariamente
        tempdir = tempfile.mkdtemp()
        filename = os.path.join(tempdir, f"{uuid.uuid4()}.jpg")
        with open(filename, "wb") as buffer:
            buffer.write(file.file.read())

        # Fazer upload para S3
        s3_filename = upload_to_s3(filename)
        if not s3_filename:
            raise HTTPException(status_code=500, detail="Failed to upload image to S3")

        # Detectar faces
        response = detect_faces(s3_filename)
        if not response:
            raise HTTPException(status_code=500, detail="Failed to detect faces")

        face_detected = False
        for faceDetail in response['FaceDetails']:
            if is_liveness_detected(faceDetail):
                confidence = faceDetail['Confidence']
                face_detected = True
                break

        if not face_detected:
            raise HTTPException(status_code=400, detail="Nenhuma face detectada ou critérios de vivacidade não atendidos.")

        # Limpar arquivos temporários
        os.remove(filename)
        os.rmdir(tempdir)

        return JSONResponse(content={"confidence": confidence})

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

handler = Mangum(app)
