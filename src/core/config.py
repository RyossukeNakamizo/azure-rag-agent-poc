"""
Application Configuration

Pydantic Settings for environment variable management
"""
from functools import lru_cache
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """アプリケーション設定"""
    
    # Project
    PROJECT_NAME: str = "Azure RAG Agent POC"
    VERSION: str = "0.2.0"
    API_V1_PREFIX: str = "/api"
    LOG_LEVEL: str = "INFO"
    
    # Azure OpenAI
    AZURE_OPENAI_ENDPOINT: str
    AZURE_OPENAI_DEPLOYMENT: str = "gpt-4o"
    AZURE_OPENAI_DEPLOYMENT_CHAT: str = "gpt-4o"
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT: str = "text-embedding-ada-002"
    AZURE_OPENAI_API_VERSION: str = "2024-10-01-preview"
    AZURE_OPENAI_API_KEY: Optional[str] = None  # Managed Identity優先
    
    # Azure AI Search
    AZURE_SEARCH_ENDPOINT: str = ""
    AZURE_SEARCH_INDEX: str = "rag-docs-index"
    AZURE_SEARCH_API_KEY: Optional[str] = None  # Managed Identity優先
    AZURE_SEARCH_SKU: str = "basic"
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "allow",  # 追加の環境変数を許可
    }


@lru_cache
def get_settings() -> Settings:
    """設定のシングルトンインスタンスを返す"""
    return Settings()


# 後方互換性のためのエイリアス
settings = get_settings()