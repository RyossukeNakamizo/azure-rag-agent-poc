"""
RAG API Routes

Phase 2-3: RAG エンドポイント実装
D24: Cosmos DB会話履歴統合
"""
import logging
import json
from typing import AsyncGenerator, Optional

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
from app.models.conversation import (
    ChatWithHistoryRequest,
    ChatWithHistoryResponse,
    SourceInfo,
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

# 会話履歴を考慮したシステムプロンプト
MULTI_TURN_SYSTEM_PROMPT = """あなたはAzure技術の専門家です。

【会話の継続性】
- 過去の会話履歴を参照して、文脈に沿った回答を提供してください
- 前の質問で言及された技術やトピックについては、明示的な繰り返しを避けてください
- 「それ」「その」などの指示語が使われた場合は、会話履歴から参照対象を特定してください

【コンテキスト評価基準】
以下の基準でコンテキストの関連性を判断してください：
1. 質問との直接的関連性（最重要）
2. 情報の新しさ・正確性
3. 具体的実装例の有無

【回答ルール】
1. 提供されたコンテキストと会話履歴を使用して回答する
2. コンテキストに情報がない場合は明示する
3. ソース引用は必須
4. 日本語で回答する"""

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

_query_expansion_service = QueryExpansionService()

# Cosmos DB関連（条件付き初期化）
_conversation_service = None

def _init_conversation_service():
    """ConversationServiceの遅延初期化"""
    global _conversation_service
    if _conversation_service is not None:
        return _conversation_service
    
    if not settings.COSMOS_DB_ENABLED:
        logger.info("Cosmos DB is disabled. Conversation history will not be persisted.")
        return None
    
    try:
        from app.repositories.cosmos_repository import CosmosRepository
        from app.services.conversation_service import ConversationService
        
        repo = CosmosRepository(
            endpoint=settings.AZURE_COSMOS_ENDPOINT,
            database_name=settings.AZURE_COSMOS_DATABASE,
            container_name=settings.AZURE_COSMOS_CONTAINER,
            connection_string=settings.AZURE_COSMOS_CONNECTION_STRING,
        )
        _conversation_service = ConversationService(repository=repo)
        logger.info("ConversationService initialized successfully")
        return _conversation_service
    except Exception as e:
        logger.warning(f"Failed to initialize ConversationService: {e}. Continuing without conversation history.")
        return None


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


def get_conversation_service():
    """ConversationService依存性注入（オプショナル）"""
    return _init_conversation_service()


@router.get("/health", response_model=RAGHealthResponse)
async def health_check(
    search_service: SearchService = Depends(get_search_service),
    agent_service: FoundryAgentService = Depends(get_agent_service),
    settings: Settings = Depends(get_settings),
):
    """
    RAG システム Health Check
    
    D27: グレースフルデグラデーション対応
    - healthy: 全コアサービス正常
    - degraded: オプショナルサービス障害（RAG機能は継続）
    - unhealthy: コアサービス障害
    """
    search_status = "unknown"
    openai_status = "unknown"
    cosmos_status = "disabled"
    degraded_services = []
    
    # Search サービス確認（コア）
    try:
        results = search_service.keyword_search("test", top_k=1)
        search_status = "healthy"
    except Exception as e:
        search_status = f"unhealthy: {str(e)[:50]}"
        logger.error(f"Search health check failed: {e}")
    
    # OpenAI サービス確認（コア）
    try:
        embedding = agent_service.get_embedding("test")
        if embedding and len(embedding) == 1536:
            openai_status = "healthy"
        else:
            openai_status = "unhealthy: invalid embedding"
    except Exception as e:
        openai_status = f"unhealthy: {str(e)[:50]}"
        logger.error(f"OpenAI health check failed: {e}")
    
    # Cosmos DB確認（オプショナル）
    conv_service = get_conversation_service()
    if conv_service:
        try:
            cosmos_health = conv_service.health_check()
            cosmos_status = cosmos_health.get("status", "unknown")
            
            # オプショナルサービスの障害を記録
            if cosmos_status != "healthy":
                degraded_services.append("cosmos_db")
        except Exception as e:
            cosmos_status = f"unhealthy: {str(e)[:50]}"
            degraded_services.append("cosmos_db")
            logger.warning(f"Cosmos DB health check failed (optional service): {e}")
    
    # 全体ステータス判定
    core_healthy = search_status == "healthy" and openai_status == "healthy"
    
    if core_healthy and not degraded_services:
        overall = "healthy"
        message = "All services operational"
    elif core_healthy and degraded_services:
        overall = "degraded"
        message = f"Core services healthy, optional services degraded: {', '.join(degraded_services)}"
    else:
        overall = "unhealthy"
        unhealthy_cores = []
        if search_status != "healthy":
            unhealthy_cores.append("search")
        if openai_status != "healthy":
            unhealthy_cores.append("openai")
        message = f"Core services unhealthy: {', '.join(unhealthy_cores)}"
    
    return RAGHealthResponse(
        status=overall,
        search_service=search_status,
        index_name=settings.AZURE_SEARCH_INDEX,
        openai_service=openai_status,
        cosmos_db=cosmos_status,
        degraded_services=degraded_services if degraded_services else None,
        message=message,
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
        response = agent_service.chat_with_messages(
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


@router.post("/chat/with-history", response_model=ChatWithHistoryResponse)
async def rag_chat_with_history(
    request: ChatWithHistoryRequest,
    search_service: SearchService = Depends(get_search_service),
    agent_service: FoundryAgentService = Depends(get_agent_service),
    query_expansion_service: QueryExpansionService = Depends(get_query_expansion_service),
    settings: Settings = Depends(get_settings),
):
    """
    RAG Chat with Conversation History（D24新規追加）
    
    会話履歴を含むマルチターン対話をサポート。
    Cosmos DBが有効な場合、会話履歴が永続化される。
    """
    try:
        logger.info(f"RAG chat with history: message='{request.message[:50]}...', session_id={request.session_id}")
        
        conv_service = get_conversation_service()
        
        # Step 0: セッション管理
        session_id = request.session_id
        history_messages = []
        turn_number = 1
        
        if conv_service:
            session_id = conv_service.get_or_create_session(request.session_id)
            
            # 履歴取得
            if request.include_history and request.max_history_turns > 0:
                history_messages = conv_service.get_context_messages(
                    session_id=session_id,
                    max_turns=request.max_history_turns,
                )
            
            turn_number = conv_service.get_turn_count(session_id) + 1
        else:
            # Cosmos DB無効時はセッションIDを生成のみ
            if not session_id:
                from uuid import uuid4
                session_id = f"sess_{uuid4().hex[:12]}"
        
        # Step 1: Query Expansion
        expanded_queries = [request.message]
        if request.use_query_expansion:
            expanded_queries = query_expansion_service.expand_query(
                request.message,
                max_expansions=3
            )
        
        # Step 2: 検索
        all_search_results = []
        for query in expanded_queries:
            query_embedding = agent_service.get_embedding(query)
            if not query_embedding:
                continue
            
            results = search_service.hybrid_search(
                query=query,
                embedding=query_embedding,
                top_k=request.top_k // len(expanded_queries),
                filter_expression=request.filter,
            )
            all_search_results.extend(results)
        
        # 重複排除 + スコアソート
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
        
        # Step 4: メッセージ構築（履歴含む）
        system_prompt = request.system_prompt or (
            MULTI_TURN_SYSTEM_PROMPT if history_messages else DEFAULT_RAG_SYSTEM_PROMPT
        )
        
        messages = [{"role": "system", "content": system_prompt}]
        
        # 会話履歴を追加
        messages.extend(history_messages)
        
        # 現在の質問とコンテキスト
        user_message = f"""以下のコンテキストを参照して、質問に回答してください。

【コンテキスト】
{context_text}

【質問】
{request.message}"""
        
        messages.append({"role": "user", "content": user_message})
        
        # Step 5: LLM呼び出し
        response = agent_service.chat_with_messages(
            messages=messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )
        
        answer = response.get("content", "")
        
        # Step 6: 会話履歴に保存
        if conv_service:
            try:
                sources_dict = [
                    {"id": doc.get("id", ""), "title": doc.get("title", ""), "score": doc.get("score", 0.0)}
                    for doc in search_results
                ]
                conv_service.add_turn(
                    session_id=session_id,
                    user_message=request.message,
                    assistant_message=answer,
                    sources=sources_dict,
                    metadata={
                        "model": settings.AZURE_OPENAI_DEPLOYMENT_CHAT,
                        "sources_count": len(search_results),
                        "query_expansion": request.use_query_expansion,
                    },
                )
            except Exception as e:
                logger.warning(f"Failed to save conversation turn: {e}")
        
        # Step 7: レスポンス構築
        sources = [
            SourceInfo(
                id=doc.get("id", ""),
                title=doc.get("title", ""),
                score=doc.get("score", 0.0),
            )
            for doc in search_results
        ]
        
        return ChatWithHistoryResponse(
            answer=answer,
            session_id=session_id,
            turn_number=turn_number,
            sources=sources,
            context_used=len(search_results),
            history_used=len(history_messages) // 2,
            model=settings.AZURE_OPENAI_DEPLOYMENT_CHAT,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"RAG chat with history error: {e}", exc_info=True)
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
            stream = agent_service.chat_with_messages(
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
