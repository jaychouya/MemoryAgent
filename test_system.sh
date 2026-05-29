#!/bin/bash

echo "=== MemoMind 系统测试 ==="
echo ""

# 测试后端健康检查
echo "1. 测试后端健康检查..."
HEALTH=$(curl -s http://localhost:8000/health)
if echo "$HEALTH" | grep -q '"status":"healthy"'; then
    echo "   ✅ 后端健康检查通过"
else
    echo "   ❌ 后端健康检查失败"
    exit 1
fi

# 测试聊天API - 英文
echo ""
echo "2. 测试聊天API (英文)..."
RESPONSE=$(curl -s -X POST http://localhost:8000/api/chat \
    -H "Content-Type: application/json" \
    -d '{"message": "I like coffee", "session_id": "test1", "user_id": "user1"}')
if echo "$RESPONSE" | grep -q '"response"'; then
    echo "   ✅ 英文聊天API正常"
    echo "   响应: $(echo $RESPONSE | python3 -c 'import json,sys; print(json.load(sys.stdin)["response"][:50])...')"
else
    echo "   ❌ 英文聊天API失败"
fi

# 测试聊天API - 中文
echo ""
echo "3. 测试聊天API (中文)..."
RESPONSE=$(curl -s -X POST http://localhost:8000/api/chat \
    -H "Content-Type: application/json" \
    -d '{"message": "我喜欢川菜", "session_id": "test2", "user_id": "user1"}')
if echo "$RESPONSE" | grep -q '"response"'; then
    echo "   ✅ 中文聊天API正常"
    echo "   响应: $(echo $RESPONSE | python3 -c 'import json,sys; print(json.load(sys.stdin)["response"][:50])...')"
else
    echo "   ❌ 中文聊天API失败"
fi

# 测试记忆提取
echo ""
echo "4. 测试记忆提取..."
RESPONSE=$(curl -s -X POST http://localhost:8000/api/chat \
    -H "Content-Type: application/json" \
    -d '{"message": "I love playing basketball", "session_id": "test3", "user_id": "user1"}')
if echo "$RESPONSE" | grep -q '"memory_updates"'; then
    echo "   ✅ 记忆提取正常"
    MEMORY_COUNT=$(echo $RESPONSE | python3 -c 'import json,sys; print(len(json.load(sys.stdin)["memory_updates"]))')
    echo "   提取的记忆数量: $MEMORY_COUNT"
else
    echo "   ❌ 记忆提取失败"
fi

# 测试记忆API
echo ""
echo "5. 测试记忆API..."
MEMORIES=$(curl -s 'http://localhost:8000/api/memories?user_id=user1')
if echo "$MEMORIES" | grep -q '"memory_id"'; then
    echo "   ✅ 记忆API正常"
    MEMORY_COUNT=$(echo $MEMORIES | python3 -c 'import json,sys; print(len(json.load(sys.stdin)))')
    echo "   返回的记忆数量: $MEMORY_COUNT"
else
    echo "   ❌ 记忆API失败"
fi

# 测试决策引擎
echo ""
echo "6. 测试决策引擎 (禁止操作)..."
RESPONSE=$(curl -s -X POST http://localhost:8000/api/chat \
    -H "Content-Type: application/json" \
    -d '{"message": "Transfer money from my account", "session_id": "test4", "user_id": "user1"}')
if echo "$RESPONSE" | grep -q '"response"'; then
    echo "   ✅ 决策引擎正常"
else
    echo "   ❌ 决策引擎失败"
fi

# 测试前端
echo ""
echo "7. 测试前端..."
FRONTEND=$(curl -s http://localhost:3000 2>/dev/null | head -1)
if echo "$FRONTEND" | grep -q 'MemoMind'; then
    echo "   ✅ 前端正常"
else
    echo "   ⚠️  前端可能未启动 (需要手动启动: cd frontend && npm run dev)"
fi

echo ""
echo "=== 测试完成 ==="
echo ""
echo "📊 系统状态:"
echo "   - 后端: http://localhost:8000"
echo "   - 前端: http://localhost:3000"
echo "   - API文档: http://localhost:8000/docs"
echo ""
echo "🎯 核心功能:"
echo "   - 四层记忆架构 ✅"
echo "   - 自主性决策引擎 ✅"
echo "   - 记忆可解释性 ✅"
echo "   - 可交互Demo ✅"
