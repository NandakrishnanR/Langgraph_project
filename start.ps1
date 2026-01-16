# Start Complete Application
Write-Host "🚀 LangGraph Multi-Agent ML Analysis System" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Check Ollama
Write-Host "1. Checking Ollama..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -Method GET -TimeoutSec 2 -ErrorAction SilentlyContinue
    Write-Host "   ✓ Ollama is running" -ForegroundColor Green
} catch {
    Write-Host "   ✗ Ollama not running. Please run: ollama serve" -ForegroundColor Red
    exit 1
}

# Start backend in new window
Write-Host "`n2. Starting Backend (Multi-Agent System)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-File", "$PSScriptRoot\start-backend.ps1"
Start-Sleep -Seconds 3

# Start frontend in new window
Write-Host "3. Starting Frontend (React UI)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-File", "$PSScriptRoot\start-frontend.ps1"

Write-Host "`n✅ Application Started!" -ForegroundColor Green
Write-Host "   Backend:  http://localhost:8000" -ForegroundColor Cyan
Write-Host "   Frontend: http://localhost:5173" -ForegroundColor Cyan
Write-Host "   Docs:     http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "`nPress any key to exit..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
