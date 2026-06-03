#!/usr/bin/env python3
"""MemoryAgent Demo Script - 模拟记忆效果演示"""

import time
import sys
import os

# 颜色代码
BLUE = '\033[94m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
CYAN = '\033[96m'
BOLD = '\033[1m'
RESET = '\033[0m'
GRAY = '\033[90m'

def typewriter(text, delay=0.03):
    """打字机效果"""
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    print()

def slow_print(text, delay=0.5):
    """慢速打印"""
    print(text)
    time.sleep(delay)

def clear_screen():
    """清屏"""
    os.system('clear' if os.name == 'posix' else 'cls')

def print_header():
    """打印头部"""
    print(f"{BOLD}{CYAN}╔══════════════════════════════════════════════════════════════╗{RESET}")
    print(f"{BOLD}{CYAN}║           🧠 MemoryAgent - 记忆效果演示                      ║{RESET}")
    print(f"{BOLD}{CYAN}╚══════════════════════════════════════════════════════════════╝{RESET}")
    print()

def print_user_message(text):
    """打印用户消息"""
    print(f"{BOLD}{BLUE}┌─ 用户 ─────────────────────────────────────────────────────┐{RESET}")
    print(f"{BLUE}│{RESET} {text}")
    print(f"{BOLD}{BLUE}└───────────────────────────────────────────────────────────┘{RESET}")
    time.sleep(1)

def print_ai_message(text):
    """打印 AI 消息"""
    print(f"{BOLD}{GREEN}┌─ MemoryAI ─────────────────────────────────────────────────┐{RESET}")
    for line in text.split('\n'):
        print(f"{GREEN}│{RESET} {line}")
    print(f"{BOLD}{GREEN}└───────────────────────────────────────────────────────────┘{RESET}")
    time.sleep(1.5)

def print_memory_status(text):
    """打印记忆状态"""
    print(f"{YELLOW}💾 记忆系统: {text}{RESET}")
    time.sleep(0.8)

def print_divider():
    """打印分隔线"""
    print(f"{GRAY}{'─' * 60}{RESET}")
    time.sleep(0.5)

def demo_scene_1():
    """场景 1: 用户告诉 AI 偏好"""
    clear_screen()
    print_header()
    
    print(f"{CYAN}📍 场景 1: 用户告诉 AI 自己的偏好{RESET}")
    print()
    time.sleep(1)
    
    print_user_message("我喜欢 Python，讨厌 Java，因为 Python 语法简洁")
    time.sleep(1)
    
    print_memory_status("正在保存记忆...")
    time.sleep(1)
    
    print_ai_message("好的，我记住了你的偏好：\n\n• 喜欢 Python\n• 讨厌 Java\n• 原因：语法简洁\n\n这些信息会在以后的对话中自动使用。")
    time.sleep(1)
    
    print_memory_status("✅ 记忆已保存到 memories/user/user_abc123.md")
    time.sleep(2)

def demo_scene_2():
    """场景 2: 新对话自动使用记忆"""
    clear_screen()
    print_header()
    
    print(f"{CYAN}📍 场景 2: 新对话 - AI 自动使用记忆{RESET}")
    print()
    time.sleep(1)
    
    print_divider()
    print(f"{GRAY}🔄 开启新对话...{RESET}")
    time.sleep(1)
    print_divider()
    
    print_user_message("帮我写个排序函数")
    time.sleep(1)
    
    print_memory_status("正在检索相关记忆...")
    time.sleep(1)
    
    print(f"{YELLOW}📚 找到 1 条相关记忆:{RESET}")
    print(f"{GRAY}   • 用户喜欢 Python（相关度: 0.95）{RESET}")
    time.sleep(1)
    
    print_ai_message("用 Python 实现（因为你偏好 Python）：\n\ndef bubble_sort(arr):\n    n = len(arr)\n    for i in range(n):\n        for j in range(0, n-i-1):\n            if arr[j] > arr[j+1]:\n                arr[j], arr[j+1] = arr[j+1], arr[j]\n    return arr\n\n这个实现简洁易读，符合 Python 风格。")
    time.sleep(2)

