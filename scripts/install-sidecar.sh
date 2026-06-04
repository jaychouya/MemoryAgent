#!/usr/bin/env bash
set -euo pipefail

TARGET="."
INSTALL_CLAUDE=false
while [[ $# -gt 0 ]]; do
  case "$1" in
    --claude) INSTALL_CLAUDE=true; shift ;;
    -h|--help)
      echo "Usage: bash scripts/install-sidecar.sh [project_dir] [--claude]"
      exit 0
      ;;
    *) TARGET="$1"; shift ;;
  esac
done

AGENT_HOME="$(cd "$(dirname "$0")/.." && pwd)"
TARGET="$(cd "$TARGET" && pwd)"
STORAGE="$TARGET/.memoryagent/memories"

mkdir -p "$TARGET/.cursor/rules" "$STORAGE"

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
echo "  Reload Cursor MCP or restart IDE"
$INSTALL_CLAUDE && echo "  Claude Code: $TARGET/.mcp.json"
