# Start Backend - LangGraph Multi-Agent System
Write-Host "🚀 Starting LangGraph Multi-Agent Backend..." -ForegroundColor Cyan

# Activate virtual environment
if (Test-Path "backend\.venv\Scripts\Activate.ps1") {
    Write-Host "✓ Activating virtual environment" -ForegroundColor Green
    & backend\.venv\Scripts\Activate.ps1
} else {
    Write-Host "⚠ Virtual environment not found. Creating..." -ForegroundColor Yellow
    Set-Location backend
    python -m venv .venv
    & .venv\Scripts\Activate.ps1
    Write-Host "✓ Installing dependencies..." -ForegroundColor Green
    pip install -r requirements.txt
    Set-Location ..
}

# Check if Ollama is running
Write-Host "Checking Ollama..." -ForegroundColor Cyan
try {
    $response = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -Method GET -TimeoutSec 2 -ErrorAction SilentlyContinue
    Write-Host "✓ Ollama is running" -ForegroundColor Green
} catch {
    Write-Host "⚠ Warning: Ollama not detected. Make sure to run 'ollama serve'" -ForegroundColor Yellow
}

# Start backend
Write-Host "`n🤖 Starting Multi-Agent System on http://localhost:8000" -ForegroundColor Green
Write-Host "   Agent 1: Data Analyst" -ForegroundColor Gray
Write-Host "   Agent 2: Algorithm Selector" -ForegroundColor Gray
Write-Host "   Agent 3: Code Generator" -ForegroundColor Gray
Write-Host "`nPress Ctrl+C to stop`n" -ForegroundColor Yellow

Set-Location backend
python main.py
