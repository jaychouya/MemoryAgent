#!/usr/bin/env python3
"""MemoryAgent - Main Entry Point for Windows."""

import os
import sys
import threading
import time
import webbrowser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.backend.main import app
import uvicorn


def open_browser():
    time.sleep(2)
    for port in (3000, 3001):
        webbrowser.open(f"http://localhost:{port}")


def main():
    print("Starting MemoryAgent API on http://localhost:8000")
    print("Web UI: cd frontend && npm run dev")
    threading.Thread(target=open_browser, daemon=True).start()
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")


if __name__ == "__main__":
    main()
