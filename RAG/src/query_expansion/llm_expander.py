"""LLM-driven query expansion module for improved retrieval."""
from typing import List
from src.utils.models import QueryExpansionResult
from src.utils.logger import logger


class QueryExpander:
    """Expands queries using LLM for improved retrieval coverage."""

    def __init__(self, llm_client):
        """
        Initialize query expander with LLM client.

        Args:
            llm_client: OpenAI or compatible LLM client
        """
        self.llm_client = llm_client

    def expand_query(
        self,
        query: str,
        expansion_count: int = 3,
        context: str = ""
    ) -> QueryExpansionResult:
        """
        Expand a query to multiple related queries using LLM.

        Args:
            query: Original search query
            expansion_count: Number of expanded queries to generate
            context: Optional context about the codebase

        Returns:
            QueryExpansionResult with expanded queries and rationale
        """
        prompt = self._build_expansion_prompt(query, expansion_count, context)

        try:
            response = self.llm_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert at understanding code search queries.
Your task is to expand a user's search query into multiple alternative queries that would
help find relevant code. Generate queries that explore different aspects and phrasings."""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=500
            )

            content = response.choices[0].message.content
            expanded_queries = self._parse_expanded_queries(content)

            return QueryExpansionResult(
                original_query=query,
                expanded_queries=expanded_queries[:expansion_count],
                expansion_rationale=content
            )

        except Exception as e:
            logger.error(f"Query expansion failed: {e}")
            # Return original query on failure
            return QueryExpansionResult(
                original_query=query,
                expanded_queries=[query],
                expansion_rationale=f"Expansion failed: {str(e)}"
            )

    def _build_expansion_prompt(
        self,
        query: str,
        expansion_count: int,
        context: str
    ) -> str:
        """Build prompt for query expansion."""
        context_str = f"\nContext: {context}" if context else ""

        return f"""Given the following code search query, generate {expansion_count} alternative queries that would help find related code.
Each query should explore different aspects, use different terminology, or approach the search from a different angle.

Original Query: {query}{context_str}

Please provide exactly {expansion_count} alternative queries, one per line, without numbering or prefixes.
Focus on queries that would be useful for code search and retrieval."""

    @staticmethod
    def _parse_expanded_queries(response: str) -> List[str]:
        """Parse expanded queries from LLM response."""
        queries = []
        lines = response.strip().split("\n")

        for line in lines:
            # Remove common prefixes and numbering
            cleaned = line.strip()
            for prefix in ["- ", "* ", "• ", ") ", "] ", "]: "]:
                if cleaned.startswith(prefix):
                    cleaned = cleaned[len(prefix):].strip()

            # Remove numbering like "1.", "1)"
            import re
            cleaned = re.sub(r"^\d+[.)]\s*", "", cleaned)

            if cleaned and len(cleaned) > 3:
                queries.append(cleaned)

        return queries

    def get_expansion_strategies(self) -> List[str]:
        """Return available expansion strategies."""
        return [
            "synonym_expansion",
            "related_concepts",
            "implementation_patterns",
            "error_handling",
            "performance_optimization"
        ]

    def expand_with_strategy(
        self,
        query: str,
        strategy: str = "related_concepts"
    ) -> List[str]:
        """
        Expand query using a specific strategy.

        Args:
            query: Original query
            strategy: Expansion strategy to use

        Returns:
            List of expanded queries
        """
        strategy_prompts = {
            "synonym_expansion": "Generate queries using different terminology and synonyms.",
            "related_concepts": "Generate queries for related concepts and variations.",
            "implementation_patterns": "Generate queries for common implementation patterns.",
            "error_handling": "Generate queries for error handling and edge cases.",
            "performance_optimization": "Generate queries for performance and optimization aspects."
        }

        strategy_prompt = strategy_prompts.get(strategy, strategy_prompts["related_concepts"])

        prompt = f"""Query: {query}

{strategy_prompt}

Generate 3 alternative queries based on this strategy."""

        try:
            response = self.llm_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=300
            )

            content = response.choices[0].message.content
            return self._parse_expanded_queries(content)

        except Exception as e:
            logger.error(f"Strategy-based expansion failed: {e}")
            return [query]


class HybridQueryExpander:
    """Combines multiple expansion strategies for comprehensive coverage."""

    def __init__(self, llm_client):
        """Initialize hybrid expander."""
        self.expander = QueryExpander(llm_client)

    def expand_comprehensively(
        self,
        query: str,
        strategies: List[str] = None
    ) -> List[str]:
        """
        Expand query using multiple strategies.

        Args:
            query: Original query
            strategies: List of strategies to apply

        Returns:
            Comprehensive list of expanded queries
        """
        if strategies is None:
            strategies = [
                "related_concepts",
                "implementation_patterns",
                "synonym_expansion"
            ]

        all_queries = {query}  # Use set to avoid duplicates

        for strategy in strategies:
            try:
                expanded = self.expander.expand_with_strategy(query, strategy)
                all_queries.update(expanded)
            except Exception as e:
                logger.warning(f"Strategy {strategy} failed: {e}")

        return list(all_queries)

    def rank_queries(
        self,
        queries: List[str],
        original: str
    ) -> List[str]:
        """
        Rank expanded queries by relevance to original.

        Args:
            queries: List of queries to rank
            original: Original query for reference

        Returns:
            Ranked list of queries
        """
        # Simple ranking: original first, then by length similarity to original
        original_len = len(original.split())

        def score_query(q: str) -> float:
            if q == original:
                return float('inf')
            len_diff = abs(len(q.split()) - original_len)
            return -len_diff

        return sorted(queries, key=score_query, reverse=True)
