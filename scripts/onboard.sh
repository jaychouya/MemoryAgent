#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TARGET="${1:-.}"
shift || true
echo "== MemoryAgent 侧车 onboarding =="
bash "$ROOT/scripts/install-sidecar.sh" "$TARGET" --verify "$@"
echo ""
echo "下一步："
echo "  1. Cursor → 重载 MCP"
echo "  2. 说：记住我喜欢 Python，讨厌 Java"
echo "  3. 新会话问：我用什么语言写代码"
echo "  4. 查看 $TARGET/.memoryagent/status.json"
