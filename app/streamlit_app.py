import streamlit as st
import cv2
import os
import tempfile
import uuid
import numpy as np
from utils import upload_to_s3, detect_faces_in_video, clear_s3_bucket

def capture_video():
    video_file = st.file_uploader("Upload a video file", type=["mp4", "mov", "avi"])
    if video_file:
        tempdir = tempfile.mkdtemp()
        filepath = os.path.join(tempdir, video_file.name)
        with open(filepath, 'wb') as f:
            f.write(video_file.read())
        return filepath, tempdir
    else:
        return None, None

def main():
    st.title("Quantum Finance - Facial Liveness Detection")
    st.write("Click the button below to capture a video and verify liveness.")

    if st.button("Capture Video"):
        try:
            clear_s3_bucket()
            filepath, tempdir = capture_video()
            
            if filepath:
                st.write("Captured Video:")
                st.video(filepath)

                s3_filename = upload_to_s3(filepath)
                response = detect_faces_in_video(s3_filename)

                if response:
                    liveness_confidence = response['FaceDetails'][0]['Confidence']
                    st.success(f"Face detected successfully! Liveness confidence: {liveness_confidence:.2f}%")
                else:
                    st.error("No face detected or liveness criteria not met.")

                os.remove(filepath)
                os.rmdir(tempdir)
            else:
                st.error("No video captured.")

        except Exception as e:
            st.error(f"Error: {e}")

if __name__ == "__main__":
    main()
