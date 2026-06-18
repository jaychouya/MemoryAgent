#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT"

if ! command -v python3 &>/dev/null; then
  echo "Python 3 is required."
  exit 1
fi

if ! python3 -c "import fastapi" &>/dev/null; then
  echo "Installing Python dependencies..."
  pip3 install -r requirements.txt
fi

FE_PORT=3000
if lsof -iTCP:"$FE_PORT" -sTCP:LISTEN &>/dev/null; then
  FE_PORT=3001
fi

python3 -m uvicorn src.backend.main:app --host 0.0.0.0 --port 8000 &
UV_PID=$!
cleanup() { kill "$UV_PID" 2>/dev/null || true; }
trap cleanup EXIT INT TERM

if command -v node &>/dev/null && [[ -d "$ROOT/frontend" ]]; then
  (sleep 2 && open "http://localhost:${FE_PORT}" 2>/dev/null || true) &
  cd "$ROOT/frontend"
  if [[ ! -d node_modules ]]; then
    npm install --silent
  fi
  echo "Backend: http://localhost:8000"
  echo "Web UI:  http://localhost:${FE_PORT}"
  exec npm run dev -- -p "$FE_PORT"
fi

echo "Backend: http://localhost:8000"
echo "Install Node.js for Web UI, or use Cursor MCP sidecar."
wait "$UV_PID"
