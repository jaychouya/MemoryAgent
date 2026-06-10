"""Chat export and file upload functionality."""

import json
import logging
import mimetypes
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime
from pathlib import Path

from src.agent.multimodal import MultimodalProcessor

logger = logging.getLogger(__name__)

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}


def build_user_message_content(
    message: str,
    attachments: Optional[List[Dict[str, str]]] = None,
) -> Tuple[Union[str, List[Dict[str, Any]]], List[Dict[str, str]]]:
    processor = MultimodalProcessor()
    parts: List[Dict[str, Any]] = []
    meta: List[Dict[str, str]] = []

    if (message or "").strip():
        parts.append({"type": "text", "text": message.strip()})

    for att in attachments or []:
        path = att.get("path", "")
        filename = att.get("filename", Path(path).name)
        kind = att.get("kind", "file")
        if not path or not Path(path).exists():
            continue
        suffix = Path(path).suffix.lower()
        is_image = kind == "image" or suffix in IMAGE_EXTENSIONS
        if is_image:
            img = processor.process_image(path)
            if img and img.image_data:
                mime, _ = mimetypes.guess_type(path)
                mime = mime or "image/jpeg"
                parts.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:{mime};base64,{img.image_data}"},
                })
                meta.append({"filename": filename, "kind": "image", "path": path})
        else:
            file_content = processor.process_file(path)
            if file_content and file_content.text:
                parts.append({"type": "text", "text": file_content.text})
                meta.append({"filename": filename, "kind": "file", "path": path})

    if not parts:
        return message or "（空消息）", meta
    if len(parts) == 1 and parts[0]["type"] == "text":
        return parts[0]["text"], meta
    return parts, meta


class ChatExporter:
    """Export chat history in various formats."""
    
    @staticmethod
    def to_json(messages: List[Dict], pretty: bool = True) -> str:
        """Export messages as JSON."""
        export = {
            "exported_at": datetime.now().isoformat(),
            "message_count": len(messages),
            "messages": messages
        }
        if pretty:
            return json.dumps(export, indent=2, ensure_ascii=False)
        return json.dumps(export, ensure_ascii=False)
    
    @staticmethod
    def to_markdown(messages: List[Dict]) -> str:
        """Export messages as Markdown."""
        lines = ["# Chat History\n"]
        lines.append(f"Exported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        lines.append(f"Messages: {len(messages)}\n\n---\n\n")
        
        for msg in messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            timestamp = msg.get("timestamp", "")
            
            if role == "user":
                lines.append(f"## User\n")
            elif role == "assistant":
                lines.append(f"## Assistant\n")
            elif role == "tool":
                lines.append(f"## Tool Result\n")
            else:
                lines.append(f"## {role}\n")
            
            if timestamp:
                lines.append(f"*{timestamp}*\n")
            
            lines.append(f"{content}\n\n---\n\n")
        
        return "\n".join(lines)
    
    @staticmethod
    def to_text(messages: List[Dict]) -> str:
        """Export messages as plain text."""
        lines = []
        
        for msg in messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            
            if role == "user":
                lines.append(f"User: {content}")
            elif role == "assistant":
                lines.append(f"Assistant: {content}")
            elif role == "tool":
                lines.append(f"[Tool Result]: {content}")
            
            lines.append("")
        
        return "\n".join(lines)


class FileUploader:
    """Handle file uploads for context."""
    
    UPLOAD_DIR = Path("uploads")
    
    @classmethod
    def ensure_upload_dir(cls):
        """Ensure upload directory exists."""
        cls.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    async def save_upload(
        cls,
        filename: str,
        content: bytes,
        user_id: str
    ) -> Dict[str, Any]:
        """Save uploaded file."""
        cls.ensure_upload_dir()
        
        # Create user directory
        user_dir = cls.UPLOAD_DIR / user_id
        user_dir.mkdir(exist_ok=True)
        
        # Save file
        file_path = user_dir / filename
        file_path.write_bytes(content)
        
        logger.info(f"Saved upload: {file_path}")
        
        return {
            "filename": filename,
            "path": str(file_path),
            "size": len(content),
            "uploaded_at": datetime.now().isoformat()
        }
    
    @classmethod
    def read_file(cls, file_path: str) -> Optional[str]:
        """Read file content as text."""
        try:
            path = Path(file_path)
            if path.exists():
                return path.read_text(encoding="utf-8")
        except Exception as e:
            logger.error(f"Failed to read file {file_path}: {e}")
        return None
    
    @classmethod
    def get_user_files(cls, user_id: str) -> List[Dict[str, Any]]:
        """Get list of user's uploaded files."""
        user_dir = cls.UPLOAD_DIR / user_id
        if not user_dir.exists():
            return []
        
        files = []
        for file_path in user_dir.iterdir():
            if file_path.is_file():
                files.append({
                    "filename": file_path.name,
                    "path": str(file_path),
                    "size": file_path.stat().st_size,
                    "modified": datetime.fromtimestamp(
                        file_path.stat().st_mtime
                    ).isoformat()
                })
        
        return files
