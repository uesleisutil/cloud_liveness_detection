import streamlit as st
import os
import requests

st.set_page_config(page_title="Quantum Finance - Facial Liveness Detection", layout="wide")

def main():
    st.title("Quantum Finance - Facial Liveness Detection")
    st.write("Click the button below to capture a video and verify liveness.")

    st.markdown(
        """
        <style>
        .record-button {
            padding: 10px 20px;
            font-size: 16px;
            color: #fff;
            background-color: #007bff;
            border: none;
            border-radius: 5px;
            cursor: pointer;
        }
        .record-button:hover {
            background-color: #0056b3;
        }
        </style>
        <button id="recordButton" class="record-button">Start Recording</button>
        <button id="stopButton" class="record-button" style="display: none;">Stop Recording</button>
        <video id="video" width="640" height="480" autoplay muted></video>
        <script>
        let mediaRecorder;
        let recordedBlobs;

        const video = document.querySelector('video');
        const recordButton = document.getElementById('recordButton');
        const stopButton = document.getElementById('stopButton');

        recordButton.addEventListener('click', async () => {
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
                    Streamlit.setComponentValue(data);
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
            recordButton.style.display = 'none';
            stopButton.style.display = 'block';
        });

        stopButton.addEventListener('click', () => {
            mediaRecorder.stop();
            video.srcObject.getTracks().forEach(track => track.stop());
            stopButton.style.display = 'none';
            recordButton.style.display = 'block';
        });
        </script>
        """,
        unsafe_allow_html=True,
    )

    if 'video_data' in st.session_state:
        video_data = st.session_state.video_data
        st.video(video_data)

        if st.button("Analyze Uploaded Video"):
            try:
                s3_filename = upload_to_s3(video_data)
                response = detect_faces_in_video(s3_filename)

                if response:
                    liveness_confidence = response['FaceDetails'][0]['Confidence']
                    st.success(f"Face detected successfully! Liveness confidence: {liveness_confidence:.2f}%")
                else:
                    st.error("No face detected or liveness criteria not met.")
            except Exception as e:
                st.error(f"Error: {e}")

if __name__ == "__main__":
    main()
