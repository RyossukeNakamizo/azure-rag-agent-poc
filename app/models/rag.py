"""
RAG API Schemas

Phase 2-3: RAG エンドポイント用 Pydantic モデル定義
D22-1: Query Expansion対応
"""
from pydantic import BaseModel, Field
from typing import Optional


class RAGSearchRequest(BaseModel):
    """ハイブリッド検索リクエスト"""
    query: str = Field(..., description="検索クエリ", min_length=1, max_length=1000)
    top_k: int = Field(default=5, ge=1, le=20, description="取得件数")
    filter: Optional[str] = Field(default=None, description="OData フィルター式")


class SearchResult(BaseModel):
    """検索結果アイテム"""
    id: str = Field(..., description="ドキュメントID")
    title: str = Field(default="", description="タイトル")
    content: str = Field(default="", description="コンテンツ")
    chunk_id: Optional[str] = Field(default=None, description="チャンクID")
    score: float = Field(..., description="検索スコア")


class RAGSearchResponse(BaseModel):
    """ハイブリッド検索レスポンス"""
    query: str = Field(..., description="実行したクエリ")
    results: list[SearchResult] = Field(default_factory=list, description="検索結果")
    total_count: int = Field(..., description="取得件数")


class RAGChatRequest(BaseModel):
    """RAG Chat リクエスト"""
    message: str = Field(..., description="ユーザーメッセージ", min_length=1, max_length=4000)
    top_k: int = Field(default=5, ge=1, le=10, description="コンテキスト取得件数")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="生成温度")
    max_tokens: int = Field(default=1000, ge=100, le=4000, description="最大トークン数")
    system_prompt: Optional[str] = Field(default=None, description="カスタムシステムプロンプト")
    filter: Optional[str] = Field(default=None, description="検索フィルター")
    use_query_expansion: bool = Field(
        default=False,
        description="Query Expansionを有効化（+$0.001/query、Relevance改善）"
    )


class SourceReference(BaseModel):
    """ソース参照情報"""
    id: str = Field(..., description="ドキュメントID")
    title: str = Field(default="", description="タイトル")
    score: float = Field(..., description="関連度スコア")


class RAGChatResponse(BaseModel):
    """RAG Chat レスポンス"""
    answer: str = Field(..., description="生成された回答")
    sources: list[SourceReference] = Field(default_factory=list, description="参照ソース")
    context_used: int = Field(..., description="使用したコンテキスト数")
    model: str = Field(..., description="使用モデル")
    expanded_queries: Optional[list[str]] = Field(
        default=None,
        description="展開されたクエリ（use_query_expansion=true時のみ）"
    )


class RAGHealthResponse(BaseModel):
    """RAG Health Check レスポンス"""
    status: str = Field(..., description="ステータス")
    search_service: str = Field(..., description="Search サービス状態")
    index_name: str = Field(..., description="使用インデックス名")
    openai_service: str = Field(..., description="OpenAI サービス状態")
