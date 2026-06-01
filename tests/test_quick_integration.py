"""Quick integration test for memory agent fixes."""
import requests
import json
from pathlib import Path

BASE_URL = "http://localhost:8000"


def test_memory_storage():
    """测试记忆存储"""
    print("=== 测试: 记忆存储 ===")
    
    response = requests.post(f"{BASE_URL}/api/chat", json={
        "message": "记住我喜欢Python",
        "session_id": "quick_test",
        "user_id": "user1"
    }, timeout=30)
    
    result = response.json()
    print(f"Response: {result['response'][:100]}...")
    
    # 检查记忆文件
    import glob
    memory_files = glob.glob("memories/user/user1_*.md")
    if memory_files:
        with open(memory_files[-1]) as f:
            content = f.read()
            print(f"Memory file:\n{content[:200]}...")
            
            if "喜欢Python" in content:
                print("✅ 测试通过: 记忆保存了完整内容")
                return True
            else:
                print("❌ 测试失败: 记忆没有保存完整内容")
                return False
    else:
        print("❌ 测试失败: 没有找到记忆文件")
        return False


def test_output_format():
    """测试输出格式"""
    print("\n=== 测试: 输出格式 ===")
    
    response = requests.post(f"{BASE_URL}/api/chat", json={
        "message": "什么是Python？",
        "session_id": "format_test",
        "user_id": "user1"
    }, timeout=30)
    
    result = response.json()
    content = result['response']
    
    # 检查是否包含 Markdown 符号
    has_markdown = any(symbol in content for symbol in ["#", "**", "```"])
    
    if not has_markdown:
        print("✅ 测试通过: 输出是纯文本格式")
        return True
    else:
        print(f"❌ 测试失败: 输出包含 Markdown 符号")
        return False


def main():
    """运行测试"""
    print("开始快速集成测试...\n")
    
    results = []
    results.append(test_memory_storage())
    results.append(test_output_format())
    
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
