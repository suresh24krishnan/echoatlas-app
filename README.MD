# EchoAtlas 🌍

EchoAtlas is a cultural intelligence assistant that helps you:
- Ask region-aware, city-specific cultural questions
- Get suggested phrases, tone, and gestures
- Build and browse a memory of past interactions
- Generate a **Cultural Playbook** for any region/city from your own questions

The app is built with **Streamlit**, **LangChain**, and **Chroma** and is designed to be deployed on:
- Local machine (for development)
- Streamlit Cloud / Hugging Face Spaces (for demos & hackathons)

---

## 🏗 Project Structure (high-level)

- `app_glass_ultra.py` — main Streamlit UI (EchoAtlas 2.0 glassmorphism version)
- `app.py` (if present) — small wrapper that imports & runs `app_glass_ultra`
- `agents/` — memory agent logic (`memory_agent.py`, etc.)
- `langchain_runner.py` — glue to call the LangChain agent (`run_agent`)
- `langchain_tools.py` — tools used by the agent
- `memory_store/` — Chroma DB files (ignored in git)
- `models/` — local models (e.g., Vosk) (ignored in git)
- `.streamlit/` — optional Streamlit config

> Note: `env/`, `memory_store/`, `models/` and other local-only artifacts are ignored by `.gitignore`.

---

## 🧰 Prerequisites

- Python 3.10+ (3.11 recommended)
- Git
- (Optional) Virtual environment: `venv` / `conda`

---

## 📦 Installation (local)

Clone the repo:

```bash
git clone https://github.com/suresh24krishnan/echoatlas-app.git
cd echoatlas-app

python -m venv env
# Windows:
env\\Scripts\\activate
# macOS / Linux:
# source env/bin/activate

pip install -r requirements.txt

streamlit run app_glass_ultra.py
streamlit run app.py
streamlit
openai
langchain
langchain-openai
chromadb
tiktoken
python-dotenv

# For local mic + Vosk experiments (optional)
streamlit-webrtc
vosk
av

# Other utilities
pydantic

Steps to add it:

```bash
cd "C:\Personal_Folders\EchoAtlasAppV10"

# make sure you're on the repo root
echo (or create via editor) README.md

git add README.md
git commit -m "Add README for EchoAtlas"
git push
env/
.venv/
venv/
__pycache__/
memory_store/
models/
.streamlit/
*.pyc
*.log
.env
git add .gitignore
git commit -m "Update .gitignore to ignore env, models, memory"
git push
