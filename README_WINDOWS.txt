# MemoryAgent for Windows

## Quick Start

1. Double-click `MemoryAgent.bat` to start
2. Or run `MemoryAgent.ps1` in PowerShell
3. Open http://localhost:3000 in your browser

## Requirements

- Windows 10 or later
- Python 3.9 or later (https://www.python.org/)
- Internet connection (for API calls)

## Configuration

1. Open http://localhost:3000
2. Click "Settings" button
3. Select model provider and enter API Key

## Supported Models

- OpenAI (GPT-4, GPT-4o)
- Alibaba Cloud (qwen-max)
- Xiaomi MiMo (mimo-v2.5)
- Zhipu GLM (glm-5)
- DeepSeek (deepseek-v4)
- Moonshot Kimi (kimi-k2)
- And more...

## Troubleshooting

If you see "Python is not installed":
1. Download Python from https://www.python.org/
2. During installation, check "Add Python to PATH"
3. Restart your terminal and try again

If dependencies fail to install:
1. Open Command Prompt as Administrator
2. Run: pip install -r requirements.txt
