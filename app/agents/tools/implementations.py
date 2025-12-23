"""
Tool Implementations

Function Calling Agentで使用する各ツールの実装。
各関数は辞書形式で結果を返す。
"""
import os
import math
from datetime import datetime
from typing import Dict, Any, Optional
import pytz

from azure.identity import DefaultAzureCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()


# =============================================================================
# Search Documents Tool
# =============================================================================

def search_documents_impl(
    query: str,
    top_k: int = 5,
    filters: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    ドキュメント検索ツール実装
    
    Args:
        query: 検索クエリ
        top_k: 取得件数
        filters: 検索フィルター
    
    Returns:
        {
            "results": [
                {"title": "...", "content": "...", "score": 0.95},
                ...
            ],
            "total": 3
        }
    """
    try:
        # Azure AI Search接続
        credential = DefaultAzureCredential()
        search_client = SearchClient(
            endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
            index_name=os.getenv("AZURE_SEARCH_INDEX", "rag-docs-index"),
            credential=credential
        )
        
        # フィルター構築
        filter_expr = None
        if filters:
            filter_parts = []
            if "category" in filters:
                filter_parts.append(f"category eq '{filters['category']}'")
            if "department" in filters:
                filter_parts.append(f"department eq '{filters['department']}'")
            
            if filter_parts:
                filter_expr = " and ".join(filter_parts)
        
        # 埋め込み生成（ベクトル検索用）
        openai_client = AzureOpenAI(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            azure_ad_token_provider=lambda: credential.get_token(
                "https://cognitiveservices.azure.com/.default"
            ).token,
            api_version="2024-10-01-preview"
        )
        
        embedding_response = openai_client.embeddings.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT_EMBEDDING", "text-embedding-ada-002"),
            input=query
        )
        query_embedding = embedding_response.data[0].embedding
        
        # ハイブリッド検索
        vector_query = VectorizedQuery(
            vector=query_embedding,
            k_nearest_neighbors=top_k,
            fields="contentVector"
        )
        
        results = search_client.search(
            search_text=query,
            vector_queries=[vector_query],
            filter=filter_expr,
            select=["title", "content", "category", "source"],
            top=top_k
        )
        
        # 結果整形
        documents = [
            {
                "title": r.get("title", ""),
                "content": r.get("content", "")[:500],  # 500文字まで
                "category": r.get("category", ""),
                "source": r.get("source", ""),
                "score": r.get("@search.score", 0)
            }
            for r in results
        ]
        
        return {
            "results": documents,
            "total": len(documents),
            "query": query,
            "filters": filters or {}
        }
    
    except Exception as e:
        return {
            "error": str(e),
            "results": [],
            "total": 0
        }


# =============================================================================
# Calculator Tool
# =============================================================================

def calculate_impl(expression: str) -> Dict[str, Any]:
    """
    数値計算ツール実装
    
    Args:
        expression: 評価する数式
    
    Returns:
        {"result": 42, "expression": "6 * 7"}
    """
    try:
        # セキュリティ: 許可された関数のみ
        allowed_names = {
            "abs": abs,
            "round": round,
            "pow": pow,
            "sqrt": math.sqrt,
            "sin": math.sin,
            "cos": math.cos,
            "tan": math.tan,
            "log": math.log,
            "exp": math.exp,
            "pi": math.pi,
            "e": math.e
        }
        
        # eval実行（制限付き）
        result = eval(expression, {"__builtins__": {}}, allowed_names)
        
        return {
            "result": result,
            "expression": expression
        }
    
    except Exception as e:
        return {
            "error": str(e),
            "expression": expression,
            "hint": "使用可能な関数: abs, round, pow, sqrt, sin, cos, tan, log, exp, pi, e"
        }


# =============================================================================
# DateTime Tool
# =============================================================================

def get_current_datetime_impl(
    timezone: str = "Asia/Tokyo",
    format: str = "japanese"
) -> Dict[str, Any]:
    """
    現在日時取得ツール実装
    
    Args:
        timezone: タイムゾーン
        format: 出力フォーマット
    
    Returns:
        {
            "datetime": "2025-12-22 14:30:00",
            "timezone": "Asia/Tokyo",
            "timestamp": 1703232600
        }
    """
    try:
        tz = pytz.timezone(timezone)
        now = datetime.now(tz)
        
        # フォーマット選択
        if format == "iso":
            formatted = now.isoformat()
        elif format == "japanese":
            formatted = now.strftime("%Y年%m月%d日 %H時%M分%S秒")
        elif format == "unix":
            formatted = str(int(now.timestamp()))
        else:
            formatted = now.strftime("%Y-%m-%d %H:%M:%S")
        
        return {
            "datetime": formatted,
            "timezone": timezone,
            "timestamp": int(now.timestamp()),
            "iso_format": now.isoformat(),
            "day_of_week": now.strftime("%A"),
            "day_of_week_ja": ["月", "火", "水", "木", "金", "土", "日"][now.weekday()]
        }
    
    except Exception as e:
        return {
            "error": str(e),
            "timezone": timezone
        }


# =============================================================================
# Equipment Status Tool (工場向けスタブ)
# =============================================================================

def get_equipment_status_impl(
    equipment_id: str,
    include_history: bool = False
) -> Dict[str, Any]:
    """
    設備状態確認ツール実装（スタブ）
    
    実際の実装では、MES（Manufacturing Execution System）APIや
    IoTプラットフォームと連携する。
    
    Args:
        equipment_id: 設備ID
        include_history: 履歴含む
    
    Returns:
        {
            "equipment_id": "LINE-A-01",
            "status": "running",
            "uptime_hours": 12.5,
            "error_count": 0
        }
    """
    # スタブデータ
    stub_data = {
        "LINE-A-01": {
            "status": "running",
            "uptime_hours": 12.5,
            "production_count": 1250,
            "error_count": 0,
            "last_maintenance": "2025-12-15",
            "next_maintenance": "2026-01-15"
        },
        "ROBOT-B-03": {
            "status": "warning",
            "uptime_hours": 8.2,
            "production_count": 820,
            "error_count": 2,
            "last_error": "センサー通信タイムアウト",
            "last_maintenance": "2025-12-10",
            "next_maintenance": "2026-01-10"
        },
        "PRESS-C-05": {
            "status": "stopped",
            "uptime_hours": 0,
            "production_count": 0,
            "error_count": 1,
            "last_error": "油圧系統異常",
            "stopped_at": "2025-12-22 10:30:00",
            "last_maintenance": "2025-12-01",
            "next_maintenance": "2026-01-01"
        }
    }
    
    if equipment_id not in stub_data:
        return {
            "error": f"Equipment not found: {equipment_id}",
            "available_equipment": list(stub_data.keys())
        }
    
    result = {
        "equipment_id": equipment_id,
        **stub_data[equipment_id],
        "retrieved_at": datetime.now().isoformat()
    }
    
    if include_history:
        # スタブ履歴データ
        result["history_24h"] = [
            {"time": "2025-12-22 12:00", "status": "running", "production": 120},
            {"time": "2025-12-22 11:00", "status": "running", "production": 125},
            {"time": "2025-12-22 10:00", "status": "running", "production": 118}
        ]
    
    return result


if __name__ == "__main__":
    # 各ツールの動作確認
    print("=== Search Documents ===")
    print(search_documents_impl("Azure AI Search", top_k=3))
    
    print("\n=== Calculate ===")
    print(calculate_impl("sqrt(16) + 2 ** 3"))
    
    print("\n=== Current DateTime ===")
    print(get_current_datetime_impl())
    
    print("\n=== Equipment Status ===")
    print(get_equipment_status_impl("LINE-A-01", include_history=True))
