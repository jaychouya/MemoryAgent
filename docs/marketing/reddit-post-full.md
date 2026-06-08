# Reddit 发帖内容

## Title
I built an open-source memory system for AI coding agents - it remembers your preferences across sessions

## Post Content

Hey r/LocalLLaMA!

I've been frustrated with having to re-explain my preferences to AI coding assistants every time I start a new session. "I prefer Python over Java", "Don't use mock databases", "My project deadline is Friday" - I've said these things 50+ times.

So I built **MemoryAgent** - an open-source memory system that gives AI agents persistent memory.

### What it does

1. **Four-type memory system**
   - User profile (who you are, your skill level)
   - Behavioral feedback (what you like/dislike)
   - Project context (deadlines, decisions)
   - External references (where to find things)

2. **Cross-session memory**
   - First session: "I like Python"
   - Second session: "Help me write sorting" → Automatically uses Python

3. **Local-first**
   - All data stored locally
   - Memories are Markdown files (Obsidian compatible)
   - Nothing uploaded to cloud

4. **Works with 15+ LLM providers**
   - OpenAI, DeepSeek, Qwen, MiMo, GLM, Kimi, etc.

### Why not vector databases?

After studying Claude Code's source code, I found an interesting fact: **it doesn't use vector databases**.

Reasons:
- Similarity ≠ relevance
- Embedding model changes = completely different results
- High maintenance cost
- Users can't read vector data

MemoryAgent uses **LLM as a selector** instead of vector retrieval. Works better.

### Architecture

```
User Input → Agent Loop → LLM Call → Tool Execution → Memory Update
                ↑
        Context Compression (5-step)
        Memory Retrieval (4-type)
        Skill Matching (networkx)
```

### Tech Stack

- Backend: Python 3.9, FastAPI
- Frontend: Next.js 14, TypeScript, Tailwind CSS
- Storage: Markdown + SQLite
- Vector: In-memory vector store

### GitHub

https://github.com/jaychouya/MemoryAgent

Would love to hear your feedback! What features would you find most useful?

---

**Tags:** open-source, ai-agent, memory-system, llm, python, cursor, claude-code
