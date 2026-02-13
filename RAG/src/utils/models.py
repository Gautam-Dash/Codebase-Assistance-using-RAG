"""Data models for the RAG system."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any


@dataclass
class CodeChunk:
    """Represents a chunk of code with metadata."""

    chunk_id: str
    content: str
    file_path: str
    start_line: int
    end_line: int
    language: str
    ast_node_type: Optional[str] = None
    function_name: Optional[str] = None
    class_name: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    def __hash__(self):
        return hash(self.chunk_id)


@dataclass
class RetrievalResult:
    """Represents a retrieved code chunk with relevance score."""

    chunk: CodeChunk
    relevance_score: float
    retrieval_type: str = "semantic"  # semantic, keyword, hybrid


@dataclass
class RankedResult:
    """Represents a re-ranked retrieval result."""

    result: RetrievalResult
    reranker_score: float
    final_score: float


@dataclass
class CommitContext:
    """Represents commit context for a code chunk."""

    commit_hash: str
    author: str
    date: datetime
    message: str
    changed_files: List[str] = field(default_factory=list)
    insertions: int = 0
    deletions: int = 0


@dataclass
class ContextualResult:
    """Represents a result with full context."""

    ranked_result: RankedResult
    commit_context: Optional[CommitContext] = None
    related_chunks: List[RetrievalResult] = field(default_factory=list)
    expanded_queries: List[str] = field(default_factory=list)


@dataclass
class QueryExpansionResult:
    """Represents expanded queries from the original query."""

    original_query: str
    expanded_queries: List[str]
    expansion_rationale: str
