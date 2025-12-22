"""Application Configuration"""

from pydantic_settings import BaseSettings
from pydantic import Field


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
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT: str = Field(
        default="text-embedding-ada-002",
        description="Azure OpenAI Embedding Deployment Name"
    )
    AZURE_OPENAI_API_VERSION: str = Field(
        default="2024-10-01-preview",
        description="Azure OpenAI API Version"
    )
    
    # API Settings
    API_V1_PREFIX: str = "/api"
    PROJECT_NAME: str = "Azure RAG Agent POC"
    VERSION: str = "1.0.0"
    
    # Logging
    LOG_LEVEL: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
