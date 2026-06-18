#!/usr/bin/env bash
set -euo pipefail

TARGET="."
INSTALL_CLAUDE=false
RUN_VERIFY=false
while [[ $# -gt 0 ]]; do
  case "$1" in
    --claude) INSTALL_CLAUDE=true; shift ;;
    --verify) RUN_VERIFY=true; shift ;;
    -h|--help)
      echo "Usage: bash scripts/install-sidecar.sh [project_dir] [--claude] [--verify]"
      exit 0
      ;;
    *) TARGET="$1"; shift ;;
  esac
done

AGENT_HOME="$(cd "$(dirname "$0")/.." && pwd)"
TARGET="$(cd "$TARGET" && pwd)"
STORAGE="$TARGET/.memoryagent/memories"
STATUS_FILE="$TARGET/.memoryagent/status.json"

mkdir -p "$TARGET/.cursor/rules" "$STORAGE"

cat > "$TARGET/.memoryagent/README.md" <<'EOF'
# MemoryAgent 侧车（本项目）

记忆数据在 `memories/`；运行状态见 `status.json`（最近一次 recall/store 人话摘要）。

**Cursor 用户**：重载 MCP 后，在对话中说「记住：我喜欢 Python」→ 新会话问「我用什么语言」验证。

验证：`bash /path/to/MemoryAgent/scripts/verify-sidecar.sh --storage .memoryagent/memories`
EOF

cat > "$TARGET/.cursor/mcp.json" <<EOF
{
  "mcpServers": {
    "memoryagent": {
      "command": "python3",
      "args": ["-m", "src.mcp_server.server"],
      "cwd": "$AGENT_HOME",
      "env": {
        "MEMORYAGENT_STORAGE_DIR": "$STORAGE",
        "MEMORYAGENT_WORKSPACE_DIR": "$TARGET"
      }
    }
  }
}
EOF

cp "$AGENT_HOME/integrations/cursor/memory-sidecar.mdc" "$TARGET/.cursor/rules/memory-sidecar.mdc"

if $INSTALL_CLAUDE; then
  cat > "$TARGET/.mcp.json" <<EOF
{
  "mcpServers": {
    "memoryagent": {
      "command": "python3",
      "args": ["-m", "src.mcp_server.server"],
      "cwd": "$AGENT_HOME",
      "env": {
        "MEMORYAGENT_STORAGE_DIR": "$STORAGE",
        "MEMORYAGENT_WORKSPACE_DIR": "$TARGET"
      }
    }
  }
}
EOF
fi

echo "OK MemoryAgent sidecar installed"
echo "  Cursor MCP: $TARGET/.cursor/mcp.json"
echo "  Rule:       $TARGET/.cursor/rules/memory-sidecar.mdc"
echo "  Memories:   $STORAGE"
echo "  Status:     $STATUS_FILE"
echo "  Reload Cursor MCP or restart IDE"
$INSTALL_CLAUDE && echo "  Claude Code: $TARGET/.mcp.json"

if $RUN_VERIFY; then
  echo ""
  echo "Running first-win verification..."
  export MEMORYAGENT_STORAGE_DIR="$STORAGE"
  export MEMORYAGENT_WORKSPACE_DIR="$TARGET"
  if bash "$AGENT_HOME/scripts/verify-sidecar.sh" --storage "$STORAGE"; then
    echo "First-win OK — sidecar store/recall works"
  else
    echo "First-win FAILED — see hints above (MCP reload / Python deps)"
    exit 1
  fi
fi
