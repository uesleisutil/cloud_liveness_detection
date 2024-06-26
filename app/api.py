import os
import boto3
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
import tempfile
import logging

load_dotenv()

AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
REGION_NAME = os.getenv('AWS_REGION')
BUCKET_NAME = os.getenv('S3_BUCKET')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info(f"AWS_ACCESS_KEY_ID: {AWS_ACCESS_KEY_ID}")
logger.info(f"AWS_SECRET_ACCESS_KEY: {AWS_SECRET_ACCESS_KEY}")
logger.info(f"REGION_NAME: {REGION_NAME}")
logger.info(f"BUCKET_NAME: {BUCKET_NAME}")

rekognition = boto3.client('rekognition', aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY, region_name=REGION_NAME)
s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY, region_name=REGION_NAME)

app = FastAPI()

def clear_s3_bucket():
    try:
        bucket = s3.list_objects_v2(Bucket=BUCKET_NAME)
        if 'Contents' in bucket:
            for item in bucket['Contents']:
                s3.delete_object(Bucket=BUCKET_NAME, Key=item['Key'])
        logger.info("All images deleted from S3 bucket.")
    except Exception as e:
        logger.error(f"Error deleting images from S3: {e}")

def upload_to_s3(filename):
    try:
        logger.info(f"Attempting to upload {filename} to bucket {BUCKET_NAME}")
        s3.upload_file(filename, BUCKET_NAME, os.path.basename(filename))
        logger.info(f"File {filename} uploaded to S3 bucket {BUCKET_NAME}")
        return os.path.basename(filename)
    except Exception as e:
        logger.error(f"Error uploading file to S3: {e}")
        return None

def detect_faces_in_video(filename):
    try:
        response = rekognition.detect_faces(
            Video={'S3Object': {'Bucket': BUCKET_NAME, 'Name': filename}},
            Attributes=['ALL']
        )
        logger.info(f"Rekognition response: {response}")
        return response
    except Exception as e:
        logger.error(f"Error detecting faces: {e}")
        return None

@app.post("/upload_video")
async def upload_video(file: UploadFile = File(...)):
    try:
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(await file.read())
            tmp_file_path = tmp_file.name
        
        logger.info(f"Received file {file.filename}, saved as {tmp_file_path}")

        s3_filename = upload_to_s3(tmp_file_path)
        if s3_filename:
            response = detect_faces_in_video(s3_filename)
            os.remove(tmp_file_path)
            if response:
                return JSONResponse(content={"message": "File uploaded and processed successfully", "response": response})
            else:
                return JSONResponse(content={"message": "File uploaded but face detection failed"}, status_code=500)
        else:
            os.remove(tmp_file_path)
            return JSONResponse(content={"message": "File upload failed"}, status_code=500)
    except Exception as e:
        logger.error(f"Error in /upload_video endpoint: {e}")
        return JSONResponse(content={"message": f"Error processing video: {e}"}, status_code=500)

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.post("/clear_bucket")
async def clear_bucket():
    clear_s3_bucket()
    return {"message": "Bucket cleared successfully"}
