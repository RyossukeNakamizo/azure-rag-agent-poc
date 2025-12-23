"""
Azure RAG Agent POC - Main Application

Phase 1: Chat Completions API
Phase 2: Azure AI Search Integration
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import chat
from app.core.config import settings

# Phase 2-3: RAG ルーター追加
from src.api.routes.rag import router as rag_router

# ロギング設定
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーションライフサイクル管理"""
    logger.info("Starting Azure RAG Agent POC...")
    logger.info(f"OpenAI Endpoint: {settings.AZURE_OPENAI_ENDPOINT}")
    logger.info(f"Chat Deployment: {settings.AZURE_OPENAI_DEPLOYMENT_CHAT}")
    logger.info(f"Embedding Deployment: {settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT}")
    
    # Phase 2: Search 設定ログ
    if hasattr(settings, 'AZURE_SEARCH_ENDPOINT'):
        logger.info(f"Search Endpoint: {settings.AZURE_SEARCH_ENDPOINT}")
        logger.info(f"Search Index: {settings.AZURE_SEARCH_INDEX}")
    
    yield
    
    logger.info("Shutting down Azure RAG Agent POC...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Azure AI Foundry を活用した RAG エージェント POC",
    lifespan=lifespan,
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ルーター登録
app.include_router(chat.router, prefix=settings.API_V1_PREFIX)

# Phase 2-3: RAG ルーター追加
app.include_router(rag_router, prefix="/api/v1")


@app.get("/")
async def root():
    """ルートエンドポイント"""
    return {
        "message": "Azure RAG Agent POC",
        "version": settings.VERSION,
        "docs": "/docs",
        "endpoints": {
            "chat": "/api/v1/chat",
            "rag_search": "/api/v1/rag/search",
            "rag_chat": "/api/v1/rag/chat",
            "rag_health": "/api/v1/rag/health",
        }
    }


@app.get("/health")
async def health():
    """ヘルスチェックエンドポイント"""
    return {"status": "healthy", "version": settings.VERSION}