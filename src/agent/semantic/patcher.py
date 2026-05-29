"""
Semantic Patcher for code modification.

Applies patches based on AST matching instead of text matching.
This allows for more robust code modifications that survive:
- Code formatting changes
- Variable renames
- Logic-preserving refactors
"""

from typing import Optional, List, Tuple
from dataclasses import dataclass
from .parser import CodeParser, ASTNode
from .matcher import ASTMatcher, MatchResult


@dataclass
class PatchResult:
    """
    Result of a semantic patch operation.
    
    Attributes:
        success: Whether the patch was applied successfully
        modified_content: The modified code (if successful)
        match: The match result used for patching
        message: Human-readable message about the result
    """
    success: bool
    modified_content: Optional[str]
    match: Optional[MatchResult]
    message: str
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            "success": self.success,
            "has_content": self.modified_content is not None,
            "match_similarity": self.match.similarity if self.match else None,
            "message": self.message
        }


class SemanticPatcher:
    """
    Apply code patches using semantic matching.
    
    Instead of exact text matching, this patcher:
    1. Parses both the target code and the pattern to replace
    2. Finds semantically similar AST nodes
    3. Replaces the matched node with the new code
    
    This approach is more robust than text-based patching because:
    - It survives formatting changes
    - It can match renamed variables
    - It understands code structure
    """
    
    def __init__(self, similarity_threshold: float = 0.7):
        """
        Initialize the semantic patcher.
        
        Args:
            similarity_threshold: Minimum similarity to consider a match
        """
        self.parser = CodeParser()
        self.matcher = ASTMatcher(similarity_threshold)
    
    def find_and_replace(
        self,
        file_content: str,
        old_pattern: str,
        new_pattern: str,
        language: str = "python"
    ) -> PatchResult:
        """
        Find and replace using semantic matching.
        
        Args:
            file_content: Current file content
            old_pattern: Pattern to find (can be semantically different)
            new_pattern: Replacement pattern
            language: Programming language
            
        Returns:
            PatchResult with the modified content or error message
        """
        # Parse both
        file_ast = self.parser.parse(file_content, language)
        pattern_ast = self.parser.parse(old_pattern, language)
        
        if not file_ast:
            return PatchResult(
                success=False,
                modified_content=None,
                match=None,
                message=f"Failed to parse file content as {language}"
            )
        
        if not pattern_ast:
            return PatchResult(
                success=False,
                modified_content=None,
                match=None,
                message=f"Failed to parse pattern as {language}"
            )
        
        # Find similar nodes
        matches = self.matcher.find_similar(pattern_ast, file_ast)
        
        if not matches:
            return PatchResult(
                success=False,
                modified_content=None,
                match=None,
                message="No similar code found in file"
            )
        
        # Get best match
        best_match = matches[0]
        
        # Check if similarity is high enough
        if best_match.similarity < 0.5:
            return PatchResult(
                success=False,
                modified_content=None,
                match=best_match,
                message=f"Best match similarity too low: {best_match.similarity:.2f}"
            )
        
        # Apply patch
        try:
            modified_content = self._apply_patch(
                file_content,
                best_match,
                new_pattern
            )
            
            return PatchResult(
                success=True,
                modified_content=modified_content,
                match=best_match,
                message=f"Patch applied successfully (similarity: {best_match.similarity:.2f})"
            )
        except Exception as e:
            return PatchResult(
                success=False,
                modified_content=None,
                match=best_match,
                message=f"Failed to apply patch: {str(e)}"
            )
    
    def _apply_patch(
        self,
        original_content: str,
        match: MatchResult,
        new_pattern: str
    ) -> str:
        """
        Apply the patch to the original content.
        
        Args:
            original_content: Original code
            match: Match result indicating where to apply patch
            new_pattern: New code to insert
            
        Returns:
            Modified code
        """
        lines = original_content.split("\n")
        
        # Get the lines to replace
        start_line = match.start_line
        end_line = match.end_line
        
        # Build new content
        new_lines = lines[:start_line]
        new_lines.extend(new_pattern.split("\n"))
        new_lines.extend(lines[end_line + 1:])
        
        return "\n".join(new_lines)
    
    def find_function(
        self,
        file_content: str,
        function_name: str,
        language: str = "python"
    ) -> Optional[MatchResult]:
        """
        Find a specific function by name.
        
        Args:
            file_content: File content to search
            function_name: Name of the function to find
            language: Programming language
            
        Returns:
            MatchResult if found, None otherwise
        """
        file_ast = self.parser.parse(file_content, language)
        if not file_ast:
            return None
        
        # Search for function definitions
        for node in self.matcher._walk_ast(file_ast):
            if node.type in ["function_definition", "function_declaration"]:
                # Check if this is the function we're looking for
                if function_name in node.text:
                    return MatchResult(
                        node=node,
                        similarity=1.0,
                        start_line=node.start_line,
                        end_line=node.end_line,
                        confidence=1.0
                    )
        
        return None
    
    def extract_function(
        self,
        file_content: str,
        function_name: str,
        language: str = "python"
    ) -> Optional[str]:
        """
        Extract a specific function from the file.
        
        Args:
            file_content: File content
            function_name: Name of the function to extract
            language: Programming language
            
        Returns:
            Function code if found, None otherwise
        """
        match = self.find_function(file_content, function_name, language)
        if not match:
            return None
        
        lines = file_content.split("\n")
        return "\n".join(lines[match.start_line:match.end_line + 1])
