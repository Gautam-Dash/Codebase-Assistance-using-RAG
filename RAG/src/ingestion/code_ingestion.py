"""AST-aware code ingestion module for parsing and extracting code structure."""
import ast
import re
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass

from src.utils.models import CodeChunk
from src.utils.logger import logger


@dataclass
class ASTNode:
    """Represents an AST node with metadata."""

    node_type: str
    name: Optional[str]
    start_line: int
    end_line: int
    parent_name: Optional[str] = None
    doc_string: Optional[str] = None


class ASTAnalyzer:
    """Analyzes Python code using AST to extract code structure."""

    def __init__(self):
        self.current_class: Optional[str] = None
        self.current_function: Optional[str] = None

    def parse_python_file(self, file_path: Path, content: str) -> List[ASTNode]:
        """
        Parse a Python file and extract AST nodes.

        Args:
            file_path: Path to the Python file
            content: File content

        Returns:
            List of AST nodes found in the file
        """
        nodes = []
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                    ast_node = self._extract_node_info(node)
                    nodes.append(ast_node)
        except SyntaxError as e:
            logger.warning(f"Failed to parse {file_path}: {e}")
        return nodes

    def _extract_node_info(self, node: ast.AST) -> ASTNode:
        """Extract information from an AST node."""
        doc_string = None
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            doc_string = ast.get_docstring(node)

        return ASTNode(
            node_type=node.__class__.__name__,
            name=getattr(node, "name", None),
            start_line=getattr(node, "lineno", 0),
            end_line=getattr(node, "end_lineno", 0),
            doc_string=doc_string
        )


class LanguageAnalyzer:
    """Factory for language-specific analyzers."""

    def __init__(self):
        self.python_analyzer = ASTAnalyzer()

    def analyze_file(self, file_path: Path, content: str) -> List[ASTNode]:
        """
        Analyze a file based on its extension.

        Args:
            file_path: Path to the file
            content: File content

        Returns:
            List of AST nodes extracted from the file
        """
        suffix = file_path.suffix.lower()

        if suffix == ".py":
            return self.python_analyzer.parse_python_file(file_path, content)
        else:
            # For non-Python files, return simple line-based extraction
            return self._extract_functions_by_pattern(content, suffix)

    def _extract_functions_by_pattern(
        self,
        content: str,
        language: str
    ) -> List[ASTNode]:
        """Extract function-like structures using regex patterns."""
        nodes = []
        lines = content.split("\n")

        # Language-specific patterns
        patterns = {
            ".js": r"^\s*(async\s+)?function\s+(\w+)",
            ".ts": r"^\s*(async\s+)?(function|class)\s+(\w+)",
            ".java": r"^\s*(public|private|protected)?\s*(static)?\s*(class|interface|enum)\s+(\w+)",
            ".cpp": r"^\s*(\w+\s+)?(\w+)\s*\(",
            ".go": r"^func\s+(\w+)",
            ".rb": r"^\s*def\s+(\w+)",
        }

        pattern = patterns.get(language, r"^\s*def\s+(\w+)")

        for i, line in enumerate(lines, 1):
            match = re.match(pattern, line)
            if match:
                function_name = match.group(2) if len(match.groups()) > 1 else match.group(1)
                nodes.append(
                    ASTNode(
                        node_type="Function",
                        name=function_name,
                        start_line=i,
                        end_line=min(i + 50, len(lines))
                    )
                )

        return nodes


