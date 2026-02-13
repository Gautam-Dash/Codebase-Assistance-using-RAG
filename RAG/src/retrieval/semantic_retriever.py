"""FAISS-based semantic retrieval module."""
from typing import List, Optional, Tuple
from pathlib import Path
import pickle
import numpy as np

import faiss
from sentence_transformers import SentenceTransformer

from src.utils.models import CodeChunk, RetrievalResult
from src.utils.logger import logger


class SemanticRetriever:
    """Semantic retrieval using FAISS and sentence transformers."""

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        index_path: Optional[Path] = None
    ):
        """
        Initialize the semantic retriever.

        Args:
            model_name: HuggingFace model name for embeddings
            index_path: Path to save/load FAISS index
        """
        self.model_name = model_name
        self.index_path = index_path
        self.embedding_model = SentenceTransformer(model_name)
        self.embedding_dim = self.embedding_model.get_sentence_embedding_dimension()

        self.faiss_index: Optional[faiss.IndexFlatL2] = None
        self.chunk_map: List[CodeChunk] = []
        self.is_built = False

    def build_index(self, chunks: List[CodeChunk], batch_size: int = 32) -> None:
        """
        Build FAISS index from code chunks.

        Args:
            chunks: List of code chunks
            batch_size: Batch size for embedding computation
        """
        logger.info(f"Building FAISS index for {len(chunks)} chunks...")

        # Prepare texts for embedding
        texts = [chunk.content for chunk in chunks]

        # Compute embeddings in batches
        embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_embeddings = self.embedding_model.encode(
                batch,
                show_progress_bar=True,
                convert_to_numpy=True
            )
            embeddings.append(batch_embeddings)

        embeddings_array = np.vstack(embeddings)

        # Create and populate FAISS index
        self.faiss_index = faiss.IndexFlatL2(self.embedding_dim)
        self.faiss_index.add(embeddings_array.astype(np.float32))

        self.chunk_map = chunks
        self.is_built = True

        logger.info(f"FAISS index built successfully with {len(chunks)} chunks")

    def search(
        self,
        query: str,
        k: int = 10,
        return_scores: bool = False
    ) -> List[RetrievalResult] | Tuple[List[RetrievalResult], np.ndarray]:
        """
        Search for similar chunks using semantic similarity.

        Args:
            query: Search query
            k: Number of results to return
            return_scores: Whether to return distance scores

        Returns:
            List of retrieval results, optionally with scores
        """
        if not self.is_built:
            logger.warning("FAISS index not built. Building from empty chunks...")
            self.build_index([])
            return []

        # Encode query
        query_embedding = self.embedding_model.encode(
            [query],
            convert_to_numpy=True
        )[0]

        # Search
        distances, indices = self.faiss_index.search(
            np.array([query_embedding], dtype=np.float32),
            k
        )

        # Convert distances to similarity scores (L2 distance to similarity)
        scores = 1 / (1 + distances[0])

        results = []
        for idx, score in zip(indices[0], scores):
            if idx < 0 or idx >= len(self.chunk_map):
                continue

            chunk = self.chunk_map[int(idx)]
            result = RetrievalResult(
                chunk=chunk,
                relevance_score=float(score),
                retrieval_type="semantic"
            )
            results.append(result)

        if return_scores:
            return results, distances[0]
        return results

    def save_index(self, path: Optional[Path] = None) -> None:
        """
        Save FAISS index and chunk map to disk.

        Args:
            path: Path to save index (uses self.index_path if not provided)
        """
        save_path = path or self.index_path
        if not save_path:
            logger.warning("No index path specified for saving")
            return

        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)

        # Save FAISS index
        faiss.write_index(self.faiss_index, str(save_path / "index.faiss"))

        # Save chunk map
        with open(save_path / "chunks.pkl", "wb") as f:
            pickle.dump(self.chunk_map, f)

        logger.info(f"Index saved to {save_path}")

    def load_index(self, path: Optional[Path] = None) -> None:
        """
        Load FAISS index and chunk map from disk.

        Args:
            path: Path to load index from (uses self.index_path if not provided)
        """
        load_path = path or self.index_path
        if not load_path:
            logger.warning("No index path specified for loading")
            return

        load_path = Path(load_path)
        if not load_path.exists():
            logger.warning(f"Index path does not exist: {load_path}")
            return

        # Load FAISS index
        self.faiss_index = faiss.read_index(str(load_path / "index.faiss"))

        # Load chunk map
        with open(load_path / "chunks.pkl", "rb") as f:
            self.chunk_map = pickle.load(f)

        self.is_built = True
        logger.info(f"Index loaded from {load_path}")

    def update_index(self, new_chunks: List[CodeChunk]) -> None:
        """
        Add new chunks to existing index.

        Args:
            new_chunks: New chunks to add
        """
        if not self.is_built:
            self.build_index(new_chunks)
            return

        logger.info(f"Adding {len(new_chunks)} new chunks to index...")

        # Encode new chunks
        texts = [chunk.content for chunk in new_chunks]
        embeddings = self.embedding_model.encode(
            texts,
            show_progress_bar=True,
            convert_to_numpy=True
        )

        # Add to FAISS index
        self.faiss_index.add(embeddings.astype(np.float32))
        self.chunk_map.extend(new_chunks)

        logger.info(f"Index now contains {len(self.chunk_map)} chunks")


class KeywordRetriever:
    """Simple keyword-based retrieval for comparison/hybrid approaches."""

    @staticmethod
    def search(
        query: str,
        chunks: List[CodeChunk],
        k: int = 10
    ) -> List[RetrievalResult]:
        """
        Search for chunks using keyword matching.

        Args:
            query: Search query
            chunks: Chunks to search
            k: Number of results to return

        Returns:
            List of retrieval results sorted by relevance
        """
        query_terms = query.lower().split()
        results = []

        for chunk in chunks:
            score = 0.0
            content_lower = chunk.content.lower()

            # Score based on term frequency
            for term in query_terms:
                score += content_lower.count(term)

            # Boost score for matching function/class names
            if chunk.function_name and any(
                term in chunk.function_name.lower() for term in query_terms
            ):
                score += 5.0
            if chunk.class_name and any(
                term in chunk.class_name.lower() for term in query_terms
            ):
                score += 5.0

            if score > 0:
                results.append(
                    RetrievalResult(
                        chunk=chunk,
                        relevance_score=score,
                        retrieval_type="keyword"
                    )
                )

        # Sort by score and return top k
        results.sort(key=lambda x: x.relevance_score, reverse=True)
        return results[:k]
