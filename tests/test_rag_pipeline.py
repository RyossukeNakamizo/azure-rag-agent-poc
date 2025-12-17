"""
Unit tests for RAG Pipeline components.

Run with: pytest tests/ -v
"""
import pytest
from unittest.mock import MagicMock, patch

# Test fixtures


@pytest.fixture
def mock_settings():
    """Mock settings for testing."""
    with patch("src.config.get_settings") as mock:
        mock.return_value = MagicMock(
            search_endpoint="https://test.search.windows.net",
            search_index="test-index",
            openai_endpoint="https://test.openai.azure.com",
            openai_deployment_chat="gpt-4o",
            openai_deployment_embedding="text-embedding-ada-002",
            openai_api_version="2024-10-01-preview",
            rag_top_k=5,
            rag_score_threshold=0.7,
            chunk_size=500,
            chunk_overlap=100,
        )
        yield mock


@pytest.fixture
def mock_credential():
    """Mock Azure credential."""
    with patch("src.config.get_azure_credential") as mock:
        credential = MagicMock()
        credential.get_token.return_value = MagicMock(token="test-token")
        mock.return_value = credential
        yield mock


# TextChunker Tests


class TestTextChunker:
    """Tests for TextChunker class."""

    def test_chunk_short_text(self):
        """Short text should produce single chunk."""
        from src.embedding import TextChunker

        chunker = TextChunker(chunk_size=100, chunk_overlap=20)
        text = "This is a short sentence."

        chunks = list(chunker.chunk_text(text))

        assert len(chunks) == 1
        assert chunks[0]["text"] == text

    def test_chunk_long_text(self):
        """Long text should produce multiple chunks."""
        from src.embedding import TextChunker

        chunker = TextChunker(chunk_size=50, chunk_overlap=10)
        text = " ".join(["This is a test sentence."] * 20)

        chunks = list(chunker.chunk_text(text))

        assert len(chunks) > 1
        # Verify token counts are within limits
        for chunk in chunks:
            assert chunk["token_count"] <= 50

    def test_chunk_overlap(self):
        """Chunks should have overlapping content."""
        from src.embedding import TextChunker

        chunker = TextChunker(chunk_size=30, chunk_overlap=10)
        text = "First sentence here. Second sentence follows. Third sentence ends."

        chunks = list(chunker.chunk_text(text))

        # With overlap, content from end of one chunk should appear in next
        if len(chunks) > 1:
            # Overlap should create some shared content
            assert chunks[0]["end_token"] >= chunks[1]["start_token"]


# SearchResult Tests


class TestSearchResult:
    """Tests for SearchResult dataclass."""

    def test_search_result_creation(self):
        """SearchResult should be creatable with required fields."""
        from src.retriever import SearchResult

        result = SearchResult(
            id="test-1",
            document_id="doc-1",
            content="Test content",
            score=0.85,
        )

        assert result.id == "test-1"
        assert result.score == 0.85
        assert result.source is None  # Optional field


# ContextBuilder Tests


class TestContextBuilder:
    """Tests for ContextBuilder class."""

    def test_build_context_basic(self):
        """Context builder should combine results."""
        from src.retriever import ContextBuilder, SearchResult

        builder = ContextBuilder(max_context_tokens=1000)

        results = [
            SearchResult(
                id="1",
                document_id="doc1",
                content="First chunk content.",
                score=0.9,
                source="source1.txt",
                title="Document 1",
            ),
            SearchResult(
                id="2",
                document_id="doc2",
                content="Second chunk content.",
                score=0.8,
                source="source2.txt",
                title="Document 2",
            ),
        ]

        context, sources = builder.build_context(results)

        assert "First chunk content" in context
        assert "Second chunk content" in context
        assert len(sources) == 2

    def test_build_context_deduplication(self):
        """Duplicate sources should be deduplicated."""
        from src.retriever import ContextBuilder, SearchResult

        builder = ContextBuilder()

        results = [
            SearchResult(
                id="1",
                document_id="doc1",
                content="Chunk 1",
                score=0.9,
                source="same-source.txt",
            ),
            SearchResult(
                id="2",
                document_id="doc1",
                content="Chunk 2",
                score=0.8,
                source="same-source.txt",
            ),
        ]

        _, sources = builder.build_context(results)

        # Should deduplicate to single source
        assert len(sources) == 1
        # Should keep higher relevance score
        assert sources[0]["relevance_score"] == 0.9


