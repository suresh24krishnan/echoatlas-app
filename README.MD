# 🌍 EchoAtlas

[![Hugging Face Spaces](https://img.shields.io/badge/🤗%20Hugging%20Face-EchoAtlas-blue)](https://huggingface.co/spaces/YOUR_USERNAME/EchoAtlas)

**Real-time cultural translator for global and Indian state empathy.**  
Built with Streamlit + Weaviate. Demo-ready, memory-powered, and emotionally intelligent.

---

## 🚀 EchoAtlas is Live on Hugging Face Spaces

What if cultural empathy could be translated in real time?

Introducing **EchoAtlas**—a multi-agent AI app that transforms everyday phrases into culturally appropriate expressions across global and Indian regions. Whether you're navigating Tokyo, Chennai, Kerala, Paris, or Cairo, EchoAtlas helps you speak with respect, warmth, and local nuance.

🧠 Powered by:
- Modular agents for tone, gesture, and phrasing
- Embedded memory graph via Weaviate
- Streamlit UI with simulated voice input
- Lightweight, hackathon-ready architecture

🎯 Built for:
- Travelers, educators, and cultural enthusiasts
- Hackathons and AI showcases
- Anyone who believes empathy is a superpower

🔗 [Try it on Hugging Face Spaces](https://huggingface.co/spaces/YOUR_USERNAME/EchoAtlas)

---

## ✨ Features

- 🎤 Dual input: mic (simulated) + text
- 🌐 Mode toggle: International vs Indian States
- 🧠 Agentic suggestions: culturally appropriate phrasing, tone, gestures, and etiquette
- 🧬 Semantic memory: stores and recalls past interactions using Weaviate vector search
- 🗺️ Demo regions: Tokyo 🇯🇵, Chennai 🇮🇳, Kerala 🇮🇳, Paris 🇫🇷, Cairo 🇪🇬

---

## 🧱 Architecture

EchoAtlas uses a modular multi-agent design:

| Agent              | Role                                      |
|--------------------|-------------------------------------------|
| 🗣️ Speech Agent     | Transcribes voice input                   |
| 🌍 Location Agent   | Detects region                            |
| 🧠 Culture Agent    | Suggests phrasing                         |
| 🎭 Tone Agent       | Adjusts emotional tone                    |
| 📚 Customs Agent    | Explains etiquette                        |
| 🧬 Memory Agent     | Stores and recalls interactions           |

Memory is powered by **Weaviate (embedded mode)**—no API key or external URL required.

---

## 🧪 Run Locally

```bash
git clone https://github.com/YOUR_USERNAME/EchoAtlas.git
cd EchoAtlas
pip install -r requirements.txt
streamlit run echoatlas_app.py
