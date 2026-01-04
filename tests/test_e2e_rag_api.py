"""
E2E Tests for RAG API Endpoints

D25-2: 包括的なE2Eテストスクリプト
- ヘルスチェック
- 単発RAG Chat
- マルチターン会話（Cosmos DB統合）
- Query Expansion
- ハイブリッド検索

Run with:
    # 全テスト実行
    pytest tests/test_e2e_rag_api.py -v

    # 特定テスト実行
    pytest tests/test_e2e_rag_api.py::TestHealthCheck -v

    # マーカー指定
    pytest tests/test_e2e_rag_api.py -m "not slow" -v

Requirements:
    - FastAPIサーバーが起動済み（uvicorn app.main:app --port 8000）
    - 環境変数が設定済み（.env）
    - Azure AI Search, OpenAI, Cosmos DBが利用可能
"""
import os
import time
import pytest
import requests
from typing import Optional
from dataclasses import dataclass


# =============================================================================
# Configuration
# =============================================================================

BASE_URL = os.getenv("TEST_API_BASE_URL", "http://localhost:8000")
API_PREFIX = "/api/v1/rag"


@dataclass
class TestConfig:
    """テスト設定"""
    base_url: str = BASE_URL
    api_prefix: str = API_PREFIX
    timeout: int = 30
    
    @property
    def health_url(self) -> str:
        return f"{self.base_url}{self.api_prefix}/health"
    
    @property
    def search_url(self) -> str:
        return f"{self.base_url}{self.api_prefix}/search"
    
    @property
    def chat_url(self) -> str:
        return f"{self.base_url}{self.api_prefix}/chat"
    
    @property
    def chat_with_history_url(self) -> str:
        return f"{self.base_url}{self.api_prefix}/chat/with-history"


config = TestConfig()


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture(scope="session")
def api_base_url():
    """API Base URL"""
    return config.base_url


@pytest.fixture(scope="session")
def check_server_running():
    """サーバー起動確認"""
    try:
        response = requests.get(f"{config.base_url}/", timeout=5)
        return True
    except requests.exceptions.ConnectionError:
        pytest.skip(f"Server not running at {config.base_url}")


# =============================================================================
# Test: Health Check
# =============================================================================

class TestHealthCheck:
    """ヘルスチェックエンドポイントテスト"""
    
    def test_health_endpoint_returns_200(self, check_server_running):
        """ヘルスチェックが200を返す"""
        response = requests.get(config.health_url, timeout=config.timeout)
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
    
    def test_health_includes_all_services(self, check_server_running):
        """全サービスステータスが含まれる"""
        response = requests.get(config.health_url, timeout=config.timeout)
        data = response.json()
        
        # 必須フィールド
        assert "search_service" in data
        assert "openai_service" in data
        assert "index_name" in data
        assert "cosmos_db" in data
    
    def test_health_services_healthy(self, check_server_running):
        """主要サービスがhealthy"""
        response = requests.get(config.health_url, timeout=config.timeout)
        data = response.json()
        
        assert data["search_service"] == "healthy", f"Search unhealthy: {data['search_service']}"
        assert data["openai_service"] == "healthy", f"OpenAI unhealthy: {data['openai_service']}"
    
    def test_cosmos_db_status(self, check_server_running):
        """Cosmos DBステータスが返却される"""
        response = requests.get(config.health_url, timeout=config.timeout)
        data = response.json()
        
        # disabled, healthy, または unhealthy: のいずれか
        cosmos_status = data["cosmos_db"]
        valid_statuses = ["disabled", "healthy"]
        is_valid = cosmos_status in valid_statuses or cosmos_status.startswith("unhealthy:")
        
        assert is_valid, f"Unexpected cosmos_db status: {cosmos_status}"


# =============================================================================
# Test: Hybrid Search
# =============================================================================

