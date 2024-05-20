import threading
import uvicorn
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import streamlit as st
import cv2
import os
import tempfile
import uuid
import numpy as np

# FastAPI application
app = FastAPI()

def detect_faces_opencv(image_path):
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.1, 4)
    return faces

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

    threshold = 5000  # Relaxado para reduzir falsos negativos
    return total_movement > threshold

@app.post("/capture-images/")
async def capture_images_api(num_images: int = 10, delay: float = 0.2, initial_delay: float = 1):
    cap = cv2.VideoCapture(0)
    images = []
    tempdirs = []

    cv2.waitKey(int(initial_delay * 1000))

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
            raise HTTPException(status_code=500, detail="Could not capture image from webcam")

    cap.release()
    return JSONResponse(content={"images": images})

@app.post("/detect-faces/")
async def detect_faces_api(file: UploadFile = File(...)):
    try:
        tempdir = tempfile.mkdtemp()
        file_path = os.path.join(tempdir, f"{uuid.uuid4()}.jpg")
        with open(file_path, "wb") as f:
            f.write(file.file.read())
        
        faces = detect_faces_opencv(file_path)
        if len(faces) == 0:
            raise HTTPException(status_code=404, detail="No faces detected")

        return JSONResponse(content={"message": "Face(s) detected", "faces": faces.tolist()})

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        os.remove(file_path)
        os.rmdir(tempdir)

@app.post("/analyze-movement/")
async def analyze_movement_api(files: list[UploadFile] = File(...)):
    try:
        tempdir = tempfile.mkdtemp()
        file_paths = []
        for file in files:
            file_path = os.path.join(tempdir, f"{uuid.uuid4()}.jpg")
            with open(file_path, "wb") as f:
                f.write(file.file.read())
            file_paths.append(file_path)

        if not analyze_movement(file_paths):
            raise HTTPException(status_code=400, detail="Insufficient movement detected")

        return JSONResponse(content={"message": "Sufficient movement detected"})

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        for file_path in file_paths:
            os.remove(file_path)
        os.rmdir(tempdir)

def run_fastapi():
    uvicorn.run(app, host="0.0.0.0", port=8000)

def run_streamlit():
    st.set_page_config(page_title="Quantum Finance - Facial Liveness Detection", layout="wide")

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

    # Custom styles
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
            width: 400px; /* Ajuste o tamanho das imagens */
            height: 300px;
            object-fit: cover; /* Centralizar as imagens */
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
        unsafe_allow_html=True,
    )

    # Header and title of the application
    st.markdown('<div class="stMarkdown header">Quantum Finance</div>', unsafe_allow_html=True)
    st.markdown('<div class="stMarkdown subheader">Detecção de Vivacidade Facial</div>', unsafe_allow_html=True)
    st.markdown('<div class="stMarkdown subheader">Clique no botão abaixo para capturar imagens e verificar a vivacidade.</div>', unsafe_allow_html=True)

    if st.button("Capturar Imagem"):
        try:
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

            faces_detected = False
            for img in images:
                faces = detect_faces_opencv(img)
                if len(faces) > 0:
                    st.markdown('<div class="stMarkdown success-message">Face detectada com sucesso!</div>', unsafe_allow_html=True)
                    faces_detected = True
                    break

            if not faces_detected:
                st.markdown('<div class="stMarkdown error-message">Nenhuma face detectada ou critérios de vivacidade não atendidos.</div>', unsafe_allow_html=True)

            for img in images:
                os.remove(img)
            for tempdir in tempdirs:
                os.rmdir(tempdir)

        except Exception as e:
            st.markdown(f'<div class="stMarkdown error-message">Erro: {e}</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    # Run FastAPI in a separate thread
    fastapi_thread = threading.Thread(target=run_fastapi)
    fastapi_thread.daemon = True
    fastapi_thread.start()

    # Run Streamlit
    run_streamlit()