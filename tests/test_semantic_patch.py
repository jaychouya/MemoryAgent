"""
Unit tests for Semantic Patch module.
"""

import pytest
from src.agent.semantic.parser import CodeParser, ASTNode
from src.agent.semantic.matcher import ASTMatcher, MatchResult
from src.agent.semantic.patcher import SemanticPatcher, PatchResult


class TestCodeParser:
    """Tests for CodeParser."""
    
    def test_parse_python_function(self):
        parser = CodeParser()
        code = "def hello():\n    print('world')"
        result = parser.parse(code, "python")
        
        assert result is not None
        assert result.type == "module"
        assert len(result.children) > 0
    
    def test_parse_python_class(self):
        parser = CodeParser()
        code = "class MyClass:\n    def method(self):\n        pass"
        result = parser.parse(code, "python")
        
        assert result is not None
        assert result.type == "module"
    
    def test_parse_invalid_code(self):
        parser = CodeParser()
        code = "def invalid syntax!!!"
        result = parser.parse(code, "python")
        
        assert result is not None
    
    def test_parse_empty_code(self):
        parser = CodeParser()
        result = parser.parse("", "python")
        
        assert result is not None
    
    def test_get_supported_languages(self):
        parser = CodeParser()
        languages = parser.get_supported_languages()
        
        assert "python" in languages
        assert "javascript" in languages


class TestASTNode:
    """Tests for ASTNode."""
    
    def test_node_creation(self):
        node = ASTNode(
            type="identifier",
            text="hello",
            start_line=0,
            end_line=0,
            children=[]
        )
        
        assert node.type == "identifier"
        assert node.text == "hello"
        assert node.start_line == 0
        assert node.end_line == 0
        assert node.hash != ""
    
    def test_node_to_dict(self):
        node = ASTNode(
            type="function_definition",
            text="def hello(): pass",
            start_line=0,
            end_line=0,
            children=[]
        )
        
        result = node.to_dict()
        assert "type" in result
        assert "text" in result
        assert "hash" in result


class TestASTMatcher:
    """Tests for ASTMatcher."""
    
    def test_find_similar_nodes(self):
        parser = CodeParser()
        matcher = ASTMatcher()
        
        code1 = "def hello():\n    print('hello')"
        code2 = "def greet():\n    print('greet')"
        
        ast1 = parser.parse(code1, "python")
        ast2 = parser.parse(code2, "python")
        
        matches = matcher.find_similar(ast1, ast2)
        
        assert len(matches) > 0
    
    def test_find_similar_with_threshold(self):
        parser = CodeParser()
        matcher = ASTMatcher(similarity_threshold=0.9)
        
        code1 = "def hello():\n    print('hello')"
        code2 = "x = 1 + 2"
        
        ast1 = parser.parse(code1, "python")
        ast2 = parser.parse(code2, "python")
        
        matches = matcher.find_similar(ast1, ast2, threshold=0.9)
        
        assert isinstance(matches, list)
    
    def test_find_exact_type_match(self):
        parser = CodeParser()
        matcher = ASTMatcher()
        
        code = "def hello():\n    pass\n\ndef world():\n    pass"
        ast = parser.parse(code, "python")
        
        matches = matcher.find_exact_type_match("function_definition", ast)
        
        assert len(matches) == 2


class TestSemanticPatcher:
    """Tests for SemanticPatcher."""
    
    def test_find_and_replace_similar(self):
        patcher = SemanticPatcher()
        
        file_content = "def hello():\n    print('world')"
        old_pattern = "def hello():\n    print('world')"
        new_pattern = "def greet():\n    print('greet')"
        
        result = patcher.find_and_replace(file_content, old_pattern, new_pattern, "python")
        
        assert isinstance(result, PatchResult)
        assert result.success is True
        assert result.modified_content is not None
    
    def test_find_and_replace_no_match(self):
        patcher = SemanticPatcher()
        
        file_content = "x = 1 + 2"
        old_pattern = "def hello():\n    print('world')"
        new_pattern = "def greet():\n    print('greet')"
        
        result = patcher.find_and_replace(file_content, old_pattern, new_pattern, "python")
        
        assert isinstance(result, PatchResult)
    
    def test_find_function(self):
        patcher = SemanticPatcher()
        
        file_content = "def hello():\n    print('world')\n\ndef greet():\n    print('greet')"
        
        result = patcher.find_function(file_content, "hello", "python")
        
        assert result is not None
        assert result.similarity == 1.0
    
    def test_extract_function(self):
        patcher = SemanticPatcher()
        
        file_content = "def hello():\n    print('world')\n\ndef greet():\n    print('greet')"
        
        result = patcher.extract_function(file_content, "hello", "python")
        
        assert result is not None
        assert "hello" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
