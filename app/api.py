from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import base64
import boto3
import os
from dotenv import load_dotenv

app = FastAPI()

load_dotenv()

AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
REGION_NAME = os.getenv('AWS_REGION')
BUCKET_NAME = os.getenv('S3_BUCKET')

rekognition = boto3.client('rekognition', aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY, region_name='us-east-1')
s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY, region_name='us-east-1')

@app.post("/upload")
async def upload_image(request: Request):
    try:
        data = await request.json()
        image_data = data['image'].split(",")[1]
        image_bytes = base64.b64decode(image_data)

        # Save image to a temporary file
        temp_image_path = "/tmp/uploaded_image.png"
        with open(temp_image_path, "wb") as f:
            f.write(image_bytes)

        # Upload to S3
        s3.upload_file(temp_image_path, BUCKET_NAME, "uploaded_image.png")

        # Use Rekognition to detect faces
        response = rekognition.detect_faces(
            Image={'S3Object': {'Bucket': BUCKET_NAME, 'Name': "uploaded_image.png"}},
            Attributes=['ALL']
        )
        return JSONResponse(content=response)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
