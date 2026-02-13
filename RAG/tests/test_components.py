"""Basic tests for RAG system components."""
import pytest
from pathlib import Path
from src.utils.models import CodeChunk, RetrievalResult
from src.ingestion.code_ingestion import CodeChunker, ASTAnalyzer
from src.retrieval.semantic_retriever import KeywordRetriever


class TestCodeChunker:
    """Test code chunking functionality."""

    def test_chunk_python_code(self):
        """Test Python code chunking."""
        chunker = CodeChunker(chunk_size=512)

        code = '''
def hello_world():
    """Say hello."""
    return "Hello, World!"

class MyClass:
    def __init__(self):
        self.value = 42
    
    def method(self):
        return self.value
'''

        path = Path("test.py")
        chunks = chunker.chunk_file(path, code, "py")

        assert len(chunks) > 0
        assert all(isinstance(chunk, CodeChunk) for chunk in chunks)
        assert chunks[0].language == "py"


class TestKeywordRetriever:
    """Test keyword-based retrieval."""

    def test_keyword_search(self):
        """Test keyword search functionality."""
        chunks = [
            CodeChunk(
                chunk_id="1",
                content="def authenticate_user(username, password):\n    return verify(username, password)",
                file_path="auth.py",
                start_line=1,
                end_line=2,
                language="py"
            ),
            CodeChunk(
                chunk_id="2",
                content="def process_data(data):\n    return transform(data)",
                file_path="process.py",
                start_line=1,
                end_line=2,
                language="py"
            )
        ]

        results = KeywordRetriever.search("authentication", chunks, k=5)

        assert len(results) > 0
        assert results[0].chunk.chunk_id == "1"
        assert results[0].relevance_score > results[1].relevance_score


class TestASTAnalyzer:
    """Test AST analysis."""

    def test_python_ast_analysis(self):
        """Test Python AST parsing."""
        analyzer = ASTAnalyzer()

        code = '''
def fibonacci(n):
    """Calculate fibonacci number."""
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

class DataProcessor:
    def __init__(self):
        self.data = []
    
    def process(self):
        pass
'''

        path = Path("test.py")
        nodes = analyzer.parse_python_file(path, code)

        assert len(nodes) > 0
        # Should find at least function and class
        node_types = [n.node_type for n in nodes]
        assert "FunctionDef" in node_types or "ClassDef" in node_types


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
