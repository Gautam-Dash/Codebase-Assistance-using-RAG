"""Cross-encoder based re-ranking module for improved result quality."""
from typing import List, Tuple
import numpy as np
from sentence_transformers import CrossEncoder

from src.utils.models import RetrievalResult, RankedResult
from src.utils.logger import logger


class CrossEncoderReranker:
    """Re-ranks retrieval results using cross-encoder models."""

    def __init__(
        self,
        model_name: str = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1",
        batch_size: int = 32
    ):
        """
        Initialize cross-encoder reranker.

        Args:
            model_name: HuggingFace cross-encoder model name
            batch_size: Batch size for scoring
        """
        self.model_name = model_name
        self.batch_size = batch_size
        self.model = CrossEncoder(model_name)
        logger.info(f"Loaded cross-encoder model: {model_name}")

    def rerank(
        self,
        query: str,
        results: List[RetrievalResult],
        top_k: int = 5,
        threshold: float = 0.0
    ) -> List[RankedResult]:
        """
        Re-rank retrieval results using cross-encoder.

        Args:
            query: Search query
            results: Initial retrieval results
            top_k: Number of top results to return
            threshold: Minimum score threshold

        Returns:
            Re-ranked results
        """
        if not results:
            return []

        # Prepare pairs for cross-encoder
        pairs = [
            [query, result.chunk.content[:512]]  # Use first 512 chars
            for result in results
        ]

        # Score in batches
        scores = []
        for i in range(0, len(pairs), self.batch_size):
            batch = pairs[i:i + self.batch_size]
            batch_scores = self.model.predict(batch)
            scores.extend(batch_scores)

        # Combine with original results
        ranked_pairs = [
            (result, score) for result, score in zip(results, scores)
        ]

        # Sort by cross-encoder score
        ranked_pairs.sort(key=lambda x: x[1], reverse=True)

        # Filter by threshold and top_k
        ranked_results = []
        for result, ce_score in ranked_pairs:
            if ce_score < threshold:
                break

            # Calculate final score as weighted combination
            final_score = 0.7 * ce_score + 0.3 * result.relevance_score

            ranked_results.append(
                RankedResult(
                    result=result,
                    reranker_score=float(ce_score),
                    final_score=float(final_score)
                )
            )

            if len(ranked_results) >= top_k:
                break

        return ranked_results

    def batch_rerank(
        self,
        query: str,
        result_batches: List[List[RetrievalResult]],
        top_k: int = 5
    ) -> List[RankedResult]:
        """
        Re-rank multiple batches of results.

        Args:
            query: Search query
            result_batches: Multiple batches of retrieval results
            top_k: Number of top results to return

        Returns:
            Combined re-ranked results
        """
        all_results = []
        for batch in result_batches:
            all_results.extend(batch)

        return self.rerank(query, all_results, top_k)

    def diversify_results(
        self,
        ranked_results: List[RankedResult],
        max_from_file: int = 2
    ) -> List[RankedResult]:
        """
        Diversify results to avoid redundancy from same file.

        Args:
            ranked_results: Re-ranked results
            max_from_file: Maximum results from same file

        Returns:
            Diversified results
        """
        file_count = {}
        diversified = []

        for ranked_result in ranked_results:
            file_path = ranked_result.result.chunk.file_path
            file_count[file_path] = file_count.get(file_path, 0) + 1

            if file_count[file_path] <= max_from_file:
                diversified.append(ranked_result)

        return diversified

    def score_relevance(
        self,
        query: str,
        text: str,
        return_raw: bool = False
    ) -> float | Tuple[float, np.ndarray]:
        """
        Score relevance of text to query.

        Args:
            query: Query text
            text: Text to score
            return_raw: Whether to return raw scores

        Returns:
            Relevance score (0-1 range typically), optionally with raw scores
        """
        pair = [[query, text]]
        scores = self.model.predict(pair)

        # Normalize to 0-1 range
        score = float(scores[0])

        if return_raw:
            return score, scores
        return score

    def explain_ranking(
        self,
        query: str,
        text: str
    ) -> dict:
        """
        Explain why text was ranked for this query.

        Args:
            query: Query text
            text: Text being ranked

        Returns:
            Dictionary with ranking explanation
        """
        score = self.score_relevance(query, text)

        # Simple heuristic-based explanation
        query_terms = set(query.lower().split())
        text_lower = text.lower()

        matched_terms = [term for term in query_terms if term in text_lower]
        coverage = len(matched_terms) / len(query_terms) if query_terms else 0

        return {
            "score": score,
            "term_coverage": coverage,
            "matched_terms": matched_terms,
            "explanation": self._generate_explanation(score, coverage, matched_terms)
        }

    @staticmethod
    def _generate_explanation(score: float, coverage: float, matched_terms: List[str]) -> str:
        """Generate human-readable ranking explanation."""
        if score < 0.3:
            return "Low relevance - minimal match to query terms"
        elif score < 0.6:
            reason = f"Moderate relevance - matched {len(matched_terms)} query terms"
        else:
            reason = f"High relevance - matched {len(matched_terms)} query terms comprehensively"

        return reason


class EnsembleReranker:
    """Combines multiple re-ranking strategies."""

    def __init__(self, cross_encoder_model: str = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"):
        """Initialize ensemble reranker."""
        self.ce_reranker = CrossEncoderReranker(cross_encoder_model)

    def rerank_ensemble(
        self,
        query: str,
        results: List[RetrievalResult],
        top_k: int = 5,
        weights: dict = None
    ) -> List[RankedResult]:
        """
        Re-rank using ensemble of strategies.

        Args:
            query: Search query
            results: Initial results
            top_k: Number of results to return
            weights: Weighting for different strategies

        Returns:
            Ensemble re-ranked results
        """
        if weights is None:
            weights = {
                "cross_encoder": 0.6,
                "semantic": 0.3,
                "metadata": 0.1
            }

        # Get cross-encoder scores
        ce_results = self.ce_reranker.rerank(query, results, top_k * 2)

        # Calculate ensemble scores
        ensemble_results = []
        for ranked_result in ce_results:
            final_score = (
                weights["cross_encoder"] * ranked_result.reranker_score +
                weights["semantic"] * ranked_result.result.relevance_score
            )

            # Bonus for metadata matches
            metadata_bonus = 0.0
            if ranked_result.result.chunk.metadata:
                metadata_bonus = weights["metadata"]

            final_score += metadata_bonus

            ranked_result.final_score = final_score
            ensemble_results.append(ranked_result)

        # Sort by final score
        ensemble_results.sort(key=lambda x: x.final_score, reverse=True)

        return ensemble_results[:top_k]
