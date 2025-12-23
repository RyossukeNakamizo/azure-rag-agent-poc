"""Application Configuration"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""
    
    # Azure OpenAI
    AZURE_OPENAI_ENDPOINT: str = Field(
        ...,
        description="Azure OpenAI Endpoint"
    )
    AZURE_OPENAI_DEPLOYMENT: str = Field(
        default="gpt-4o",
        description="Azure OpenAI Chat Deployment Name"
    )
    AZURE_OPENAI_DEPLOYMENT_CHAT: str = Field(
        default="gpt-4o",
        description="Azure OpenAI Chat Deployment Name (Phase 2)"
    )
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT: str = Field(
        default="text-embedding-ada-002",
        description="Azure OpenAI Embedding Deployment Name"
    )
    AZURE_OPENAI_DEPLOYMENT_EMBEDDING: str = Field(
        default="text-embedding-ada-002",
        description="Azure OpenAI Embedding Deployment Name (Phase 2)"
    )
    AZURE_OPENAI_API_VERSION: str = Field(
        default="2024-10-01-preview",
        description="Azure OpenAI API Version"
    )
    
    # Azure AI Search (Phase 2)
    AZURE_SEARCH_ENDPOINT: str = Field(
        default="",
        description="Azure AI Search Endpoint"
    )
    AZURE_SEARCH_INDEX: str = Field(
        default="rag-docs-index",
        description="Azure AI Search Index Name"
    )
    AZURE_SEARCH_API_KEY: Optional[str] = Field(
        default=None,
        description="Azure AI Search API Key (optional, Managed Identity preferred)"
    )
    AZURE_SEARCH_SKU: str = Field(
        default="basic",
        description="Azure AI Search SKU"
    )
    
    # API Settings
    API_V1_PREFIX: str = "/api"
    PROJECT_NAME: str = "Azure RAG Agent POC"
    VERSION: str = "0.2.0"
    
    # Logging
    LOG_LEVEL: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"  # 追加フィールドを許可


def get_settings() -> Settings:
    """Get settings instance"""
    return Settings()


settings = Settings()