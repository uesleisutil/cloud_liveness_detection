import os
import boto3
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File
from starlette.responses import JSONResponse
import tempfile

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
async def upload_video(file: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_file.write(await file.read())
        tmp_file_path = tmp_file.name
    
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

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.post("/clear_bucket")
async def clear_bucket():
    clear_s3_bucket()
    return {"message": "Bucket cleared successfully"}
