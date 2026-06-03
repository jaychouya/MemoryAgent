"""Conditional rules system for CLAUDE.md."""

import logging
import os
import re
import yaml
from typing import Dict, List, Any, Optional
from pathlib import Path
from dataclasses import dataclass, field
from fnmatch import fnmatch

logger = logging.getLogger(__name__)


@dataclass
class ConditionalRule:
    """A conditional rule that loads based on file patterns."""
    name: str
    description: str
    paths: List[str]  # glob patterns
    content: str
    source_file: Optional[str] = None


class ConditionalRules:
    """
    Conditional rules system.
    
    Inspired by Claude Code's .claude/rules/ directory:
    - Rules are .md files with YAML frontmatter
    - Each rule has a 'paths' field with glob patterns
    - Rules only load when current file matches patterns
    """
    
    def __init__(self, rules_dir: str = ".claude/rules"):
        self.rules_dir = Path(rules_dir)
        self.rules: List[ConditionalRule] = []
    
    def load_rules(self):
        """Load all rules from rules directory."""
        self.rules = []
        
        if not self.rules_dir.exists():
            logger.debug(f"Rules directory not found: {self.rules_dir}")
            return
        
        for rule_file in self.rules_dir.glob("*.md"):
            try:
                rule = self._parse_rule_file(rule_file)
                if rule:
                    self.rules.append(rule)
            except Exception as e:
                logger.warning(f"Failed to parse rule file {rule_file}: {e}")
        
        logger.info(f"Loaded {len(self.rules)} conditional rules")
    
    def _parse_rule_file(self, file_path: Path) -> Optional[ConditionalRule]:
        """Parse a rule file with YAML frontmatter."""
        content = file_path.read_text(encoding="utf-8")
        
        # 解析 YAML frontmatter
        frontmatter_match = re.match(r'^---\n(.*?)\n---\n(.*)$', content, re.DOTALL)
        
        if not frontmatter_match:
            # 没有 frontmatter，整个文件作为内容
            return ConditionalRule(
                name=file_path.stem,
                description="",
                paths=["**"],  # 匹配所有文件
                content=content,
                source_file=str(file_path)
            )
        
        yaml_content = frontmatter_match.group(1)
        body_content = frontmatter_match.group(2)
        
        try:
            metadata = yaml.safe_load(yaml_content)
        except yaml.YAMLError:
            metadata = {}
        
        return ConditionalRule(
            name=metadata.get("name", file_path.stem),
            description=metadata.get("description", ""),
            paths=metadata.get("paths", ["**"]),
            content=body_content.strip(),
            source_file=str(file_path)
        )
    
    def get_matching_rules(self, current_file: str) -> List[ConditionalRule]:
        """Get rules that match the current file path."""
        matching = []
        
        for rule in self.rules:
            for pattern in rule.paths:
                if fnmatch(current_file, pattern) or fnmatch(current_file, f"**/{pattern}"):
                    matching.append(rule)
                    break
        
        return matching
    
    def get_rules_for_files(self, files: List[str]) -> List[ConditionalRule]:
        """Get rules that match any of the given files."""
        matching = []
        seen_names = set()
        
        for file_path in files:
            for rule in self.get_matching_rules(file_path):
                if rule.name not in seen_names:
                    matching.append(rule)
                    seen_names.add(rule.name)
        
        return matching
    
    def assemble_rules(self, current_file: str) -> str:
        """Assemble matching rules for current file."""
        matching = self.get_matching_rules(current_file)
        
        if not matching:
            return ""
        
        parts = []
        for rule in matching:
            if rule.name:
                parts.append(f"# Rule: {rule.name}")
            if rule.description:
                parts.append(f"# {rule.description}")
            parts.append(rule.content)
            parts.append("")
        
        return "\n".join(parts)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get rules statistics."""
        total_patterns = sum(len(rule.paths) for rule in self.rules)
        
        return {
            "total_rules": len(self.rules),
            "total_patterns": total_patterns,
            "rules_dir": str(self.rules_dir),
            "rules": [
                {
                    "name": rule.name,
                    "paths": rule.paths,
                    "source": rule.source_file
                }
                for rule in self.rules
            ]
        }


class IncludeProcessor:
    """
    @include directive processor.
    
    Inspired by Claude Code's @include support:
    - Include files using @path/to/file.md
    - Prevent circular includes
    - Support relative and absolute paths
    """
    
    def __init__(self, max_depth: int = 10):
        self.max_depth = max_depth
        self._included_files: set = set()
    
    def process(self, content: str, base_dir: Path, depth: int = 0) -> str:
        """Process @include directives."""
        if depth >= self.max_depth:
            logger.warning(f"Max include depth reached ({self.max_depth})")
            return content
        
        include_pattern = re.compile(r'@include\s+([^\s]+)')
        
        def replace_include(match):
            include_path = match.group(1)
            
            # 检查循环引用
            resolved_path = self._resolve_path(include_path, base_dir)
            if resolved_path in self._included_files:
                logger.warning(f"Circular include detected: {include_path}")
                return f"[Circular include: {include_path}]"
            
            # 标记为已包含
            self._included_files.add(resolved_path)
            
            # 读取文件
            path = Path(resolved_path)
            if path.exists():
                try:
                    included_content = path.read_text(encoding="utf-8")
                    # 递归处理嵌套的 @include
                    return self.process(included_content, path.parent, depth + 1)
                except Exception as e:
                    logger.warning(f"Failed to include {path}: {e}")
                    return f"[Include error: {include_path}]"
            else:
                logger.warning(f"Include file not found: {path}")
                return f"[Include not found: {include_path}]"
        
        return include_pattern.sub(replace_include, content)
    
    def _resolve_path(self, include_path: str, base_dir: Path) -> str:
        """Resolve include path."""
        expanded = os.path.expanduser(include_path)
        expanded = os.path.expandvars(expanded)
        
        if not os.path.isabs(expanded):
            expanded = str(base_dir / expanded)
        
        return str(Path(expanded).resolve())
    
    def clear_cache(self):
        """Clear included files cache."""
        self._included_files.clear()
