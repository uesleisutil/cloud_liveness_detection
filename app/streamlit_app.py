import streamlit as st
import cv2
import os
import tempfile
import uuid
import numpy as np
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.utils import upload_to_s3, detect_faces, clear_s3_bucket

def capture_images(num_images=10, delay=0.5, initial_delay=1):
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

    movement_detected = False
    for i in range(len(images) - 1):
        img1 = cv2.imread(images[i], cv2.IMREAD_GRAYSCALE)
        img2 = cv2.imread(images[i + 1], cv2.IMREAD_GRAYSCALE)

        diff = cv2.absdiff(img1, img2)
        non_zero_count = np.count_nonzero(diff)

        # Ajustar o limite de mudança aceitável
        threshold = 10000  # Ajuste para ser mais rigoroso
        if non_zero_count > threshold:
            movement_detected = True
            break

    return movement_detected

def detect_blinking(images):
    eye_statuses = []

    for image_path in images:
        img = cv2.imread(image_path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')

        detected_faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        for (x, y, w, h) in detected_faces:
            roi_gray = gray[y:y + h, x:x + w]
            detected_eyes = eye_cascade.detectMultiScale(roi_gray)
            eye_statuses.append(len(detected_eyes) > 0)

    # Verificar se há alternância entre olhos abertos e fechados
    blink_detected = any(eye_statuses[i] != eye_statuses[i + 1] for i in range(len(eye_statuses) - 1))
    return blink_detected

def main():
    st.title("Aplicativo de Detecção de Vivacidade Facial")
    st.write("Clique no botão abaixo para capturar uma imagem e verificar a vivacidade usando AWS Rekognition.")

    if st.button("Capturar Imagem"):
        try:
            clear_s3_bucket()  # Excluir todas as imagens do S3
            images, tempdirs = capture_images(initial_delay=2)  # Adicionar o atraso inicial
            for img in images:
                st.image(img, caption="Imagem Capturada", use_column_width=True)

            if not analyze_movement(images):
                st.warning("Vivacidade não detectada. Por favor, mova sua cabeça ou pisque.")
                return

            if not detect_blinking(images):
                st.warning("Vivacidade não detectada. Por favor, pisque.")
                return

            s3_filenames = []
            for img in images:
                s3_filename = upload_to_s3(img)
                if not s3_filename:
                    st.error("Failed to upload image to S3")
                    raise ValueError("Failed to upload image to S3")
                s3_filenames.append(s3_filename)

            st.write("Imagens carregadas no S3")

            response = detect_faces(s3_filenames[0])  # Usar a primeira imagem para detecção de faces
            if not response:
                st.error("Failed to detect faces")
                raise ValueError("Failed to detect faces")

            st.write("Detecção de faces realizada")

            face_detected = False
            for faceDetail in response['FaceDetails']:
                if is_liveness_detected(faceDetail):  # Verificar liveness
                    confidence = faceDetail['Confidence']
                    st.success(f"Confiança na vivacidade: {confidence:.2f}%")
                    face_detected = True
                    break

            if not face_detected:
                st.warning("Nenhuma face detectada ou critérios de vivacidade não atendidos.")

            # Remover arquivos temporários
            for img in images:
                os.remove(img)
            for tempdir in tempdirs:
                os.rmdir(tempdir)

        except Exception as e:
            st.error(f"Erro: {e}")

if __name__ == "__main__":
    main()