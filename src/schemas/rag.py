"""
RAG API Routes

Phase 2-3: RAG エンドポイント実装
- GET /health: Search + OpenAI 疎通確認
- POST /search: ハイブリッド検索
- POST /chat: RAG + 回答生成
- POST /chat/stream: ストリーミング対応
"""
import logging
from typing import AsyncGenerator

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse

from src.core.config import get_settings, Settings
from src.services.search_service import SearchService
from src.schemas.rag import (
    RAGSearchRequest,
    RAGSearchResponse,
    SearchResult,
    RAGChatRequest,
    RAGChatResponse,
    SourceReference,
    RAGHealthResponse,
)

# FoundryAgentService のインポート（既存）
from app.services.foundry_agent import FoundryAgentService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rag", tags=["RAG"])

# デフォルトシステムプロンプト
DEFAULT_RAG_SYSTEM_PROMPT = """あなたはAzure技術の専門家です。
以下のルールに従って回答してください：
1. 提供されたコンテキストのみを使用して回答する
2. コンテキストに情報がない場合は、その旨を明示する
3. 回答には必ずソースを引用する
4. 技術的に正確かつ実用的な回答を心がける
5. 日本語で回答する"""


def get_search_service(settings: Settings = Depends(get_settings)) -> SearchService:
    """SearchService 依存性注入"""
    return SearchService(
        endpoint=settings.AZURE_SEARCH_ENDPOINT,
        index_name=settings.AZURE_SEARCH_INDEX,
        openai_endpoint=settings.AZURE_OPENAI_ENDPOINT,
        embedding_deployment=settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
    )


def get_agent_service(settings: Settings = Depends(get_settings)) -> FoundryAgentService:
    """FoundryAgentService 依存性注入"""
    return FoundryAgentService()


@router.get("/health", response_model=RAGHealthResponse)
async def health_check(
    search_service: SearchService = Depends(get_search_service),
    agent_service: FoundryAgentService = Depends(get_agent_service),
    settings: Settings = Depends(get_settings),
):
    """
    RAG システム Health Check
    
    Search サービスと OpenAI サービスの疎通を確認
    """
    search_status = "unknown"
    openai_status = "unknown"
    
    # Search サービス確認
    try:
        # 軽量なテストクエリ
        results = search_service.keyword_search("test", top_k=1)
        search_status = "healthy"
        logger.info(f"Search health check passed: {len(results)} results")
    except Exception as e:
        search_status = f"unhealthy: {str(e)}"
        logger.error(f"Search health check failed: {e}")
    
    # OpenAI サービス確認
    try:
        # Embedding テスト
        embedding = agent_service.get_embedding("test")
        if embedding and len(embedding) == 1536:
            openai_status = "healthy"
            logger.info("OpenAI health check passed")
        else:
            openai_status = "unhealthy: invalid embedding"
    except Exception as e:
        openai_status = f"unhealthy: {str(e)}"
        logger.error(f"OpenAI health check failed: {e}")
    
    overall_status = "healthy" if "healthy" in search_status and "healthy" in openai_status else "degraded"
    
    return RAGHealthResponse(
        status=overall_status,
        search_service=search_status,
        index_name=settings.AZURE_SEARCH_INDEX,
        openai_service=openai_status,
    )


