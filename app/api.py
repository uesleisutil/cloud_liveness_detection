from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
import boto3
import os
import uuid

app = FastAPI()

AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
REGION_NAME = os.getenv('AWS_REGION')
BUCKET_NAME = os.getenv('S3_BUCKET')

rekognition = boto3.client('rekognition', aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY, region_name=REGION_NAME)
s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY, region_name=REGION_NAME)

@app.post("/upload/")
async def upload_image(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        filename = f"{uuid.uuid4()}.jpg"
        with open(filename, 'wb') as f:
            f.write(contents)

        s3.upload_file(filename, BUCKET_NAME, filename)

        response = rekognition.detect_faces(
            Image={'S3Object': {'Bucket': BUCKET_NAME, 'Name': filename}},
            Attributes=['ALL']
        )

        if not response or not response['FaceDetails']:
            raise HTTPException(status_code=400, detail="No faces detected")

        face_details = response['FaceDetails'][0]

        return JSONResponse(content=face_details)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        os.remove(filename)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
