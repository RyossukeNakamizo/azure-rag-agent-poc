"""
Azure RAG Agent POC - Main Application

FastAPI application entry point with RAG endpoints.
D28: OpenTelemetry統合
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.telemetry import configure_telemetry
from app.api.routes import rag, health, chat, tools

settings = get_settings()
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION}")
    logger.info(f"Cosmos DB enabled: {settings.COSMOS_DB_ENABLED}")
    
    if settings.OTEL_ENABLED:
        telemetry_configured = configure_telemetry()
        logger.info(f"OpenTelemetry configured: {telemetry_configured}")
        try:
            from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
            FastAPIInstrumentor.instrument_app(app)
            logger.info("FastAPI instrumented with OpenTelemetry")
        except ImportError:
            logger.warning("FastAPIInstrumentor not available")
    else:
        logger.info("OpenTelemetry disabled")
    
    yield
    logger.info("Shutting down application")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Azure AI Search + OpenAI RAG POC",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api/v1", tags=["Health"])
app.include_router(rag.router, prefix="/api/v1/rag", tags=["RAG"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["Chat"])
app.include_router(tools.router, prefix="/api/v1/tools", tags=["Tools"])


@app.get("/")
async def root():
    return {"name": settings.PROJECT_NAME, "version": settings.VERSION, "status": "running"}
