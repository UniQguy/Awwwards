# Starts Vite development server and Django runserver concurrently
$ErrorActionPreference = "Stop"
Write-Host "Starting ELECTROCART dual dev servers (Vite + Django)..." -ForegroundColor Cyan

$env:VITE_DEV_MODE = "true"

# Start Vite in background job
$viteJob = Start-Job -ScriptBlock {
    npm run dev
}

try {
    Write-Host "Vite dev server running on http://localhost:5173" -ForegroundColor Yellow
    Write-Host "Starting Django runserver on http://localhost:8000..." -ForegroundColor Yellow
    .venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
} finally {
    Write-Host "Stopping Vite dev server job..." -ForegroundColor Cyan
    Stop-Job $viteJob
    Remove-Job $viteJob
}
