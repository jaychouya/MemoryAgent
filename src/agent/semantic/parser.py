"""
AST Parser for semantic code understanding.

Uses tree-sitter to parse code into AST for semantic matching.
Supports Python and JavaScript/TypeScript.
"""

import tree_sitter_python as tspython
import tree_sitter_javascript as tsjavascript
from tree_sitter import Language, Parser, Node
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
import hashlib


@dataclass
class ASTNode:
    """
    Represents an AST node with metadata.
    
    Attributes:
        type: Node type (e.g., 'function_definition', 'if_statement')
        text: Original source text
        start_line: Starting line number (0-based)
        end_line: Ending line number (0-based)
        children: Child nodes
        hash: Structural hash for quick comparison
    """
    type: str
    text: str
    start_line: int
    end_line: int
    children: List["ASTNode"] = field(default_factory=list)
    hash: str = ""
    
    def __post_init__(self):
        if not self.hash:
            self.hash = self._compute_hash()
    
    def _compute_hash(self) -> str:
        """Compute hash based on structure, not text."""
        structure = f"{self.type}:{len(self.children)}"
        for child in self.children[:3]:  # Limit depth for performance
            structure += f":{child.type}"
        return hashlib.md5(structure.encode()).hexdigest()[:8]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "type": self.type,
            "text": self.text[:100] + "..." if len(self.text) > 100 else self.text,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "children_count": len(self.children),
            "hash": self.hash
        }


class CodeParser:
    """
    Parse code into AST using tree-sitter.
    
    Supports:
    - Python
    - JavaScript
    - TypeScript
    """
    
    def __init__(self):
        self._parsers: Dict[str, Parser] = {}
        self._init_parsers()
    
    def _init_parsers(self):
        """Initialize language parsers."""
        try:
            # Python
            PY_LANGUAGE = Language(tspython.language())
            self._parsers["python"] = Parser(PY_LANGUAGE)
            
            # JavaScript
            JS_LANGUAGE = Language(tsjavascript.language())
            self._parsers["javascript"] = Parser(JS_LANGUAGE)
            self._parsers["typescript"] = Parser(JS_LANGUAGE)
        except Exception as e:
            print(f"Warning: Failed to initialize some parsers: {e}")
    
    def parse(self, code: str, language: str = "python") -> Optional[ASTNode]:
        """
        Parse code into AST.
        
        Args:
            code: Source code string
            language: Programming language ('python', 'javascript', 'typescript')
            
        Returns:
            ASTNode root node, or None if parsing fails
        """
        parser = self._parsers.get(language.lower())
        if not parser:
            return None
        
        try:
            tree = parser.parse(bytes(code, "utf8"))
            return self._convert_node(tree.root_node)
        except Exception as e:
            print(f"Parse error: {e}")
            return None
    
    def _convert_node(self, node: Node) -> ASTNode:
        """Convert tree-sitter node to ASTNode."""
        children = [self._convert_node(child) for child in node.children]
        
        text = ""
        if node.text:
            try:
                text = node.text.decode("utf8")
            except:
                text = str(node.text)
        
        return ASTNode(
            type=node.type,
            text=text,
            start_line=node.start_point[0],
            end_line=node.end_point[0],
            children=children
        )
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages."""
        return list(self._parsers.keys())