@router.post("/search", response_model=RAGSearchResponse)
async def hybrid_search(
    request: RAGSearchRequest,
    search_service: SearchService = Depends(get_search_service),
    agent_service: FoundryAgentService = Depends(get_agent_service),
):
    """
    ハイブリッド検索（Vector + Keyword）
    
    クエリを埋め込みベクトルに変換し、ベクトル検索とキーワード検索を組み合わせて実行
    """
    try:
        logger.info(f"Hybrid search request: query='{request.query}', top_k={request.top_k}")
        
        # Embedding 生成
        query_embedding = agent_service.get_embedding(request.query)
        
        if not query_embedding:
            raise HTTPException(status_code=500, detail="Failed to generate embedding")
        
        # ハイブリッド検索実行
        raw_results = search_service.hybrid_search(
            query=request.query,
            embedding=query_embedding,
            top_k=request.top_k,
            filter_expression=request.filter,
        )
        
        # レスポンス整形
        results = [
            SearchResult(
                id=r.get("id", ""),
                title=r.get("title", ""),
                content=r.get("content", ""),
                chunk_id=r.get("chunk_id"),
                score=r.get("score", 0.0),
            )
            for r in raw_results
        ]
        
        logger.info(f"Hybrid search completed: {len(results)} results")
        
        return RAGSearchResponse(
            query=request.query,
            results=results,
            total_count=len(results),
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Hybrid search error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.post("/chat", response_model=RAGChatResponse)
async def rag_chat(
    request: RAGChatRequest,
    search_service: SearchService = Depends(get_search_service),
    agent_service: FoundryAgentService = Depends(get_agent_service),
    settings: Settings = Depends(get_settings),
):
    """
    RAG Chat（検索 + 回答生成）
    
    1. クエリでハイブリッド検索を実行
    2. 検索結果をコンテキストとして LLM に渡す
    3. コンテキストに基づいた回答を生成
    """
    try:
        logger.info(f"RAG chat request: message='{request.message[:50]}...', top_k={request.top_k}")
        
        # Step 1: Embedding 生成
        query_embedding = agent_service.get_embedding(request.message)
        
        if not query_embedding:
            raise HTTPException(status_code=500, detail="Failed to generate embedding")
        
        # Step 2: ハイブリッド検索
        search_results = search_service.hybrid_search(
            query=request.message,
            embedding=query_embedding,
            top_k=request.top_k,
            filter_expression=request.filter,
        )
        
        logger.info(f"Retrieved {len(search_results)} context documents")
        
        # Step 3: コンテキスト構築
        if search_results:
            context_parts = []
            for i, doc in enumerate(search_results, 1):
                title = doc.get("title", "Untitled")
                content = doc.get("content", "")
                context_parts.append(f"【ソース{i}: {title}】\n{content}")
            
            context_text = "\n\n---\n\n".join(context_parts)
        else:
            context_text = "（関連するコンテキストが見つかりませんでした）"
        
        # Step 4: プロンプト構築
        system_prompt = request.system_prompt or DEFAULT_RAG_SYSTEM_PROMPT
        
        user_message = f"""以下のコンテキストを参照して、質問に回答してください。

【コンテキスト】
{context_text}

【質問】
{request.message}

【回答】"""
        
        # Step 5: LLM 呼び出し
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]
        
        response = agent_service.chat(
            messages=messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            stream=False,
        )
        
        answer = response.choices[0].message.content if response.choices else "回答を生成できませんでした"
        
        # Step 6: ソース参照情報の構築
        sources = [
            SourceReference(
                id=doc.get("id", ""),
                title=doc.get("title", ""),
                score=doc.get("score", 0.0),
            )
            for doc in search_results
        ]
        
        logger.info(f"RAG chat completed: answer length={len(answer)}, sources={len(sources)}")
        
        return RAGChatResponse(
            answer=answer,
            sources=sources,
            context_used=len(search_results),
            model=settings.AZURE_OPENAI_DEPLOYMENT_CHAT,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"RAG chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"RAG chat failed: {str(e)}")


@router.post("/chat/stream")
async def rag_chat_stream(
    request: RAGChatRequest,
    search_service: SearchService = Depends(get_search_service),
    agent_service: FoundryAgentService = Depends(get_agent_service),
):
    """
    RAG Chat ストリーミング版
    
    Server-Sent Events (SSE) 形式で回答をストリーミング配信
    """
    try:
        logger.info(f"RAG chat stream request: message='{request.message[:50]}...'")
        
        # Step 1: Embedding 生成
        query_embedding = agent_service.get_embedding(request.message)
        
        if not query_embedding:
            raise HTTPException(status_code=500, detail="Failed to generate embedding")
        
        # Step 2: ハイブリッド検索
        search_results = search_service.hybrid_search(
            query=request.message,
            embedding=query_embedding,
            top_k=request.top_k,
            filter_expression=request.filter,
        )
        
        # Step 3: コンテキスト構築
        if search_results:
            context_parts = []
            for i, doc in enumerate(search_results, 1):
                title = doc.get("title", "Untitled")
                content = doc.get("content", "")
                context_parts.append(f"【ソース{i}: {title}】\n{content}")
            
            context_text = "\n\n---\n\n".join(context_parts)
        else:
            context_text = "（関連するコンテキストが見つかりませんでした）"
        
        # Step 4: プロンプト構築
        system_prompt = request.system_prompt or DEFAULT_RAG_SYSTEM_PROMPT
        
        user_message = f"""以下のコンテキストを参照して、質問に回答してください。

【コンテキスト】
{context_text}

【質問】
{request.message}

【回答】"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]
        
        # Step 5: ストリーミングジェネレーター
        async def generate_stream() -> AsyncGenerator[str, None]:
            import json
            
            # まずソース情報を送信
            sources_data = {
                "type": "sources",
                "sources": [
                    {
                        "id": doc.get("id", ""),
                        "title": doc.get("title", ""),
                        "score": doc.get("score", 0.0),
                    }
                    for doc in search_results
                ],
                "context_used": len(search_results),
            }
            yield f"data: {json.dumps(sources_data, ensure_ascii=False)}\n\n"
            
            # 回答をストリーミング
            stream_response = agent_service.chat(
                messages=messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                stream=True,
            )
            
            for chunk in stream_response:
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    chunk_data = {"type": "content", "content": content}
                    yield f"data: {json.dumps(chunk_data, ensure_ascii=False)}\n\n"
            
            # 完了シグナル
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"RAG chat stream error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"RAG chat stream failed: {str(e)}")