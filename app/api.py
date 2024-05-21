import os
import boto3
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File
from typing import List
from starlette.responses import JSONResponse
from starlette.background import BackgroundTasks

load_dotenv()

AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
REGION_NAME = os.getenv('AWS_REGION')
BUCKET_NAME = os.getenv('S3_BUCKET')

rekognition = boto3.client('rekognition', aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY, region_name='us-east-1')
s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY, region_name='us-east-1')

app = FastAPI()

def clear_s3_bucket():
    try:
        bucket = s3.list_objects_v2(Bucket=BUCKET_NAME)
        if 'Contents' in bucket:
            for item in bucket['Contents']:
                s3.delete_object(Bucket=BUCKET_NAME, Key=item['Key'])
        print("All images deleted from S3 bucket.")
    except Exception as e:
        print(f"Error deleting images from S3: {e}")

def upload_to_s3(filename):
    try:
        s3.upload_file(filename, BUCKET_NAME, os.path.basename(filename))
        return os.path.basename(filename)
    except Exception as e:
        print(f"Error uploading file to S3: {e}")
        return None

def detect_faces_in_video(filename):
    try:
        response = rekognition.detect_faces(
            Video={'S3Object': {'Bucket': BUCKET_NAME, 'Name': filename}},
            Attributes=['ALL']
        )
        return response
    except Exception as e:
        print(f"Error detecting faces: {e}")
        return None

@app.post("/upload_video")
async def upload_video(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    file_path = f"/tmp/{file.filename}"
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    output_path = detect_faces_in_video(file_path)
    object_name = os.path.basename(output_path)
    background_tasks.add_task(upload_to_s3, output_path, BUCKET_NAME, object_name)

    return JSONResponse(content={"message": "File uploaded successfully"})

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.post("/clear_bucket")
async def clear_bucket():
    clear_s3_bucket()
    return {"message": "Bucket cleared successfully"}
