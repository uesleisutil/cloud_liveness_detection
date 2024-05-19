#!/bin/bash

# Variáveis de ambiente
INSTANCE_IP=$1
EC2_KEY_PEM=$2

# Criar arquivo temporário para a chave privada
KEY_FILE=$(mktemp /tmp/ec2-key.XXXXXX.pem)
echo "$EC2_KEY_PEM" > $KEY_FILE
chmod 400 $KEY_FILE

# Conectar-se à instância EC2 e executar os comandos
ssh -o StrictHostKeyChecking=no -i $KEY_FILE ec2-user@$INSTANCE_IP << 'EOF'
cd /home/ec2-user/liveness_detection
git pull
pkill streamlit
nohup streamlit run app/streamlit_app.py --server.port 80 --server.address 0.0.0.0 &
EOF

# Remover o arquivo temporário
rm -f $KEY_FILE
