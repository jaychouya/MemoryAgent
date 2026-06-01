#!/usr/bin/env python3
"""Build script for creating MemoryAgent DMG installer."""

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


def create_spec_file():
    """Create PyInstaller spec file."""
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
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.icns',
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


def create_main_entry():
    """Create main entry point for the app."""
    main_content = """#!/usr/bin/env python3
\"\"\"MemoryAgent - Main Entry Point.\"\"\"

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


def create_app_bundle():
    """Create macOS app bundle structure."""
    app_name = "MemoryAgent.app"
    contents = f"{app_name}/Contents"
    macos = f"{contents}/MacOS"
    resources = f"{contents}/Resources"
    
    # Create directories
    os.makedirs(macos, exist_ok=True)
    os.makedirs(resources, exist_ok=True)
    
    # Create Info.plist
    plist_content = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleDevelopmentRegion</key>
    <string>English</string>
    <key>CFBundleDisplayName</key>
    <string>MemoryAgent</string>
    <key>CFBundleExecutable</key>
    <string>MemoryAgent</string>
    <key>CFBundleIconFile</key>
    <string>icon.icns</string>
    <key>CFBundleIdentifier</key>
    <string>com.memoryagent.app</string>
    <key>CFBundleInfoDictionaryVersion</key>
    <string>6.0</string>
    <key>CFBundleName</key>
    <string>MemoryAgent</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0.0</string>
    <key>CFBundleVersion</key>
    <string>1</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>NSRequiresAquaSystemAppearance</key>
    <false/>
</dict>
</plist>
"""
    with open(f"{contents}/Info.plist", 'w') as f:
        f.write(plist_content)
    
    # Create launcher script
    launcher_content = """#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR/../Resources"
./MemoryAgent
"""
    launcher_path = f"{macos}/MemoryAgent"
    with open(launcher_path, 'w') as f:
        f.write(launcher_content)
    os.chmod(launcher_path, 0o755)
    
    print(f"Created {app_name} bundle")
    return app_name


def create_dmg():
    """Create DMG installer."""
    app_name = "MemoryAgent.app"
    dmg_name = "MemoryAgent-1.0.0.dmg"
    
    # Create temporary directory for DMG contents
    dmg_dir = "dmg_staging"
    if os.path.exists(dmg_dir):
        shutil.rmtree(dmg_dir)
    os.makedirs(dmg_dir)
    
    # Copy app to staging
    if os.path.exists(app_name):
        shutil.copytree(app_name, f"{dmg_dir}/{app_name}")
    
    # Create Applications symlink
    os.symlink("/Applications", f"{dmg_dir}/Applications")
    
    # Create DMG
    cmd = [
        "hdiutil", "create",
        "-volname", "MemoryAgent",
        "-srcfolder", dmg_dir,
        "-ov",
        "-format", "UDZO",
        dmg_name
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print(f"Created {dmg_name}")
    except subprocess.CalledProcessError as e:
        print(f"Failed to create DMG: {e}")
        return None
    
    # Clean up staging
    shutil.rmtree(dmg_dir)
    
    return dmg_name


def main():
    """Main build function."""
    print("Building MemoryAgent DMG...")
    
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
    except subprocess.CalledProcessError as e:
        print(f"PyInstaller build failed: {e}")
        print("Falling back to simple bundle creation...")
    
    # Step 5: Create app bundle
    app_name = create_app_bundle()
    
    # Step 6: Copy built files to app bundle
    dist_dir = "dist/MemoryAgent"
    if os.path.exists(dist_dir):
        resources_dir = f"{app_name}/Contents/Resources"
        for item in os.listdir(dist_dir):
            src = os.path.join(dist_dir, item)
            dst = os.path.join(resources_dir, item)
            if os.path.isdir(src):
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)
    
    # Step 7: Create DMG
    dmg_name = create_dmg()
    
    if dmg_name:
        print(f"\nBuild complete!")
        print(f"DMG file: {dmg_name}")
        print(f"Size: {os.path.getsize(dmg_name) / 1024 / 1024:.1f} MB")
    else:
        print("\nBuild failed!")


if __name__ == "__main__":
    main()
