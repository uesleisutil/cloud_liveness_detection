# Quantum Finance - Facial Liveness Detection


## Descrição

Este projeto implementa um sistema de detecção de vivacidade facial para o aplicativo Quantum Finance. O objetivo é melhorar a segurança ao autenticar a identidade dos usuários através da detecção de vivacidade usando a câmera do dispositivo.

A aplicação utiliza o OpenCV para detectar faces e determinar a vivacidade. É construída usando Streamlit para a interface do usuário e FastAPI para os serviços de backend.

## Funcionalidades

- Captura de imagens em tempo real usando a câmera do dispositivo.
- Upload das imagens capturadas para o AWS S3.
- Análise de movimento e detecção de vivacidade facial usando AWS Rekognition.
- Feedback em tempo real sobre a autenticidade da face capturada.

## Estrutura do Projeto

```plaintext
.
├── .github/workflows
│   └── deploy.yml
├── app
│   ├── __init__.py
│   ├── api.py
│   ├── main.py
│   ├── streamlit_app.py
│   └── utils.py
├── .gitattributes
├── .gitignore
├── Dockerfile
├── requirements.txt
└── README.md
```

## Configuração e Deploy

### Pré-requisitos

- Conta AWS com permissões para EC2, S3 e VPC e Rekognition.
- Chaves de acesso AWS configuradas.
- Python 3.8 ou superior.

## Deploy na AWS EC2

Atualize o arquivo .github/workflows/deploy.yml com as variáveis necessárias no GitHub Secrets:

- AWS_ACCESS_KEY_ID
- AWS_SECRET_ACCESS_KEY
- AWS_DEFAULT_REGION
- SUBNET_ID
- SECURITY_GROUP_ID
- EC2_KEY_NAME
- AMI_ID_AWS
- NAT_GATEWAY_ELASTIC_IP (opcional)
- INTERNET_GATEWAY_ID (opcional)
- EC2_KEY_PEM (chave privada para SSH)

## Uso

### Componentes

- **Aplicativo Streamlit**: fornece uma interface web para capturar imagens e exibir resultados.
- **FastAPI**: fornece endpoints de API REST para detecção facial.
- **AWS Rekognition**: analisa as imagens para detecção facial e vivacidade.

### Aplicativo Streamlit
- Acesse a interface do Streamlit no navegador.
- Clique em "Capturar Imagem" para iniciar a captura de imagens.
- As imagens capturadas serão exibidas na tela.
- O sistema irá verificar a vivacidade e fornecer um feedback.
- Acesse a interface da web Streamlit em http://<EC2_IP>:8080.

## API FastAPI
- A API está configurada para lidar com uploads de imagens e análise de vivacidade.
- Endpoint principal: /upload/
- Para fazer uma requisição, envie um POST request com o arquivo da imagem.
- Endpoints FastAPI: acesse os endpoints FastAPI em http://<EC2_IP>:8000.
