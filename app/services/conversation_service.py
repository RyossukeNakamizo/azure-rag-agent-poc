"""
Conversation Service

D24: 会話管理ビジネスロジック
D27: エラーハンドリング強化 - グレースフルデグラデーション対応
"""
import logging
from typing import Optional
from datetime import datetime
from uuid import uuid4

from app.repositories.cosmos_repository import CosmosRepository
from app.models.conversation import (
    ConversationMessage,
    ConversationSession,
    MessageMetadata,
    SourceInfo,
)

logger = logging.getLogger(__name__)


class ConversationService:
    """
    会話管理サービス
    
    D27強化ポイント:
    - リポジトリ操作失敗時のフォールバック動作
    - 一貫したエラーハンドリング
    - サービス利用可否の明示的管理
    
    セッション管理、履歴取得、メッセージ保存を担当。
    """
    
    def __init__(self, repository: CosmosRepository):
        """
        初期化
        
        Args:
            repository: Cosmos DBリポジトリ
        """
        self._repo = repository
        logger.info("ConversationService initialized")
    
    @property
    def is_available(self) -> bool:
        """サービスが利用可能かどうか"""
        return self._repo.is_available
    
    # =========================================================================
    # Session Management
    # =========================================================================
    
    def start_new_session(self, user_id: Optional[str] = None) -> str:
        """
        新しいセッションを開始
        
        D27: リポジトリ障害時もセッションIDを返す（履歴なしモード）
        
        Args:
            user_id: ユーザーID（オプション）
            
        Returns:
            新しいセッションID
        """
        session = ConversationSession(
            user_id=user_id,
            title="New Conversation",
        )
        
        # リポジトリが利用可能なら永続化を試行
        if self._repo.is_available:
            session_id = self._repo.create_session_sync(session)
            if session_id:
                logger.info(f"Started new session (persisted): {session_id}")
                return session_id
            else:
                logger.warning(f"Failed to persist session, using transient ID: {session.id}")
        else:
            logger.info(f"Cosmos DB unavailable, using transient session ID: {session.id}")
        
        return session.id
    
    def get_or_create_session(self, session_id: Optional[str] = None, user_id: Optional[str] = None) -> str:
        """
        セッションを取得または作成
        
        Args:
            session_id: 既存セッションID（Noneで新規作成）
            user_id: ユーザーID
            
        Returns:
            セッションID
        """
        if session_id:
            logger.info(f"Using existing session: {session_id}")
            return session_id
        
        return self.start_new_session(user_id)
    
    # =========================================================================
    # Message Operations
    # =========================================================================
    
    def add_turn(
        self,
        session_id: str,
        user_message: str,
        assistant_message: str,
        sources: Optional[list[dict]] = None,
        metadata: Optional[dict] = None,
        user_id: Optional[str] = None,
    ) -> tuple[Optional[str], Optional[str]]:
        """
        会話ターン（ユーザー + アシスタント）を追加
        
        D27: 保存失敗時は(None, None)を返し、RAG機能は継続
        
        Args:
            session_id: セッションID
            user_message: ユーザーメッセージ
            assistant_message: アシスタントメッセージ
            sources: 参照ソース
            metadata: メタデータ
            user_id: ユーザーID
            
        Returns:
            (user_msg_id, assistant_msg_id) - 失敗時は(None, None)
        """
        if not self._repo.is_available:
            logger.warning("Cosmos DB unavailable, skipping conversation turn persistence")
            return (None, None)
        
        now = datetime.utcnow()
        
        # ユーザーメッセージ
        user_msg = ConversationMessage(
            session_id=session_id,
            user_id=user_id,
            role="user",
            content=user_message,
            created_at=now,
        )
        
        # アシスタントメッセージ
        source_infos = [SourceInfo(**s) for s in (sources or [])]
        meta = MessageMetadata(**(metadata or {}))
        
        assistant_msg = ConversationMessage(
            session_id=session_id,
            user_id=user_id,
            role="assistant",
            content=assistant_message,
            sources=source_infos,
            metadata=meta,
            created_at=now,
        )
        
        user_msg_id = self._repo.create_message_sync(user_msg)
        assistant_msg_id = self._repo.create_message_sync(assistant_msg)
        
        if user_msg_id and assistant_msg_id:
            logger.info(f"Added turn to session {session_id}: user={user_msg_id}, assistant={assistant_msg_id}")
        else:
            logger.warning(f"Failed to persist conversation turn for session {session_id}")
        
        return (user_msg_id, assistant_msg_id)
    
    def get_context_messages(
        self,
        session_id: str,
        max_turns: int = 5,
    ) -> list[dict]:
        """
        LLMコンテキスト用のメッセージ履歴を取得
        
        D27: 取得失敗時は空リストを返す（履歴なしモード）
        
        Args:
            session_id: セッションID
            max_turns: 最大ターン数（1ターン = user + assistant）
            
        Returns:
            OpenAI API形式のメッセージリスト（エラー時は空リスト）
        """
        if not self._repo.is_available:
            logger.info(f"Cosmos DB unavailable, returning empty history for session: {session_id}")
            return []
        
        # 最新のメッセージを取得（max_turns * 2 = user + assistant）
        messages = self._repo.get_session_history_sync(
            session_id=session_id,
            limit=max_turns * 2,
        )
        
        if not messages:
            return []
        
        # 時系列順に並べ替え（古い順）
        messages = sorted(messages, key=lambda m: m.created_at)
        
        # OpenAI形式に変換
        context = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
        
        logger.info(f"Retrieved {len(context)} context messages for session: {session_id}")
        return context
    
    def get_turn_count(self, session_id: str) -> int:
        """
        セッションのターン数を取得
        
        D27: 取得失敗時は0を返す
        
        Args:
            session_id: セッションID
            
        Returns:
            ターン数（メッセージ数 / 2）、エラー時は0
        """
        if not self._repo.is_available:
            return 0
        
        count = self._repo.get_message_count_sync(session_id)
        return count // 2
    
    # =========================================================================
    # Utility
    # =========================================================================
    
    def health_check(self) -> dict:
        """
        ヘルスチェック
        
        Returns:
            ステータス情報
        """
        repo_health = self._repo.health_check()
        
        return {
            **repo_health,
            "service_available": self.is_available,
        }
