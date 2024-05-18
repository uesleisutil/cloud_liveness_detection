import cv2
import os
import tempfile
import uuid
from app.utils import upload_to_s3, detect_faces

def capture_image():
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    if ret:
        tempdir = tempfile.mkdtemp()
        filename = os.path.join(tempdir, f"temp_{uuid.uuid4()}.jpg")
        cv2.imwrite(filename, frame)
        cap.release()
        return filename, tempdir
    else:
        cap.release()
        raise Exception("Could not capture image from webcam")

def main():
    try:
        filename, tempdir = capture_image()
        print("Imagem capturada")
        
        s3_filename = upload_to_s3(filename)
        if not s3_filename:
            raise ValueError("Failed to upload image to S3")

        print("Imagem carregada no S3")

        response = detect_faces(s3_filename)
        if not response:
            raise ValueError("Failed to detect faces")

        print("Detecção de faces realizada")

        for faceDetail in response['FaceDetails']:
            if 'Confidence' in faceDetail:
                confidence = faceDetail['Confidence']
                print(f"Confiança na vivacidade: {confidence:.2f}%")
            else:
                print("Nenhuma face detectada.")

        # Remover arquivo temporário
        os.remove(filename)
        os.rmdir(tempdir)

    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    main()
import cv2
import os
import tempfile
import uuid
from app.utils import upload_to_s3, detect_faces

def capture_image():
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    if ret:
        tempdir = tempfile.mkdtemp()
        filename = os.path.join(tempdir, f"temp_{uuid.uuid4()}.jpg")
        cv2.imwrite(filename, frame)
        cap.release()
        return filename, tempdir
    else:
        cap.release()
        raise Exception("Could not capture image from webcam")

def main():
    try:
        filename, tempdir = capture_image()
        print("Imagem capturada")
        
        s3_filename = upload_to_s3(filename)
        if not s3_filename:
            raise ValueError("Failed to upload image to S3")

        print("Imagem carregada no S3")

        response = detect_faces(s3_filename)
        if not response:
            raise ValueError("Failed to detect faces")

        print("Detecção de faces realizada")

        for faceDetail in response['FaceDetails']:
            if 'Confidence' in faceDetail:
                confidence = faceDetail['Confidence']
                print(f"Confiança na vivacidade: {confidence:.2f}%")
            else:
                print("Nenhuma face detectada.")

        # Remover arquivo temporário
        os.remove(filename)
        os.rmdir(tempdir)

    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    main()
