from fastapi import FastAPI, UploadFile, File, HTTPException
import boto3
import os
import tempfile
import uuid
from app.utils import upload_to_s3, detect_faces, clear_s3_bucket

app = FastAPI()

@app.post("/upload/")
async def upload_image(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        tempdir = tempfile.mkdtemp()
        filename = os.path.join(tempdir, f"{uuid.uuid4()}.jpg")
        with open(filename, 'wb') as f:
            f.write(contents)
        s3_filename = upload_to_s3(filename)
        response = detect_faces(s3_filename)
        return {"filename": s3_filename, "detection": response}
    except Exception as e:
        return {"error": str(e)}

@app.get("/clear_s3/")
def clear_bucket():
    clear_s3_bucket()
    return {"message": "S3 bucket cleared"}
