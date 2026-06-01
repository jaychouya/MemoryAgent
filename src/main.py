#!/usr/bin/env python3
"""MemoryAgent - Main Entry Point for Windows."""

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
    """Open browser after server starts."""
    time.sleep(2)
    webbrowser.open('http://localhost:3000')


def main():
    """Main entry point."""
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
