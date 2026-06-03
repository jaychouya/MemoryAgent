# Reddit Post for r/LocalLLaMA

## Title
I built an AI Agent with cognitive memory architecture - it remembers your preferences across conversations

## Post Content

Hey r/LocalLLaMA!

I've been working on **MemoryAgent** - an AI Agent framework with a cognitive memory architecture that actually remembers who you are across conversations.

### The Problem

Every time you start a new conversation with ChatGPT/Claude, you have to re-introduce yourself:
- "I prefer Python over Java"
- "Don't use mock databases"
- "My project deadline is Friday"

This is because current AI assistants are **prompt-centric**, not **user-centric**.

### The Solution

MemoryAgent implements a **four-type memory system**:

| Type | Purpose | Example |
|------|---------|---------|
| **User Profile** | Your preferences, role, knowledge level | "I like Python" |
| **Behavioral Feedback** | What to do/not to do | "Don't use mock DB" |
| **Project Context** | Deadlines, decisions | "API due Friday" |
| **External References** | Where to find things | "Grafana dashboard URL" |

### Key Features

- **Cross-session memory** - Remembers you across conversations
- **Obsidian compatible** - Memories stored as Markdown with YAML frontmatter
- **15+ LLM providers** - OpenAI, Qwen, DeepSeek, MiMo, GLM, Kimi, etc.
- **Local-first** - Your data stays on your machine
- **Skill learning** - Automatically learns from execution traces
- **Semantic code understanding** - tree-sitter AST parsing

### Architecture

```
User Input → Agent Loop → LLM Call → Tool Execution → Memory Update
                ↑
        Context Compression (5-step)
        Memory Retrieval (4-type)
        Skill Matching (networkx)
```

### Tech Stack

- **Backend**: Python 3.9, FastAPI, OpenAI SDK
- **Frontend**: Next.js 14, TypeScript, Tailwind CSS
- **Memory**: Markdown + YAML, SQLite index, vector search
- **Graph**: networkx for skill knowledge graph

### GitHub

https://github.com/jaychouya/MemoryAgent

Would love to hear your feedback! What features would you find most useful?

---

*Built with inspiration from Claude Code's architecture*
