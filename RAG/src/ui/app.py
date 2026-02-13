"""Streamlit UI for the RAG system."""
import os
import sys

# Ensure project root is on sys.path so `import src` works when running Streamlit
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import streamlit as st
from typing import List
import os
from dotenv import load_dotenv

from src.config import settings
from src.retrieval.semantic_retriever import SemanticRetriever
from src.ranking.cross_encoder import CrossEncoderReranker
from src.context.git_context import GitContextManager, ContextualRetriever
from src.utils.logger import logger

# Load environment variables
load_dotenv()

# Page config
st.set_page_config(
    page_title="Codebase RAG System",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .result-card {
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        background-color: #f9f9f9;
    }
    .score-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: bold;
    }
    .high-score {
        background-color: #d4edda;
        color: #155724;
    }
    .medium-score {
        background-color: #fff3cd;
        color: #856404;
    }
    .low-score {
        background-color: #f8d7da;
        color: #721c24;
    }
    </style>
""", unsafe_allow_html=True)

# Session state initialization
if "retriever" not in st.session_state:
    try:
        st.session_state.retriever = SemanticRetriever(
            model_name="all-MiniLM-L6-v2",
            index_path=settings.faiss_index_path
        )
        st.session_state.retriever.load_index()
        st.session_state.index_loaded = True
    except Exception as e:
        st.session_state.index_loaded = False
        st.session_state.error = str(e)

if "reranker" not in st.session_state:
    st.session_state.reranker = CrossEncoderReranker(
        model_name=settings.reranker_model
    )

if "git_context" not in st.session_state:
    st.session_state.git_context = GitContextManager(settings.repo_path)

# Header
col1, col2 = st.columns([3, 1])
with col1:
    st.markdown("<div class='main-header'>🔍 Codebase RAG System</div>", unsafe_allow_html=True)
    st.markdown("Semantic search for large codebases with intelligent ranking and context")

with col2:
    if st.session_state.index_loaded:
        st.success("✓ Index Loaded")
    else:
        st.error("✗ Index Not Loaded")

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")

    # Search parameters
    st.subheader("Search Parameters")
    top_k_retrieval = st.slider(
        "Top-K Retrieval",
        min_value=5,
        max_value=50,
        value=settings.top_k_retrieval,
        help="Number of initial semantic results"
    )

    top_k_ranking = st.slider(
        "Top-K Final Results",
        min_value=1,
        max_value=top_k_retrieval,
        value=settings.top_k_ranking,
        help="Number of final re-ranked results"
    )

    reranker_threshold = st.slider(
        "Re-ranker Threshold",
        min_value=0.0,
        max_value=1.0,
        value=settings.reranker_threshold,
        step=0.05,
        help="Minimum score for results"
    )

    # Options
    st.subheader("Options")
    show_scores = st.checkbox("Show Scores", value=True)
    show_metadata = st.checkbox("Show Metadata", value=True)
    show_commit_context = st.checkbox("Show Commit Context", value=True)

    # Index management
    st.subheader("Index Management")
    if st.button("🔄 Reload Index"):
        try:
            st.session_state.retriever.load_index()
            st.success("Index reloaded successfully")
        except Exception as e:
            st.error(f"Failed to reload index: {e}")

# Main content
if not st.session_state.index_loaded:
    st.error(
        "⚠️ FAISS index not loaded. Please build the index first using the CLI tools."
    )
    st.stop()

# Search input
st.header("Search Codebase")
query = st.text_input(
    "Enter your search query:",
    placeholder="e.g., 'authentication middleware' or 'error handling in API calls'",
    help="Describe what you're looking for in the codebase"
)

# Search columns
col1, col2, col3 = st.columns(3)
with col1:
    search_button = st.button("🔍 Search", use_container_width=True)
with col2:
    advanced = st.checkbox("Advanced Options", value=False)
with col3:
    clear_button = st.button("Clear Results", use_container_width=True)

# Advanced options
if advanced:
    with st.expander("Advanced Search Options"):
        search_type = st.radio(
            "Search Type",
            options=["Semantic", "Keyword", "Hybrid"],
            help="Type of search to perform"
        )

        expansion_enabled = st.checkbox(
            "Enable Query Expansion",
            value=True,
            help="Use LLM to expand query for better coverage"
        )

        diversify = st.checkbox(
            "Diversify Results",
            value=True,
            help="Avoid multiple results from same file"
        )

# Search results
if search_button and query:
    with st.spinner("Searching codebase..."):
        try:
            # Retrieve results
            results = st.session_state.retriever.search(
                query,
                k=top_k_retrieval,
                return_scores=True
            )

            if not results:
                st.warning("No results found. Try a different query.")
            else:
                # Re-rank results
                ranked_results = st.session_state.reranker.rerank(
                    query,
                    results[0],  # First element is results list
                    top_k=top_k_ranking,
                    threshold=reranker_threshold
                )

                if not ranked_results:
                    st.warning("No results met the score threshold.")
                else:
                    # Display results
                    st.success(f"Found {len(ranked_results)} relevant code chunks")

                    # Tabs for different views
                    tab1, tab2, tab3 = st.tabs(["Results", "Analysis", "Settings"])

                    with tab1:
                        for i, ranked_result in enumerate(ranked_results, 1):
                            chunk = ranked_result.result.chunk
                            scores = ranked_result

                            with st.container():
                                col1, col2 = st.columns([4, 1] if show_scores else [1, 0])

                                with col1:
                                    st.markdown(f"### Result {i}: {chunk.file_path}")

                                    # Score badges
                                    if show_scores:
                                        score_html = f"""
                                        <div>
                                            <span class="score-badge high-score">
                                                Cross-Encoder: {scores.reranker_score:.3f}
                                            </span>
                                            <span class="score-badge medium-score">
                                                Semantic: {scores.result.relevance_score:.3f}
                                            </span>
                                            <span class="score-badge high-score">
                                                Final: {scores.final_score:.3f}
                                            </span>
                                        </div>
                                        """
                                        st.markdown(score_html, unsafe_allow_html=True)

                                with col2:
                                    if show_scores:
                                        st.metric("Score", f"{scores.final_score:.2%}")

                                # Code content
                                st.markdown("**Code Preview:**")
                                st.code(chunk.content[:500], language=chunk.language)

                                # Metadata
                                if show_metadata:
                                    col1, col2, col3 = st.columns(3)
                                    with col1:
                                        st.metric("Lines", f"{chunk.start_line}-{chunk.end_line}")
                                    with col2:
                                        if chunk.function_name:
                                            st.metric("Function", chunk.function_name)
                                        elif chunk.class_name:
                                            st.metric("Class", chunk.class_name)
                                    with col3:
                                        st.metric("Type", chunk.ast_node_type or "Code")

                                # Commit context
                                if show_commit_context:
                                    commits = st.session_state.git_context.get_file_commits(
                                        chunk.file_path,
                                        limit=3
                                    )
                                    if commits:
                                        with st.expander("📝 Recent Commits"):
                                            for commit in commits:
                                                st.write(f"**{commit.commit_hash}** by {commit.author}")
                                                st.caption(commit.message)

                                st.divider()

                    with tab2:
                        st.subheader("Search Analysis")
                        col1, col2, col3 = st.columns(3)

                        with col1:
                            st.metric("Results Returned", len(ranked_results))
                        with col2:
                            avg_score = sum(r.final_score for r in ranked_results) / len(ranked_results)
                            st.metric("Average Score", f"{avg_score:.2%}")
                        with col3:
                            st.metric("Query Length", len(query.split()))

                        # Score distribution
                        st.subheader("Score Distribution")
                        scores = [r.final_score for r in ranked_results]
                        st.bar_chart({"Score": scores})

                    with tab3:
                        st.subheader("Current Settings")
                        st.json({
                            "top_k_retrieval": top_k_retrieval,
                            "top_k_ranking": top_k_ranking,
                            "reranker_threshold": reranker_threshold,
                            "index_path": str(settings.faiss_index_path)
                        })

        except Exception as e:
            st.error(f"Search failed: {e}")
            logger.error(f"Search error: {e}")

elif clear_button:
    st.rerun()

# Footer
st.divider()
st.markdown("""
    <div style='text-align: center; color: #888; font-size: 0.9rem;'>
    <p>Codebase RAG System | AST-aware ingestion • FAISS semantic search • Cross-encoder ranking</p>
    </div>
""", unsafe_allow_html=True)
