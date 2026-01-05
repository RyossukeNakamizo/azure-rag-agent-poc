"""
OpenTelemetry Usage Examples

D28: 各サービス層でのトレース統合サンプルコード
"""
from typing import List, Dict, Any

from app.core.telemetry import (
    trace_search_operation,
    trace_openai_operation,
    trace_cosmos_operation,
    add_span_event,
    set_span_attributes,
)


# =============================================================================
# Search Service での使用例
# =============================================================================

async def example_search_service_with_tracing(query: str) -> List[Dict[str, Any]]:
    """
    Azure AI Search でのトレース統合例
    
    実際のコード（例: app/services/search_service.py）で使用:
    """
    with trace_search_operation(
        operation="hybrid_search",
        query=query,
        index_name="rag-docs-index"
    ) as span:
        # 検索実行前のイベント
        add_span_event(span, "search.started", {"query_length": len(query)})
        
        # 実際の検索処理（例）
        # results = await self.search_client.search(...)
        results = []  # Placeholder
        
        # 検索完了後の属性追加
        set_span_attributes(span, {
            "search.results_count": len(results),
            "search.latency_ms": 150,  # 実際は計測値
        })
        
        return results


# =============================================================================
# OpenAI Service での使用例
# =============================================================================

async def example_openai_service_with_tracing(
    messages: List[Dict[str, str]]
) -> str:
    """
    Azure OpenAI でのトレース統合例
    
    実際のコード（例: app/services/openai_service.py）で使用:
    """
    with trace_openai_operation(
        operation="chat",
        model="gpt-4o",
        prompt_tokens=500  # 事前計測済みの場合
    ) as span:
        # API呼び出し前のイベント
        add_span_event(span, "openai.request_started", {
            "message_count": len(messages)
        })
        
        # 実際のAPI呼び出し（例）
        # response = await self.client.chat.completions.create(...)
        response_text = "Example response"  # Placeholder
        
        # 完了後の属性追加
        set_span_attributes(span, {
            "openai.completion_tokens": 200,
            "openai.total_tokens": 700,
            "openai.response_length": len(response_text),
        })
        
        return response_text


# =============================================================================
# Cosmos DB Repository での使用例
# =============================================================================

async def example_cosmos_repository_with_tracing(
    conversation_id: str
) -> Dict[str, Any]:
    """
    Cosmos DB でのトレース統合例
    
    実際のコード（例: app/repositories/cosmos_repository.py）で使用:
    """
    with trace_cosmos_operation(
        operation="read",
        container="conversations",
        item_id=conversation_id
    ) as span:
        # DB操作前のイベント
        add_span_event(span, "cosmos.query_started")
        
        # 実際のCosmos DB操作（例）
        # item = await self.container.read_item(...)
        item = {"id": conversation_id}  # Placeholder
        
        # 完了後の属性追加
        set_span_attributes(span, {
            "cosmos.request_charge": 2.5,
            "cosmos.item_size_bytes": 1024,
        })
        
        return item


# =============================================================================
# RAGエンドポイントでの複合トレース例
# =============================================================================

async def example_rag_endpoint_with_tracing(query: str) -> Dict[str, Any]:
    """
    RAGエンドポイント全体でのトレース例
    
    FastAPIInstrumentor が自動的にリクエスト全体のspanを作成するため、
    個別操作のみをトレースすればよい。
    """
    # 1. 検索フェーズ
    with trace_search_operation("hybrid_search", query=query) as search_span:
        # 検索実行
        documents = []  # await search_service.search(query)
        add_span_event(search_span, "search.completed", {
            "docs_found": len(documents)
        })
    
    # 2. コンテキスト構築（トレース不要の軽量処理の場合）
    context = "\n".join([doc.get("content", "") for doc in documents])
    
    # 3. LLM生成フェーズ
    with trace_openai_operation("chat", model="gpt-4o") as openai_span:
        # プロンプト構築
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": f"Context: {context}\n\nQuestion: {query}"}
        ]
        
        # LLM呼び出し
        response = ""  # await openai_service.generate(messages)
        
        set_span_attributes(openai_span, {
            "openai.context_length": len(context),
            "openai.response_length": len(response),
        })
    
    # 4. 会話履歴保存（オプショナル）
    if True:  # settings.COSMOS_DB_ENABLED
        with trace_cosmos_operation("create", item_id="conv_123") as cosmos_span:
            # 保存処理
            # await cosmos_repo.save_conversation(...)
            add_span_event(cosmos_span, "conversation.saved")
    
    return {
        "answer": response,
        "sources": documents,
    }


# =============================================================================
# エラー処理とトレース
# =============================================================================

async def example_error_handling_with_tracing(query: str):
    """
    エラー発生時のトレース例
    
    trace_operation は自動的にエラーをspanに記録する
    """
    try:
        with trace_search_operation("hybrid_search", query=query) as span:
            # 検索実行
            raise Exception("Connection timeout")  # 例外発生
            
    except Exception as e:
        # span には自動的にエラー情報が記録される:
        # - span.status = ERROR
        # - span.events にexception情報が追加
        # - Application Insightsで "Failed Request" として表示
        
        # 必要に応じて追加のエラー処理
        print(f"Search failed: {e}")
        raise
