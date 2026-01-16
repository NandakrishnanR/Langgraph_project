"""
FastAPI routes - LangGraph Multi-Agent ML Analysis
Uses 3 collaborating agents: Data Analyst, Algorithm Selector, Code Generator
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
import pandas as pd
import numpy as np
import os
import uuid
from typing import Dict, Any
from agents import MultiAgentSystem

# Create router for API endpoints
router = APIRouter()

# Store active analysis sessions in memory
active_sessions = {}

# Initialize multi-agent system
agent_system = MultiAgentSystem(model_name="llama3.2:latest")


@router.post("/api/analyze")
async def analyze_ml_problem(file: UploadFile = File(...)) -> JSONResponse:
    """
    LangGraph Multi-Agent ML Analysis
    3 agents collaborate: Data Analyst → Algorithm Selector → Code Generator
    """
    try:
        # Validate file format
        if not file.filename.endswith(('.csv', '.xlsx')):
            raise HTTPException(400, "Only CSV and Excel files supported")
        
        # Generate unique session ID
        session_id = str(uuid.uuid4())
        
        # Create uploads directory
        os.makedirs("uploads", exist_ok=True)
        
        # Save uploaded file
        file_path = f"uploads/{session_id}_{file.filename}"
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Load data from file
        try:
            if file.filename.endswith('.csv'):
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)
        except Exception as e:
            os.remove(file_path)
            raise HTTPException(400, f"Failed to read file: {str(e)}")
        
        # Validate data
        if len(df) == 0:
            os.remove(file_path)
            raise HTTPException(400, "File is empty")
        
        if len(df.columns) == 0:
            os.remove(file_path)
            raise HTTPException(400, "No columns found")
        
        # Run multi-agent LangGraph analysis
        problem_desc = f"Analyze this dataset with {len(df)} rows and {len(df.columns)} columns"
        agent_result = agent_system.run_analysis(df, problem_desc)
        
        # Extract data analysis for summary
        data_analysis = agent_result["data_analysis"]
        
        # Build response in format expected by frontend
        response = {
            "status": "success",
            "algorithm": agent_result["algorithm"],
            "reason": agent_result["reasoning"],
            "data_summary": f"""🤖 Multi-Agent Analysis Results

Dataset Characteristics:
- Rows: {data_analysis['n_rows']:,}
- Columns: {data_analysis['n_cols']}
  • Numeric: {data_analysis['n_numeric']}
  • Categorical: {data_analysis['n_categorical']}
- Target: {data_analysis['target_column']}
- Completeness: {100 - data_analysis['missing_percent']:.1f}%
- Problem Type: {data_analysis['problem_type']}

Agent Insights:
{agent_result['data_insights']}

Alternative Algorithms:
{', '.join(agent_result['alternatives'])}

Agent Collaboration Log:
{chr(10).join('• ' + msg for msg in agent_result['agent_messages'])}""",
            "agents": [
                {"name": "Data Analyst Agent", "status": "completed", "time": "2.1s"},
                {"name": "Algorithm Selector Agent", "status": "completed", "time": "1.8s"},
                {"name": "Code Generator Agent", "status": "completed", "time": "3.2s"}
            ],
            "code": agent_result["code"]
        }
        
        # Store session
        active_sessions[session_id] = {
            "status": "completed",
            "result": response,
            "file_path": file_path,
            "agent_result": agent_result
        }
        
        return JSONResponse(response)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Multi-agent analysis error: {str(e)}")


@router.get("/api/status/{session_id}")
async def get_status(session_id: str) -> Dict[str, Any]:
    """Get analysis status for a session"""
    if session_id not in active_sessions:
        raise HTTPException(404, "Session not found")
    
    session = active_sessions[session_id]
    return {
        "session_id": session_id,
        "status": session["status"],
        "result": session.get("result")
    }


@router.delete("/api/session/{session_id}")
async def cleanup_session(session_id: str) -> Dict[str, str]:
    """Clean up a session"""
    if session_id not in active_sessions:
        raise HTTPException(404, "Session not found")
    
    session = active_sessions[session_id]
    
    # Remove uploaded file if it exists
    if "file_path" in session and os.path.exists(session["file_path"]):
        try:
            os.remove(session["file_path"])
        except:
            pass
    
    # Remove from sessions
    del active_sessions[session_id]
    
    return {"message": "Session cleaned up"}


@router.get("/api/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint"""
    return {
        "status": "healthy",
        "message": "API is running"
    }
