from pydantic import BaseModel, Field
from typing import Optional, List

class ChatRequest(BaseModel):
    """チャットリクエストモデル"""
    message: str = Field(..., description="ユーザーメッセージ")
    stream: bool = Field(default=False, description="ストリーミング有効化")
    thread_id: Optional[str] = Field(default=None, description="会話スレッドID")

class ChatResponse(BaseModel):
    """チャットレスポンスモデル"""
    response: str = Field(..., description="エージェントの応答")
    conversation_id: str = Field(..., description="会話ID")
    assistant_id: str = Field(..., description="アシスタントID")

class ChatStreamResponse(BaseModel):
    """ストリーミングレスポンスモデル"""
    delta: str = Field(..., description="レスポンスの差分")
    conversation_id: str = Field(..., description="会話ID")
    is_final: bool = Field(default=False, description="最終チャンクかどうか")

class ToolInfo(BaseModel):
    """ツール情報モデル"""
    name: str = Field(..., description="ツール名")
    description: str = Field(..., description="ツールの説明")
    parameters: Optional[dict] = Field(default=None, description="ツールのパラメータ")
