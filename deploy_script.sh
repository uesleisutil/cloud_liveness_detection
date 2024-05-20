#!/bin/bash
set -e

# Stop any running package managers
sudo pkill -f yum || true
sudo pkill -f apt-get || true
sudo pkill -9 -f yum || true
sudo pkill -9 -f apt-get || true
sudo killall -9 yum || true
sudo killall -9 apt-get || true

# Clean and update package cache
sudo yum clean all
sudo yum makecache

echo "Atualizando pacotes e instalando dependências"
timeout 5m sudo yum update -y
timeout 5m sudo yum install -y python3 tmux

echo "Instalando bibliotecas Python"
sudo python3 -m ensurepip
sudo pip3 install --upgrade pip
sudo pip3 install -r /home/ec2-user/liveness_detection/requirements.txt

# Verifica se o Streamlit foi instalado corretamente
if ! command -v streamlit &> /dev/null
then
    echo "Streamlit não foi instalado corretamente"
    exit 1
fi

# Adicione o caminho do Streamlit ao PATH
export PATH=$PATH:/usr/local/bin/

# Inicia o Streamlit usando tmux
tmux new -d -s streamlit_session "streamlit run /home/ec2-user/liveness_detection/app/streamlit_app.py --server.port 8080 --server.address 0.0.0.0"
