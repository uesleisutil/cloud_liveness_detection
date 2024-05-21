import streamlit as st
import cv2
import os
import tempfile
import uuid
from app.utils import upload_to_s3, detect_faces, clear_s3_bucket, analyze_movement

def capture_images(num_images=10, delay=0.2, initial_delay=1):
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise Exception("Could not open webcam")
    images = []
    tempdirs = []

    st.info(f"Initial delay of {initial_delay} seconds to adjust camera...")
    cv2.waitKey(initial_delay * 1000)

    for _ in range(num_images):
        ret, frame = cap.read()
        if not ret:
            cap.release()
            raise Exception("Could not capture image from webcam")
        tempdir = tempfile.mkdtemp()
        filename = os.path.join(tempdir, f"temp_{uuid.uuid4()}.jpg")
        cv2.imwrite(filename, frame)
        images.append(filename)
        tempdirs.append(tempdir)
        st.info(f"Captured image {_ + 1}")
        cv2.waitKey(int(delay * 1000))

    cap.release()
    return images, tempdirs

def main():
    st.title("Quantum Finance - Facial Liveness Detection")
    st.write("Click the button below to capture images and verify liveness.")

    if st.button("Capture Image"):
        try:
            clear_s3_bucket()
            images, tempdirs = capture_images()

            st.write("Captured Images:")
            for img in images:
                st.image(img, caption="Captured Image", use_column_width=True)

            if not analyze_movement(images):
                st.error("Liveness not detected. Please move your head.")
                return

            s3_filenames = [upload_to_s3(img) for img in images]
            response = detect_faces(s3_filenames[0])

            if response:
                st.success("Face detected successfully!")
            else:
                st.error("No face detected or liveness criteria not met.")

            for img in images:
                os.remove(img)
            for tempdir in tempdirs:
                os.rmdir(tempdir)

        except Exception as e:
            st.error(f"Error: {e}")

if __name__ == "__main__":
    main()
