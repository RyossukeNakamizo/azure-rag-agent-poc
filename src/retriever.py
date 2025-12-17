"""
Retriever module for RAG search operations.

Features:
- Hybrid search (vector + keyword)
- Semantic reranking (optional)
- Configurable filtering
- Score-based result filtering
"""
from dataclasses import dataclass
from typing import Literal

from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery

from .config import get_azure_credential, get_settings
from .embedding import EmbeddingService


@dataclass
class SearchResult:
    """Represents a single search result."""

    id: str
    document_id: str
    content: str
    score: float
    source: str | None = None
    title: str | None = None
    category: str | None = None
    chunk_index: int | None = None


class HybridRetriever:
    """
    Hybrid search retriever combining vector and keyword search.

    Search Modes:
    - vector: Pure vector similarity search
    - keyword: Traditional BM25 keyword search
    - hybrid: Combined vector + keyword (recommended)
    """

    def __init__(self):
        """Initialize retriever with search client and embedding service."""
        settings = get_settings()
        credential = get_azure_credential()

        self.search_client = SearchClient(
            endpoint=settings.search_endpoint,
            index_name=settings.search_index,
            credential=credential,
        )
        self.embedding_service = EmbeddingService()
        self.default_top_k = settings.rag_top_k
        self.score_threshold = settings.rag_score_threshold

    def search(
        self,
        query: str,
        top_k: int | None = None,
        mode: Literal["vector", "keyword", "hybrid"] = "hybrid",
        filters: str | None = None,
        select_fields: list[str] | None = None,
    ) -> list[SearchResult]:
        """
        Execute search query.

        Args:
            query: User query text
            top_k: Number of results to return
            mode: Search mode (vector/keyword/hybrid)
            filters: OData filter expression (e.g., "category eq 'tech'")
            select_fields: Fields to return in results

        Returns:
            list[SearchResult]: Ranked search results
        """
        top_k = top_k or self.default_top_k
        select_fields = select_fields or [
            "id",
            "document_id",
            "content",
            "source",
            "title",
            "category",
            "chunk_index",
        ]

        # Build search parameters
        search_kwargs = {
            "select": select_fields,
            "top": top_k,
        }

        if filters:
            search_kwargs["filter"] = filters

        # Execute search based on mode
        match mode:
            case "vector":
                results = self._vector_search(query, **search_kwargs)
            case "keyword":
                results = self._keyword_search(query, **search_kwargs)
            case "hybrid":
                results = self._hybrid_search(query, **search_kwargs)
            case _:
                raise ValueError(f"Invalid search mode: {mode}")

        # Filter by score threshold
        filtered_results = [
            r for r in results if r.score >= self.score_threshold
        ]

        return filtered_results

    def _vector_search(
        self,
        query: str,
        **kwargs,
    ) -> list[SearchResult]:
        """Execute pure vector search."""
        query_embedding = self.embedding_service.embed_text(query)

        vector_query = VectorizedQuery(
            vector=query_embedding,
            k_nearest_neighbors=kwargs.get("top", self.default_top_k),
            fields="content_vector",
        )

        results = self.search_client.search(
            search_text=None,  # No keyword search
            vector_queries=[vector_query],
            **kwargs,
        )

        return self._parse_results(results)

    def _keyword_search(
        self,
        query: str,
        **kwargs,
    ) -> list[SearchResult]:
        """Execute pure keyword search."""
        results = self.search_client.search(
            search_text=query,
            **kwargs,
        )

        return self._parse_results(results)

    def _hybrid_search(
        self,
        query: str,
        **kwargs,
    ) -> list[SearchResult]:
        """Execute hybrid (vector + keyword) search."""
        query_embedding = self.embedding_service.embed_text(query)

        vector_query = VectorizedQuery(
            vector=query_embedding,
            k_nearest_neighbors=kwargs.get("top", self.default_top_k),
            fields="content_vector",
        )

        results = self.search_client.search(
            search_text=query,
            vector_queries=[vector_query],
            **kwargs,
        )

        return self._parse_results(results)

    def _parse_results(self, results) -> list[SearchResult]:
        """Convert Azure search results to SearchResult objects."""
        parsed = []
        for r in results:
            parsed.append(
                SearchResult(
                    id=r.get("id", ""),
                    document_id=r.get("document_id", ""),
                    content=r.get("content", ""),
                    score=r.get("@search.score", 0.0),
                    source=r.get("source"),
                    title=r.get("title"),
                    category=r.get("category"),
                    chunk_index=r.get("chunk_index"),
                )
            )
        return parsed


class ContextBuilder:
    """
    Builds context from search results for LLM consumption.

    Features:
    - Token-aware context truncation
    - Source deduplication
    - Relevance-based ordering
    """

    def __init__(self, max_context_tokens: int = 4000):
        """
        Initialize context builder.

        Args:
            max_context_tokens: Maximum tokens for combined context
        """
        self.max_tokens = max_context_tokens

    def build_context(
        self,
        results: list[SearchResult],
        include_metadata: bool = True,
    ) -> tuple[str, list[dict]]:
        """
        Build context string from search results.

        Args:
            results: Search results to include
            include_metadata: Whether to include source/category info

        Returns:
            tuple: (context_string, source_references)
        """
        import tiktoken

        encoding = tiktoken.encoding_for_model("gpt-4")
        context_parts = []
        sources = []
        current_tokens = 0

        for result in results:
            # Build chunk text
            if include_metadata:
                chunk_text = f"[Source: {result.source or 'Unknown'}]\n"
                if result.title:
                    chunk_text += f"Title: {result.title}\n"
                chunk_text += f"{result.content}\n"
            else:
                chunk_text = f"{result.content}\n"

            chunk_tokens = len(encoding.encode(chunk_text))

            # Check token limit
            if current_tokens + chunk_tokens > self.max_tokens:
                break

            context_parts.append(chunk_text)
            current_tokens += chunk_tokens

            # Track sources
            if result.source:
                sources.append({
                    "source": result.source,
                    "title": result.title,
                    "relevance_score": result.score,
                })

        context = "\n---\n".join(context_parts)
        unique_sources = self._deduplicate_sources(sources)

        return context, unique_sources

    def _deduplicate_sources(self, sources: list[dict]) -> list[dict]:
        """Remove duplicate sources, keeping highest relevance."""
        seen = {}
        for source in sources:
            key = source["source"]
            if key not in seen or source["relevance_score"] > seen[key]["relevance_score"]:
                seen[key] = source
        return list(seen.values())
