import threading
import uvicorn
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import streamlit as st
import cv2
import os
import tempfile
import uuid
import boto3
from dotenv import load_dotenv

load_dotenv()

AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
REGION_NAME = os.getenv('AWS_REGION')
BUCKET_NAME = os.getenv('S3_BUCKET')

if not all([AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, REGION_NAME, BUCKET_NAME]):
    raise ValueError("AWS environment variables not set properly")

rekognition = boto3.client('rekognition', aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY, region_name='us-east-1')
s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY, region_name='us-east-1')

app = FastAPI()

def upload_to_s3(filename):
    try:
        s3.upload_file(filename, BUCKET_NAME, os.path.basename(filename))
        return os.path.basename(filename)
    except Exception as e:
        print(f"Error uploading file to S3: {e}")
        return None

def detect_faces(filename):
    try:
        response = rekognition.detect_faces(
            Image={'S3Object': {'Bucket': BUCKET_NAME, 'Name': filename}},
            Attributes=['ALL']
        )
        return response
    except Exception as e:
        print(f"Error detecting faces: {e}")
        return None

@app.post("/upload/")
async def upload(file: UploadFile = File(...)):
    try:
        tempdir = tempfile.mkdtemp()
        filepath = os.path.join(tempdir, file.filename)
        with open(filepath, 'wb') as f:
            f.write(await file.read())
        s3_filename = upload_to_s3(filepath)
        if not s3_filename:
            raise HTTPException(status_code=500, detail="Failed to upload file to S3")
        response = detect_faces(s3_filename)
        if not response:
            raise HTTPException(status_code=500, detail="Failed to detect faces")
        return JSONResponse(content=response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(filepath):
            os.remove(filepath)
        os.rmdir(tempdir)

def run_fastapi():
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    fastapi_thread = threading.Thread(target=run_fastapi)
    fastapi_thread.start()
