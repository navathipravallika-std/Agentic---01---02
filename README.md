# Customer Support Routing Agent

An intelligent multi-agent support ticket routing and auto-resolution system powered by **LangGraph** and **Google Gemini**.

---

## 🚀 Features

- **Multi-Agent StateGraph Architecture**: Built on LangGraph (`ingest` → `classify_intent` → `conditional_route` → `subagent_resolution` → `qa_guardrail`).
- **Dynamic Subagents**:
  - 💳 **Billing & Refunds Agent**: Policy checks, refund eligibility calculation, invoice breakdown.
  - 🛠️ **Tech Support Agent**: Stack trace debugging, webhook diagnostic steps, SDK guidance.
  - 💼 **Sales & Upgrades Agent**: Pricing calculation, enterprise upgrade qualification.
  - 🚨 **Account & Escalation Agent**: Security lockout handling, high-urgency manager dispatch.
  - ℹ️ **General Inquiry Agent**: Knowledge base query matching and resolution.
- **Guardrails & Quality Assurance**: Secondary validation node ensures no hallucinations, missing variables, or compliance violations.
- **Glassmorphic UI**: Real-time ticket simulator, interactive node trace visualizer, policy editor, and batch evaluation suite.

---

## 🌐 Deploying to Render (2 Minutes)

This repository includes a [`render.yaml`](./render.yaml) configuration for 1-click cloud deployment.

### Step 1: Upload Files to GitHub
In the project directory, run:
```bash
git init
git add .
git commit -m "Initial commit - Customer Support Routing Agent"
git branch -M main
git remote add origin https://github.com/<YOUR_GITHUB_USERNAME>/<YOUR_REPOSITORY_NAME>.git
git push -u origin main
```

### Step 2: Deploy on Render
1. Log in to **[Render.com](https://render.com/)**.
2. Click **New +** → **Web Service** (or **Blueprint**).
3. Connect your GitHub repository.
4. Render will auto-detect the configuration, or you can specify:
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn server:app --host 0.0.0.0 --port $PORT`
5. *(Optional)* Add Environment Variable:
   - `GEMINI_API_KEY`: `your_gemini_api_key_here`
6. Click **Create Web Service**! Render will build and deploy your app with a public live URL (e.g. `https://your-app.onrender.com`).

---

## 💻 Local Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start the Server
```bash
python server.py
```

### 3. Open in Browser
Navigate to [http://127.0.0.1:8000](http://127.0.0.1:8000).

---

## 📁 Project Structure

```
customer-support-routing-agent/
├── core/
│   ├── classifier.py       # Intent classification engine (Gemini structured outputs + heuristic fallback)
│   ├── graph.py            # LangGraph workflow definition & execution logic
│   ├── knowledge_base.py   # In-memory and configurable department policies
│   ├── simulator.py        # Preset scenarios & batch evaluation runner
│   ├── state.py            # Pydantic schemas & TypedDict state definitions
│   └── subagents.py        # Department resolution subagents & QA guardrail
├── static/
│   ├── index.html          # Interactive dashboard frontend
│   ├── style.css           # Modern dark-mode glassmorphic styling
│   └── app.js              # Real-time state visualizer, graph rendering & API handler
├── .gitignore              # Ignores __pycache__, virtual environments & temp files
├── .python-version         # Python runtime version definition (3.11.8)
├── Procfile                # Web process entry point
├── render.yaml             # Render Blueprint cloud deployment manifest
├── requirements.txt        # Python dependency manifest
├── server.py               # FastAPI backend with REST endpoints
└── test_server_endpoints.py# Automated endpoint test suite
```
