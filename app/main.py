"""
Azure RAG Agent POC - FastAPI Application

Main application entry point
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.api.routes import chat, health, tools

# ロギング設定
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーションライフサイクル管理"""
    logger.info("Application startup")
    yield
    logger.info("Application shutdown")


# FastAPI アプリケーション
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan
)

# CORS 設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ルーター登録
app.include_router(health.router, prefix=settings.API_V1_PREFIX, tags=["health"])
app.include_router(tools.router, prefix=settings.API_V1_PREFIX, tags=["tools"])
app.include_router(chat.router, prefix=settings.API_V1_PREFIX, tags=["chat"])


@app.get("/")
async def root():
    """ルートエンドポイント"""
    return {
        "message": "Azure RAG Agent POC API",
        "version": settings.VERSION,
        "docs": "/docs"
    }
