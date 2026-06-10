#!/bin/bash
set -e
API="${API:-http://localhost:8000}"
PASS=0
FAIL=0

check() {
  local name="$1"
  local cond="$2"
  if eval "$cond"; then
    echo "✅ $name"
    PASS=$((PASS+1))
  else
    echo "❌ $name"
    FAIL=$((FAIL+1))
  fi
}

echo "=== Smoke tests @ $API ==="

# 1. Health
H=$(curl -sf "$API/health")
check "health" "echo '$H' | grep -q healthy"

# 2. Config status
CFG=$(curl -sf "$API/api/config")
check "config endpoint" "echo '$CFG' | grep -q configured"

# 3. Sessions list
SESS=$(curl -sf "$API/api/sessions?user_id=smoke-user")
check "sessions list" "echo '$SESS' | grep -q sessions"

# 4. No-config chat error (clear global first not possible; test with empty key request)
ERR=$(curl -sN -X POST "$API/api/chat/stream" -H 'Content-Type: application/json' \
  -d '{"message":"ping","session_id":"smoke-nocfg","user_id":"smoke-user","llm_config":null}' 2>&1 | head -20)
if echo "$ERR" | grep -qE 'error|未配置|API Key'; then
  echo "✅ no-config stream shows clear error"
  PASS=$((PASS+1))
else
  echo "❌ no-config stream"
  FAIL=$((FAIL+1))
fi

# 5. Configured chat (if config exists)
if echo "$CFG" | grep -q '"configured":true'; then
  OUT=$(curl -sN -X POST "$API/api/chat/stream" -H 'Content-Type: application/json' \
    -d '{"message":"1+1=?","session_id":"smoke-math","user_id":"smoke-user"}' 2>&1 | python3 -c "
import sys,json
tokens=[]; done=''
for l in sys.stdin:
 l=l.strip()
 if l.startswith('data:'):
  p=json.loads(l[5:])
  if p.get('type')=='token': tokens.append(p.get('content',''))
  if p.get('type')=='done': done=p.get('metadata',{}).get('response','')
text=''.join(tokens) or done
print('len',len(text))
print('has_math', any(c in text for c in ['2','$','+','='']))
" 2>&1)
  check "configured chat returns content" "echo '$OUT' | grep -q 'len [1-9]'"
else
  echo "⏭️  configured chat (skipped: no API key saved)"
fi

# 6. Math markdown preserved (unit via python)
PYTHONPATH=. python3 -c "
from src.backend.services import LLMService
t = LLMService()._clean_markdown('**解：**\n\$\$x^2\$\$\n<tool_call>x</tool_call>')
assert '**解：**' in t and '\$\$x^2\$\$' in t and '<tool_call>' not in t
print('markdown preserved ok')
"
check "markdown not stripped" "true"

# 7. Upload
echo "hello upload" > /tmp/smoke_upload.txt
UP=$(curl -sf -X POST "$API/api/upload?user_id=smoke-user" -F "file=@/tmp/smoke_upload.txt")
check "file upload" "echo '$UP' | grep -q filename"

# 8. Sessions messages
curl -sf "$API/api/sessions/smoke-math/messages?user_id=smoke-user" > /dev/null 2>&1 || true
check "session messages endpoint" "curl -sf '$API/api/sessions/smoke-math/messages?user_id=smoke-user' | grep -q messages"

# 9. Frontend
FE=$(curl -sf -o /dev/null -w '%{http_code}' http://localhost:3000/ 2>/dev/null || echo 000)
check "frontend http 200" "[ '$FE' = '200' ]"

echo ""
echo "=== Result: $PASS passed, $FAIL failed ==="
[ "$FAIL" -eq 0 ]
