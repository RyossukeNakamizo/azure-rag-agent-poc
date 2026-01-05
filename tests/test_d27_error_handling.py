"""
D27 Error Handling Tests

エラーハンドリング強化のテスト
- グレースフルデグラデーション
- フォールバック動作
- 接続エラー回復
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from app.core.exceptions import (
    CosmosDBConnectionError,
    CosmosDBOperationError,
    CosmosDBNotAvailableError,
)
from app.repositories.cosmos_repository import CosmosRepository, ConnectionState
from app.services.conversation_service import ConversationService
from app.models.conversation import ConversationMessage, ConversationSession


class TestCosmosRepositoryErrorHandling:
    """CosmosRepository エラーハンドリングテスト"""
    
    def test_connection_failure_graceful_degradation(self):
        """接続失敗時のグレースフルデグラデーション"""
        with patch("app.repositories.cosmos_repository.DefaultAzureCredential"):
            with patch("app.repositories.cosmos_repository.CosmosClient") as mock_client:
                # コンテナ読み取りで例外発生
                mock_container = MagicMock()
                mock_container.read.side_effect = Exception("Connection failed")
                
                mock_database = MagicMock()
                mock_database.get_container_client.return_value = mock_container
                
                mock_client_instance = MagicMock()
                mock_client_instance.get_database_client.return_value = mock_database
                mock_client.return_value = mock_client_instance
                
                # 初期化は例外をスローしない（retry_on_init_failure=True）
                repo = CosmosRepository(
                    endpoint="https://test.cosmos.azure.com",
                    database_name="test-db",
                    container_name="test-container",
                    retry_on_init_failure=True,
                )
                
                # 状態はERROR
                assert repo._state == ConnectionState.ERROR
                assert not repo.is_available
    
    def test_create_message_returns_none_on_failure(self):
        """メッセージ作成失敗時にNoneを返す"""
        with patch("app.repositories.cosmos_repository.DefaultAzureCredential"):
            with patch("app.repositories.cosmos_repository.CosmosClient") as mock_client:
                mock_container = MagicMock()
                mock_container.read.return_value = {"id": "test"}
                mock_container.create_item.side_effect = Exception("Write failed")
                
                mock_database = MagicMock()
                mock_database.get_container_client.return_value = mock_container
                mock_database.read.return_value = {"id": "test-db"}
                
                mock_client_instance = MagicMock()
                mock_client_instance.get_database_client.return_value = mock_database
                mock_client.return_value = mock_client_instance
                
                repo = CosmosRepository(
                    endpoint="https://test.cosmos.azure.com",
                    database_name="test-db",
                    container_name="test-container",
                )
                
                message = ConversationMessage(
                    session_id="test-session",
                    role="user",
                    content="Test message",
                )
                
                # 例外ではなくNoneを返す
                result = repo.create_message_sync(message)
                assert result is None
    
    def test_get_session_history_returns_empty_on_failure(self):
        """履歴取得失敗時に空リストを返す"""
        with patch("app.repositories.cosmos_repository.DefaultAzureCredential"):
            with patch("app.repositories.cosmos_repository.CosmosClient") as mock_client:
                mock_container = MagicMock()
                mock_container.read.return_value = {"id": "test"}
                mock_container.query_items.side_effect = Exception("Query failed")
                
                mock_database = MagicMock()
                mock_database.get_container_client.return_value = mock_container
                mock_database.read.return_value = {"id": "test-db"}
                
                mock_client_instance = MagicMock()
                mock_client_instance.get_database_client.return_value = mock_database
                mock_client.return_value = mock_client_instance
                
                repo = CosmosRepository(
                    endpoint="https://test.cosmos.azure.com",
                    database_name="test-db",
                    container_name="test-container",
                )
                
                # 例外ではなく空リストを返す
                result = repo.get_session_history_sync("test-session")
                assert result == []
    
    def test_health_check_reports_error_state(self):
        """ヘルスチェックがエラー状態を報告"""
        with patch("app.repositories.cosmos_repository.DefaultAzureCredential"):
            with patch("app.repositories.cosmos_repository.CosmosClient") as mock_client:
                mock_container = MagicMock()
                mock_container.read.side_effect = Exception("Health check failed")
                
                mock_database = MagicMock()
                mock_database.get_container_client.return_value = mock_container
                
                mock_client_instance = MagicMock()
                mock_client_instance.get_database_client.return_value = mock_database
                mock_client.return_value = mock_client_instance
                
                repo = CosmosRepository(
                    endpoint="https://test.cosmos.azure.com",
                    database_name="test-db",
                    container_name="test-container",
                    retry_on_init_failure=True,
                )
                
                health = repo.health_check()
                assert health["status"] == "unhealthy"
                assert health["state"] == "error"


class TestConversationServiceErrorHandling:
    """ConversationService エラーハンドリングテスト"""
    
    def test_start_session_returns_id_when_repo_unavailable(self):
        """リポジトリ利用不可時もセッションIDを返す"""
        mock_repo = Mock(spec=CosmosRepository)
        mock_repo.is_available = False
        
        service = ConversationService(repository=mock_repo)
        session_id = service.start_new_session()
        
        # セッションIDは生成される（永続化されない）
        assert session_id is not None
        assert len(session_id) > 0
    
    def test_add_turn_returns_none_when_repo_unavailable(self):
        """リポジトリ利用不可時は(None, None)を返す"""
        mock_repo = Mock(spec=CosmosRepository)
        mock_repo.is_available = False
        
        service = ConversationService(repository=mock_repo)
        user_id, assistant_id = service.add_turn(
            session_id="test-session",
            user_message="Hello",
            assistant_message="Hi there",
        )
        
        assert user_id is None
        assert assistant_id is None
    
    def test_get_context_messages_returns_empty_when_unavailable(self):
        """リポジトリ利用不可時は空リストを返す"""
        mock_repo = Mock(spec=CosmosRepository)
        mock_repo.is_available = False
        
        service = ConversationService(repository=mock_repo)
        messages = service.get_context_messages("test-session")
        
        assert messages == []
    
    def test_get_turn_count_returns_zero_when_unavailable(self):
        """リポジトリ利用不可時は0を返す"""
        mock_repo = Mock(spec=CosmosRepository)
        mock_repo.is_available = False
        
        service = ConversationService(repository=mock_repo)
        count = service.get_turn_count("test-session")
        
        assert count == 0
    
    def test_is_available_reflects_repo_state(self):
        """is_availableがリポジトリ状態を反映"""
        mock_repo = Mock(spec=CosmosRepository)
        
        mock_repo.is_available = True
        service = ConversationService(repository=mock_repo)
        assert service.is_available is True
        
        mock_repo.is_available = False
        assert service.is_available is False


class TestCustomExceptions:
    """カスタム例外テスト"""
    
    def test_cosmos_db_connection_error(self):
        """CosmosDBConnectionErrorのテスト"""
        cause = Exception("Network error")
        error = CosmosDBConnectionError(
            endpoint="https://test.cosmos.azure.com",
            cause=cause,
        )
        
        assert "test.cosmos.azure.com" in str(error)
        assert error.endpoint == "https://test.cosmos.azure.com"
        assert error.cause == cause
    
    def test_cosmos_db_operation_error(self):
        """CosmosDBOperationErrorのテスト"""
        error = CosmosDBOperationError(operation="create_item")
        
        assert "create_item" in str(error)
        assert error.operation == "create_item"
    
    def test_cosmos_db_not_available_error(self):
        """CosmosDBNotAvailableErrorのテスト"""
        error = CosmosDBNotAvailableError()
        
        assert "not available" in str(error).lower()


class TestHealthCheckGracefulDegradation:
    """ヘルスチェックのグレースフルデグラデーションテスト"""
    
    def test_health_response_with_degraded_services(self):
        """degradedサービスを含むヘルスレスポンス"""
        from app.models.rag import RAGHealthResponse
        
        response = RAGHealthResponse(
            status="degraded",
            search_service="healthy",
            index_name="test-index",
            openai_service="healthy",
            cosmos_db="unhealthy",
            degraded_services=["cosmos_db"],
            message="Core services healthy, optional services degraded: cosmos_db",
        )
        
        assert response.status == "degraded"
        assert "cosmos_db" in response.degraded_services
        assert "optional services degraded" in response.message
    
    def test_health_response_all_healthy(self):
        """全サービス正常時のヘルスレスポンス"""
        from app.models.rag import RAGHealthResponse
        
        response = RAGHealthResponse(
            status="healthy",
            search_service="healthy",
            index_name="test-index",
            openai_service="healthy",
            cosmos_db="healthy",
            degraded_services=None,
            message="All services operational",
        )
        
        assert response.status == "healthy"
        assert response.degraded_services is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
