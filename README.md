<div align="center">
<br/>
<img src="static/static/splash.png" width="120px" alt="">
<br/>

# Open TutorAI 👋

![GitHub stars](https://img.shields.io/github/stars/Open-TutorAi/open-tutor-ai-CE?style=social)
![GitHub forks](https://img.shields.io/github/forks/Open-TutorAi/open-tutor-ai-CE?style=social)
![GitHub watchers](https://img.shields.io/github/watchers/Open-TutorAi/open-tutor-ai-CE?style=social)
![GitHub repo size](https://img.shields.io/github/repo-size/Open-TutorAi/open-tutor-ai-CE)
![GitHub language count](https://img.shields.io/github/languages/count/Open-TutorAi/open-tutor-ai-CE)
![GitHub top language](https://img.shields.io/github/languages/top/Open-TutorAi/open-tutor-ai-CE)
![GitHub last commit](https://img.shields.io/github/last-commit/Open-TutorAi/open-tutor-ai-CE)
[![Discord](https://img.shields.io/badge/Discord-Open_TutorAI-blue?logo=discord&logoColor=white)](https://discord.gg/BTQtE2deEm)

</div>
<br>
<div align="left">

**OpenTutorAI-CE** (Community Edition) is an open-source project designed to provide an educational and collaborative AI-powered platform. This public edition is the foundation for a proprietary Enterprise Edition (EE) and is built to encourage community contributions.

> [!TIP]  

> **Looking for a Support?** – **[Speak with our support Team Today!](mailto:opentutorai@gmail.com)**

>
> Get **enhanced capabilities**, including **custom theming and branding**, **Service Level Agreement (SLA) support**, **Long-Term Support (LTS) versions**, and **more!**

For more information, be sure to check out our [Open TutorAI Documentation](https://opentutorai.com/docs/intro).

## ⭐ Key Features of Open TutorAI

Open TutorAI-CE is packed with powerful features designed for educational and collaborative AI experiences. Here’s what makes it stand out:

- 🚀 **Effortless Setup with Docker**  
  Set up your environment in minutes using Docker with support for `:ollama` and `:cuda` tagged images, ensuring a streamlined and hassle-free deployment.

- 🤖 **Ollama & OpenAI API Compatibility**  
  Easily integrate OpenAI-compatible APIs for flexible conversations. Customize the API endpoint to connect with services like **LMStudio**, **GroqCloud**, **Mistral**, **OpenRouter**, and more—alongside local **Ollama** models.

- 🛡️ **Granular Permissions & User Groups**  
  Admins can define detailed roles and permissions, allowing for secure, customized user experiences while promoting accountability and collaboration.

- 🧑‍💻 **Responsive & Mobile-Optimized Design**  
  Enjoy a smooth user experience across desktops, laptops, and mobile devices with a fully responsive interface.

- 📱 **Progressive Web App (PWA) Support**  
  Install Open TutorAI on your mobile device for an app-like experience, including **offline mode** on localhost and full access to core functionality.

- 🎤📹 **Voice, Video & Avatar Discussion Mode**  
  Interact hands-free using integrated **voice and video calls**, or dive into an engaging experience with our **avatar-powered discussion mode**—a lifelike conversational interface that brings your AI to life.

- 🧑‍🏫 **Personalized Learning Experience**  
  Open TutorAI is purpose-built for education:  
  - 🎓 **Customize learning support** to meet individual learner needs.  
  - 🧠 **Generate a personalized LLM**, optionally paired with a user-selected **avatar**, tailored to each learner's style, personality, or curriculum.

- 🛠️ **Model Builder**: Easily create Ollama models. Create and add custom characters/agents, customize chat elements, and import models effortlessly.

- 📚 **Local RAG Integration for Educational Content**  
  Empower learners and educators with **Retrieval-Augmented Generation (RAG)** tailored for education. Seamlessly integrate textbooks, lecture notes, assignments, and research papers into the chat experience. Students can load documents directly into the conversation or access classroom resources from their document library using the `#` command—enabling **context-aware tutoring**, **assignment help**, and **in-depth discussion of study material**.
  
- 🔍 **Educational Web Search for RAG**  
  Enhance learning with real-time **web search integration**. Students and educators can perform targeted research using providers like `Google PSE`, `SearXNG`, `Brave`, `DuckDuckGo`, and more—right from the chat. The search results are automatically injected into the conversation, enabling **fact-checking**, **discovery of up-to-date information**, and **exploration of external academic resources** without leaving the tutoring environment.

- 🌐 **Web Browsing Capability**: Seamlessly integrate websites into your chat experience using the `#` command followed by a URL. This feature allows you to incorporate web content directly into your conversations, enhancing the richness and depth of your interactions.

- 🎨 **Image Generation Integration**: Seamlessly incorporate image generation capabilities using options such as AUTOMATIC1111 API or ComfyUI (local), and OpenAI's DALL-E (external), enriching your chat experience with dynamic visual content.

- ⚙️ **Many Models Conversations**: Effortlessly engage with various models simultaneously, harnessing their unique strengths for optimal responses. Enhance your experience by leveraging a diverse set of models in parallel.

- 🔐 **Role-Based Access Control (RBAC)**: Ensure secure access with restricted permissions; only authorized individuals can access your Ollama, and exclusive model creation/pulling rights are reserved for administrators.

- 🌐🌍 **Multilingual Support**: Experience Open TutorAI in your preferred language with our internationalization (i18n) support. Join us in expanding our supported languages! We're actively seeking contributors!

- 🌟 **Continuous Updates**: We are committed to improving Open TutorAI with regular updates, fixes, and new features.

Want to learn more about Open TutorAI's features? Check out our [Open TutorAI documentation](https://opentutorai.com/docs/intro) for a comprehensive overview!

## 🔗 Also Check Out Open TutorAI Community!

Don't forget to explore our sibling project, [Open TutorAI Community](https://discord.gg/BTQtE2deEm), where you can discover, download, and explore customized Modelfiles. Open TutorAI Community offers a wide range of exciting possibilities for enhancing your chat interactions with Open TutorAI! 🚀

## How to Install 🚀

Below is a list of essential steps and resources to help you get started, manage, and develop with Open TutorAI.

### 🛠️ Setup Guide
Follow these steps to set up the project locally:

1. **Fork and Clone the Repository**
   - Go to [GitHub Repository](https://github.com/Open-TutorAi/open-tutor-ai-CE)
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

### 🐳 Docker & Docker Compose Setup (Recommended)

For a hassle-free setup without installing Python, Node.js, or other dependencies, use Docker and Docker Compose.

#### Prerequisites
1. **Install Docker and Docker Compose** from [docker.com](https://www.docker.com/get-started)
2. **Git** for cloning the repository
3. **At least 8GB RAM** (recommended for AI models)

#### Step 1: Clone the Repository
```bash
git clone https://github.com/Open-TutorAi/open-tutor-ai-CE.git
cd open-tutor-ai-CE
```

#### Step 2: Set Up Environment Variables
```bash
cp .env.example .env
```

Edit `.env` file with a text editor. Default values are fine for local development:
```
OLLAMA_BASE_URL='http://localhost:11434'
OPENAI_API_BASE_URL=''
OPENAI_API_KEY=''
ENABLE_SIGNUP=true
WEBUI_SECRET_KEY=mysecretkey
SUPPRESS_WEBUI_BANNER=true
SCARF_NO_ANALYTICS=true
DO_NOT_TRACK=true
ANONYMIZED_TELEMETRY=false
```

#### Step 3: Choose Your Setup Method

**Option A: Full Stack with Docker Compose (Recommended)**

Ensure your `docker-compose.yaml` includes the Ollama service:
```yaml
ollama:
  image: ollama/ollama:latest
  container_name: ollama
  ports:
    - "11434:11434"
  volumes:
    - ollama:/root/.ollama
  networks:
    - app-network

volumes:
  ollama:
```

Also ensure the backend service has this environment variable:
```yaml
environment:
  - PYTHONUNBUFFERED=1
  - OLLAMA_BASE_URL=http://ollama:11434
```

Then start all services:
```bash
docker compose up --build
```

This starts backend (port 8080), frontend (port 5173), and Ollama (port 11434) together.

**Option B: Docker Compose without Ollama in Compose**

If your `docker-compose.yaml` does NOT include the Ollama service, start only backend and frontend:
```bash
docker compose up --build
```

Then in another terminal, start Ollama separately:
```bash
chmod +x run-ollama-docker.sh
./run-ollama-docker.sh
```

Ensure `.env` has the correct Ollama URL:
```
OLLAMA_BASE_URL='http://localhost:11434'
```

#### Step 4: Download AI Models

Once Ollama is running, download a model:
```bash
docker exec -it ollama ollama pull llama3.2
```

Verify the model is installed:
```bash
docker exec -it ollama ollama list
```

If the backend was already running before the model was installed, restart it:
```bash
docker restart open-tutor-backend
```

#### Step 5: Access the Application

Open your browser and go to `http://localhost:5173`. You should see the Open TutorAI interface!

- **Create an account** or log in
- **Select the model** (llama3.2 or any model you pulled)
- **Start a chat** with the AI

#### Stopping the Services

To stop all containers:
```bash
docker compose down
```

Or press `Ctrl + C` in the terminal where Docker Compose is running.

---

### Troubleshooting

Encountering connection issues? Our [Open TutorAI Documentation](https://opentutorai.com/docs/troubleshooting/) has got you covered. For further assistance and to join our vibrant community, visit the [Open TutorAI Discord](https://discord.gg/BTQtE2deEm).

## 🌟 What's Next? 

Discover upcoming features on our roadmap in the [Open TutorAI Documentation](https://opentutorai.com/docs/roadmap).

## 📜 License

This project is licensed under the [BSD-3-Clause License](LICENSE) - see the [LICENSE](LICENSE) file for details. 📄

## 💬 Support

If you have any questions, suggestions, or need assistance, please open an issue or join our
[Open TutorAI Discord community](https://discord.gg/BTQtE2deEm) to connect with us! 🤝

## Star History


<a href="https://www.star-history.com/#Open-TutorAi/open-tutor-ai-CE&Date">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=Open-TutorAi/open-tutor-ai-CE&type=Date&theme=dark" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=Open-TutorAi/open-tutor-ai-CE&type=Date" />
   <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=Open-TutorAi/open-tutor-ai-CE&type=Date" />
 </picture>
</a>

---

Created by [El Hajji](https://github.com/pr-elhajji) - Let's make Open TutorAI even more amazing together! 💪
