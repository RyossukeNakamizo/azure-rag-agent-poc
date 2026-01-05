"""
Cosmos DB Repository

D24: 会話履歴管理用リポジトリパターン実装
D27: エラーハンドリング強化 - グレースフルデグラデーション対応
"""
import logging
from typing import Optional
from datetime import datetime
from enum import Enum

from azure.cosmos import CosmosClient, PartitionKey
from azure.cosmos.exceptions import CosmosResourceNotFoundError, CosmosHttpResponseError
from azure.identity import DefaultAzureCredential

from app.models.conversation import ConversationMessage, ConversationSession
from app.core.exceptions import (
    CosmosDBConnectionError,
    CosmosDBOperationError,
    CosmosDBNotAvailableError,
)

logger = logging.getLogger(__name__)


class ConnectionState(Enum):
    """Repository connection state"""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"


class CosmosRepository:
    """
    Cosmos DB操作の抽象化層
    
    D27強化ポイント:
    - 接続エラー時のグレースフルデグラデーション
    - 操作エラーの一貫したハンドリング
    - ヘルスチェックによる状態管理
    
    Managed Identity認証を使用。
    開発環境ではConnection String認証にフォールバック可能。
    """
    
    def __init__(
        self,
        endpoint: str,
        database_name: str = "rag-conversations",
        container_name: str = "conversations",
        connection_string: Optional[str] = None,
        retry_on_init_failure: bool = True,
    ):
        """
        初期化
        
        Args:
            endpoint: Cosmos DBエンドポイント
            database_name: データベース名
            container_name: コンテナ名
            connection_string: 接続文字列（開発用、省略時はManaged Identity）
            retry_on_init_failure: 初期化失敗時にリトライ可能状態を維持
        """
        self.endpoint = endpoint
        self.database_name = database_name
        self.container_name = container_name
        self._connection_string = connection_string
        self._retry_on_init_failure = retry_on_init_failure
        
        # 状態管理
        self._state = ConnectionState.DISCONNECTED
        self._last_error: Optional[Exception] = None
        self._client: Optional[CosmosClient] = None
        self._database = None
        self._container = None
        
        # 初期接続試行
        self._initialize_connection()
    
    def _initialize_connection(self) -> bool:
        """
        接続初期化（エラー時はログのみ、例外は発生させない）
        
        Returns:
            成功フラグ
        """
        try:
            if self._connection_string:
                logger.info("Initializing Cosmos DB with connection string")
                self._client = CosmosClient.from_connection_string(self._connection_string)
            else:
                logger.info("Initializing Cosmos DB with Managed Identity")
                credential = DefaultAzureCredential()
                self._client = CosmosClient(self.endpoint, credential=credential)
            
            # Database & Container参照（遅延評価のため実際の接続は発生しない）
            self._database = self._client.get_database_client(self.database_name)
            self._container = self._database.get_container_client(self.container_name)
            
            # 接続テスト（実際にリクエストを発行）
            self._container.read()
            
            self._state = ConnectionState.CONNECTED
            self._last_error = None
            logger.info(f"Cosmos DB repository initialized: {self.endpoint}/{self.database_name}/{self.container_name}")
            return True
            
        except Exception as e:
            self._state = ConnectionState.ERROR
            self._last_error = e
            logger.error(f"Failed to initialize Cosmos DB connection: {e}")
            
            if not self._retry_on_init_failure:
                raise CosmosDBConnectionError(self.endpoint, e)
            
            return False
    
    @property
    def is_available(self) -> bool:
        """Cosmos DBが利用可能かどうか"""
        return self._state == ConnectionState.CONNECTED
    
    def _ensure_connection(self) -> bool:
        """
        接続確認（必要に応じて再接続）
        
        Returns:
            接続可能フラグ
        """
        if self._state == ConnectionState.CONNECTED:
            return True
        
        # 再接続試行
        logger.info("Attempting to reconnect to Cosmos DB...")
        return self._initialize_connection()
    
    def _safe_operation(self, operation_name: str, operation_func, default_value=None):
        """
        安全な操作実行ラッパー
        
        Args:
            operation_name: 操作名（ログ用）
            operation_func: 実行する関数
            default_value: エラー時のデフォルト値
            
        Returns:
            操作結果またはデフォルト値
        """
        if not self._ensure_connection():
            logger.warning(f"Cosmos DB not available for operation: {operation_name}")
            return default_value
        
        try:
            return operation_func()
        except CosmosResourceNotFoundError as e:
            logger.warning(f"Resource not found in {operation_name}: {e}")
            return default_value
        except CosmosHttpResponseError as e:
            logger.error(f"HTTP error in {operation_name}: {e.status_code} - {e.message}")
            if e.status_code >= 500:
                # サーバーエラーは再接続が必要かもしれない
                self._state = ConnectionState.ERROR
                self._last_error = e
            return default_value
        except Exception as e:
            logger.error(f"Unexpected error in {operation_name}: {e}")
            self._state = ConnectionState.ERROR
            self._last_error = e
            return default_value
    
    # =========================================================================
    # Message Operations
    # =========================================================================
    
    async def create_message(self, message: ConversationMessage) -> Optional[str]:
        """
        メッセージを作成
        
        Args:
            message: 会話メッセージ
            
        Returns:
            作成されたメッセージID（失敗時はNone）
        """
        return self.create_message_sync(message)
    
    def create_message_sync(self, message: ConversationMessage) -> Optional[str]:
        """メッセージを作成（同期版）"""
        def _create():
            doc = message.to_cosmos_dict()
            result = self._container.create_item(body=doc)
            logger.info(f"Created message: {result['id']} in session: {result['sessionId']}")
            return result["id"]
        
        return self._safe_operation("create_message", _create, default_value=None)
    
    async def get_session_history(
        self,
        session_id: str,
        limit: int = 10,
        offset: int = 0,
    ) -> list[ConversationMessage]:
        """
        セッションの会話履歴を取得
        
        Args:
            session_id: セッションID
            limit: 取得件数
            offset: オフセット
            
        Returns:
            メッセージリスト（エラー時は空リスト）
        """
        return self.get_session_history_sync(session_id, limit, offset)
    
    def get_session_history_sync(
        self,
        session_id: str,
        limit: int = 10,
        offset: int = 0,
    ) -> list[ConversationMessage]:
        """セッションの会話履歴を取得（同期版）"""
        def _get_history():
            query = """
                SELECT * FROM c 
                WHERE c.sessionId = @sessionId 
                AND c.role IN ('user', 'assistant')
                ORDER BY c.createdAt DESC
                OFFSET @offset LIMIT @limit
            """
            parameters = [
                {"name": "@sessionId", "value": session_id},
                {"name": "@offset", "value": offset},
                {"name": "@limit", "value": limit},
            ]
            
            items = list(self._container.query_items(
                query=query,
                parameters=parameters,
                partition_key=session_id,
            ))
            
            messages = [ConversationMessage.from_cosmos_dict(item) for item in items]
            logger.info(f"Retrieved {len(messages)} messages for session: {session_id}")
            return messages
        
        return self._safe_operation("get_session_history", _get_history, default_value=[])
    
    async def get_message_count(self, session_id: str) -> int:
        """
        セッションのメッセージ数を取得
        
        Args:
            session_id: セッションID
            
        Returns:
            メッセージ数（エラー時は0）
        """
        return self.get_message_count_sync(session_id)
    
    def get_message_count_sync(self, session_id: str) -> int:
        """セッションのメッセージ数を取得（同期版）"""
        def _get_count():
            query = """
                SELECT VALUE COUNT(1) FROM c 
                WHERE c.sessionId = @sessionId 
                AND c.role IN ('user', 'assistant')
            """
            parameters = [{"name": "@sessionId", "value": session_id}]
            
            items = list(self._container.query_items(
                query=query,
                parameters=parameters,
                partition_key=session_id,
            ))
            
            return items[0] if items else 0
        
        return self._safe_operation("get_message_count", _get_count, default_value=0)
    
    # =========================================================================
    # Session Operations
    # =========================================================================
    
    async def create_session(self, session: ConversationSession) -> Optional[str]:
        """
        セッションを作成
        
        Args:
            session: 会話セッション
            
        Returns:
            作成されたセッションID（失敗時はNone）
        """
        return self.create_session_sync(session)
    
    def create_session_sync(self, session: ConversationSession) -> Optional[str]:
        """セッションを作成（同期版）"""
        def _create():
            doc = session.to_cosmos_dict()
            result = self._container.create_item(body=doc)
            logger.info(f"Created session: {result['id']}")
            return result["id"]
        
        return self._safe_operation("create_session", _create, default_value=None)
    
    async def get_session(self, session_id: str) -> Optional[ConversationSession]:
        """
        セッションを取得
        
        Args:
            session_id: セッションID
            
        Returns:
            セッション（存在しない場合はNone）
        """
        return self.get_session_sync(session_id)
    
    def get_session_sync(self, session_id: str) -> Optional[ConversationSession]:
        """セッションを取得（同期版）"""
        def _get():
            query = """
                SELECT * FROM c 
                WHERE c.sessionId = @sessionId 
                AND c.type = 'session'
            """
            parameters = [{"name": "@sessionId", "value": session_id}]
            
            items = list(self._container.query_items(
                query=query,
                parameters=parameters,
                partition_key=session_id,
            ))
            
            if items:
                return ConversationSession(**items[0])
            return None
        
        return self._safe_operation("get_session", _get, default_value=None)
    
    async def update_session(
        self,
        session_id: str,
        updates: dict,
    ) -> bool:
        """
        セッションを更新
        
        Args:
            session_id: セッションID
            updates: 更新内容
            
        Returns:
            成功フラグ
        """
        def _update():
            session = self.get_session_sync(session_id)
            if not session:
                return False
            
            doc = session.to_cosmos_dict()
            doc.update(updates)
            doc["updatedAt"] = datetime.utcnow().isoformat() + "Z"
            
            self._container.replace_item(
                item=doc["id"],
                body=doc,
            )
            logger.info(f"Updated session: {session_id}")
            return True
        
        return self._safe_operation("update_session", _update, default_value=False)
    
    # =========================================================================
    # Delete Operations
    # =========================================================================
    
    async def delete_session(self, session_id: str) -> bool:
        """
        セッションと全メッセージを削除
        
        Args:
            session_id: セッションID
            
        Returns:
            成功フラグ
        """
        def _delete():
            query = "SELECT c.id FROM c WHERE c.sessionId = @sessionId"
            parameters = [{"name": "@sessionId", "value": session_id}]
            
            items = list(self._container.query_items(
                query=query,
                parameters=parameters,
                partition_key=session_id,
            ))
            
            for item in items:
                self._container.delete_item(
                    item=item["id"],
                    partition_key=session_id,
                )
            
            logger.info(f"Deleted session {session_id} with {len(items)} documents")
            return True
        
        return self._safe_operation("delete_session", _delete, default_value=False)
    
    # =========================================================================
    # Health Check
    # =========================================================================
    
    def health_check(self) -> dict:
        """
        ヘルスチェック
        
        Returns:
            ステータス情報
        """
        if not self._ensure_connection():
            return {
                "status": "unhealthy",
                "state": self._state.value,
                "error": str(self._last_error) if self._last_error else "Connection failed",
                "endpoint": self.endpoint,
            }
        
        try:
            db_props = self._database.read()
            container_props = self._container.read()
            
            return {
                "status": "healthy",
                "state": self._state.value,
                "database": db_props["id"],
                "container": container_props["id"],
                "endpoint": self.endpoint,
            }
        except Exception as e:
            self._state = ConnectionState.ERROR
            self._last_error = e
            return {
                "status": "unhealthy",
                "state": self._state.value,
                "error": str(e),
                "endpoint": self.endpoint,
            }
