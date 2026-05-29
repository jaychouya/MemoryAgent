"""
AST Matcher for semantic code matching.

Finds semantically similar code blocks using AST comparison.
Supports fuzzy matching with configurable similarity threshold.
"""

from typing import List, Optional, Tuple
from dataclasses import dataclass
from .parser import ASTNode


@dataclass
class MatchResult:
    """
    Result of AST matching.
    
    Attributes:
        node: Matched AST node
        similarity: Similarity score (0.0 to 1.0)
        start_line: Starting line number
        end_line: Ending line number
        confidence: Match confidence
    """
    node: ASTNode
    similarity: float
    start_line: int
    end_line: int
    confidence: float = 0.0
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            "similarity": self.similarity,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "confidence": self.confidence,
            "node_type": self.node.type
        }


class ASTMatcher:
    """
    Match code blocks using AST similarity.
    
    Features:
    - Type-based matching
    - Structure-based matching
    - Configurable similarity threshold
    - Support for multiple match results
    """
    
    def __init__(self, similarity_threshold: float = 0.7):
        """
        Initialize matcher.
        
        Args:
            similarity_threshold: Minimum similarity score to consider a match
        """
        self.similarity_threshold = similarity_threshold
    
    def find_similar(
        self,
        target: ASTNode,
        source: ASTNode,
        threshold: float = None,
        max_results: int = 10
    ) -> List[MatchResult]:
        """
        Find nodes in source similar to target.
        
        Args:
            target: Target AST node to match
            source: Source AST node to search in
            threshold: Override default similarity threshold
            max_results: Maximum number of results
            
        Returns:
            List of MatchResult sorted by similarity
        """
        if threshold is None:
            threshold = self.similarity_threshold
        
        results = []
        
        # Compare target with each node in source
        for source_node in self._walk_ast(source):
            similarity = self._compute_similarity(target, source_node)
            
            if similarity >= threshold:
                results.append(MatchResult(
                    node=source_node,
                    similarity=similarity,
                    start_line=source_node.start_line,
                    end_line=source_node.end_line,
                    confidence=similarity * 0.9  # Slight discount for fuzzy match
                ))
        
        # Sort by similarity (descending)
        results.sort(key=lambda r: r.similarity, reverse=True)
        
        return results[:max_results]
    
    def find_exact_type_match(
        self,
        target_type: str,
        source: ASTNode
    ) -> List[MatchResult]:
        """
        Find all nodes of a specific type in source.
        
        Args:
            target_type: AST node type to find
            source: Source AST node to search in
            
        Returns:
            List of MatchResult for matching nodes
        """
        results = []
        
        for node in self._walk_ast(source):
            if node.type == target_type:
                results.append(MatchResult(
                    node=node,
                    similarity=1.0,
                    start_line=node.start_line,
                    end_line=node.end_line,
                    confidence=1.0
                ))
        
        return results
    
    def _compute_similarity(self, node1: ASTNode, node2: ASTNode) -> float:
        """
        Compute similarity between two AST nodes.
        
        Uses multiple factors:
        - Type match
        - Structure match (children count)
        - Hash match (structural hash)
        """
        # Type match (most important)
        type_score = 1.0 if node1.type == node2.type else 0.0
        
        # Structure match (children count)
        max_children = max(len(node1.children), len(node2.children), 1)
        structure_score = 1.0 - abs(len(node1.children) - len(node2.children)) / max_children
        
        # Hash match (structural hash)
        hash_score = 1.0 if node1.hash == node2.hash else 0.0
        
        # Weighted average
        return (type_score * 0.5 + structure_score * 0.3 + hash_score * 0.2)
    
    def _walk_ast(self, node: ASTNode):
        """Walk through all nodes in AST (generator)."""
        yield node
        for child in node.children:
            yield from self._walk_ast(child)
    
    def get_node_at_line(self, root: ASTNode, line: int) -> Optional[ASTNode]:
        """
        Get the most specific node at a given line.
        
        Args:
            root: Root AST node
            line: Line number (0-based)
            
        Returns:
            Most specific AST node at that line
        """
        best_match = None
        
        for node in self._walk_ast(root):
            if node.start_line <= line <= node.end_line:
                if best_match is None or (
                    node.end_line - node.start_line < best_match.end_line - best_match.start_line
                ):
                    best_match = node
        
        return best_match
