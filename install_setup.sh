#!/bin/bash
# Open Tutor AI Environment Setup Script
# Based on local Ubuntu 22.04 configuration

echo "1. Cloning repository..."
git clone git@github.com:Ouissal99/open-tutor-ai-CE.git
cd open-tutor-ai-CE

echo "2. Setting up Node.js environment..."
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
source ~/.bashrc
nvm install 20
npm install

echo "3. Setting up Python backend environment..."
cd backend
conda create -n tutorai-env python=3.11 -y
conda activate tutorai-env

echo "4. Installing Python dependencies..."
pip install -r requirements.txt
pip install --upgrade packaging
pip install packaging==23.2

echo "Setup complete. Ready to run using ./dev.sh or npm run dev."
