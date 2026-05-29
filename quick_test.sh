#!/bin/bash

echo "=== MemoMind 快速测试 ==="
echo ""

# 测试后端
echo "1. 后端健康检查..."
curl -s http://localhost:8000/health | python3 -m json.tool

echo ""
echo "2. 聊天API测试..."
curl -s -X POST http://localhost:8000/api/chat \
    -H "Content-Type: application/json" \
    -d '{"message": "I like coffee", "session_id": "test", "user_id": "user1"}' | python3 -m json.tool

echo ""
echo "3. 记忆API测试..."
curl -s 'http://localhost:8000/api/memories?user_id=user1' | python3 -m json.tool

echo ""
echo "4. 决策引擎测试 (禁止操作)..."
curl -s -X POST http://localhost:8000/api/chat \
    -H "Content-Type: application/json" \
    -d '{"message": "Transfer money", "session_id": "test", "user_id": "user1"}' | python3 -m json.tool

echo ""
echo "=== 测试完成 ==="
echo ""
echo "访问 http://localhost:3000 查看前端界面"
echo "访问 http://localhost:8000/docs 查看API文档"
