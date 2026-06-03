"""CLAUDE.md six-level hierarchy system."""

import logging
import os
import re
from typing import Dict, List, Any, Optional
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ConfigLevel(str, Enum):
    """Configuration levels (from lowest to highest priority)."""
    MANAGED = "managed"      # System-level, admin only
    USER = "user"            # User home directory, global preferences
    PROJECT = "project"      # Project root, shared with team
    LOCAL = "local"          # Project root, not in git
    AUTO = "auto"            # Auto-generated memories (MEMORY.md)
    TEAM = "team"            # Team-shared AI-learned preferences


@dataclass
class ConfigLayer:
    """A configuration layer."""
    level: ConfigLevel
    path: Path
    content: str = ""
    loaded: bool = False


class ConfigHierarchy:
    """
    CLAUDE.md six-level hierarchy system.
    
    Inspired by Claude Code:
    - Managed: System-level policies
    - User: Global user preferences
    - Project: Project rules (shared via git)
    - Local: Local overrides (not in git)
    - Auto: Auto-generated memories
    - Team: Team-shared AI-learned preferences
    """
    
    # 层级定义（按加载顺序）
    LEVELS = [
        ConfigLevel.MANAGED,
        ConfigLevel.USER,
        ConfigLevel.PROJECT,
        ConfigLevel.LOCAL,
        ConfigLevel.AUTO,
        ConfigLevel.TEAM,
    ]
    
    # 各层级的文件路径模式
    PATH_PATTERNS = {
        ConfigLevel.MANAGED: [
            "/etc/memoryagent/CLAUDE.md",
            "~/.config/memoryagent/managed/CLAUDE.md",
        ],
        ConfigLevel.USER: [
            "~/.config/memoryagent/CLAUDE.md",
            "~/CLAUDE.md",
        ],
        ConfigLevel.PROJECT: [
            "CLAUDE.md",
            ".claude/CLAUDE.md",
        ],
        ConfigLevel.LOCAL: [
            "CLAUDE.local.md",
            ".claude/local/CLAUDE.md",
        ],
        ConfigLevel.AUTO: [
            "memories/MEMORY.md",
            ".claude/memories/MEMORY.md",
        ],
        ConfigLevel.TEAM: [
            "memories/team/MEMORY.md",
            ".claude/memories/team/MEMORY.md",
        ],
    }
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.layers: Dict[ConfigLevel, ConfigLayer] = {}
        self._init_layers()
    
    def _init_layers(self):
        """Initialize all layers."""
        for level in self.LEVELS:
            self.layers[level] = ConfigLayer(
                level=level,
                path=self._resolve_path(level)
            )
    
    def _resolve_path(self, level: ConfigLevel) -> Path:
        """Resolve file path for a level."""
        patterns = self.PATH_PATTERNS.get(level, [])
        
        for pattern in patterns:
            # 展开 ~ 和环境变量
            expanded = os.path.expanduser(pattern)
            expanded = os.path.expandvars(expanded)
            
            # 如果是相对路径，基于项目根目录
            if not os.path.isabs(expanded):
                expanded = str(self.project_root / expanded)
            
            path = Path(expanded)
            
            # 返回第一个存在的路径
            if path.exists():
                return path
        
        # 如果都不存在，返回第一个模式
        if patterns:
            expanded = os.path.expanduser(patterns[0])
            if not os.path.isabs(expanded):
                expanded = str(self.project_root / expanded)
            return Path(expanded)
        
        return Path(str(self.project_root))
    
    def load_all(self) -> str:
        """Load all configuration layers and return assembled content."""
        parts = []
        
        for level in self.LEVELS:
            layer = self.layers[level]
            content = self._load_layer(layer)
            
            if content:
                parts.append(f"# [{level.value.upper()}]")
                parts.append(content)
                parts.append("")
        
        assembled = "\n".join(parts)
        
        logger.info(f"Loaded {sum(1 for l in self.layers.values() if l.loaded)} config layers")
        return assembled
    
    def _load_layer(self, layer: ConfigLayer) -> Optional[str]:
        """Load a single layer."""
        path = layer.path
        
        if not path.exists():
            return None
        
        try:
            content = path.read_text(encoding="utf-8")
            
            # 处理 @include 指令
            content = self._process_includes(content, path.parent)
            
            layer.content = content
            layer.loaded = True
            
            return content
            
        except Exception as e:
            logger.warning(f"Failed to load {layer.level.value} config from {path}: {e}")
            return None
    
    def _process_includes(self, content: str, base_dir: Path) -> str:
        """Process @include directives."""
        # 匹配 @include 指令
        include_pattern = re.compile(r'@include\s+([^\s]+)')
        
        def replace_include(match):
            include_path = match.group(1)
            
            # 展开路径
            expanded = os.path.expanduser(include_path)
            if not os.path.isabs(expanded):
                expanded = str(base_dir / expanded)
            
            path = Path(expanded)
            
            if path.exists():
                try:
                    included_content = path.read_text(encoding="utf-8")
                    return included_content
                except Exception as e:
                    logger.warning(f"Failed to include {path}: {e}")
                    return f"[Include failed: {include_path}]"
            else:
                logger.warning(f"Include file not found: {path}")
                return f"[Include not found: {include_path}]"
        
        return include_pattern.sub(replace_include, content)
    
    def get_layer(self, level: ConfigLevel) -> Optional[ConfigLayer]:
        """Get a specific layer."""
        return self.layers.get(level)
    
    def get_loaded_layers(self) -> List[ConfigLayer]:
        """Get all loaded layers."""
        return [layer for layer in self.layers.values() if layer.loaded]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get hierarchy statistics."""
        loaded = self.get_loaded_layers()
        
        return {
            "total_levels": len(self.LEVELS),
            "loaded_levels": len(loaded),
            "loaded_levels_list": [l.level.value for l in loaded],
            "project_root": str(self.project_root)
        }
