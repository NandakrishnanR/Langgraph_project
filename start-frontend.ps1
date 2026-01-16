# Start Frontend - React UI
Write-Host "🎨 Starting React Frontend..." -ForegroundColor Cyan

Set-Location frontend

# Check if node_modules exists
if (-not (Test-Path "node_modules")) {
    Write-Host "⚠ Dependencies not found. Installing..." -ForegroundColor Yellow
    npm install
}

Write-Host "`n✓ Starting development server on http://localhost:5173" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop`n" -ForegroundColor Yellow

npm run dev
