"""
Conversation Data Models

D24: 会話履歴管理用Pydanticモデル
"""
from datetime import datetime
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class MessageMetadata(BaseModel):
    """メッセージメタデータ"""
    model: str = Field(default="gpt-4o", description="使用LLMモデル")
    tokens_used: Optional[int] = Field(default=None, description="消費トークン数")
    sources_count: int = Field(default=0, description="参照ソース数")
    latency_ms: Optional[int] = Field(default=None, description="レイテンシ（ミリ秒）")
    query_expansion: bool = Field(default=False, description="Query Expansion使用フラグ")


class SourceInfo(BaseModel):
    """ソース参照情報"""
    id: str = Field(..., description="ドキュメントID")
    title: str = Field(default="", description="タイトル")
    score: float = Field(default=0.0, description="関連度スコア")


class ConversationMessage(BaseModel):
    """会話メッセージ（Cosmos DBドキュメント）"""
    id: str = Field(default_factory=lambda: f"msg_{uuid4().hex[:12]}", description="メッセージID")
    session_id: str = Field(..., description="セッションID（パーティションキー）")
    user_id: Optional[str] = Field(default=None, description="ユーザーID")
    role: str = Field(..., description="ロール（user/assistant）")
    content: str = Field(..., description="メッセージ内容")
    metadata: MessageMetadata = Field(default_factory=MessageMetadata, description="メタデータ")
    sources: list[SourceInfo] = Field(default_factory=list, description="参照ソース")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="作成日時")
    ttl: int = Field(default=2592000, description="TTL（秒）: デフォルト30日")

    def to_cosmos_dict(self) -> dict:
        """Cosmos DB用辞書変換"""
        return {
            "id": self.id,
            "sessionId": self.session_id,  # Cosmos DBのパーティションキー形式
            "userId": self.user_id,
            "role": self.role,
            "content": self.content,
            "metadata": self.metadata.model_dump(),
            "sources": [s.model_dump() for s in self.sources],
            "createdAt": self.created_at.isoformat() + "Z",
            "ttl": self.ttl,
        }

    @classmethod
    def from_cosmos_dict(cls, data: dict) -> "ConversationMessage":
        """Cosmos DBドキュメントからインスタンス生成"""
        return cls(
            id=data.get("id", ""),
            session_id=data.get("sessionId", ""),
            user_id=data.get("userId"),
            role=data.get("role", ""),
            content=data.get("content", ""),
            metadata=MessageMetadata(**data.get("metadata", {})),
            sources=[SourceInfo(**s) for s in data.get("sources", [])],
            created_at=datetime.fromisoformat(data.get("createdAt", "").replace("Z", "+00:00")),
            ttl=data.get("ttl", 2592000),
        )


class ConversationSession(BaseModel):
    """会話セッション"""
    id: str = Field(default_factory=lambda: f"sess_{uuid4().hex[:12]}", description="セッションID")
    session_id: str = Field(default="", description="セッションID（パーティションキー）")
    user_id: Optional[str] = Field(default=None, description="ユーザーID")
    type: str = Field(default="session", description="ドキュメントタイプ")
    title: str = Field(default="New Conversation", description="会話タイトル")
    message_count: int = Field(default=0, description="メッセージ数")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="作成日時")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="更新日時")
    status: str = Field(default="active", description="ステータス（active/archived）")
    ttl: int = Field(default=-1, description="TTL（-1で無期限）")

    def __init__(self, **data):
        super().__init__(**data)
        if not self.session_id:
            self.session_id = self.id

    def to_cosmos_dict(self) -> dict:
        """Cosmos DB用辞書変換"""
        return {
            "id": self.id,
            "sessionId": self.session_id,
            "userId": self.user_id,
            "type": self.type,
            "title": self.title,
            "messageCount": self.message_count,
            "createdAt": self.created_at.isoformat() + "Z",
            "updatedAt": self.updated_at.isoformat() + "Z",
            "status": self.status,
            "ttl": self.ttl,
        }


class ConversationTurn(BaseModel):
    """会話ターン（ユーザー + アシスタント）"""
    user_message: ConversationMessage
    assistant_message: ConversationMessage
    turn_number: int = Field(default=1, description="ターン番号")


# API用モデル拡張
class ChatWithHistoryRequest(BaseModel):
    """履歴付きチャットリクエスト"""
    message: str = Field(..., description="ユーザーメッセージ", min_length=1, max_length=4000)
    session_id: Optional[str] = Field(default=None, description="セッションID（新規セッションはNone）")
    include_history: bool = Field(default=True, description="履歴を含むか")
    max_history_turns: int = Field(default=5, ge=0, le=20, description="履歴の最大ターン数")
    top_k: int = Field(default=5, ge=1, le=10, description="コンテキスト取得件数")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="生成温度")
    max_tokens: int = Field(default=1000, ge=100, le=4000, description="最大トークン数")
    system_prompt: Optional[str] = Field(default=None, description="カスタムシステムプロンプト")
    filter: Optional[str] = Field(default=None, description="検索フィルター")
    use_query_expansion: bool = Field(default=False, description="Query Expansion有効化")


class ChatWithHistoryResponse(BaseModel):
    """履歴付きチャットレスポンス"""
    answer: str = Field(..., description="生成された回答")
    session_id: str = Field(..., description="セッションID")
    turn_number: int = Field(..., description="現在のターン番号")
    sources: list[SourceInfo] = Field(default_factory=list, description="参照ソース")
    context_used: int = Field(..., description="使用コンテキスト数")
    history_used: int = Field(default=0, description="使用した履歴ターン数")
    model: str = Field(..., description="使用モデル")
