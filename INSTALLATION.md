# Getting Started with Open TutorAI

Welcome to the **Open TutorAI - Getting started** Below is a list of essential steps and resources to help you get started, manage, and develop with Open TutorAI.

## 🛠️ Setup Guide

Follow these steps to set up the project locally:

1. **Fork and Clone the Repository**
   - Go to [GitHub Repository](https://github.com/R2D-dev/open-tutor-ai-CE)
   - Click on **Fork**, then clone your forked repo:
     ```bash
     git clone https://github.com/YOUR_USERNAME/open-tutor-ai-CE.git
     cd open-tutor-ai-CE
     ```

2. **Backend Setup**
   - Navigate to the backend folder:
     ```bash
     cd backend
     ```
   - Create and activate a new Conda environment:
     ```bash
     conda create -n tutorai-env python=3.11
     conda activate tutorai-env
     ```
   - Install the required packages:
     ```bash
     pip install -r requirements.txt
     ```

   - For development:
     ```bash
     ./dev.sh
     ```
   - Or for production:
     ```bash
     ./start.sh
     ```

3. **Frontend Setup**
   - From the root of the project (or navigate to the frontend folder):
     ```bash
     npm install
     npm run dev
     ```

---
