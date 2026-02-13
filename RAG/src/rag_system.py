"""Main RAG coordinator class."""
from pathlib import Path
from typing import List, Optional

from src.ingestion.code_ingestion import RepositoryIngester
from src.retrieval.semantic_retriever import SemanticRetriever
from src.ranking.cross_encoder import CrossEncoderReranker
from src.context.git_context import GitContextManager, ContextualRetriever
from src.query_expansion.llm_expander import QueryExpander
from src.config import settings
from src.utils.models import CodeChunk, ContextualResult
from src.utils.logger import logger


class RAGSystem:
    """Main RAG system coordinator."""

    def __init__(self, llm_client=None):
        """
        Initialize RAG system.

        Args:
            llm_client: Optional LLM client for query expansion
        """
        self.ingester = RepositoryIngester(
            settings.repo_path,
            chunk_size=settings.chunk_size,
            overlap=settings.chunk_overlap
        )

        self.retriever = SemanticRetriever(
            model_name=settings.embedding_model,
            index_path=settings.faiss_index_path
        )

        self.reranker = CrossEncoderReranker(
            model_name=settings.reranker_model
        )

        self.git_context = GitContextManager(settings.repo_path)
        self.contextual_retriever = ContextualRetriever(self.git_context)

        self.query_expander = None
        if llm_client:
            self.query_expander = QueryExpander(llm_client)

    def ingest_repository(self) -> List[CodeChunk]:
        """
        Ingest repository and build FAISS index.

        Returns:
            List of ingested code chunks
        """
        logger.info(f"Starting repository ingestion from {settings.repo_path}")

        chunks = self.ingester.ingest_repository(
            include_extensions=settings.included_extensions,
            exclude_patterns=settings.excluded_patterns_list
        )

        logger.info(f"Ingested {len(chunks)} chunks")

        # Build and save index
        logger.info("Building FAISS index...")
        self.retriever.build_index(chunks, batch_size=settings.batch_size)
        self.retriever.save_index()

        logger.info(f"Index saved to {settings.faiss_index_path}")
        return chunks

    def search(
        self,
        query: str,
        expand_query: bool = True,
        include_context: bool = True,
        top_k: Optional[int] = None
    ) -> List[ContextualResult]:
        """
        Search the codebase with full RAG pipeline.

        Args:
            query: Search query
            expand_query: Whether to use query expansion
            include_context: Whether to include git context
            top_k: Number of results (uses settings.top_k_ranking if None)

        Returns:
            List of contextual results
        """
        top_k = top_k or settings.top_k_ranking

        # Step 1: Query expansion (optional)
        queries = [query]
        if expand_query and self.query_expander:
            try:
                expansion_result = self.query_expander.expand_query(query)
                queries.extend(expansion_result.expanded_queries)
                logger.info(f"Expanded query to {len(queries)} total queries")
            except Exception as e:
                logger.warning(f"Query expansion failed: {e}")

        # Step 2: Semantic retrieval
        all_results = []
        for q in queries:
            results = self.retriever.search(q, k=settings.top_k_retrieval)
            all_results.extend(results)
            logger.info(f"Retrieved {len(results)} results for: {q}")

        # Deduplicate by chunk ID
        seen = set()
        unique_results = []
        for result in all_results:
            if result.chunk.chunk_id not in seen:
                seen.add(result.chunk.chunk_id)
                unique_results.append(result)

        logger.info(f"After deduplication: {len(unique_results)} results")

        # Step 3: Cross-encoder re-ranking
        ranked_results = self.reranker.rerank(
            query,
            unique_results,
            top_k=settings.top_k_ranking,
            threshold=settings.reranker_threshold
        )

        logger.info(f"After re-ranking: {len(ranked_results)} results")

        # Step 4: Add contextual information
        if include_context:
            contextual_results = self.contextual_retriever.enrich_results(
                ranked_results,
                include_history=True,
                include_related=True
            )
        else:
            contextual_results = [
                ContextualResult(ranked_result=r) for r in ranked_results
            ]

        return contextual_results

    def load_existing_index(self) -> None:
        """Load existing FAISS index."""
        logger.info(f"Loading index from {settings.faiss_index_path}")
        self.retriever.load_index(settings.faiss_index_path)
        logger.info("Index loaded successfully")

    def update_index(self, new_files: List[Path]) -> None:
        """
        Update index with new files.

        Args:
            new_files: List of new file paths to index
        """
        new_chunks = []
        for file_path in new_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    chunks = self.ingester.chunker.chunk_file(
                        file_path,
                        content,
                        file_path.suffix[1:]
                    )
                    new_chunks.extend(chunks)
            except Exception as e:
                logger.warning(f"Failed to process {file_path}: {e}")

        if new_chunks:
            self.retriever.update_index(new_chunks)
            self.retriever.save_index()
            logger.info(f"Updated index with {len(new_chunks)} new chunks")

    def get_system_info(self) -> dict:
        """Get current system information."""
        return {
            "index_loaded": self.retriever.is_built,
            "index_size": len(self.retriever.chunk_map),
            "repo_path": str(settings.repo_path),
            "embedding_model": settings.embedding_model,
            "reranker_model": settings.reranker_model,
            "git_repo_available": self.git_context.repo is not None
        }
