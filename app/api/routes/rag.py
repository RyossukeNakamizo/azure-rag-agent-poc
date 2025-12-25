"""
RAG API Routes

Phase 2-3: RAG エンドポイント実装
"""
import logging
import json
from typing import AsyncGenerator

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse

from app.core.config import get_settings, Settings
from app.services.search_service import SearchService
from app.services.foundry_agent import FoundryAgentService
from app.services.query_expansion_service import QueryExpansionService
from app.models.rag import (
    RAGSearchRequest,
    RAGSearchResponse,
    SearchResult,
    RAGChatRequest,
    RAGChatResponse,
    SourceReference,
    RAGHealthResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# デフォルトシステムプロンプト
DEFAULT_RAG_SYSTEM_PROMPT = """あなたはAzure技術の専門家です。

【コンテキスト評価基準】
以下の基準でコンテキストの関連性を判断してください：
1. 質問との直接的関連性（最重要）
   - 質問で尋ねられている技術要素が明示的に含まれているか
   - 実装手順や設定方法など、具体的な情報が含まれているか
2. 情報の新しさ・正確性
   - 最新のAPI仕様やベストプラクティスが反映されているか
   - 非推奨機能ではなく、現在推奨される方法が記載されているか
3. 具体的実装例の有無
   - コード例、CLIコマンド、設定値などの実践的情報があるか

【回答ルール】
1. 提供されたコンテキストのみを使用して回答する
2. コンテキストに情報がない、または不十分な場合：
   - 「提供されたコンテキストには[具体的な内容]に関する情報が含まれていません」と明示する
   - 推測や一般知識での補完は行わない
3. 複数ソースが矛盾する場合：
   - 両方の情報を提示し、「コンテキストに矛盾する情報があります」と明記する
   - 可能であれば、より新しい情報や詳細な情報を優先する旨を説明する
4. ソース引用は必須：
   - 回答の根拠となった箇所を「[出典: ドキュメントタイトル]」形式で明記する
   - 複数ソースを使用した場合は、それぞれを個別に引用する
5. 技術的正確性：
   - コマンド、設定値、APIエンドポイントなどは正確に記載する
   - 不確実な情報は「コンテキストでは明示されていませんが」と前置きする
6. 実用性重視：
   - 理論的説明だけでなく、実装手順や具体例を含める
   - トラブルシューティング情報があれば積極的に提供する
7. 日本語で回答する

【回答フォーマット】
- 簡潔な要約（1-2文）
- 詳細な説明
- 実装例（該当する場合）
- 参照元の明記"""

# グローバルインスタンス初期化
settings = get_settings()

_search_service = SearchService(
    endpoint=settings.AZURE_SEARCH_ENDPOINT,
    index_name=settings.AZURE_SEARCH_INDEX,
)

_agent_service = FoundryAgentService(
    azure_openai_endpoint=settings.AZURE_OPENAI_ENDPOINT,
    azure_openai_deployment=settings.AZURE_OPENAI_DEPLOYMENT,
)

# Query Expansion Service初期化
_query_expansion_service = QueryExpansionService()


def get_search_service():
    """SearchService 依存性注入"""
    if not _search_service:
        raise HTTPException(
            status_code=500, detail="SearchService not initialized"
        )
    return _search_service
def get_agent_service():
    """FoundryAgentService依存性注入"""
    if not _agent_service:
        raise HTTPException(
            status_code=500, detail="FoundryAgentService not initialized"
        )
    return _agent_service


def get_query_expansion_service():
    """QueryExpansionService依存性注入"""
    if not _query_expansion_service:
        raise HTTPException(
            status_code=500, detail="QueryExpansionService not initialized"
        )
    return _query_expansion_service




@router.get("/health", response_model=RAGHealthResponse)
async def health_check(
    search_service: SearchService = Depends(get_search_service),
    agent_service: FoundryAgentService = Depends(get_agent_service),
    settings: Settings = Depends(get_settings),
):
    """RAG システム Health Check"""
    search_status = "unknown"
    openai_status = "unknown"
    
    # Search サービス確認
    try:
        results = search_service.keyword_search("test", top_k=1)
        search_status = "healthy"
    except Exception as e:
        search_status = f"unhealthy: {str(e)[:50]}"
        logger.error(f"Search health check failed: {e}")
    
    # OpenAI サービス確認
    try:
        embedding = agent_service.get_embedding("test")
        if embedding and len(embedding) == 1536:
            openai_status = "healthy"
        else:
            openai_status = "unhealthy: invalid embedding"
    except Exception as e:
        openai_status = f"unhealthy: {str(e)[:50]}"
        logger.error(f"OpenAI health check failed: {e}")
    
    overall = "healthy" if search_status == "healthy" and openai_status == "healthy" else "degraded"
    
    return RAGHealthResponse(
        status=overall,
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
    """ハイブリッド検索（Vector + Keyword）"""
    try:
        logger.info(f"Search request: query='{request.query}', top_k={request.top_k}")
        
        # Embedding 生成
        query_embedding = agent_service.get_embedding(request.query)
        if not query_embedding:
            raise HTTPException(status_code=500, detail="Failed to generate embedding")
        
        # 検索実行
        raw_results = search_service.hybrid_search(
            query=request.query,
            embedding=query_embedding,
            top_k=request.top_k,
            filter_expression=request.filter,
        )
        
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
        
        return RAGSearchResponse(
            query=request.query,
            results=results,
            total_count=len(results),
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Search error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat", response_model=RAGChatResponse)
async def rag_chat(
    request: RAGChatRequest,
    search_service: SearchService = Depends(get_search_service),
    agent_service: FoundryAgentService = Depends(get_agent_service),
    query_expansion_service: QueryExpansionService = Depends(get_query_expansion_service),
    settings: Settings = Depends(get_settings),
):
    """RAG Chat（検索 + 回答生成）"""
    try:
        logger.info(f"RAG chat: message='{request.message[:50]}...', use_query_expansion={request.use_query_expansion}")
        
        # Step 0: Query Expansion
        expanded_queries = None
        if request.use_query_expansion:
            expanded_queries = query_expansion_service.expand_query(
                request.message,
                max_expansions=3
            )
            logger.info(f"Expanded queries: {expanded_queries}")
        else:
            expanded_queries = [request.message]
        
        # Step 1: Embedding（複数クエリ対応）
        all_search_results = []
        
        for query in expanded_queries:
            query_embedding = agent_service.get_embedding(query)
            if not query_embedding:
                continue
            
            # Step 2: 検索
            results = search_service.hybrid_search(
                query=query,
                embedding=query_embedding,
                top_k=request.top_k // len(expanded_queries),
                filter_expression=request.filter,
            )
            all_search_results.extend(results)
        
        # Step 2.5: 重複排除 + スコアソート
        unique_results = {}
        for doc in all_search_results:
            doc_id = doc.get("id", "")
            if doc_id not in unique_results or doc.get("score", 0) > unique_results[doc_id].get("score", 0):
                unique_results[doc_id] = doc
        
        search_results = sorted(
            unique_results.values(),
            key=lambda x: x.get("score", 0),
            reverse=True
        )[:request.top_k]
        
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
        
        # Step 4: プロンプト
        system_prompt = request.system_prompt or DEFAULT_RAG_SYSTEM_PROMPT
        user_message = f"""以下のコンテキストを参照して、質問に回答してください。

【コンテキスト】
{context_text}

【質問】
{request.message}"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]
        
        # Step 5: LLM呼び出し
        response = agent_service.chat(
            messages=messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )
        
        answer = response.get("content", "")
        
        # Step 6: ソース参照構築
        sources = [
            SourceReference(
                id=doc.get("id", ""),
                title=doc.get("title", ""),
                score=doc.get("score", 0.0),
            )
            for doc in search_results
        ]
        
        return RAGChatResponse(
            answer=answer,
            sources=sources,
            context_used=len(search_results),
            model=settings.AZURE_OPENAI_DEPLOYMENT_CHAT,
            expanded_queries=expanded_queries if request.use_query_expansion else None,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"RAG chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/stream")
async def rag_chat_stream(
    request: RAGChatRequest,
    search_service: SearchService = Depends(get_search_service),
    agent_service: FoundryAgentService = Depends(get_agent_service),
):
    """RAG Chat ストリーミング版"""
    try:
        # Embedding
        query_embedding = agent_service.get_embedding(request.message)
        if not query_embedding:
            raise HTTPException(status_code=500, detail="Failed to generate embedding")
        
        # 検索
        search_results = search_service.hybrid_search(
            query=request.message,
            embedding=query_embedding,
            top_k=request.top_k,
            filter_expression=request.filter,
        )
        
        # コンテキスト
        if search_results:
            context_parts = []
            for i, doc in enumerate(search_results, 1):
                title = doc.get("title", "Untitled")
                content = doc.get("content", "")
                context_parts.append(f"【ソース{i}: {title}】\n{content}")
            context_text = "\n\n---\n\n".join(context_parts)
        else:
            context_text = "（関連するコンテキストが見つかりませんでした）"
        
        system_prompt = request.system_prompt or DEFAULT_RAG_SYSTEM_PROMPT
        user_message = f"""以下のコンテキストを参照して、質問に回答してください。

【コンテキスト】
{context_text}

【質問】
{request.message}"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]
        
        async def generate() -> AsyncGenerator[str, None]:
            # ソース情報送信
            sources_data = {
                "type": "sources",
                "sources": [
                    {"id": doc.get("id", ""), "title": doc.get("title", ""), "score": doc.get("score", 0.0)}
                    for doc in search_results
                ],
                "context_used": len(search_results),
            }
            yield f"data: {json.dumps(sources_data, ensure_ascii=False)}\n\n"
            
            # ストリーミング
            stream = agent_service.chat(
                messages=messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                stream=True,
            )
            
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    yield f"data: {json.dumps({'type': 'content', 'content': content}, ensure_ascii=False)}\n\n"
            
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
        
        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"RAG stream error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))