"""Tests for chat export and file upload."""
import pytest
import json
from src.backend.chat_utils import ChatExporter, FileUploader


def test_chat_exporter_to_json():
    """ChatExporter 应该能导出 JSON 格式。"""
    messages = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"}
    ]
    
    result = ChatExporter.to_json(messages)
    data = json.loads(result)
    
    assert data["message_count"] == 2
    assert len(data["messages"]) == 2


def test_chat_exporter_to_markdown():
    """ChatExporter 应该能导出 Markdown 格式。"""
    messages = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"}
    ]
    
    result = ChatExporter.to_markdown(messages)
    
    assert "# Chat History" in result
    assert "## User" in result
    assert "## Assistant" in result
    assert "Hello" in result
    assert "Hi there!" in result


def test_chat_exporter_to_text():
    """ChatExporter 应该能导出纯文本格式。"""
    messages = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"}
    ]
    
    result = ChatExporter.to_text(messages)
    
    assert "User: Hello" in result
    assert "Assistant: Hi there!" in result


def test_file_uploader_ensure_dir():
    """FileUploader 应该能创建上传目录。"""
    FileUploader.ensure_upload_dir()
    assert FileUploader.UPLOAD_DIR.exists()


@pytest.mark.asyncio
async def test_file_uploader_save():
    """FileUploader 应该能保存上传文件。"""
    result = await FileUploader.save_upload(
        filename="test.txt",
        content=b"Hello World",
        user_id="test_user"
    )
    
    assert result["filename"] == "test.txt"
    assert result["size"] == 11
    
    # 清理
    import shutil
    from pathlib import Path
    upload_dir = Path("uploads/test_user")
    if upload_dir.exists():
        shutil.rmtree(upload_dir)


def test_file_uploader_read():
    """FileUploader 应该能读取文件内容。"""
    from pathlib import Path
    
    # 创建测试文件
    test_dir = Path("uploads/test_user")
    test_dir.mkdir(parents=True, exist_ok=True)
    test_file = test_dir / "test_read.txt"
    test_file.write_text("Test content")
    
    content = FileUploader.read_file(str(test_file))
    assert content == "Test content"
    
    # 清理
    import shutil
    shutil.rmtree(test_dir)


def test_file_uploader_list():
    """FileUploader 应该能列出用户文件。"""
    from pathlib import Path
    
    # 创建测试文件
    test_dir = Path("uploads/test_user")
    test_dir.mkdir(parents=True, exist_ok=True)
    (test_dir / "file1.txt").write_text("File 1")
    (test_dir / "file2.txt").write_text("File 2")
    
    files = FileUploader.get_user_files("test_user")
    assert len(files) == 2
    
    # 清理
    import shutil
    shutil.rmtree(test_dir)
