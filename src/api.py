"""
FastAPI REST API for RAG Pipeline.

Endpoints:
- POST /query - Execute RAG query
- POST /query/stream - Execute RAG query with streaming
- POST /ingest - Ingest documents
- GET /health - Health check
"""
import uuid
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from .indexer import DocumentIngestionPipeline, SearchIndexManager
from .rag_pipeline import ConversationManager, RAGPipeline


# === Pydantic Models ===


class QueryRequest(BaseModel):
    """Request model for RAG query."""

    question: str = Field(..., min_length=1, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=20)
    search_mode: str = Field(default="hybrid", pattern="^(vector|keyword|hybrid)$")
    filters: str | None = Field(default=None)
    session_id: str | None = Field(default=None)


class QueryResponse(BaseModel):
    """Response model for RAG query."""

    answer: str
    sources: list[dict]
    session_id: str


class DocumentInput(BaseModel):
    """Single document for ingestion."""

    id: str
    content: str
    metadata: dict = Field(default_factory=dict)


class IngestRequest(BaseModel):
    """Request model for document ingestion."""

    documents: list[DocumentInput]


class IngestResponse(BaseModel):
    """Response model for document ingestion."""

    succeeded: int
    failed: int
    errors: list[dict]


class HealthResponse(BaseModel):
    """Response model for health check."""

    status: str
    index_name: str
    document_count: int


# === Application Setup ===


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup: Initialize components
    app.state.rag_pipeline = RAGPipeline()
    app.state.conversation_manager = ConversationManager()
    app.state.index_manager = SearchIndexManager()
    app.state.ingestion_pipeline = DocumentIngestionPipeline()

    yield

    # Shutdown: Cleanup if needed
    pass


app = FastAPI(
    title="Azure RAG Pipeline API",
    description="Production-ready RAG system using Azure AI Search and Azure OpenAI",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# === Endpoints ===


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.

    Returns:
        HealthResponse: System health status
    """
    try:
        index_manager: SearchIndexManager = app.state.index_manager
        doc_count = index_manager.get_document_count()

        return HealthResponse(
            status="healthy",
            index_name=index_manager.index_name,
            document_count=doc_count,
        )
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")


@app.post("/query", response_model=QueryResponse)
async def query_rag(request: QueryRequest):
    """
    Execute RAG query (non-streaming).

    Args:
        request: Query request with question and parameters

    Returns:
        QueryResponse: Generated answer with sources
    """
    try:
        pipeline: RAGPipeline = app.state.rag_pipeline
        conversation_manager: ConversationManager = app.state.conversation_manager

        # Get or create session
        session_id = request.session_id or str(uuid.uuid4())
        history = conversation_manager.get_history(session_id)

        # Execute query
        response = pipeline.query(
            question=request.question,
            top_k=request.top_k,
            search_mode=request.search_mode,
            filters=request.filters,
            stream=False,
            conversation_history=history if history else None,
        )

        # Update conversation history
        conversation_manager.add_turn(
            session_id=session_id,
            user_message=request.question,
            assistant_message=response.answer,
        )

        return QueryResponse(
            answer=response.answer,
            sources=response.sources,
            session_id=session_id,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@app.post("/query/stream")
async def query_rag_stream(request: QueryRequest):
    """
    Execute RAG query with streaming response.

    Args:
        request: Query request with question and parameters

    Returns:
        StreamingResponse: Server-sent events stream
    """

    async def generate():
        try:
            pipeline: RAGPipeline = app.state.rag_pipeline
            conversation_manager: ConversationManager = app.state.conversation_manager

            session_id = request.session_id or str(uuid.uuid4())
            history = conversation_manager.get_history(session_id)

            # Execute streaming query
            generator = pipeline.query(
                question=request.question,
                top_k=request.top_k,
                search_mode=request.search_mode,
                filters=request.filters,
                stream=True,
                conversation_history=history if history else None,
            )

            answer_parts = []
            for chunk in generator:
                answer_parts.append(chunk)
                yield f"data: {chunk}\n\n"

            # Get final response for sources
            full_answer = "".join(answer_parts)

            # Update conversation
            conversation_manager.add_turn(
                session_id=session_id,
                user_message=request.question,
                assistant_message=full_answer,
            )

            # Send final metadata
            yield f"data: [DONE]\n\n"
            yield f"data: {{'session_id': '{session_id}'}}\n\n"

        except Exception as e:
            yield f"data: [ERROR] {str(e)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@app.post("/ingest", response_model=IngestResponse)
async def ingest_documents(request: IngestRequest):
    """
    Ingest documents into the search index.

    Args:
        request: List of documents to ingest

    Returns:
        IngestResponse: Ingestion results
    """
    try:
        pipeline: DocumentIngestionPipeline = app.state.ingestion_pipeline

        # Convert to expected format
        documents = [
            {
                "id": doc.id,
                "content": doc.content,
                "metadata": doc.metadata,
            }
            for doc in request.documents
        ]

        result = pipeline.ingest_documents(documents)

        return IngestResponse(
            succeeded=result["succeeded"],
            failed=result["failed"],
            errors=result["errors"],
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


@app.post("/index/create")
async def create_index():
    """
    Create or update the search index.

    Returns:
        dict: Index creation status
    """
    try:
        index_manager: SearchIndexManager = app.state.index_manager
        index = index_manager.create_index()

        return {
            "status": "created",
            "index_name": index.name,
            "fields": [f.name for f in index.fields],
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Index creation failed: {str(e)}")


@app.delete("/conversation/{session_id}")
async def clear_conversation(session_id: str):
    """
    Clear conversation history for a session.

    Args:
        session_id: Session identifier to clear

    Returns:
        dict: Clear status
    """
    conversation_manager: ConversationManager = app.state.conversation_manager
    conversation_manager.clear_session(session_id)

    return {"status": "cleared", "session_id": session_id}


# === Main Entry Point ===

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
