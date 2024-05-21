import streamlit as st
import os
import tempfile
import streamlit.components.v1 as components
import boto3
from dotenv import load_dotenv
import cv2

# Carregar variáveis de ambiente
load_dotenv()

AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
REGION_NAME = os.getenv('AWS_REGION')
BUCKET_NAME = os.getenv('S3_BUCKET')

rekognition = boto3.client('rekognition', aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY, region_name='us-east-1')
s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY, region_name='us-east-1')

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

def handle_uploaded_video(video_file):
    tempdir = tempfile.mkdtemp()
    video_path = os.path.join(tempdir, "uploaded_video.webm")
    
    with open(video_path, 'wb') as f:
        f.write(video_file.read())

    return video_path, tempdir

# HTML and JavaScript for video capture
video_html = f"""
    <div>
        <video id="video" width="640" height="480" autoplay muted></video>
        <div>
            <button id="startButton">Start Recording</button>
            <button id="stopButton" disabled>Stop Recording</button>
        </div>
        <script>
            let mediaRecorder;
            let recordedBlobs;

            const video = document.querySelector('video');
            const startButton = document.getElementById('startButton');
            const stopButton = document.getElementById('stopButton');

            startButton.addEventListener('click', async () => {{
                console.log("Start button clicked");
                try {{
                    const stream = await navigator.mediaDevices.getUserMedia({{ video: true }});
                    console.log("Media stream obtained", stream);
                    video.srcObject = stream;
                    recordedBlobs = [];
                    const options = {{ mimeType: 'video/webm;codecs=vp9' }};
                    mediaRecorder = new MediaRecorder(stream, options);

                    mediaRecorder.onstop = async (event) => {{
                        console.log("Recording stopped", event);
                        const blob = new Blob(recordedBlobs, {{ type: 'video/webm' }});
                        const url = window.URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.style.display = 'none';
                        a.href = url;
                        a.download = 'test.webm';
                        document.body.appendChild(a);
                        a.click();
                        window.URL.revokeObjectURL(url);

                        const formData = new FormData();
                        formData.append('file', blob, 'recorded.webm');

                        fetch('http://44.207.160.25:8000/upload_video', {{
                            method: 'POST',
                            body: formData
                        }}).then(response => response.json())
                          .then(data => console.log('Success:', data))
                          .catch(error => console.error('Error:', error));
                    }};

                    mediaRecorder.ondataavailable = (event) => {{
                        if (event.data && event.data.size > 0) {{
                            recordedBlobs.push(event.data);
                        }}
                    }};

                    mediaRecorder.start();
                    console.log("MediaRecorder started", mediaRecorder);
                    startButton.disabled = true;
                    stopButton.disabled = false;
                }} catch (error) {{
                    console.error("Error accessing media devices.", error);
                }}
            }});

            stopButton.addEventListener('click', () => {{
                mediaRecorder.stop();
                video.srcObject.getTracks().forEach(track => track.stop());
                startButton.disabled = false;
                stopButton.disabled = true;
            }});
        </script>
    </div>
"""

def main():
    st.title("Quantum Finance - Facial Liveness Detection")
    st.write("Click the button below to capture a video and verify liveness.")

    components.html(video_html, height=600)

    uploaded_video = st.file_uploader("Upload your recorded video", type=["webm", "mp4", "avi", "mov"])
    if uploaded_video is not None:
        video_path, tempdir = handle_uploaded_video(uploaded_video)

        st.video(video_path)

        if st.button("Analyze Uploaded Video"):
            try:
                clear_s3_bucket()
                s3_filename = upload_to_s3(video_path)
                response = detect_faces_in_video(s3_filename)

                if response:
                    liveness_confidence = response['FaceDetails'][0]['Confidence']
                    st.success(f"Face detected successfully! Liveness confidence: {liveness_confidence:.2f}%")
                else:
                    st.error("No face detected or liveness criteria not met.")
            except Exception as e:
                st.error(f"Error: {e}")
            finally:
                os.remove(video_path)
                os.rmdir(tempdir)

if __name__ == "__main__":
    main()
