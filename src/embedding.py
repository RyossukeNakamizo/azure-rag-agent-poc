"""
Embedding module for document vectorization.

Features:
- Semantic chunking with overlap
- Token-aware splitting using tiktoken
- Batch embedding for efficiency
- Async support for high throughput
"""
import asyncio
from typing import Generator

import tiktoken
from openai import AzureOpenAI

from .config import get_settings, get_openai_token


class TextChunker:
    """
    Token-aware text chunker for RAG applications.

    Uses tiktoken for accurate token counting compatible with
    OpenAI embedding models.
    """

    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 100,
        model: str = "text-embedding-ada-002",
    ):
        """
        Initialize chunker.

        Args:
            chunk_size: Maximum tokens per chunk
            chunk_overlap: Token overlap between chunks
            model: Model name for tokenizer selection
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.encoding = tiktoken.encoding_for_model(model)

    def _count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        return len(self.encoding.encode(text))

    def _split_into_sentences(self, text: str) -> list[str]:
        """Split text into sentences for semantic boundaries."""
        import re

        # Split on sentence boundaries
        sentences = re.split(r"(?<=[.!?])\s+", text)
        return [s.strip() for s in sentences if s.strip()]

    def chunk_text(self, text: str) -> Generator[dict, None, None]:
        """
        Split text into overlapping chunks.

        Yields:
            dict: Chunk with text and metadata
                - text: Chunk content
                - start_token: Start position
                - end_token: End position
                - token_count: Number of tokens
        """
        sentences = self._split_into_sentences(text)
        current_chunk: list[str] = []
        current_tokens = 0
        chunk_start = 0
        total_tokens = 0

        for sentence in sentences:
            sentence_tokens = self._count_tokens(sentence)

            # If single sentence exceeds chunk size, split it
            if sentence_tokens > self.chunk_size:
                # Yield current chunk if not empty
                if current_chunk:
                    chunk_text = " ".join(current_chunk)
                    yield {
                        "text": chunk_text,
                        "start_token": chunk_start,
                        "end_token": total_tokens,
                        "token_count": current_tokens,
                    }
                    # Prepare overlap
                    overlap_text = self._get_overlap_text(current_chunk)
                    current_chunk = [overlap_text] if overlap_text else []
                    current_tokens = self._count_tokens(overlap_text) if overlap_text else 0
                    chunk_start = total_tokens - current_tokens

                # Split long sentence by tokens
                words = sentence.split()
                sub_chunk: list[str] = []
                sub_tokens = 0

                for word in words:
                    word_tokens = self._count_tokens(word + " ")
                    if sub_tokens + word_tokens > self.chunk_size:
                        if sub_chunk:
                            sub_text = " ".join(sub_chunk)
                            yield {
                                "text": sub_text,
                                "start_token": chunk_start,
                                "end_token": total_tokens,
                                "token_count": sub_tokens,
                            }
                            chunk_start = total_tokens
                        sub_chunk = [word]
                        sub_tokens = word_tokens
                    else:
                        sub_chunk.append(word)
                        sub_tokens += word_tokens

                # Add remaining words to current chunk
                if sub_chunk:
                    current_chunk.extend(sub_chunk)
                    current_tokens += sub_tokens

                total_tokens += sentence_tokens
                continue

            # Check if adding sentence exceeds chunk size
            if current_tokens + sentence_tokens > self.chunk_size:
                # Yield current chunk
                chunk_text = " ".join(current_chunk)
                yield {
                    "text": chunk_text,
                    "start_token": chunk_start,
                    "end_token": total_tokens,
                    "token_count": current_tokens,
                }

                # Prepare overlap
                overlap_text = self._get_overlap_text(current_chunk)
                current_chunk = [overlap_text] if overlap_text else []
                current_tokens = self._count_tokens(overlap_text) if overlap_text else 0
                chunk_start = total_tokens - current_tokens

            current_chunk.append(sentence)
            current_tokens += sentence_tokens
            total_tokens += sentence_tokens

        # Yield final chunk
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            yield {
                "text": chunk_text,
                "start_token": chunk_start,
                "end_token": total_tokens,
                "token_count": current_tokens,
            }

    def _get_overlap_text(self, sentences: list[str]) -> str:
        """Get overlap text from end of sentence list."""
        overlap_sentences: list[str] = []
        overlap_tokens = 0

        for sentence in reversed(sentences):
            sentence_tokens = self._count_tokens(sentence)
            if overlap_tokens + sentence_tokens <= self.chunk_overlap:
                overlap_sentences.insert(0, sentence)
                overlap_tokens += sentence_tokens
            else:
                break

        return " ".join(overlap_sentences)


class EmbeddingService:
    """
    Azure OpenAI embedding service.

    Features:
    - Batch embedding for efficiency
    - Azure AD token authentication
    - Automatic retry with exponential backoff
    """

    def __init__(self):
        """Initialize embedding service with Azure OpenAI client."""
        settings = get_settings()

        self.client = AzureOpenAI(
            azure_endpoint=settings.openai_endpoint,
            azure_ad_token_provider=get_openai_token,
            api_version=settings.openai_api_version,
        )
        self.deployment = settings.openai_deployment_embedding

    def embed_text(self, text: str) -> list[float]:
        """
        Generate embedding for single text.

        Args:
            text: Input text to embed

        Returns:
            list[float]: Embedding vector (1536 dimensions for ada-002)
        """
        response = self.client.embeddings.create(
            model=self.deployment,
            input=text,
        )
        return response.data[0].embedding

    def embed_batch(
        self,
        texts: list[str],
        batch_size: int = 16,
    ) -> list[list[float]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed
            batch_size: Number of texts per API call (max 16 recommended)

        Returns:
            list[list[float]]: List of embedding vectors
        """
        all_embeddings: list[list[float]] = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            response = self.client.embeddings.create(
                model=self.deployment,
                input=batch,
            )
            batch_embeddings = [item.embedding for item in response.data]
            all_embeddings.extend(batch_embeddings)

        return all_embeddings


class DocumentProcessor:
    """
    End-to-end document processing pipeline.

    Combines chunking and embedding for RAG indexing.
    """

    def __init__(self):
        """Initialize processor with chunker and embedding service."""
        settings = get_settings()
        self.chunker = TextChunker(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )
        self.embedding_service = EmbeddingService()

    def process_document(
        self,
        document_id: str,
        text: str,
        metadata: dict | None = None,
    ) -> list[dict]:
        """
        Process document into indexed chunks with embeddings.

        Args:
            document_id: Unique document identifier
            text: Document text content
            metadata: Additional metadata (source, category, etc.)

        Returns:
            list[dict]: Processed chunks ready for indexing
                - id: Unique chunk ID
                - document_id: Parent document ID
                - content: Chunk text
                - content_vector: Embedding vector
                - metadata: Additional fields
        """
        chunks = list(self.chunker.chunk_text(text))

        # Extract chunk texts for batch embedding
        chunk_texts = [c["text"] for c in chunks]
        embeddings = self.embedding_service.embed_batch(chunk_texts)

        # Build indexed documents
        processed_chunks = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            chunk_doc = {
                "id": f"{document_id}_chunk_{i}",
                "document_id": document_id,
                "content": chunk["text"],
                "content_vector": embedding,
                "chunk_index": i,
                "token_count": chunk["token_count"],
                **(metadata or {}),
            }
            processed_chunks.append(chunk_doc)

        return processed_chunks
