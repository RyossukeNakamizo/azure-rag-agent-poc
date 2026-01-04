"""
Cosmos DB Repository

D24: 会話履歴管理用リポジトリパターン実装
"""
import logging
from typing import Optional
from datetime import datetime

from azure.cosmos import CosmosClient, PartitionKey
from azure.cosmos.exceptions import CosmosResourceNotFoundError, CosmosHttpResponseError
from azure.identity import DefaultAzureCredential

from app.models.conversation import ConversationMessage, ConversationSession

logger = logging.getLogger(__name__)


class CosmosRepository:
    """
    Cosmos DB操作の抽象化層
    
    Managed Identity認証を使用。
    開発環境ではConnection String認証にフォールバック可能。
    """
    
    def __init__(
        self,
        endpoint: str,
        database_name: str = "rag-conversations",
        container_name: str = "conversations",
        connection_string: Optional[str] = None,
    ):
        """
        初期化
        
        Args:
            endpoint: Cosmos DBエンドポイント
            database_name: データベース名
            container_name: コンテナ名
            connection_string: 接続文字列（開発用、省略時はManaged Identity）
        """
        self.endpoint = endpoint
        self.database_name = database_name
        self.container_name = container_name
        
        # クライアント初期化
        if connection_string:
            # 開発環境: Connection String
            logger.info("Initializing Cosmos DB with connection string")
            self._client = CosmosClient.from_connection_string(connection_string)
        else:
            # 本番環境: Managed Identity
            logger.info("Initializing Cosmos DB with Managed Identity")
            credential = DefaultAzureCredential()
            self._client = CosmosClient(endpoint, credential=credential)
        
        # Database & Container参照
        self._database = self._client.get_database_client(database_name)
        self._container = self._database.get_container_client(container_name)
        
        logger.info(f"Cosmos DB repository initialized: {endpoint}/{database_name}/{container_name}")
    
    # =========================================================================
    # Message Operations
    # =========================================================================
    
    async def create_message(self, message: ConversationMessage) -> str:
        """
        メッセージを作成
        
        Args:
            message: 会話メッセージ
            
        Returns:
            作成されたメッセージID
        """
        try:
            doc = message.to_cosmos_dict()
            result = self._container.create_item(body=doc)
            logger.info(f"Created message: {result['id']} in session: {result['sessionId']}")
            return result["id"]
        except CosmosHttpResponseError as e:
            logger.error(f"Failed to create message: {e}")
            raise
    
    def create_message_sync(self, message: ConversationMessage) -> str:
        """メッセージを作成（同期版）"""
        try:
            doc = message.to_cosmos_dict()
            result = self._container.create_item(body=doc)
            logger.info(f"Created message: {result['id']} in session: {result['sessionId']}")
            return result["id"]
        except CosmosHttpResponseError as e:
            logger.error(f"Failed to create message: {e}")
            raise
    
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
            メッセージリスト（新しい順）
        """
        try:
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
            
        except CosmosHttpResponseError as e:
            logger.error(f"Failed to get session history: {e}")
            raise
    
    def get_session_history_sync(
        self,
        session_id: str,
        limit: int = 10,
        offset: int = 0,
    ) -> list[ConversationMessage]:
        """セッションの会話履歴を取得（同期版）"""
        try:
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
            
        except CosmosHttpResponseError as e:
            logger.error(f"Failed to get session history: {e}")
            raise
    
    async def get_message_count(self, session_id: str) -> int:
        """
        セッションのメッセージ数を取得
        
        Args:
            session_id: セッションID
            
        Returns:
            メッセージ数
        """
        try:
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
            
        except CosmosHttpResponseError as e:
            logger.error(f"Failed to get message count: {e}")
            raise
    
    def get_message_count_sync(self, session_id: str) -> int:
        """セッションのメッセージ数を取得（同期版）"""
        try:
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
            
        except CosmosHttpResponseError as e:
            logger.error(f"Failed to get message count: {e}")
            raise
    
    # =========================================================================
    # Session Operations
    # =========================================================================
    
    async def create_session(self, session: ConversationSession) -> str:
        """
        セッションを作成
        
        Args:
            session: 会話セッション
            
        Returns:
            作成されたセッションID
        """
        try:
            doc = session.to_cosmos_dict()
            result = self._container.create_item(body=doc)
            logger.info(f"Created session: {result['id']}")
            return result["id"]
        except CosmosHttpResponseError as e:
            logger.error(f"Failed to create session: {e}")
            raise
    
    def create_session_sync(self, session: ConversationSession) -> str:
        """セッションを作成（同期版）"""
        try:
            doc = session.to_cosmos_dict()
            result = self._container.create_item(body=doc)
            logger.info(f"Created session: {result['id']}")
            return result["id"]
        except CosmosHttpResponseError as e:
            logger.error(f"Failed to create session: {e}")
            raise
    
    async def get_session(self, session_id: str) -> Optional[ConversationSession]:
        """
        セッションを取得
        
        Args:
            session_id: セッションID
            
        Returns:
            セッション（存在しない場合はNone）
        """
        try:
            # セッションドキュメントを検索
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
            
        except CosmosHttpResponseError as e:
            logger.error(f"Failed to get session: {e}")
            raise
    
    def get_session_sync(self, session_id: str) -> Optional[ConversationSession]:
        """セッションを取得（同期版）"""
        try:
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
            
        except CosmosHttpResponseError as e:
            logger.error(f"Failed to get session: {e}")
            raise
    
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
        try:
            session = await self.get_session(session_id)
            if not session:
                return False
            
            # 更新
            doc = session.to_cosmos_dict()
            doc.update(updates)
            doc["updatedAt"] = datetime.utcnow().isoformat() + "Z"
            
            self._container.replace_item(
                item=doc["id"],
                body=doc,
            )
            logger.info(f"Updated session: {session_id}")
            return True
            
        except CosmosHttpResponseError as e:
            logger.error(f"Failed to update session: {e}")
            raise
    
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
        try:
            # パーティション内の全ドキュメントを取得
            query = "SELECT c.id FROM c WHERE c.sessionId = @sessionId"
            parameters = [{"name": "@sessionId", "value": session_id}]
            
            items = list(self._container.query_items(
                query=query,
                parameters=parameters,
                partition_key=session_id,
            ))
            
            # 削除実行
            for item in items:
                self._container.delete_item(
                    item=item["id"],
                    partition_key=session_id,
                )
            
            logger.info(f"Deleted session {session_id} with {len(items)} documents")
            return True
            
        except CosmosHttpResponseError as e:
            logger.error(f"Failed to delete session: {e}")
            raise
    
    # =========================================================================
    # Health Check
    # =========================================================================
    
    def health_check(self) -> dict:
        """
        ヘルスチェック
        
        Returns:
            ステータス情報
        """
        try:
            # データベース存在確認
            db_props = self._database.read()
            container_props = self._container.read()
            
            return {
                "status": "healthy",
                "database": db_props["id"],
                "container": container_props["id"],
                "endpoint": self.endpoint,
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "endpoint": self.endpoint,
            }