# RAGPipeline Tests


class TestRAGPipeline:
    """Tests for RAGPipeline class."""

    @patch("src.rag_pipeline.HybridRetriever")
    @patch("src.rag_pipeline.AzureOpenAI")
    def test_build_messages(self, mock_openai, mock_retriever, mock_settings, mock_credential):
        """Message building should include system prompt and context."""
        from src.rag_pipeline import RAGPipeline

        pipeline = RAGPipeline()

        messages = pipeline._build_messages(
            question="Test question?",
            context="Test context here.",
            conversation_history=None,
        )

        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert "Test context here" in messages[1]["content"]
        assert "Test question?" in messages[1]["content"]

    @patch("src.rag_pipeline.HybridRetriever")
    @patch("src.rag_pipeline.AzureOpenAI")
    def test_build_messages_with_history(self, mock_openai, mock_retriever, mock_settings, mock_credential):
        """Message building should include conversation history."""
        from src.rag_pipeline import RAGPipeline

        pipeline = RAGPipeline()

        history = [
            {"role": "user", "content": "Previous question"},
            {"role": "assistant", "content": "Previous answer"},
        ]

        messages = pipeline._build_messages(
            question="Follow-up question?",
            context="New context.",
            conversation_history=history,
        )

        assert len(messages) == 4  # system + history(2) + user
        assert messages[1]["content"] == "Previous question"
        assert messages[2]["content"] == "Previous answer"


# ConversationManager Tests


class TestConversationManager:
    """Tests for ConversationManager class."""

    def test_add_turn(self):
        """Adding turns should append to history."""
        from src.rag_pipeline import ConversationManager

        manager = ConversationManager(max_history_turns=5)

        manager.add_turn("session-1", "Hello", "Hi there!")

        history = manager.get_history("session-1")
        assert len(history) == 2
        assert history[0]["role"] == "user"
        assert history[1]["role"] == "assistant"

    def test_max_turns_truncation(self):
        """History should truncate when exceeding max turns."""
        from src.rag_pipeline import ConversationManager

        manager = ConversationManager(max_history_turns=2)

        # Add 3 turns
        manager.add_turn("session-1", "Q1", "A1")
        manager.add_turn("session-1", "Q2", "A2")
        manager.add_turn("session-1", "Q3", "A3")

        history = manager.get_history("session-1")

        # Should only keep last 2 turns (4 messages)
        assert len(history) == 4
        assert "Q1" not in str(history)

    def test_clear_session(self):
        """Clearing session should remove all history."""
        from src.rag_pipeline import ConversationManager

        manager = ConversationManager()

        manager.add_turn("session-1", "Test", "Response")
        manager.clear_session("session-1")

        history = manager.get_history("session-1")
        assert len(history) == 0


# Integration Tests (require mocking Azure services)


class TestAPIEndpoints:
    """Tests for FastAPI endpoints."""

    @pytest.fixture
    def client(self, mock_settings, mock_credential):
        """Create test client with mocked dependencies."""
        from fastapi.testclient import TestClient

        with patch("src.api.RAGPipeline"), patch("src.api.SearchIndexManager"):
            from src.api import app

            with TestClient(app) as client:
                yield client

    def test_health_check(self, client):
        """Health endpoint should return status."""
        # Note: This would need proper mocking of SearchIndexManager
        # Skipping for now as it requires more complex setup
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
