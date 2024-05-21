#!/bin/bash

# Instalar awscli se não estiver instalado
if ! command -v aws &> /dev/null
then
    sudo apt-get update
    sudo apt-get install -y awscli
fi

# Atualizar o registro DNS com o IP público da instância
INSTANCE_ID=$(curl -s http://169.254.169.254/latest/meta-data/instance-id)
PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)
HOSTED_ZONE_ID=YOUR_HOSTED_ZONE_ID  # Substitua pelo seu Hosted Zone ID
RECORD_SET_NAME=your-subdomain.yourdomain.com  # Substitua pelo seu nome de domínio ou subdomínio

cat > update-dns.json << EOF
{
  "Comment": "Atualizando o registro A para apontar para o IP público da instância EC2",
  "Changes": [
    {
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "$RECORD_SET_NAME",
        "Type": "A",
        "TTL": 60,
        "ResourceRecords": [{ "Value": "$PUBLIC_IP" }]
      }
    }
  ]
}
EOF

aws route53 change-resource-record-sets --hosted-zone-id $HOSTED_ZONE_ID --change-batch file://update-dns.json

#!/bin/bash
sudo yum update -y
sudo yum install -y python3 git
sudo pip3 install --upgrade pip
sudo pip3 install boto3 opencv-python-headless python-dotenv streamlit fastapi uvicorn
sudo systemctl start sshd
sudo systemctl enable sshd
sudo systemctl status sshd
git clone https://github.com/uesleisutil/liveness_detection.git /home/ec2-user/liveness_detection
cd /home/ec2-user/liveness_detection