@echo off
echo Starting MemoryAgent...
echo.
echo Access API: http://localhost:8000
echo Web UI:    cd frontend ^&^& npm run dev  (http://localhost:3000 or :3001)
echo.
echo Press Ctrl+C to stop the server
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed or not in PATH.
    echo Please install Python 3.9 or later from https://www.python.org/
    pause
    exit /b 1
)

REM Check if dependencies are installed
python -c "import fastapi" >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r requirements.txt
)

REM Start the application
python src/main.py
pause
