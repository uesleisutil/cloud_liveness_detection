import cv2
import os
from utils import upload_to_s3, detect_faces

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
                if is_liveness_detected(faceDetail):
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