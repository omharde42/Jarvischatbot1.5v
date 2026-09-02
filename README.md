# JARVIS AI Assistant v2.0

An upgraded, powerful Voice + System-Control AI Assistant built with FastAPI, Web Speech API, and a modular Skills Engine.

[Open the JARVIS Dashboard](static/index.html)

---

## ⚡ Overview & Features

JARVIS v2.0 transforms your desktop environment into a voice-enabled command center. It listens to natural language speech/text commands, determines intent, enforces safety permissions, and executes system operations with concise voice and visual feedback.

### Key Capabilities

- 🎙️ **Voice Command Pipeline:** Speech-to-Text (STT) and Text-to-Speech (TTS) via Web Speech API with real-time state tracking (`IDLE`, `LISTENING`, `THINKING`, `EXECUTING`, `SPEAKING`).
- 🧠 **Natural Language Intent Engine:** Flexible intent parser mapping arbitrary user phrasing ("What's using the most CPU?", "Delete file example.txt", "Search code for main") into structured actions.
- 🔐 **Safety & Permission Engine:** Categorizes actions into `LOW`, `MEDIUM`, and `HIGH` risk levels. Destructive operations (e.g. file deletion) require explicit user confirmation via an interactive modal dialog.
- 🧩 **Modular Skill System:** Capabilities separated into clean skill modules (`skills/system`, `skills/filesystem`, `skills/browser`, `skills/developer`, `skills/git`, `skills/voice`, `skills/productivity`, `skills/ai`).
- 📊 **Real-time Telemetry Dashboard:** Live CPU, RAM, Disk storage, Uptime, and Top Process monitor powered by `psutil`.

---

## 🏗 Architecture & Project Structure

```text
.
├── server.py               # FastAPI backend entry point & REST endpoints
├── app/
│   ├── __init__.py
│   ├── intent.py           # Intent parser & command router
│   └── safety.py           # Safety permission engine & confirmation queue
├── skills/
│   ├── __init__.py
│   ├── system.py           # CPU, RAM, Disk, Process telemetry
│   ├── filesystem.py       # File and directory operations
│   ├── browser.py          # Browser navigation and web search
│   ├── developer.py        # Code search, server control, error explanations
│   ├── git.py              # Git repository status and commit log
│   ├── voice.py            # Concise voice response formatting
│   ├── productivity.py     # Reminders and task logging
│   └── ai.py               # Text summarization and LLM abstraction
├── static/
│   ├── index.html          # Modern AI Command Center Web UI
│   ├── style.css           # Sci-Fi / Cyberpunk theme styling
│   └── app.js             # Voice control, Web Speech API, waveform visualizer
├── tests/
│   └── test_backend.py     # Comprehensive Pytest test suite
└── README.md
```

---

## 🚀 Installation & Running JARVIS

### 1. Requirements

- Python 3.10+
- Node.js (optional, for running `npm start` target dev servers)

### 2. Install Dependencies

```bash
pip install fastapi uvicorn psutil pytest requests httpx pytest-asyncio
```

### 3. Start the Server

```bash
python3 server.py
# or
python3 -m uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

Open your browser and navigate to `http://localhost:8000`.

---

## 🔑 Environment Variables

The intent parser includes a pluggable LLM provider layer. Set environment variables to enable optional LLM capabilities:

```bash
export OPENAI_API_KEY="your-openai-key"
export ANTHROPIC_API_KEY="your-anthropic-key"
```

---

## 🎙 Voice & Command Examples

- **System:**
  - *"What is using the most CPU?"*
  - *"Tell me the current system status."*
- **Filesystem:**
  - *"What files are in this folder?"*
  - *"Create a new folder called Projects."*
  - *"Read the file README.md."*
  - *"Delete file temp.txt."* *(Triggers Safety Confirmation Modal)*
- **Browser & Search:**
  - *"Search the web for Python decorators."*
  - *"Open GitHub."*
- **Developer & Git:**
  - *"Search source code for parse_and_execute."*
  - *"Explain this error: ModuleNotFoundError: No module named 'fastapi'."*
  - *"Git status"*

---

## 🧪 Testing

To run the full backend unit test suite:

```bash
PYTHONPATH=. pytest tests/test_backend.py
```

---

## 🛡 Safety & Risk Classification

1. **LOW RISK:** (Auto-executed) System info, file listing, web searching, opening URLs, reading files.
2. **MEDIUM RISK:** Running dev servers, Git commits, installing packages.
3. **HIGH RISK:** (Requires Confirmation) Deleting files/folders, destructive git hard resets, system modifications.
