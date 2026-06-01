"""ModelRouter - Intelligent model routing inspired by OpenHuman."""

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ModelType(str, Enum):
    """Model types for routing."""
    FAST = "fast"           # Quick responses (GPT-4o-mini, local Ollama)
    REASONING = "reasoning"  # Complex logic (Claude Sonnet, o1)
    VISION = "vision"        # Image analysis (GPT-4o Vision)
    LOCAL = "local"          # Local models (Ollama)


@dataclass
class ModelConfig:
    """Model configuration."""
    model_type: ModelType
    model_name: str
    api_key: str
    base_url: str
    max_tokens: int = 4096
    temperature: float = 0.7


class ModelRouter:
    """
    Intelligent model router.
    
    Inspired by OpenHuman's ModelRouter:
    - Simple tasks → Fast model
    - Complex reasoning → Reasoning model
    - Image analysis → Vision model
    - Privacy-sensitive → Local model
    """
    
    def __init__(self):
        self.models: Dict[ModelType, ModelConfig] = {}
        self._load_default_models()
    
    def _load_default_models(self):
        """Load default model configurations."""
        # Fast model (default)
        self.models[ModelType.FAST] = ModelConfig(
            model_type=ModelType.FAST,
            model_name="gpt-4o-mini",
            api_key="",
            base_url="https://api.openai.com/v1",
            max_tokens=4096,
            temperature=0.7
        )
        
        # Reasoning model
        self.models[ModelType.REASONING] = ModelConfig(
            model_type=ModelType.REASONING,
            model_name="claude-3-5-sonnet-20241022",
            api_key="",
            base_url="https://api.anthropic.com/v1",
            max_tokens=8192,
            temperature=0.5
        )
        
        # Vision model
        self.models[ModelType.VISION] = ModelConfig(
            model_type=ModelType.VISION,
            model_name="gpt-4o",
            api_key="",
            base_url="https://api.openai.com/v1",
            max_tokens=4096,
            temperature=0.7
        )
        
        # Local model
        self.models[ModelType.LOCAL] = ModelConfig(
            model_type=ModelType.LOCAL,
            model_name="llama3.2",
            api_key="",
            base_url="http://localhost:11434/v1",
            max_tokens=4096,
            temperature=0.7
        )
    
    def configure(self, model_type: ModelType, config: ModelConfig):
        """Configure a model."""
        self.models[model_type] = config
        logger.info(f"Configured {model_type} model: {config.model_name}")
    
    def route(self, prompt: str, has_images: bool = False) -> ModelType:
        """
        Route to appropriate model based on task.
        
        Args:
            prompt: User prompt
            has_images: Whether prompt contains images
            
        Returns:
            Model type to use
        """
        prompt_lower = prompt.lower()
        
        # Vision tasks
        if has_images or any(word in prompt_lower for word in [
            "图片", "图像", "屏幕", "截图", "分析图表", "看图", "image", "screen"
        ]):
            return ModelType.VISION
        
        # Reasoning tasks
        if any(word in prompt_lower for word in [
            "分析", "规划", "总结", "推理", "比较", "评估", "设计",
            "analyze", "plan", "summarize", "reason", "compare", "evaluate"
        ]):
            return ModelType.REASONING
        
        # Privacy-sensitive tasks
        if any(word in prompt_lower for word in [
            "密码", "密钥", "私密", "个人", "password", "secret", "private"
        ]):
            return ModelType.LOCAL
        
        # Default to fast model
        return ModelType.FAST
    
    def get_config(self, model_type: ModelType) -> ModelConfig:
        """Get model configuration."""
        return self.models.get(model_type, self.models[ModelType.FAST])
    
    def get_all_configs(self) -> Dict[str, ModelConfig]:
        """Get all model configurations."""
        return {k.value: v for k, v in self.models.items()}
