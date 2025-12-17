"""
Configuration module for Azure RAG Pipeline.

Supports multiple authentication methods:
- Managed Identity (production)
- Azure CLI (development)
- Service Principal (CI/CD)
"""
import os
from functools import lru_cache
from typing import Literal

from azure.identity import (
    AzureCliCredential,
    DefaultAzureCredential,
    ManagedIdentityCredential,
    ClientSecretCredential,
)
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Application settings loaded from environment variables."""

    # Azure AI Search
    search_endpoint: str = os.getenv("AZURE_SEARCH_ENDPOINT", "")
    search_index: str = os.getenv("AZURE_SEARCH_INDEX", "rag-documents")

    # Azure OpenAI
    openai_endpoint: str = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    openai_deployment_chat: str = os.getenv("AZURE_OPENAI_DEPLOYMENT_CHAT", "gpt-4o")
    openai_deployment_embedding: str = os.getenv(
        "AZURE_OPENAI_DEPLOYMENT_EMBEDDING", "text-embedding-ada-002"
    )
    openai_api_version: str = os.getenv(
        "AZURE_OPENAI_API_VERSION", "2024-10-01-preview"
    )

    # Azure Storage
    storage_account_url: str = os.getenv("AZURE_STORAGE_ACCOUNT_URL", "")
    storage_container: str = os.getenv("AZURE_STORAGE_CONTAINER", "documents")

    # Authentication
    auth_method: Literal["managed_identity", "azure_cli", "service_principal"] = (
        os.getenv("AZURE_AUTH_METHOD", "azure_cli")
    )

    # Service Principal credentials (if applicable)
    client_id: str = os.getenv("AZURE_CLIENT_ID", "")
    client_secret: str = os.getenv("AZURE_CLIENT_SECRET", "")
    tenant_id: str = os.getenv("AZURE_TENANT_ID", "")

    # RAG Configuration
    rag_top_k: int = int(os.getenv("RAG_TOP_K", "5"))
    rag_score_threshold: float = float(os.getenv("RAG_SCORE_THRESHOLD", "0.7"))
    chunk_size: int = int(os.getenv("CHUNK_SIZE", "500"))
    chunk_overlap: int = int(os.getenv("CHUNK_OVERLAP", "100"))


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


def get_azure_credential():
    """
    Get Azure credential based on configured authentication method.

    Returns:
        TokenCredential: Azure authentication credential

    Priority:
        1. Managed Identity (production workloads)
        2. Azure CLI (local development)
        3. Service Principal (CI/CD pipelines)
        4. Default (auto-detect)
    """
    settings = get_settings()

    match settings.auth_method:
        case "managed_identity":
            return ManagedIdentityCredential()
        case "azure_cli":
            return AzureCliCredential()
        case "service_principal":
            if not all([settings.tenant_id, settings.client_id, settings.client_secret]):
                raise ValueError(
                    "Service Principal credentials incomplete. "
                    "Set AZURE_TENANT_ID, AZURE_CLIENT_ID, AZURE_CLIENT_SECRET"
                )
            return ClientSecretCredential(
                tenant_id=settings.tenant_id,
                client_id=settings.client_id,
                client_secret=settings.client_secret,
            )
        case _:
            return DefaultAzureCredential()


def get_openai_token() -> str:
    """
    Get Azure AD token for Azure OpenAI authentication.

    Returns:
        str: Bearer token for Cognitive Services
    """
    credential = get_azure_credential()
    token = credential.get_token("https://cognitiveservices.azure.com/.default")
    return token.token
