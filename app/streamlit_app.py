import streamlit as st
import cv2
import os
import tempfile
import uuid
import numpy as np
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.utils import upload_to_s3, detect_faces, clear_s3_bucket

def capture_images(num_images=10, delay=0.2, initial_delay=1):
    cap = cv2.VideoCapture(0)
    images = []
    tempdirs = []

    # Adiciona um atraso inicial para permitir que a câmera se ajuste
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
    if len(images) < 2:
        return False

    total_movement = 0
    for i in range(len(images) - 1):
        img1 = cv2.imread(images[i], cv2.IMREAD_GRAYSCALE)
        img2 = cv2.imread(images[i + 1], cv2.IMREAD_GRAYSCALE)

        diff = cv2.absdiff(img1, img2)
        non_zero_count = np.count_nonzero(diff)
        total_movement += non_zero_count

    # Ajustar o limite de mudança aceitável
    threshold = 5000  # Relaxado para reduzir falsos negativos
    return total_movement > threshold

def main():
    # Adiciona estilo customizado ao Streamlit
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
        }
        .subheader {
            text-align: center;
            color: #333;
            font-size: 18px;
        }
        .captured-images {
            display: flex;
            justify-content: center;
            flex-wrap: wrap;
            gap: 10px;
        }
        .captured-images img {
            margin: 5px;
            width: 180px;
            height: auto;
            border-radius: 10px;
            box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1);
        }
        .error-message {
            color: red;
            font-weight: bold;
            text-align: center;
        }
        .success-message {
            color: green;
            font-weight: bold;
            text-align: center;
        }
        </style>
        """, 
        unsafe_allow_html=True
    )

    # Cabeçalho e título do aplicativo
    st.markdown('<div class="stMarkdown header">Quantum Finance</div>', unsafe_allow_html=True)
    st.markdown('<div class="stMarkdown subheader">Detecção de Vivacidade Facial</div>', unsafe_allow_html=True)
    st.markdown('<div class="stMarkdown subheader">Clique no botão abaixo para capturar imagens e verificar a vivacidade.</div>', unsafe_allow_html=True)
    
    if st.button("Capturar Imagem"):
        try:
            clear_s3_bucket()  # Excluir todas as imagens do S3
            images, tempdirs = capture_images(initial_delay=1)  # Adicionar o atraso inicial
            
            # Exibir imagens capturadas
            st.markdown('<div class="stMarkdown subheader">Imagens Capturadas:</div>', unsafe_allow_html=True)
            st.markdown('<div class="captured-images">', unsafe_allow_html=True)
            for img in images:
                st.image(img, caption="Imagem Capturada", use_column_width=False)
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

            response = detect_faces(s3_filenames[0])  # Usar a primeira imagem para detecção de faces
            if not response:
                st.markdown('<div class="stMarkdown error-message">Falha na detecção de faces.</div>', unsafe_allow_html=True)
                raise ValueError("Failed to detect faces")

            st.markdown('<div class="stMarkdown subheader">Detecção de faces realizada</div>', unsafe_allow_html=True)

            face_detected = False
            for faceDetail in response['FaceDetails']:
                if is_liveness_detected(faceDetail):  # Verificar liveness
                    confidence = faceDetail['Confidence']
                    st.markdown(f'<div class="stMarkdown success-message">Confiança na vivacidade: {confidence:.2f}%</div>', unsafe_allow_html=True)
                    face_detected = True
                    break

            if not face_detected:
                st.markdown('<div class="stMarkdown error-message">Nenhuma face detectada ou critérios de vivacidade não atendidos.</div>', unsafe_allow_html=True)

            # Remover arquivos temporários
            for img in images:
                os.remove(img)
            for tempdir in tempdirs:
                os.rmdir(tempdir)

        except Exception as e:
            st.markdown(f'<div class="stMarkdown error-message">Erro: {e}</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