class CodeChunker:
    """Chunks code into logical units based on AST structure."""

    def __init__(self, chunk_size: int = 512, overlap: int = 50):
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.analyzer = LanguageAnalyzer()

    def chunk_file(
        self,
        file_path: Path,
        content: str,
        language: str
    ) -> List[CodeChunk]:
        """
        Chunk a code file into semantic units.

        Args:
            file_path: Path to the file
            content: File content
            language: Programming language

        Returns:
            List of code chunks
        """
        chunks = []
        chunk_id_counter = 0

        lines = content.split("\n")
        ast_nodes = self.analyzer.analyze_file(file_path, content)

        # Create chunks based on AST nodes when available
        if ast_nodes:
            for node in ast_nodes:
                if node.start_line > 0 and node.end_line > 0:
                    chunk_content = "\n".join(
                        lines[node.start_line - 1:node.end_line]
                    )

                    chunk = CodeChunk(
                        chunk_id=f"{file_path}_{chunk_id_counter}",
                        content=chunk_content,
                        file_path=str(file_path),
                        start_line=node.start_line,
                        end_line=node.end_line,
                        language=language,
                        ast_node_type=node.node_type,
                        function_name=node.name if node.node_type in ["FunctionDef", "AsyncFunctionDef"] else None,
                        class_name=node.name if node.node_type == "ClassDef" else None,
                        metadata={
                            "doc_string": node.doc_string,
                            "complexity": self._estimate_complexity(chunk_content)
                        }
                    )
                    chunks.append(chunk)
                    chunk_id_counter += 1
        else:
            # Fallback to sliding window chunking
            chunks = self._chunk_by_window(
                content,
                file_path,
                language,
                chunk_id_counter
            )

        return chunks

    def _chunk_by_window(
        self,
        content: str,
        file_path: Path,
        language: str,
        start_id: int = 0
    ) -> List[CodeChunk]:
        """Chunk content using a sliding window approach."""
        chunks = []
        words = content.split()

        for i in range(0, len(words), self.chunk_size - self.overlap):
            chunk_words = words[i:i + self.chunk_size]
            if not chunk_words:
                continue

            chunk_content = " ".join(chunk_words)
            chunk = CodeChunk(
                chunk_id=f"{file_path}_{start_id + i}",
                content=chunk_content,
                file_path=str(file_path),
                start_line=i // 50 + 1,  # Rough estimation
                end_line=(i + len(chunk_words)) // 50 + 1,
                language=language,
                metadata={"chunking_method": "sliding_window"}
            )
            chunks.append(chunk)

        return chunks

    @staticmethod
    def _estimate_complexity(code: str) -> int:
        """Estimate code complexity (simple heuristic)."""
        # Count control flow statements
        complexity = 1
        patterns = ["if ", "for ", "while ", "try:", "except", "elif "]
        for pattern in patterns:
            complexity += code.count(pattern)
        return min(complexity, 10)


class RepositoryIngester:
    """Ingests code from a repository and extracts chunks."""

    def __init__(self, repo_path: Path, chunk_size: int = 512, overlap: int = 50):
        self.repo_path = repo_path
        self.chunker = CodeChunker(chunk_size, overlap)
        self.supported_extensions = {
            ".py", ".js", ".ts", ".java", ".cpp", ".c", ".go", ".rs", ".rb", ".php"
        }

    def ingest_repository(
        self,
        include_extensions: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None
    ) -> List[CodeChunk]:
        """
        Ingest all code files from a repository.

        Args:
            include_extensions: List of file extensions to include
            exclude_patterns: List of patterns to exclude

        Returns:
            List of code chunks from the repository
        """
        if include_extensions:
            self.supported_extensions = set(include_extensions)

        exclude_patterns = exclude_patterns or []
        chunks = []

        for file_path in self.repo_path.rglob("*"):
            if self._should_skip_file(file_path, exclude_patterns):
                continue

            if file_path.suffix not in self.supported_extensions:
                continue

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    file_chunks = self.chunker.chunk_file(
                        file_path,
                        content,
                        file_path.suffix[1:]  # Remove the dot
                    )
                    chunks.extend(file_chunks)
                    logger.info(f"Processed {file_path}: {len(file_chunks)} chunks")
            except Exception as e:
                logger.warning(f"Failed to process {file_path}: {e}")

        logger.info(f"Total chunks extracted: {len(chunks)}")
        return chunks

    def _should_skip_file(self, file_path: Path, exclude_patterns: List[str]) -> bool:
        """Check if a file should be skipped based on exclusion patterns."""
        path_str = str(file_path).lower()
        for pattern in exclude_patterns:
            if pattern.lower() in path_str:
                return True
        return False
