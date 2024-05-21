import streamlit as st
import os
import tempfile
from utils import upload_to_s3, detect_faces_in_video, clear_s3_bucket
import streamlit.components.v1 as components
from dotenv import load_dotenv

load_dotenv()

DOMAIN_NAME = 'cloud_liveness_fiap.com' 

def handle_uploaded_video(video_file):
    tempdir = tempfile.mkdtemp()
    video_path = os.path.join(tempdir, "uploaded_video.webm")
    
    with open(video_path, 'wb') as f:
        f.write(video_file.read())

    return video_path, tempdir

# HTML and JavaScript for video capture
video_html = """
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

                    fetch('http://your-ec2-public-ip:8000/upload_video', {{
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
""".format(DOMAIN_NAME)

def main():
    st.title("Quantum Finance - Facial Liveness Detection")
    st.write("Click the button below to capture a video and verify liveness.")

    components.html(video_html, height=600)

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