"""
Conversation Service

D24: 会話管理ビジネスロジック
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
    
    # =========================================================================
    # Session Management
    # =========================================================================
    
    def start_new_session(self, user_id: Optional[str] = None) -> str:
        """
        新しいセッションを開始
        
        Args:
            user_id: ユーザーID（オプション）
            
        Returns:
            新しいセッションID
        """
        session = ConversationSession(
            user_id=user_id,
            title="New Conversation",
        )
        
        try:
            session_id = self._repo.create_session_sync(session)
            logger.info(f"Started new session: {session_id}")
            return session_id
        except Exception as e:
            logger.error(f"Failed to start session: {e}")
            # セッション作成に失敗してもIDは返す（履歴なし動作を許容）
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
            # 既存セッション確認（存在チェックは省略、メッセージ保存時に確認）
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
    ) -> tuple[str, str]:
        """
        会話ターン（ユーザー + アシスタント）を追加
        
        Args:
            session_id: セッションID
            user_message: ユーザーメッセージ
            assistant_message: アシスタントメッセージ
            sources: 参照ソース
            metadata: メタデータ
            user_id: ユーザーID
            
        Returns:
            (user_msg_id, assistant_msg_id)
        """
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
        
        try:
            user_msg_id = self._repo.create_message_sync(user_msg)
            assistant_msg_id = self._repo.create_message_sync(assistant_msg)
            logger.info(f"Added turn to session {session_id}: user={user_msg_id}, assistant={assistant_msg_id}")
            return user_msg_id, assistant_msg_id
        except Exception as e:
            logger.error(f"Failed to add turn: {e}")
            raise
    
    def get_context_messages(
        self,
        session_id: str,
        max_turns: int = 5,
    ) -> list[dict]:
        """
        LLMコンテキスト用のメッセージ履歴を取得
        
        Args:
            session_id: セッションID
            max_turns: 最大ターン数（1ターン = user + assistant）
            
        Returns:
            OpenAI API形式のメッセージリスト
        """
        try:
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
            
        except Exception as e:
            logger.error(f"Failed to get context messages: {e}")
            return []
    
    def get_turn_count(self, session_id: str) -> int:
        """
        セッションのターン数を取得
        
        Args:
            session_id: セッションID
            
        Returns:
            ターン数（メッセージ数 / 2）
        """
        try:
            count = self._repo.get_message_count_sync(session_id)
            return count // 2
        except Exception as e:
            logger.error(f"Failed to get turn count: {e}")
            return 0
    
    # =========================================================================
    # Utility
    # =========================================================================
    
    def health_check(self) -> dict:
        """ヘルスチェック"""
        return self._repo.health_check()
