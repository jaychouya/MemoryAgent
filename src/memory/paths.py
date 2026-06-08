import os


def default_storage_dir() -> str:
    return (os.environ.get("MEMORYAGENT_STORAGE_DIR") or "memories").strip() or "memories"
