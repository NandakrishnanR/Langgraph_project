# LangGraph Multi-Agent ML Analysis System

## Project Structure

```
backend/
├── agents/
│   ├── __init__.py
│   └── agent_graph.py          # 3-agent LangGraph system
├── api/
│   ├── __init__.py
│   └── routes.py                # FastAPI endpoints
├── main.py                      # Server entry point
├── config.py                    # Configuration
└── requirements.txt             # Python dependencies

frontend/
├── src/
│   ├── components/
│   │   ├── AgentProgress.jsx    # Shows agent collaboration
│   │   ├── CodeDisplay.jsx      # Displays generated code
│   │   ├── FileUpload.jsx       # File upload UI
│   │   └── ResultsCard.jsx      # Shows results
│   ├── App.jsx                  # Main React app
│   └── main.jsx                 # React entry
├── index.html
├── package.json
└── vite.config.js
```

## Setup

### Backend
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
python main.py
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Requirements

- Python 3.10+
- Node.js 16+
- Ollama with llama3.2 model

## Run
```bash
# Start Ollama
ollama serve

# Backend: http://localhost:8000
# Frontend: http://localhost:5173
```

## Features

✅ 3 LangGraph agents collaborate:
- Data Analyst Agent
- Algorithm Selector Agent  
- Code Generator Agent

✅ Real-time agent progress display
✅ Production-ready ML code generation
✅ Dataset analysis with LLM reasoning
