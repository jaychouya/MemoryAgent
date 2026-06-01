@echo off
REM MemoryAgent Windows Build Script

echo Building MemoryAgent for Windows...
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed!
    echo Please install Python 3.9+ from https://www.python.org/
    pause
    exit /b 1
)

REM Install dependencies
echo Installing dependencies...
pip install pyinstaller
pip install -r requirements.txt

REM Build
echo.
echo Building with PyInstaller...
python build_windows.py

echo.
echo Build complete!
echo ZIP file: MemoryAgent-Windows-1.0.0.zip
pause
