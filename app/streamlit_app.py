import streamlit as st
import os
import tempfile
from utils import upload_to_s3, detect_faces_in_video, clear_s3_bucket
import streamlit.components.v1 as components

# Function to handle the uploaded video file
def handle_uploaded_video(video_file):
    tempdir = tempfile.mkdtemp()
    video_path = os.path.join(tempdir, "uploaded_video.webm")
    
    with open(video_path, 'wb') as f:
        f.write(video_file.read())

    return video_path, tempdir

# HTML and JavaScript for video capture
video_html = """
    <video id="video" width="640" height="480" autoplay></video>
    <button id="startButton">Start Recording</button>
    <button id="stopButton" disabled>Stop Recording</button>
    <script>
        let mediaRecorder;
        let recordedBlobs;

        const video = document.querySelector('video');
        const startButton = document.getElementById('startButton');
        const stopButton = document.getElementById('stopButton');

        startButton.addEventListener('click', async () => {
            const stream = await navigator.mediaDevices.getUserMedia({ video: true });
            video.srcObject = stream;
            recordedBlobs = [];
            const options = { mimeType: 'video/webm;codecs=vp9' };
            mediaRecorder = new MediaRecorder(stream, options);

            mediaRecorder.onstop = async (event) => {
                const blob = new Blob(recordedBlobs, { type: 'video/webm' });
                const formData = new FormData();
                formData.append('file', blob, 'recorded.webm');

                const response = await fetch('/upload_video', {
                    method: 'POST',
                    body: formData
                });

                if (response.ok) {
                    const data = await response.json();
                    console.log('Success:', data);
                } else {
                    console.error('Upload failed.');
                }
            };

            mediaRecorder.ondataavailable = (event) => {
                if (event.data && event.data.size > 0) {
                    recordedBlobs.push(event.data);
                }
            };

            mediaRecorder.start();
            startButton.disabled = true;
            stopButton.disabled = false;
        });

        stopButton.addEventListener('click', () => {
            mediaRecorder.stop();
            video.srcObject.getTracks().forEach(track => track.stop());
            startButton.disabled = false;
            stopButton.disabled = true;
        });
    </script>
"""

def main():
    st.title("Quantum Finance - Facial Liveness Detection")
    st.write("Click the button below to capture a video and verify liveness.")

    components.html(video_html)

    uploaded_video = st.file_uploader("Upload your recorded video", type=["webm"])
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
