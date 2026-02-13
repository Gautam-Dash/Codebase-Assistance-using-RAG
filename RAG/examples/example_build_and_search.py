"""Example: Building and searching a repository."""
from pathlib import Path
from src.rag_system import RAGSystem
from src.utils.logger import logger


def example_build_and_search():
    """Example of building index and searching."""
    logger.info("=" * 80)
    logger.info("RAG System - Build and Search Example")
    logger.info("=" * 80)

    # Initialize RAG system
    rag = RAGSystem()

    # Build index
    logger.info("\n1. Building index from repository...")
    try:
        chunks = rag.ingest_repository()
        logger.info(f"✓ Built index with {len(chunks)} chunks")
    except Exception as e:
        logger.error(f"Failed to build index: {e}")
        return

    # Perform searches
    queries = [
        "authentication and authorization",
        "error handling and exceptions",
        "database queries",
        "API endpoints",
        "logging and monitoring"
    ]

    logger.info("\n2. Performing searches...")
    for query in queries:
        logger.info(f"\n  Query: {query}")
        try:
            results = rag.search(
                query,
                expand_query=True,
                include_context=True,
                top_k=3
            )

            if results:
                logger.info(f"  Found {len(results)} results")
                for i, result in enumerate(results, 1):
                    chunk = result.ranked_result.result.chunk
                    score = result.ranked_result.final_score
                    logger.info(f"    [{i}] {chunk.file_path} (score: {score:.3f})")
            else:
                logger.info("  No results found")
        except Exception as e:
            logger.error(f"  Search failed: {e}")

    # Get system info
    logger.info("\n3. System Information")
    info = rag.get_system_info()
    for key, value in info.items():
        logger.info(f"  {key}: {value}")

    logger.info("\n" + "=" * 80)
    logger.info("Example completed!")
    logger.info("=" * 80)


if __name__ == "__main__":
    example_build_and_search()
