#!/bin/bash
sudo yum update -y
sudo yum install -y python3 git
sudo pip3 install --upgrade pip
sudo pip3 install boto3 opencv-python-headless python-dotenv streamlit fastapi uvicorn
git clone https://github.com/uesleisutil/liveness_detection.git /home/ec2-user/liveness_detection
cd /home/ec2-user/liveness_detection
nohup streamlit run app/streamlit_app.py --server.port 80 --server.address 0.0.0.0 &
