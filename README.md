# LangGraph Multi-Agent ML Analysis System

![LangGraph UI Preview](Screenshot%202026-01-17%20132505.png)

Pure LangGraph state machine with 3 specialized agents analyzing datasets and generating Python code. Local Ollama integration (no external APIs required).

## Project Structure

```
backend/
├── graph.py                     # 3-agent LangGraph state machine
├── server.py                    # aiohttp server + CSV processing
└── requirements.txt             # Python dependencies

frontend/
├── src/
│   ├── App.jsx                  # React UI component
│   ├── App.css                  # Animated styling
│   └── main.jsx                 # React entry point
├── index.html
├── package.json
└── vite.config.js              # Vite + dev server config

sample_data/                      # Example CSV files for testing
```

## Setup

### Prerequisites
- Python 3.10+
- Node.js 16+
- Ollama installed locally

### Ollama Setup (One-time)
```bash
# Download and run Ollama from: https://ollama.ai
# Pull the model (one-time):
ollama pull llama3.1
```

### Backend Setup
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### Frontend Setup
```bash
cd frontend
npm install
```

## Running the Application

### Terminal 1: Start Ollama (required once per session)
```bash
ollama serve
# Output: Listening on http://127.0.0.1:11434
```

### Terminal 2: Start Backend
```bash
cd backend
venv\Scripts\activate
python server.py
# Output: Running on http://localhost:8000
```

### Terminal 3: Start Frontend
```bash
cd frontend
npm run dev
# Output: Local: http://localhost:3000
```

### Access Application
Open browser → `http://localhost:3000`

---

## Why Backend and Frontend Use Different Ports

### **Backend (Port 8000)**
- **What it is**: Python aiohttp server running LangGraph agents
- **Why 8000**: Standard Python dev server port, avoids conflicts
- **Runs**: Computationally heavy ML workflow (agent inference, CSV processing)
- **Processes requests**: Async processing of `/api/run` endpoint

### **Frontend (Port 3000)**
- **What it is**: React development server via Vite
- **Why 3000**: Industry standard frontend dev port
- **Runs**: UI rendering, state management, file handling
- **Hot reload**: Fast refresh during development

### **Architecture**
```
Browser (Port 3000)
    ↓
    ├─ CSS/JS/HTML (served by Vite)
    └─ API Calls → http://localhost:8000/api/run
                          ↓
                    Backend (Port 8000)
                          ↓
                    LangGraph Agents
                          ↓
                    Ollama llama3.1 (Port 11434)
```

### **Why Not Same Port?**
1. **Different Technologies**: Frontend = Node/React, Backend = Python/aiohttp
2. **Different Processes**: Can't run two servers on same port simultaneously
3. **Independent Scaling**: Each can be developed/deployed separately
4. **Proxy Configuration**: Vite config proxies `/api/*` requests to port 8000 automatically
5. **Security**: In production, frontend served by CDN/web server, backend isolated

---

## How It Works

### Workflow
1. **Upload CSV** → Frontend sends file to backend `/api/run`
2. **Agent 1 (DataCleaner 🧹)** → Analyzes data shape, types, missing values
3. **Agent 2 (AlgorithmSelector 🎯)** → Recommends best ML algorithm
4. **Agent 3 (CodeGenerator ⚡)** → Generates production Python code
5. **Return Results** → Display agent analysis + generated code in UI

### State Machine
```
CSV Input → DataCleaner → AlgorithmSelector → CodeGenerator → Output
                  ↓              ↓                    ↓
           Agent 1 Message   Agent 2 Message    Agent 3 Message
```

## Features

✅ 3 LangGraph agents with shared state
✅ Local Ollama integration (no external APIs)
✅ Real-time agent progress tracking
✅ Production-ready ML code generation
✅ Dataset analysis with LLM reasoning
✅ Animated UI with professional styling
✅ Async aiohttp backend
✅ React + Vite frontend

## Technology Stack

- **Backend**: Python, LangGraph, aiohttp, Ollama
- **Frontend**: React, Vite, Axios
- **ML**: LangChain, local llama3.1 model
- **Data**: Pandas CSV processing
