@echo off
set "PYTHONPATH=%~dp0"
cd /d "%~dp0"

echo Force-closing any leftover server instances on port 8505...
netstat -ano | findstr :8505 >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8505') do taskkill /f /pid %%a >nul 2>&1
)
ping -n 2 127.0.0.1 >nul

echo Starting Professor Performance AI System...
start /b cmd /c ".\venv\Scripts\python -m streamlit run dashboard/streamlit_app.py --server.port 8505 --server.headless true"
ping -n 6 127.0.0.1 >nul
start microsoft-edge:http://localhost:8505
echo Application launched in Microsoft Edge at http://localhost:8505
