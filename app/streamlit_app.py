import streamlit as st
import os
import tempfile
import uuid
import time
from utils import upload_to_s3, detect_faces_in_video, clear_s3_bucket

def main():
    st.title("Quantum Finance - Facial Liveness Detection")
    st.write("Click the button below to capture a video and verify liveness.")

    st.markdown(
        """
        <script>
        const videoElement = document.createElement('video');
        const startButton = document.createElement('button');
        startButton.textContent = 'Start Recording';
        const stopButton = document.createElement('button');
        stopButton.textContent = 'Stop Recording';
        const uploadButton = document.createElement('button');
        uploadButton.textContent = 'Upload Video';
        const downloadLink = document.createElement('a');
        downloadLink.style.display = 'none';
        document.body.appendChild(videoElement);
        document.body.appendChild(startButton);
        document.body.appendChild(stopButton);
        document.body.appendChild(uploadButton);
        document.body.appendChild(downloadLink);

        let mediaRecorder;
        let recordedBlobs;

        startButton.addEventListener('click', async () => {
            const stream = await navigator.mediaDevices.getUserMedia({ video: true });
            videoElement.srcObject = stream;
            recordedBlobs = [];
            const options = { mimeType: 'video/webm;codecs=vp9' };
            mediaRecorder = new MediaRecorder(stream, options);

            mediaRecorder.onstop = (event) => {
                const blob = new Blob(recordedBlobs, { type: 'video/webm' });
                const url = window.URL.createObjectURL(blob);
                downloadLink.href = url;
                downloadLink.download = 'recorded.webm';
                downloadLink.style.display = 'block';
            };

            mediaRecorder.ondataavailable = (event) => {
                if (event.data && event.data.size > 0) {
                    recordedBlobs.push(event.data);
                }
            };

            mediaRecorder.start();
            console.log('MediaRecorder started', mediaRecorder);
        });

        stopButton.addEventListener('click', () => {
            mediaRecorder.stop();
            videoElement.srcObject.getTracks().forEach(track => track.stop());
        });

        uploadButton.addEventListener('click', () => {
            const blob = new Blob(recordedBlobs, { type: 'video/webm' });
            const formData = new FormData();
            formData.append('file', blob, 'recorded.webm');

            fetch('/upload_video', {
                method: 'POST',
                body: formData,
            }).then(response => response.json()).then(data => {
                console.log('Success:', data);
            }).catch(error => {
                console.error('Error:', error);
            });
        });
        </script>
        """,
        unsafe_allow_html=True,
    )

    if st.button("Analyze Uploaded Video"):
        try:
            video_filename = "recorded.webm"
            if os.path.exists(video_filename):
                clear_s3_bucket()
                s3_filename = upload_to_s3(video_filename)
                response = detect_faces_in_video(s3_filename)

                if response:
                    liveness_confidence = response['FaceDetails'][0]['Confidence']
                    st.success(f"Face detected successfully! Liveness confidence: {liveness_confidence:.2f}%")
                else:
                    st.error("No face detected or liveness criteria not met.")
            else:
                st.error("No video uploaded.")

        except Exception as e:
            st.error(f"Error: {e}")

if __name__ == "__main__":
    main()
