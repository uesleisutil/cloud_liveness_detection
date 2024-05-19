#!/bin/bash

# Variáveis de ambiente
INSTANCE_IP=$1
EC2_KEY_PATH=$2

# Conectar-se à instância EC2 e executar os comandos
ssh -o StrictHostKeyChecking=no -i $EC2_KEY_PATH ec2-user@$INSTANCE_IP << 'EOF'
cd /home/ec2-user/liveness_detection
git pull
pkill streamlit
nohup streamlit run app/streamlit_app.py --server.port 80 --server.address 0.0.0.0 &
EOF