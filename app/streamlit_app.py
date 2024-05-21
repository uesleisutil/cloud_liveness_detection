import streamlit as st
from utils import upload_to_s3, detect_faces, clear_s3_bucket, analyze_movement
import cv2
import os
import tempfile
import uuid
import numpy as np
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.utils import upload_to_s3, detect_faces, clear_s3_bucket, analyze_movement

def capture_images(num_images=10, delay=0.2, initial_delay=1):
    cap = cv2.VideoCapture(0)
    images = []
    tempdirs = []

    cv2.waitKey(initial_delay * 1000)

    for _ in range(num_images):
        ret, frame = cap.read()
        if ret:
            tempdir = tempfile.mkdtemp()
            filename = os.path.join(tempdir, f"temp_{uuid.uuid4()}.jpg")
            cv2.imwrite(filename, frame)
            images.append(filename)
            tempdirs.append(tempdir)
            cv2.waitKey(int(delay * 1000))
        else:
            cap.release()
            raise Exception("Could not capture image from webcam")

    cap.release()
    return images, tempdirs

def resize_and_center_image(image_path, target_size=(400, 300)):
    img = cv2.imread(image_path)
    h, w = img.shape[:2]
    target_w, target_h = target_size

    scale = min(target_w / w, target_h / h)
    new_w = int(w * scale)
    new_h = int(h * scale)

    resized_img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)

    top_pad = (target_h - new_h) // 2
    bottom_pad = target_h - new_h - top_pad
    left_pad = (target_w - new_w) // 2
    right_pad = target_w - new_w - left_pad

    padded_img = cv2.copyMakeBorder(resized_img, top_pad, bottom_pad, left_pad, right_pad, cv2.BORDER_CONSTANT, value=[0, 0, 0])
    return padded_img

def main():
    st.markdown(
        """
        <style>
        .main {
            background-color: #f5f5f5;
            font-family: 'Arial', sans-serif;
        }
        .stButton > button {
            background-color: #007bff;
            color: white;
            padding: 10px 24px;
            border-radius: 25px;
            border: none;
            font-size: 16px;
            font-weight: bold;
            display: block;
            margin: 0 auto;
        }
        .stButton > button:hover {
            background-color: #0056b3;
        }
        .stMarkdown {
            background-color: #ffffff;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1);
        }
        .header {
            text-align: center;
            color: #007bff;
            font-size: 32px;
            font-weight: bold;
            margin-bottom: 20px;
        }
        .subheader {
            text-align: center;
            color: #333;
            font-size: 18px;
            margin-bottom: 20px;
        }
        .captured-images {
            display: flex;
            justify-content: center;
            flex-wrap: wrap;
            gap: 10px;
            margin-bottom: 20px;
        }
        .captured-images img {
            width: 400px;
            height: 300px;
            object-fit: cover;
            border-radius: 10px;
            box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1);
        }
        .error-message {
            color: red;
            font-weight: bold;
            text-align: center;
            margin-bottom: 20px;
        }
        .success-message {
            color: green;
            font-weight: bold;
            text-align: center;
            margin-bottom: 20px;
        }
        </style>
        """, 
        unsafe_allow_html=True
    )

    st.markdown('<div class="stMarkdown header">Quantum Finance</div>', unsafe_allow_html=True)
    st.markdown('<div class="stMarkdown subheader">Detecção de Vivacidade Facial</div>', unsafe_allow_html=True)
    st.markdown('<div class="stMarkdown subheader">Clique no botão abaixo para capturar imagens e verificar a vivacidade.</div>', unsafe_allow_html=True)
    
    if st.button("Capturar Imagem"):
        try:
            clear_s3_bucket()
            images, tempdirs = capture_images(initial_delay=1)
            
            st.markdown('<div class="stMarkdown subheader">Imagens Capturadas:</div>', unsafe_allow_html=True)
            st.markdown('<div class="captured-images">', unsafe_allow_html=True)
            for img in images:
                resized_img = resize_and_center_image(img)
                temp_img_path = os.path.join(tempfile.gettempdir(), f"resized_{uuid.uuid4()}.jpg")
                cv2.imwrite(temp_img_path, resized_img)
                st.image(temp_img_path, caption="Imagem Capturada", use_column_width=False)
            st.markdown('</div>', unsafe_allow_html=True)

            if not analyze_movement(images):
                st.markdown('<div class="stMarkdown error-message">Vivacidade não detectada. Por favor, mova sua cabeça.</div>', unsafe_allow_html=True)
                return

            s3_filenames = []
            for img in images:
                s3_filename = upload_to_s3(img)
                if not s3_filename:
                    st.markdown('<div class="stMarkdown error-message">Falha ao carregar imagem no S3.</div>', unsafe_allow_html=True)
                    raise ValueError("Failed to upload image to S3")
                s3_filenames.append(s3_filename)

            st.markdown('<div class="stMarkdown subheader">Imagens carregadas no S3</div>', unsafe_allow_html=True)

            response = detect_faces(s3_filenames[0])
            if not response:
                st.markdown('<div class="stMarkdown error-message">Falha na detecção de faces.</div>', unsafe_allow_html=True)
                raise ValueError("Failed to detect faces")

            st.markdown('<div class="stMarkdown subheader">Detecção de faces realizada</div>', unsafe_allow_html=True)

            face_detected = False
            for faceDetail in response['FaceDetails']:
                if is_liveness_detected(faceDetail):
                    confidence = faceDetail['Confidence']
                    st.markdown(f'<div class="stMarkdown success-message">Confiança na vivacidade: {confidence:.2f}%</div>', unsafe_allow_html=True)
                    face_detected = True
                    break

            if not face_detected:
                st.markdown('<div class="stMarkdown error-message">Nenhuma face detectada ou critérios de vivacidade não atendidos.</div>', unsafe_allow_html=True)

            for img in images:
                os.remove(img)
            for tempdir in tempdirs:
                os.rmdir(tempdir)

        except Exception as e:
            st.markdown(f'<div class="stMarkdown error-message">Erro: {e}</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()