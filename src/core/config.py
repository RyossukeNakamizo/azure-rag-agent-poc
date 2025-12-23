"""Application Configuration"""
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Azure OpenAI
    AZURE_OPENAI_ENDPOINT: str
    AZURE_OPENAI_DEPLOYMENT: str = "gpt-4o"  # Phase 1 互換
    AZURE_OPENAI_DEPLOYMENT_CHAT: str = "gpt-4o"  # Phase 2
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT: str = "text-embedding-ada-002"  # Phase 1
    AZURE_OPENAI_DEPLOYMENT_EMBEDDING: str = "text-embedding-ada-002"  # Phase 2
    AZURE_OPENAI_API_VERSION: str = "2024-10-01-preview"
    
    # Azure AI Search (Phase 2)
    AZURE_SEARCH_ENDPOINT: str
    AZURE_SEARCH_INDEX: str = "rag-docs-index"
    AZURE_SEARCH_API_KEY: str | None = None
    AZURE_SEARCH_SKU: str = "basic"
    
    # Application
    PROJECT_NAME: str = "Azure RAG Agent POC"
    APP_NAME: str = "Azure RAG Agent POC"
    VERSION: str = "0.2.0"
    APP_VERSION: str = "0.2.0"
    API_V1_PREFIX: str = "/api"
    LOG_LEVEL: str = "INFO"
    DEBUG: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"  # 追加フィールドを許可

def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()