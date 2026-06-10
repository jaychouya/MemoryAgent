#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

KEY="${1:-${LLM_API_KEY:-}}"
if [ -z "$KEY" ]; then
  echo "用法: LLM_API_KEY=你的key ./scripts/configure_mimo.sh"
  echo "  或: ./scripts/configure_mimo.sh 你的key"
  exit 1
fi

BASE_URL="${LLM_BASE_URL:-https://token-plan-cn.xiaomimimo.com/v1}"
MODEL="${LLM_MODEL:-mimo-v2.5-pro}"

mkdir -p .memoryai
python3 - <<PY
import json
from pathlib import Path
cfg = {
    "api_key": "$KEY",
    "base_url": "$BASE_URL",
    "model": "$MODEL",
    "provider": "xiaomi",
}
Path(".memoryai/config.json").write_text(json.dumps(cfg, indent=2, ensure_ascii=False) + "\n")
print("已写入 .memoryai/config.json")
PY

if curl -sf http://localhost:8000/health >/dev/null 2>&1; then
  curl -sf -X POST http://localhost:8000/api/config \
    -H 'Content-Type: application/json' \
    -d "{\"api_key\":\"$KEY\",\"base_url\":\"$BASE_URL\",\"model\":\"$MODEL\"}" >/dev/null
  echo "已同步到运行中的后端"
fi
