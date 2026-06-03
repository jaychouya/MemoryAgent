# GIF 演示录制指南

## 录制工具

### macOS
- **QuickTime Player** - 免费，自带
- **Kap** - 免费，开源，支持 GIF 导出
- **GIF Brewery** - 付费，功能强大

### Windows
- **ScreenToGif** - 免费，开源，推荐
- **LICEcap** - 免费，简单易用
- **ShareX** - 免费，功能丰富

### 在线工具
- **ezgif.com** - 在线编辑 GIF
- **giphy.com** - 在线创建 GIF

---

## 录制脚本（30秒 GIF）

### 场景 1：展示记忆效果（10秒）

```
[用户输入]
我喜欢 Python，讨厌 Java，因为 Python 语法简洁

[AI 回复]
好的，我记住了你的偏好：
- 喜欢 Python
- 讨厌 Java
- 原因：语法简洁

[画面停留 2 秒]
```

### 场景 2：新对话自动使用（10秒）

```
[新对话]
用户：帮我写个排序函数

[AI 回复]
用 Python 实现（因为你偏好 Python）：

def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(0, n-i-1):
            if arr[j] > arr[j+1]:
                arr[j], arr[j+1] = arr[j+1], arr[j]
    return arr

[画面停留 2 秒]
```

### 场景 3：Obsidian 兼容（10秒）

```
[打开 Obsidian]
展示记忆文件：

---
name: user_abc123
description: 用户偏好
type: user
tags:
  - preference
  - python
---
#preference #python

用户喜欢 Python，讨厌 Java

[画面停留 2 秒]
```

---

## 录制步骤

### 1. 准备环境

```bash
# 启动 MemoryAgent
cd /Users/tmind/Desktop/work/github/test2
source venv/bin/activate
python src/main.py

# 启动前端
cd frontend
npm run dev
```

### 2. 打开浏览器

访问 http://localhost:3000

### 3. 配置模型

点击右上角「配置」按钮，选择模型厂商并填写 API Key。

### 4. 开始录制

1. 打开录制工具（Kap 或 ScreenToGif）
2. 选择录制区域（浏览器窗口）
3. 按照上面的脚本操作
4. 停止录制
5. 导出为 GIF

### 5. 优化 GIF

- **尺寸**：800x600 或 1200x800
- **帧率**：10-15 fps
- **时长**：20-30 秒
- **文件大小**：< 10MB

---

## GIF 优化工具

### 使用 ezgif.com

1. 访问 https://ezgif.com/optimize
2. 上传 GIF
3. 选择「Lossy GIF」压缩
4. 设置压缩级别（60-80）
5. 下载优化后的 GIF

### 使用 ImageOptim (macOS)

```bash
# 安装
brew install imageoptim

# 优化 GIF
imageoptim MemoryAgent-demo.gif
```

---

## GIF 存放位置

将优化后的 GIF 保存到：

```
docs/marketing/demo.gif
```

然后在 README 中引用：

```markdown
![MemoryAgent Demo](docs/marketing/demo.gif)
```

---

## 替代方案：截图序列

如果录制 GIF 有困难，可以使用截图序列：

1. 截取关键步骤的截图
2. 使用 ezgif.com 的「GIF Maker」功能
3. 上传截图，设置每张图片显示时间
4. 生成 GIF

---

## 发布到 GitHub

```bash
# 添加 GIF 到仓库
git add docs/marketing/demo.gif
git commit -m "docs: 添加 GIF 演示"
git push origin main

# 更新 README 引用 GIF
# 在 README.md 的演示部分添加：
# ![MemoryAgent Demo](docs/marketing/demo.gif)
```
