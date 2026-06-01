#!/usr/bin/env python3
"""Build script for creating MemoryAgent Windows installer."""

import os
import sys
import shutil
import subprocess
from pathlib import Path


def clean_build():
    """Clean previous build artifacts."""
    dirs_to_clean = ['build', 'dist', '*.egg-info']
    for pattern in dirs_to_clean:
        for path in Path('.').glob(pattern):
            if path.is_dir():
                print(f"Cleaning {path}")
                shutil.rmtree(path)


def create_main_entry():
    """Create main entry point for the app."""
    main_content = """#!/usr/bin/env python3
\"\"\"MemoryAgent - Main Entry Point for Windows.\"\"\"

import sys
import os
import webbrowser
import threading
import time

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.backend.main import app
import uvicorn


def open_browser():
    \"\"\"Open browser after server starts.\"\"\"
    time.sleep(2)
    webbrowser.open('http://localhost:3000')


def main():
    \"\"\"Main entry point.\"\"\"
    print("Starting MemoryAgent...")
    print("Access at: http://localhost:3000")
    
    # Open browser in background
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Run server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )


if __name__ == "__main__":
    main()
"""
    os.makedirs('src', exist_ok=True)
    with open('src/main.py', 'w') as f:
        f.write(main_content)
    print("Created src/main.py")


def create_spec_file():
    """Create PyInstaller spec file for Windows."""
    spec_content = """# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('src/backend/static', 'backend/static'),
        ('src/agent/prompts', 'agent/prompts'),
    ],
    hiddenimports=[
        'uvicorn',
        'fastapi',
        'pydantic',
        'openai',
        'anthropic',
        'httpx',
        'tiktoken',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='MemoryAgent',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='MemoryAgent',
)
"""
    with open('MemoryAgent.spec', 'w') as f:
        f.write(spec_content)
    print("Created MemoryAgent.spec")


def create_windows_installer():
    """Create Windows installer using NSIS or Inno Setup."""
    
    # Create batch file for easy launch
    batch_content = """@echo off
echo Starting MemoryAgent...
echo.
echo Access at: http://localhost:3000
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
"""
    with open('MemoryAgent.bat', 'w') as f:
        f.write(batch_content)
    print("Created MemoryAgent.bat")
    
    # Create PowerShell script
    ps_content = """# MemoryAgent Launcher
Write-Host "Starting MemoryAgent..." -ForegroundColor Green
Write-Host ""
Write-Host "Access at: http://localhost:3000" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

# Check Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Python: $pythonVersion" -ForegroundColor Gray
} catch {
    Write-Host "Python is not installed!" -ForegroundColor Red
    Write-Host "Please install Python 3.9+ from https://www.python.org/" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Check dependencies
python -c "import fastapi" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    pip install -r requirements.txt
}

# Start
python src/main.py
"""
    with open('MemoryAgent.ps1', 'w') as f:
        f.write(ps_content)
    print("Created MemoryAgent.ps1")
    
    # Create README for Windows
    readme_content = """# MemoryAgent for Windows

## Quick Start

1. Double-click `MemoryAgent.bat` to start
2. Or run `MemoryAgent.ps1` in PowerShell
3. Open http://localhost:3000 in your browser

## Requirements

- Windows 10 or later
- Python 3.9 or later (https://www.python.org/)
- Internet connection (for API calls)

## Configuration

1. Open http://localhost:3000
2. Click "Settings" button
3. Select model provider and enter API Key

## Supported Models

- OpenAI (GPT-4, GPT-4o)
- Alibaba Cloud (qwen-max)
- Xiaomi MiMo (mimo-v2.5)
- Zhipu GLM (glm-5)
- DeepSeek (deepseek-v4)
- Moonshot Kimi (kimi-k2)
- And more...

## Troubleshooting

If you see "Python is not installed":
1. Download Python from https://www.python.org/
2. During installation, check "Add Python to PATH"
3. Restart your terminal and try again

If dependencies fail to install:
1. Open Command Prompt as Administrator
2. Run: pip install -r requirements.txt
"""
    with open('README_WINDOWS.txt', 'w') as f:
        f.write(readme_content)
    print("Created README_WINDOWS.txt")


def create_zip_package():
    """Create ZIP package for Windows distribution."""
    import zipfile
    
    zip_name = "MemoryAgent-Windows-1.0.0.zip"
    
    with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Add main files
        zf.write('MemoryAgent.bat')
        zf.write('MemoryAgent.ps1')
        zf.write('README_WINDOWS.txt')
        zf.write('requirements.txt')
        
        # Add source code
        for root, dirs, files in os.walk('src'):
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    zf.write(filepath)
    
    print(f"Created {zip_name}")
    return zip_name


def main():
    """Main build function."""
    print("Building MemoryAgent for Windows...")
    
    # Step 1: Clean previous builds
    clean_build()
    
    # Step 2: Create entry point
    create_main_entry()
    
    # Step 3: Create spec file
    create_spec_file()
    
    # Step 4: Build with PyInstaller
    print("Building with PyInstaller...")
    try:
        subprocess.run([
            sys.executable, "-m", "PyInstaller",
            "MemoryAgent.spec",
            "--clean",
            "--noconfirm"
        ], check=True)
        print("PyInstaller build successful!")
    except subprocess.CalledProcessError as e:
        print(f"PyInstaller build failed: {e}")
        print("Creating simple package instead...")
    
    # Step 5: Create Windows launcher files
    create_windows_installer()
    
    # Step 6: Create ZIP package
    zip_name = create_zip_package()
    
    if zip_name:
        print(f"\nBuild complete!")
        print(f"ZIP file: {zip_name}")
        print(f"Size: {os.path.getsize(zip_name) / 1024 / 1024:.1f} MB")
    else:
        print("\nBuild failed!")


if __name__ == "__main__":
    main()
