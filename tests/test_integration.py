"""Integration test for all memory agent fixes."""
import asyncio
import requests
import json
from pathlib import Path

BASE_URL = "http://localhost:8000"


def test_memory_storage_saves_complete_content():
    """测试 1: 记忆存储保存完整内容"""
    print("=== 测试 1: 记忆存储 ===")
    
    # 存储记忆
    response = requests.post(f"{BASE_URL}/api/chat", json={
        "message": "记住我喜欢Python，讨厌Java，因为Python语法简洁",
        "session_id": "test_integration_1",
        "user_id": "user1"
    })
    
    result = response.json()
    print(f"Response: {result['response'][:100]}...")
    
    # 检查记忆文件
    import glob
    memory_files = glob.glob("memories/user/user1_*.md")
    if memory_files:
        with open(memory_files[-1]) as f:
            content = f.read()
            print(f"Memory file content:\n{content[:200]}...")
            
            # 验证包含完整内容
            if "喜欢Python" in content and "讨厌Java" in content:
                print("✅ 测试 1 通过: 记忆保存了完整内容")
                return True
            else:
                print("❌ 测试 1 失败: 记忆没有保存完整内容")
                return False
    else:
        print("❌ 测试 1 失败: 没有找到记忆文件")
        return False


def test_user_id_filter():
    """测试 2: 记忆检索按 user_id 过滤"""
    print("\n=== 测试 2: user_id 过滤 ===")
    
    # user1 存储记忆
    requests.post(f"{BASE_URL}/api/chat", json={
        "message": "我喜欢Python",
        "session_id": "test_user1",
        "user_id": "user1"
    })
    
    # user2 存储记忆
    requests.post(f"{BASE_URL}/api/chat", json={
        "message": "我喜欢Java",
        "session_id": "test_user2",
        "user_id": "user2"
    })
    
    # user1 查询记忆
    response = requests.post(f"{BASE_URL}/api/chat", json={
        "message": "我喜欢什么编程语言？",
        "session_id": "test_user1_query",
        "user_id": "user1"
    })
    
    result = response.json()
    if "Python" in result['response'] and "Java" not in result['response']:
        print("✅ 测试 2 通过: user1 只看到自己的记忆")
        return True
    else:
        print(f"❌ 测试 2 失败: {result['response'][:100]}")
        return False


def test_session_history():
    """测试 3: 会话历史保存完整工具调用链"""
    print("\n=== 测试 3: 会话历史 ===")
    
    # 发送会触发工具调用的消息
    requests.post(f"{BASE_URL}/api/chat", json={
        "message": "记住我喜欢Python",
        "session_id": "test_history",
        "user_id": "user1"
    })
    
    # 检查会话文件
    session_file = Path("sessions/user1_test_history.json")
    if session_file.exists():
        with open(session_file) as f:
            session = json.load(f)
            
            # 检查是否有工具调用
            has_tool_calls = any(
                msg.get("tool_calls") or msg.get("role") == "tool"
                for msg in session.get("messages", [])
            )
            
            if has_tool_calls:
                print("✅ 测试 3 通过: 会话历史包含工具调用")
                return True
            else:
                print("❌ 测试 3 失败: 会话历史缺少工具调用")
                return False
    else:
        print("❌ 测试 3 失败: 没有找到会话文件")
        return False


def test_output_format():
    """测试 4: 输出格式是纯文本"""
    print("\n=== 测试 4: 输出格式 ===")
    
    response = requests.post(f"{BASE_URL}/api/chat", json={
        "message": "帮我写一个排序函数",
        "session_id": "test_format",
        "user_id": "user1"
    })
    
    result = response.json()
    content = result['response']
    
    # 检查是否包含 Markdown 符号
    markdown_symbols = ["#", "**", "```", "|", ">", "- ", "~", "_"]
    has_markdown = any(symbol in content for symbol in markdown_symbols)
    
    if not has_markdown:
        print("✅ 测试 4 通过: 输出是纯文本格式")
        return True
    else:
        print(f"❌ 测试 4 失败: 输出包含 Markdown 符号")
        print(f"Content preview: {content[:200]}")
        return False


def test_memory_quality():
    """测试 5: 记忆质量"""
    print("\n=== 测试 5: 记忆质量 ===")
    
    # 存储记忆
    requests.post(f"{BASE_URL}/api/chat", json={
        "message": "我喜欢Python，讨厌Java",
        "session_id": "test_quality",
        "user_id": "user1"
    })
    
    # 检查记忆文件
    import glob
    memory_files = glob.glob("memories/user/user1_*.md")
    if memory_files:
        with open(memory_files[-1]) as f:
            content = f.read()
            
            # 检查是否有有意义的描述
            if "用户偏好" in content or "description:" in content:
                print("✅ 测试 5 通过: 记忆有有意义的描述")
                return True
            else:
                print("❌ 测试 5 失败: 记忆缺少有意义的描述")
                return False
    else:
        print("❌ 测试 5 失败: 没有找到记忆文件")
        return False


def main():
    """运行所有测试"""
    print("开始集成测试...\n")
    
    results = []
    results.append(test_memory_storage_saves_complete_content())
    results.append(test_user_id_filter())
    results.append(test_session_history())
    results.append(test_output_format())
    results.append(test_memory_quality())
    
    print("\n=== 测试总结 ===")
    passed = sum(results)
    total = len(results)
    print(f"通过: {passed}/{total}")
    
    if passed == total:
        print("✅ 所有测试通过！")
    else:
        print("❌ 部分测试失败")


if __name__ == "__main__":
    main()
