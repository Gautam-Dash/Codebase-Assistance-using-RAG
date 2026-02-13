"""Example: Advanced search with different strategies."""
from pathlib import Path
from src.rag_system import RAGSystem
from src.retrieval.semantic_retriever import KeywordRetriever
from src.context.git_context import GitContextManager
from src.utils.logger import logger


def example_advanced_search():
    """Example of advanced search capabilities."""
    logger.info("=" * 80)
    logger.info("RAG System - Advanced Search Example")
    logger.info("=" * 80)

    rag = RAGSystem()

    # Load existing index
    logger.info("\n1. Loading existing index...")
    try:
        rag.load_existing_index()
        logger.info("✓ Index loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load index: {e}")
        return

    # Example 1: Basic semantic search
    logger.info("\n2. Semantic Search Example")
    query = "user authentication middleware"
    logger.info(f"Query: {query}")

    results = rag.retriever.search(query, k=5)
    for i, result in enumerate(results, 1):
        logger.info(
            f"  [{i}] {result.chunk.file_path} "
            f"(score: {result.relevance_score:.3f})"
        )

    # Example 2: Re-ranking results
    logger.info("\n3. Cross-Encoder Re-ranking Example")
    ranked_results = rag.reranker.rerank(query, results, top_k=3)
    for i, ranked in enumerate(ranked_results, 1):
        logger.info(
            f"  [{i}] {ranked.result.chunk.file_path} "
            f"(CE: {ranked.reranker_score:.3f}, "
            f"Final: {ranked.final_score:.3f})"
        )

    # Example 3: Git context enrichment
    logger.info("\n4. Git Context Example")
    if ranked_results:
        chunk = ranked_results[0].result.chunk
        commits = rag.git_context.get_file_commits(chunk.file_path, limit=3)

        if commits:
            logger.info(f"Recent commits for {chunk.file_path}:")
            for commit in commits:
                logger.info(f"  - {commit.commit_hash} by {commit.author}")
                logger.info(f"    {commit.message[:60]}...")
        else:
            logger.info("No git history available")

    # Example 4: Keyword search comparison
    logger.info("\n5. Keyword Search Comparison")
    if rag.retriever.is_built and rag.retriever.chunk_map:
        keyword_results = KeywordRetriever.search(
            query,
            rag.retriever.chunk_map,
            k=5
        )
        logger.info("Top keyword matches:")
        for i, result in enumerate(keyword_results, 1):
            logger.info(
                f"  [{i}] {result.chunk.file_path} "
                f"(score: {result.relevance_score:.1f})"
            )

    logger.info("\n" + "=" * 80)
    logger.info("Advanced search example completed!")
    logger.info("=" * 80)


if __name__ == "__main__":
    example_advanced_search()
