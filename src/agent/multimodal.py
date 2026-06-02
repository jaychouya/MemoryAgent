"""Multimodal support - image, file, and voice processing."""

import logging
import base64
import mimetypes
from typing import Dict, List, Any, Optional
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ModalityType(str, Enum):
    """Types of modalities."""
    TEXT = "text"
    IMAGE = "image"
    FILE = "file"
    VOICE = "voice"


@dataclass
class MultimodalContent:
    """Content with multiple modalities."""
    text: Optional[str] = None
    image_data: Optional[str] = None  # base64 encoded
    image_url: Optional[str] = None
    file_path: Optional[str] = None
    file_content: Optional[str] = None
    voice_data: Optional[str] = None  # base64 encoded
    modality_type: ModalityType = ModalityType.TEXT


class MultimodalProcessor:
    """Process multimodal content."""
    
    # 支持的图片格式
    SUPPORTED_IMAGE_FORMATS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
    
    # 支持的文件格式
    SUPPORTED_FILE_FORMATS = {'.txt', '.md', '.py', '.js', '.json', '.csv', '.html', '.css'}
    
    # 最大文件大小 (10MB)
    MAX_FILE_SIZE = 10 * 1024 * 1024
    
    def process_image(self, image_path: str) -> Optional[MultimodalContent]:
        """Process an image file."""
        path = Path(image_path)
        
        if not path.exists():
            logger.error(f"Image not found: {image_path}")
            return None
        
        if path.suffix.lower() not in self.SUPPORTED_IMAGE_FORMATS:
            logger.error(f"Unsupported image format: {path.suffix}")
            return None
        
        try:
            # 读取图片并转换为 base64
            with open(path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')
            
            # 获取 MIME 类型
            mime_type, _ = mimetypes.guess_type(str(path))
            
            return MultimodalContent(
                image_data=image_data,
                modality_type=ModalityType.IMAGE
            )
        except Exception as e:
            logger.error(f"Failed to process image: {e}")
            return None
    
    def process_file(self, file_path: str) -> Optional[MultimodalContent]:
        """Process a text file."""
        path = Path(file_path)
        
        if not path.exists():
            logger.error(f"File not found: {file_path}")
            return None
        
        if path.suffix.lower() not in self.SUPPORTED_FILE_FORMATS:
            logger.error(f"Unsupported file format: {path.suffix}")
            return None
        
        # 检查文件大小
        if path.stat().st_size > self.MAX_FILE_SIZE:
            logger.error(f"File too large: {path.stat().st_size} bytes")
            return None
        
        try:
            content = path.read_text(encoding='utf-8')
            
            return MultimodalContent(
                text=f"文件内容 ({path.name}):\n\n{content}",
                file_path=str(path),
                file_content=content,
                modality_type=ModalityType.FILE
            )
        except Exception as e:
            logger.error(f"Failed to process file: {e}")
            return None
    
    def process_voice(self, voice_path: str) -> Optional[MultimodalContent]:
        """Process a voice file."""
        path = Path(voice_path)
        
        if not path.exists():
            logger.error(f"Voice file not found: {voice_path}")
            return None
        
        try:
            # 读取音频并转换为 base64
            with open(path, 'rb') as f:
                voice_data = base64.b64encode(f.read()).decode('utf-8')
            
            return MultimodalContent(
                voice_data=voice_data,
                modality_type=ModalityType.VOICE
            )
        except Exception as e:
            logger.error(f"Failed to process voice: {e}")
            return None
    
    def create_multimodal_message(
        self,
        text: str = None,
        image_path: str = None,
        file_path: str = None,
        voice_path: str = None
    ) -> Optional[MultimodalContent]:
        """Create a multimodal message from various inputs."""
        content = MultimodalContent(text=text)
        
        if image_path:
            image_content = self.process_image(image_path)
            if image_content:
                content.image_data = image_content.image_data
                content.modality_type = ModalityType.IMAGE
        
        if file_path:
            file_content = self.process_file(file_path)
            if file_content:
                content.text = file_content.text
                content.file_path = file_path
                content.file_content = file_content.file_content
                content.modality_type = ModalityType.FILE
        
        if voice_path:
            voice_content = self.process_voice(voice_path)
            if voice_content:
                content.voice_data = voice_content.voice_data
                content.modality_type = ModalityType.VOICE
        
        return content
    
    def format_for_llm(self, content: MultimodalContent) -> Dict[str, Any]:
        """Format multimodal content for LLM consumption."""
        messages = []
        
        if content.text:
            messages.append({
                "type": "text",
                "text": content.text
            })
        
        if content.image_data:
            messages.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{content.image_data}"
                }
            })
        
        if content.voice_data:
            messages.append({
                "type": "audio",
                "audio": {
                    "data": content.voice_data
                }
            })
        
        return {"content": messages}
    
    def get_supported_formats(self) -> Dict[str, List[str]]:
        """Get supported file formats."""
        return {
            "images": list(self.SUPPORTED_IMAGE_FORMATS),
            "files": list(self.SUPPORTED_FILE_FORMATS)
        }