def demo_scene_3():
    """场景 3: Obsidian 兼容展示"""
    clear_screen()
    print_header()
    
    print(f"{CYAN}📍 场景 3: 记忆文件 - Obsidian 兼容{RESET}")
    print()
    time.sleep(1)
    
    print(f"{GRAY}📂 打开 Obsidian → memories/user/user_abc123.md{RESET}")
    print()
    time.sleep(1)
    
    print(f"{YELLOW}┌─ YAML Frontmatter ────────────────────────────────────────┐{RESET}")
    print(f"{YELLOW}│{RESET} ---")
    print(f"{YELLOW}│{RESET} name: user_abc123")
    print(f"{YELLOW}│{RESET} description: 用户偏好")
    print(f"{YELLOW}│{RESET} type: user")
    print(f"{YELLOW}│{RESET} created: 2026-06-02T18:00:00")
    print(f"{YELLOW}│{RESET} tags:")
    print(f"{YELLOW}│{RESET}   - preference")
    print(f"{YELLOW}│{RESET}   - python")
    print(f"{YELLOW}│{RESET} ---")
    print(f"{YELLOW}└───────────────────────────────────────────────────────────┘{RESET}")
    time.sleep(1)
    
    print()
    print(f"{CYAN}┌─ Markdown 内容 ───────────────────────────────────────────┐{RESET}")
    print(f"{CYAN}│{RESET} #preference #python")
    print(f"{CYAN}│{RESET} ")
    print(f"{CYAN}│{RESET} 用户喜欢 Python，讨厌 Java")
    print(f"{CYAN}│{RESET} ")
    print(f"{CYAN}│{RESET} **原因:** Python 语法简洁")
    print(f"{CYAN}└───────────────────────────────────────────────────────────┘{RESET}")
    time.sleep(2)

def demo_scene_4():
    """场景 4: 总结"""
    clear_screen()
    print_header()
    
    print(f"{CYAN}📍 核心优势{RESET}")
    print()
    time.sleep(1)
    
    features = [
        ("🧠 四类型记忆", "用户画像 / 行为反馈 / 项目动态 / 外部引用"),
        ("🔄 跨会话共享", "记住你的偏好，下次对话继续使用"),
        ("📝 Obsidian 兼容", "记忆可编辑，透明可控"),
        ("🔧 15+ 模型", "OpenAI / DeepSeek / 通义千问 / MiMo 等"),
        ("🏠 本地优先", "数据在本地，隐私可控"),
    ]
    
    for icon_name, desc in features:
        print(f"{BOLD}{GREEN}  ✓ {icon_name}{RESET}")
        print(f"{GRAY}    {desc}{RESET}")
        time.sleep(0.8)
    
    print()
    print(f"{BOLD}{CYAN}GitHub: https://github.com/jaychouya/MemoryAgent{RESET}")
    time.sleep(2)

def main():
    """主演示流程"""
    try:
        demo_scene_1()
        demo_scene_2()
        demo_scene_3()
        demo_scene_4()
        
        clear_screen()
        print_header()
        print(f"{BOLD}{GREEN}✅ 演示完成！{RESET}")
        print()
        print(f"{CYAN}录制提示:{RESET}")
        print(f"{GRAY}• 使用 Kap (macOS) 或 ScreenToGif (Windows) 录制此终端{RESET}")
        print(f"{GRAY}• 建议录制 20-30 秒的片段{RESET}")
        print(f"{GRAY}• 导出为 GIF 后添加到 README{RESET}")
        print()
        
    except KeyboardInterrupt:
        print(f"\n{RED}演示中断{RESET}")

if __name__ == "__main__":
    main()
