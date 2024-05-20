from fastapi.responses import JSONResponse
import uvicorn
import os
import tempfile
import uuid
import cv2
import numpy as np

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

    # Ajustar o limite de mudança aceitável
    threshold = 5000  # Relaxado para reduzir falsos negativos
    return total_movement > threshold

@app.post("/capture-images/")
async def capture_images_api(num_images: int = 10, delay: float = 0.2, initial_delay: float = 1):
    cap = cv2.VideoCapture(0)
    images = []
    tempdirs = []

    # Adiciona um atraso inicial para permitir que a câmera se ajuste
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

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)