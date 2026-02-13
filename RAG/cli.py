"""Command-line interface for RAG system."""
import argparse
import json
from pathlib import Path
from typing import Optional

from src.rag_system import RAGSystem
from src.config import settings
from src.utils.logger import logger


def init_command(args):
    """Initialize and build the index from repository."""
    logger.info("Initializing RAG system...")

    repo_path = Path(args.repo_path) if args.repo_path else settings.repo_path
    if not repo_path.exists():
        logger.error(f"Repository path does not exist: {repo_path}")
        return

    rag = RAGSystem()
    chunks = rag.ingest_repository()

    logger.info(f"✓ Successfully ingested {len(chunks)} code chunks")
    logger.info(f"✓ Index saved to {settings.faiss_index_path}")

    # Print statistics
    language_stats = {}
    for chunk in chunks:
        lang = chunk.language
        language_stats[lang] = language_stats.get(lang, 0) + 1

    print("\nIngestion Summary:")
    print(f"  Total chunks: {len(chunks)}")
    print(f"  Languages: {language_stats}")
    print(f"  Index path: {settings.faiss_index_path}")


def search_command(args):
    """Search the indexed codebase."""
    query = args.query
    top_k = args.top_k or settings.top_k_ranking

    logger.info(f"Searching for: {query}")

    rag = RAGSystem()
    try:
        rag.load_existing_index()
    except Exception as e:
        logger.error(f"Failed to load index: {e}")
        return

    results = rag.search(
        query,
        expand_query=not args.no_expansion,
        include_context=not args.no_context,
        top_k=top_k
    )

    if not results:
        print("No results found.")
        return

    print(f"\n{'='*80}")
    print(f"Found {len(results)} relevant code chunks for: {query}")
    print(f"{'='*80}\n")

    for i, result in enumerate(results, 1):
        chunk = result.ranked_result.result.chunk
        score = result.ranked_result.final_score

        print(f"\n[{i}] {chunk.file_path} (Score: {score:.3f})")
        print(f"    Lines: {chunk.start_line}-{chunk.end_line}")

        if chunk.function_name:
            print(f"    Function: {chunk.function_name}")
        if chunk.class_name:
            print(f"    Class: {chunk.class_name}")

        print("\n    Code Preview:")
        preview = chunk.content[:300]
        for line in preview.split("\n"):
            print(f"      {line}")

        if result.commit_context:
            print(f"\n    Last Modified:")
            print(f"      {result.commit_context.author}")
            print(f"      {result.commit_context.date}")
            print(f"      {result.commit_context.message[:80]}...")

        print("\n" + "-"*80)


def status_command(args):
    """Show RAG system status."""
    rag = RAGSystem()
    try:
        rag.load_existing_index()
    except Exception as e:
        logger.warning(f"Could not load index: {e}")

    info = rag.get_system_info()

    print("\nRAG System Status:")
    print(f"  Repository: {info['repo_path']}")
    print(f"  Index loaded: {'Yes' if info['index_loaded'] else 'No'}")
    print(f"  Chunks indexed: {info['index_size']}")
    print(f"  Embedding model: {info['embedding_model']}")
    print(f"  Reranker model: {info['reranker_model']}")
    print(f"  Git context: {'Available' if info['git_repo_available'] else 'Not available'}")
    print(f"  Index path: {settings.faiss_index_path}")


def config_command(args):
    """Show or update configuration."""
    if args.list:
        print("\nCurrent Configuration:")
        print(json.dumps({
            "openai_api_key": "***" if settings.openai_api_key else "not set",
            "llm_model": settings.llm_model,
            "embedding_model": settings.embedding_model,
            "faiss_index_path": str(settings.faiss_index_path),
            "chunk_size": settings.chunk_size,
            "chunk_overlap": settings.chunk_overlap,
            "top_k_retrieval": settings.top_k_retrieval,
            "top_k_ranking": settings.top_k_ranking,
            "reranker_model": settings.reranker_model,
            "repo_path": str(settings.repo_path),
            "included_extensions": settings.included_extensions,
            "excluded_patterns": settings.excluded_patterns_list
        }, indent=2))


def interactive_search(rag: RAGSystem):
    """Interactive search mode."""
    print("\n" + "="*80)
    print("RAG System - Interactive Search")
    print("Type 'quit' or 'exit' to exit, 'help' for commands")
    print("="*80 + "\n")

    while True:
        try:
            query = input(">>> ")

            if query.lower() in ["quit", "exit"]:
                break

            if query.lower() == "help":
                print("""
                Commands:
                  help     - Show this help message
                  status   - Show system status
                  quit     - Exit interactive mode
                  
                Otherwise, enter a search query.
                """)
                continue

            if query.lower() == "status":
                info = rag.get_system_info()
                print(f"Index loaded: {info['index_loaded']}")
                print(f"Chunks: {info['index_size']}")
                continue

            if not query.strip():
                continue

            results = rag.search(query, top_k=5)

            if not results:
                print("No results found.")
            else:
                print(f"\nFound {len(results)} results:\n")
                for i, result in enumerate(results, 1):
                    chunk = result.ranked_result.result.chunk
                    score = result.ranked_result.final_score
                    print(f"{i}. {chunk.file_path} (score: {score:.3f})")

        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            logger.error(f"Error: {e}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Codebase RAG System - Production-grade semantic search"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Init command
    init_parser = subparsers.add_parser(
        "init",
        help="Initialize and build the FAISS index from repository"
    )
    init_parser.add_argument(
        "--repo-path",
        help="Path to repository (uses config if not specified)"
    )
    init_parser.set_defaults(func=init_command)

    # Search command
    search_parser = subparsers.add_parser(
        "search",
        help="Search the indexed codebase"
    )
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument(
        "-k", "--top-k",
        type=int,
        help="Number of results to return"
    )
    search_parser.add_argument(
        "--no-expansion",
        action="store_true",
        help="Disable query expansion"
    )
    search_parser.add_argument(
        "--no-context",
        action="store_true",
        help="Disable git context enrichment"
    )
    search_parser.set_defaults(func=search_command)

    # Status command
    status_parser = subparsers.add_parser(
        "status",
        help="Show RAG system status"
    )
    status_parser.set_defaults(func=status_command)

    # Config command
    config_parser = subparsers.add_parser(
        "config",
        help="Show configuration"
    )
    config_parser.add_argument(
        "-l", "--list",
        action="store_true",
        help="List all configuration values"
    )
    config_parser.set_defaults(func=config_command)

    # Interactive command
    interactive_parser = subparsers.add_parser(
        "interactive",
        help="Start interactive search mode"
    )

    def interactive_command(args):
        rag = RAGSystem()
        try:
            rag.load_existing_index()
        except Exception as e:
            logger.error(f"Failed to load index: {e}")
            return
        interactive_search(rag)

    interactive_parser.set_defaults(func=interactive_command)

    # Parse and execute
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    args.func(args)


if __name__ == "__main__":
    main()
