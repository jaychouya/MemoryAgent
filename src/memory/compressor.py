"""TokenJuice-style context compression for MemoryAgent."""

import re
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path
import json

logger = logging.getLogger(__name__)


@dataclass
class CompressionRule:
    """A compression rule for filtering tool output."""
    
    id: str
    match: Dict[str, Any]
    filters: Dict[str, Any] = field(default_factory=dict)
    output: Dict[str, Any] = field(default_factory=dict)
    
    def matches(self, tool_name: str, command: str = "") -> bool:
        """Check if this rule matches the tool and command."""
        # Check toolNames
        if "toolNames" in self.match:
            if tool_name not in self.match["toolNames"]:
                return False
        
        # Check argvIncludes
        if "argvIncludes" in self.match:
            for arg in self.match["argvIncludes"]:
                if arg not in command:
                    return False
        
        return True
    
    def apply(self, content: str) -> str:
        """Apply filters to content."""
        lines = content.split("\n")
        result = []
        
        skip_patterns = self.filters.get("skipPatterns", [])
        keep_patterns = self.filters.get("keepPatterns", [])
        
        for line in lines:
            # Check skip patterns first
            should_skip = False
            for pattern in skip_patterns:
                if re.match(pattern, line):
                    should_skip = True
                    break
            
            if should_skip:
                continue
            
            # If keep patterns exist, only keep matching lines
            if keep_patterns:
                for pattern in keep_patterns:
                    if re.search(pattern, line):
                        result.append(line)
                        break
            else:
                result.append(line)
        
        return "\n".join(result)
    
    def apply_head_tail(self, content: str) -> str:
        """Apply head-tail strategy."""
        lines = content.split("\n")
        
        head_lines = self.output.get("headLines", 0)
        tail_lines = self.output.get("tailLines", 0)
        
        if head_lines + tail_lines >= len(lines):
            return content
        
        result = []
        if head_lines > 0:
            result.extend(lines[:head_lines])
            result.append("...")
        if tail_lines > 0:
            result.extend(lines[-tail_lines:])
        
        return "\n".join(result)


class ContextCompressor:
    """Compresses context using rules (TokenJuice-style)."""
    
    def __init__(self):
        self.rules: List[CompressionRule] = []
        self.stats = {
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "compressions": 0
        }
        self._load_builtin_rules()
    
    def _load_builtin_rules(self):
        """Load built-in compression rules."""
        # Git status rule
        self.add_rule(CompressionRule(
            id="git__status",
            match={"toolNames": ["git"], "argvIncludes": ["status"]},
            filters={
                "skipPatterns": [
                    "^On branch ",
                    "^Your branch is ",
                    "^\\(use \"git .+\" to .+\\)$",
                    "^nothing to commit"
                ]
            }
        ))
        
        # Git diff rule
        self.add_rule(CompressionRule(
            id="git__diff",
            match={"toolNames": ["git"], "argvIncludes": ["diff"]},
            filters={"skipPatterns": ["^diff --git", "^index ", "^@@ "]},
            output={"strategy": "head-tail", "headLines": 20, "tailLines": 10}
        ))
        
        # npm install rule
        self.add_rule(CompressionRule(
            id="npm__install",
            match={"toolNames": ["npm"], "argvIncludes": ["install"]},
            filters={"skipPatterns": ["^npm WARN", "^added \\d+ packages"]},
            output={"strategy": "head-tail", "headLines": 5, "tailLines": 5}
        ))
        
        # Python test rule
        self.add_rule(CompressionRule(
            id="pytest__run",
            match={"toolNames": ["pytest"]},
            filters={"keepPatterns": ["PASSED", "FAILED", "ERROR", "test_"]},
            output={"strategy": "tail", "tailLines": 20}
        ))
    
    def add_rule(self, rule: CompressionRule):
        """Add a compression rule."""
        self.rules.append(rule)
    
    def _count_tokens(self, text: str) -> int:
        """Estimate token count (rough approximation)."""
        # Simple estimation: ~4 chars per token for English, ~2 for Chinese
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        english_chars = len(text) - chinese_chars
        return chinese_chars + (english_chars // 4)
    
    def _find_matching_rule(self, tool_name: str, command: str) -> Optional[CompressionRule]:
        """Find the most specific matching rule."""
        matching = []
        for rule in self.rules:
            if rule.matches(tool_name, command):
                matching.append(rule)
        
        if not matching:
            return None
        
        # Return most specific rule (most match criteria)
        return max(matching, key=lambda r: len(r.match))
    
    def compress(self, tool_name: str, command: str, output: str) -> str:
        """Compress tool output using rules."""
        input_tokens = self._count_tokens(output)
        self.stats["total_input_tokens"] += input_tokens
        
        rule = self._find_matching_rule(tool_name, command)
        
        if rule:
            # Apply filters
            result = rule.apply(output)
            
            # Apply output strategy
            if rule.output.get("strategy") == "head-tail":
                result = rule.apply_head_tail(result)
            elif rule.output.get("strategy") == "tail":
                tail_lines = rule.output.get("tailLines", 10)
                lines = result.split("\n")
                result = "\n".join(lines[-tail_lines:])
            
            output_tokens = self._count_tokens(result)
            self.stats["total_output_tokens"] += output_tokens
            self.stats["compressions"] += 1
            
            logger.debug(f"Compressed {tool_name}: {input_tokens} -> {output_tokens} tokens")
            return result
        
        # No rule found, return original
        self.stats["total_output_tokens"] += input_tokens
        return output
    
    def get_stats(self) -> Dict[str, Any]:
        """Get compression statistics."""
        total_input = self.stats["total_input_tokens"]
        total_output = self.stats["total_output_tokens"]
        
        return {
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "compressions": self.stats["compressions"],
            "savings_ratio": (total_input - total_output) / total_input if total_input > 0 else 0
        }