class TestHybridSearch:
    """ハイブリッド検索エンドポイントテスト"""
    
    def test_search_returns_results(self, check_server_running):
        """検索が結果を返す"""
        payload = {
            "query": "Azure AI Search",
            "top_k": 3
        }
        
        response = requests.post(
            config.search_url,
            json=payload,
            timeout=config.timeout
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "results" in data
        assert "total_count" in data
        assert data["query"] == payload["query"]
    
    def test_search_results_have_scores(self, check_server_running):
        """検索結果にスコアが含まれる"""
        payload = {
            "query": "ベクトル検索の設定方法",
            "top_k": 5
        }
        
        response = requests.post(
            config.search_url,
            json=payload,
            timeout=config.timeout
        )
        
        data = response.json()
        
        if data["total_count"] > 0:
            for result in data["results"]:
                assert "score" in result
                assert result["score"] >= 0
    
    def test_search_respects_top_k(self, check_server_running):
        """top_kパラメータが尊重される"""
        for top_k in [1, 3, 5]:
            payload = {
                "query": "Azure",
                "top_k": top_k
            }
            
            response = requests.post(
                config.search_url,
                json=payload,
                timeout=config.timeout
            )
            
            data = response.json()
            assert len(data["results"]) <= top_k


# =============================================================================
# Test: RAG Chat
# =============================================================================

class TestRAGChat:
    """RAG Chatエンドポイントテスト"""
    
    def test_chat_returns_answer(self, check_server_running):
        """Chatが回答を返す"""
        payload = {
            "message": "Azure AI Searchとは何ですか？",
            "top_k": 3,
            "temperature": 0.7
        }
        
        response = requests.post(
            config.chat_url,
            json=payload,
            timeout=config.timeout
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "answer" in data
        assert len(data["answer"]) > 0
        assert "sources" in data
        assert "context_used" in data
        assert "model" in data
    
    def test_chat_includes_sources(self, check_server_running):
        """回答にソース参照が含まれる"""
        payload = {
            "message": "Bicepでリソースをデプロイする方法を教えてください",
            "top_k": 5
        }
        
        response = requests.post(
            config.chat_url,
            json=payload,
            timeout=config.timeout
        )
        
        data = response.json()
        
        # ソースがある場合は構造を検証
        if data["context_used"] > 0:
            assert len(data["sources"]) > 0
            for source in data["sources"]:
                assert "id" in source
                assert "score" in source
    
    @pytest.mark.slow
    def test_chat_with_query_expansion(self, check_server_running):
        """Query Expansion有効時の動作"""
        payload = {
            "message": "RAGシステムの構築方法",
            "top_k": 5,
            "use_query_expansion": True
        }
        
        response = requests.post(
            config.chat_url,
            json=payload,
            timeout=config.timeout
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Query Expansion有効時はexpanded_queriesが返る
        assert "expanded_queries" in data
        if data["expanded_queries"]:
            assert len(data["expanded_queries"]) >= 1
    
    def test_chat_without_query_expansion(self, check_server_running):
        """Query Expansion無効時の動作"""
        payload = {
            "message": "Azure OpenAIの使い方",
            "top_k": 3,
            "use_query_expansion": False
        }
        
        response = requests.post(
            config.chat_url,
            json=payload,
            timeout=config.timeout
        )
        
        data = response.json()
        
        # Query Expansion無効時はexpanded_queriesがnullまたは存在しない
        assert data.get("expanded_queries") is None


# =============================================================================
# Test: Multi-turn Conversation (Cosmos DB Integration)
# =============================================================================

class TestMultiTurnConversation:
    """マルチターン会話テスト（Cosmos DB統合）"""
    
    def test_first_turn_creates_session(self, check_server_running):
        """初回ターンでセッションが作成される"""
        payload = {
            "message": "Azure AI Searchについて教えてください",
            "top_k": 3,
            "include_history": True
        }
        
        response = requests.post(
            config.chat_with_history_url,
            json=payload,
            timeout=config.timeout
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "session_id" in data
        assert data["session_id"] is not None
        assert data["turn_number"] == 1
        assert data["history_used"] == 0  # 初回は履歴なし
    
    def test_second_turn_uses_history(self, check_server_running):
        """2回目のターンで履歴が使用される"""
        # 1回目のターン
        payload1 = {
            "message": "Managed Identityとは何ですか？",
            "top_k": 3,
            "include_history": True
        }
        
        response1 = requests.post(
            config.chat_with_history_url,
            json=payload1,
            timeout=config.timeout
        )
        
        data1 = response1.json()
        session_id = data1["session_id"]
        
        # 少し待機（Cosmos DB書き込み完了待ち）
        time.sleep(1)
        
        # 2回目のターン（同じセッション）
        payload2 = {
            "message": "それをAzure AI Searchで使う方法は？",
            "session_id": session_id,
            "top_k": 3,
            "include_history": True,
            "max_history_turns": 5
        }
        
        response2 = requests.post(
            config.chat_with_history_url,
            json=payload2,
            timeout=config.timeout
        )
        
        assert response2.status_code == 200
        data2 = response2.json()
        
        assert data2["session_id"] == session_id
        assert data2["turn_number"] == 2
        assert data2["history_used"] >= 1  # 前回の履歴が使用される
    
    def test_session_continuity(self, check_server_running):
        """セッションの継続性テスト（3ターン）"""
        session_id = None
        
        messages = [
            "PythonでAzure SDKを使う方法を教えてください",
            "具体的なコード例を見せてください",
            "エラーハンドリングはどうすればいいですか？"
        ]
        
        for i, message in enumerate(messages):
            payload = {
                "message": message,
                "top_k": 3,
                "include_history": True,
                "max_history_turns": 5
            }
            
            if session_id:
                payload["session_id"] = session_id
            
            response = requests.post(
                config.chat_with_history_url,
                json=payload,
                timeout=config.timeout
            )
            
            assert response.status_code == 200
            data = response.json()
            
            if i == 0:
                session_id = data["session_id"]
                assert data["turn_number"] == 1
            else:
                assert data["session_id"] == session_id
                assert data["turn_number"] == i + 1
            
            # 少し待機
            time.sleep(0.5)
    
    def test_new_session_without_id(self, check_server_running):
        """session_idなしで新規セッション作成"""
        payload = {
            "message": "新しい質問です",
            "top_k": 3,
            "include_history": False
        }
        
        response = requests.post(
            config.chat_with_history_url,
            json=payload,
            timeout=config.timeout
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "session_id" in data
        assert data["session_id"].startswith("sess_")


# =============================================================================
# Test: Error Handling
# =============================================================================

class TestErrorHandling:
    """エラーハンドリングテスト"""
    
    def test_empty_message_rejected(self, check_server_running):
        """空メッセージが拒否される"""
        payload = {
            "message": "",
            "top_k": 3
        }
        
        response = requests.post(
            config.chat_url,
            json=payload,
            timeout=config.timeout
        )
        
        assert response.status_code == 422  # Validation Error
    
    def test_invalid_top_k_rejected(self, check_server_running):
        """無効なtop_kが拒否される"""
        payload = {
            "message": "テスト",
            "top_k": 100  # 上限超過
        }
        
        response = requests.post(
            config.chat_url,
            json=payload,
            timeout=config.timeout
        )
        
        assert response.status_code == 422
    
    def test_invalid_temperature_rejected(self, check_server_running):
        """無効なtemperatureが拒否される"""
        payload = {
            "message": "テスト",
            "temperature": 3.0  # 上限超過
        }
        
        response = requests.post(
            config.chat_url,
            json=payload,
            timeout=config.timeout
        )
        
        assert response.status_code == 422


# =============================================================================
# Test: Performance (Optional)
# =============================================================================

@pytest.mark.slow
class TestPerformance:
    """パフォーマンステスト"""
    
    def test_health_check_latency(self, check_server_running):
        """ヘルスチェックのレイテンシ"""
        start = time.time()
        response = requests.get(config.health_url, timeout=config.timeout)
        elapsed = time.time() - start
        
        assert response.status_code == 200
        assert elapsed < 5.0, f"Health check too slow: {elapsed:.2f}s"
    
    def test_search_latency(self, check_server_running):
        """検索のレイテンシ"""
        payload = {"query": "Azure", "top_k": 5}
        
        start = time.time()
        response = requests.post(
            config.search_url,
            json=payload,
            timeout=config.timeout
        )
        elapsed = time.time() - start
        
        assert response.status_code == 200
        assert elapsed < 10.0, f"Search too slow: {elapsed:.2f}s"
    
    def test_chat_latency(self, check_server_running):
        """Chatのレイテンシ"""
        payload = {
            "message": "Azure AI Searchとは？",
            "top_k": 3
        }
        
        start = time.time()
        response = requests.post(
            config.chat_url,
            json=payload,
            timeout=config.timeout
        )
        elapsed = time.time() - start
        
        assert response.status_code == 200
        assert elapsed < 15.0, f"Chat too slow: {elapsed:.2f}s"


# =============================================================================
# Main
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
