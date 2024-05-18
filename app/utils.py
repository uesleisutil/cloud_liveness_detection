import boto3
import os
import uuid
import numpy as np
import cv2

def load_env():
    from dotenv import load_dotenv
    load_dotenv()

# Carregar variáveis de ambiente
load_env()

# Variáveis de ambiente
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
REGION_NAME = os.getenv('AWS_REGION')
BUCKET_NAME = os.getenv('S3_BUCKET')

rekognition = boto3.client('rekognition', aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY, region_name=REGION_NAME)
s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY, region_name=REGION_NAME)

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

def is_liveness_detected(face_details):
    # Critérios rigorosos para detecção de vivacidade
    if 'Confidence' in face_details and face_details['Confidence'] >= 99.0:
        if 'EyesOpen' in face_details and face_details['EyesOpen']['Value'] and face_details['EyesOpen']['Confidence'] >= 90:
            if 'MouthOpen' in face_details and not face_details['MouthOpen']['Value'] and face_details['MouthOpen']['Confidence'] >= 90:
                if 'Smile' in face_details and not face_details['Smile']['Value'] and face_details['Smile']['Confidence'] >= 90:
                    if 'Sunglasses' in face_details and not face_details['Sunglasses']['Value'] and face_details['Sunglasses']['Confidence'] >= 90:
                        return True
    return False

def analyze_movement(images):
    # Simples análise de movimento
    if len(images) < 2:
        return False

    img1 = cv2.imread(images[0], cv2.IMREAD_GRAYSCALE)
    img2 = cv2.imread(images[1], cv2.IMREAD_GRAYSCALE)

    diff = cv2.absdiff(img1, img2)
    non_zero_count = np.count_nonzero(diff)

    # Definir um limite de mudança aceitável
    threshold = 5000
    return non_zero_count > threshold
