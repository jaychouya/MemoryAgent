#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PLAN="${PLAN_FILE:-$ROOT/.planning/sidecar-integration/task_plan.md}"

if [[ ! -f "$PLAN" ]]; then
  echo "NO PLAN: $PLAN"
  exit 1
fi

if grep -qE '^\*\*Status:\*\* incomplete' "$PLAN"; then
  echo "INCOMPLETE PHASES in $PLAN"
  grep '^\*\*Status:\*\*' "$PLAN" || true
  exit 1
fi

if ! (cd "$ROOT" && python3 -m pytest tests/test_mcp_workspace.py -q --tb=no 2>/dev/null); then
  echo "TESTS FAILED"
  exit 1
fi

echo "ALL PHASES COMPLETE"
