# Hacker News 发帖内容

## Title
Show HN: MemoryAgent – Local memory system for AI coding agents

## Content

I built an open-source memory system that gives AI coding agents persistent memory across sessions.

**The problem:** Every time you start a new conversation with ChatGPT/Claude/Cursor, you have to re-introduce yourself. "I prefer Python", "Don't use mock databases", etc.

**The solution:** MemoryAgent implements a cognitive memory architecture inspired by Claude Code's source code.

### Key features:

1. **Four-type memory system** - User profile, behavioral feedback, project context, external references
2. **Cross-session memory** - Remembers your preferences across conversations
3. **Local-first** - All data stored locally, memories are Markdown files (Obsidian compatible)
4. **15+ LLM providers** - OpenAI, DeepSeek, Qwen, MiMo, GLM, etc.

### Why not vector databases?

After studying Claude Code's source code, I found it doesn't use vector databases. Instead, it uses structured files + LLM selector.

Reasons:
- Similarity ≠ relevance
- Embedding model changes = different results
- High maintenance cost
- Users can't read vector data

MemoryAgent uses the same approach: LLM as selector > vector retrieval.

### Architecture:

```
User Input → Agent Loop → LLM Call → Tool Execution → Memory Update
                ↑
        Context Compression (5-step)
        Memory Retrieval (4-type)
```

### Tech Stack:

- Backend: Python 3.9, FastAPI
- Frontend: Next.js 14, TypeScript
- Storage: Markdown + SQLite
- 400+ tests

GitHub: https://github.com/jaychouya/MemoryAgent

Feedback welcome! What features would you find most useful?
