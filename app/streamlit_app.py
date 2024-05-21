import streamlit as st
import boto3
import os
from dotenv import load_dotenv
import cv2
import base64
import requests

# Load environment variables
load_dotenv()

AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
REGION_NAME = os.getenv('AWS_REGION')
BUCKET_NAME = os.getenv('S3_BUCKET')

rekognition = boto3.client('rekognition', aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY, region_name='us-east-1')
s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY, region_name='us-east-1')

def main():
    st.title("Webcam Capture with AWS Rekognition")

    # Serve the HTML page
    st.markdown("""
        <iframe src="/static/index.html" width="100%" height="600px"></iframe>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
