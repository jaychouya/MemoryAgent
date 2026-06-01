#!/bin/bash
# GitHub Release Script for MemoryAgent

set -e

VERSION="1.0.0"
REPO="jaychouya/MemoryAgent"

echo "Creating GitHub Release v${VERSION}..."

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    echo "GitHub CLI (gh) is not installed."
    echo ""
    echo "Install it with:"
    echo "  brew install gh"
    echo "  # or"
    echo "  conda install gh --channel conda-forge"
    echo ""
    echo "After installation, run: gh auth login"
    echo ""
    echo "Alternative: Create release manually at:"
    echo "  https://github.com/${REPO}/releases/new"
    exit 1
fi

# Check if authenticated
if ! gh auth status &> /dev/null; then
    echo "Not authenticated with GitHub CLI."
    echo "Run: gh auth login"
    exit 1
fi

# Create release
echo "Creating release v${VERSION}..."
gh release create "v${VERSION}" \
    --repo "${REPO}" \
    --title "MemoryAgent v${VERSION}" \
    --notes "# MemoryAgent v${VERSION}

🧠 **具备认知记忆架构的 AI Agent**

## 下载

### macOS
- \`MemoryAgent-Installer.dmg\` - macOS 安装包

### Windows
- \`MemoryAgent-Windows-${VERSION}.zip\` - Windows 便携版
- \`MemoryAgent-${VERSION}.msi\` - Windows MSI 安装包（需要 WiX Toolset 构建）

## 安装说明

### macOS
1. 下载 \`MemoryAgent-Installer.dmg\`
2. 打开 DMG 文件
3. 将 \`MemoryAgent\` 拖入 \`Applications\` 文件夹
4. 在启动台或应用程序中打开 \`MemoryAgent\`

### Windows
1. 下载 \`MemoryAgent-Windows-${VERSION}.zip\`
2. 解压到任意目录
3. 双击 \`MemoryAgent.bat\` 启动
4. 或在 PowerShell 中运行 \`.\MemoryAgent.ps1\`

## 系统要求

- **macOS**: 10.15 或更高版本
- **Windows**: 10 或更高版本
- **Python**: 3.9 或更高版本
- **网络**: 需要网络连接（用于 API 调用）

## 主要特性

- ✅ 四类型记忆系统（用户/反馈/项目/引用）
- ✅ Obsidian 兼容格式（YAML frontmatter + tags）
- ✅ TokenJuice 上下文压缩
- ✅ 智能模型路由（FAST/REASONING/VISION/LOCAL）
- ✅ MemoryTree 统一记忆接口
- ✅ SQLite 索引快速检索
- ✅ 后台记忆整理（Subconscious Loop）

## 配置

首次运行需要配置 API Key：

1. 打开 http://localhost:3000
2. 点击「配置」按钮
3. 选择模型厂商并填写 API Key

## 支持的模型

- OpenAI (GPT-4, GPT-4o)
- 阿里云百炼 (qwen-max)
- 小米 MiMo (mimo-v2.5)
- 智谱 GLM (glm-5)
- DeepSeek (deepseek-v4)
- 月之暗面 Kimi (kimi-k2)
- 更多..." \
    MemoryAgent-Installer.dmg \
    MemoryAgent-Windows-${VERSION}.zip

echo "Release created successfully!"
echo "View at: https://github.com/${REPO}/releases/tag/v${VERSION}"
