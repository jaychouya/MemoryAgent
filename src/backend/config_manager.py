"""Simplified configuration and onboarding API."""

import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class ConfigManager:
    """Manages simplified configuration flow."""
    
    # 预设的模型配置
    PRESET_CONFIGS = {
        "openai": {
            "name": "OpenAI",
            "base_url": "https://api.openai.com/v1",
            "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
            "default_model": "gpt-4o-mini"
        },
        "deepseek": {
            "name": "DeepSeek",
            "base_url": "https://api.deepseek.com/v1",
            "models": ["deepseek-chat", "deepseek-coder"],
            "default_model": "deepseek-chat"
        },
        "qwen": {
            "name": "通义千问",
            "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "models": ["qwen-turbo", "qwen-plus", "qwen-max"],
            "default_model": "qwen-turbo"
        },
        "mimo": {
            "name": "小米 MiMo",
            "base_url": "https://api.mimo.ai/v1",
            "models": ["mimo-v2.5-pro", "mimo-v2.5"],
            "default_model": "mimo-v2.5"
        },
        "zhipu": {
            "name": "智谱 GLM",
            "base_url": "https://open.bigmodel.cn/api/paas/v4",
            "models": ["glm-4", "glm-4-flash"],
            "default_model": "glm-4-flash"
        }
    }
    
    def __init__(self, config_dir: Optional[str] = None):
        if config_dir is None:
            self.config_dir = Path(__file__).resolve().parents[2] / ".memoryai"
        else:
            self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config_file = self.config_dir / "config.json"
    
    def get_presets(self) -> Dict[str, Any]:
        """Get available preset configurations."""
        return {
            "presets": [
                {
                    "id": key,
                    "name": value["name"],
                    "models": value["models"],
                    "default_model": value["default_model"]
                }
                for key, value in self.PRESET_CONFIGS.items()
            ]
        }
    
    def save_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Save configuration."""
        try:
            # 验证配置
            if not config.get("api_key"):
                return {"success": False, "error": "API Key 不能为空"}
            
            if not config.get("base_url"):
                return {"success": False, "error": "Base URL 不能为空"}
            
            if not config.get("model"):
                return {"success": False, "error": "Model 不能为空"}
            
            # 保存配置
            self.config_file.write_text(json.dumps(config, indent=2))
            
            logger.info("Configuration saved successfully")
            return {"success": True, "message": "配置已保存"}
            
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            return {"success": False, "error": str(e)}
    
    def load_config(self) -> Optional[Dict[str, Any]]:
        """Load saved configuration."""
        if not self.config_file.exists():
            return None
        
        try:
            return json.loads(self.config_file.read_text())
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return None
    
    def quick_setup(
        self,
        provider: str,
        api_key: str,
        model: str = None
    ) -> Dict[str, Any]:
        """Quick setup with preset provider."""
        if provider not in self.PRESET_CONFIGS:
            return {"success": False, "error": f"未知的提供商: {provider}"}
        
        preset = self.PRESET_CONFIGS[provider]
        
        config = {
            "api_key": api_key,
            "base_url": preset["base_url"],
            "model": model or preset["default_model"],
            "provider": provider
        }
        
        return self.save_config(config)
    
    def get_setup_guide(self, provider: str) -> Dict[str, Any]:
        """Get setup guide for a provider."""
        guides = {
            "openai": {
                "title": "OpenAI 配置指南",
                "steps": [
                    "访问 https://platform.openai.com/api-keys",
                    "创建新的 API Key",
                    "复制 API Key 并粘贴到下方"
                ],
                "url": "https://platform.openai.com/api-keys"
            },
            "deepseek": {
                "title": "DeepSeek 配置指南",
                "steps": [
                    "访问 https://platform.deepseek.com/api_keys",
                    "创建新的 API Key",
                    "复制 API Key 并粘贴到下方"
                ],
                "url": "https://platform.deepseek.com/api_keys"
            },
            "qwen": {
                "title": "通义千问配置指南",
                "steps": [
                    "访问 https://dashscope.console.aliyun.com/apiKey",
                    "创建新的 API Key",
                    "复制 API Key 并粘贴到下方"
                ],
                "url": "https://dashscope.console.aliyun.com/apiKey"
            },
            "mimo": {
                "title": "小米 MiMo 配置指南",
                "steps": [
                    "访问小米 AI 开放平台",
                    "创建新的 API Key",
                    "复制 API Key 并粘贴到下方"
                ],
                "url": "https://ai.xiaomi.com"
            },
            "zhipu": {
                "title": "智谱 GLM 配置指南",
                "steps": [
                    "访问 https://open.bigmodel.cn/usercenter/apikeys",
                    "创建新的 API Key",
                    "复制 API Key 并粘贴到下方"
                ],
                "url": "https://open.bigmodel.cn/usercenter/apikeys"
            }
        }
        
        return guides.get(provider, {"title": "未知提供商", "steps": []})
