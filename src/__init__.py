"""
Azure RAG Agent PoC Package.

A production-ready RAG pipeline using Azure AI Search and Azure OpenAI.
"""
from .config import get_settings
from .rag_pipeline import RAGPipeline, RAGResponse

__version__ = "1.0.0"
__all__ = ["RAGPipeline", "RAGResponse", "get_settings"]
