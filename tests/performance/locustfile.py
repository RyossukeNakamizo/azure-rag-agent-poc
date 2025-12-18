"""
Locust Load Testing for RAG API

Usage:
    locust -f tests/performance/locustfile.py --host=http://localhost:8000
    
    # Web UI mode
    locust -f tests/performance/locustfile.py --host=http://localhost:8000 --web-host=0.0.0.0
    
    # Headless mode
    locust -f tests/performance/locustfile.py --host=http://localhost:8000 --headless -u 10 -r 2 -t 60s
"""

from locust import HttpUser, task, between
import random


class RAGUser(HttpUser):
    """Simulates a user querying the RAG API."""
    
    wait_time = between(1, 3)
    
    def on_start(self):
        """Called when a simulated user starts."""
        self.tenant_id = f"tenant-{random.randint(1, 5)}"
        self.headers = {
            "X-Tenant-ID": self.tenant_id,
            "Content-Type": "application/json"
        }
    
    @task(3)
    def query_rag(self):
        """Test RAG query endpoint (weight: 3)."""
        queries = [
            "Azure AI Searchのセマンティック検索を有効化する方法",
            "Bicepでマネージドアイデンティティを設定する",
            "ハイブリッド検索のベストプラクティス",
            "RAGパイプラインのチャンキング戦略",
            "Application Insightsでメトリクスを取得"
        ]
        
        payload = {
            "query": random.choice(queries),
            "top_k": 5
        }
        
        with self.client.post(
            "/query",
            json=payload,
            headers=self.headers,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed with status {response.status_code}")
    
    @task(1)
    def health_check(self):
        """Test health check endpoint (weight: 1)."""
        with self.client.get("/health", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check failed: {response.status_code}")
    
    @task(2)
    def streaming_query(self):
        """Test streaming query endpoint (weight: 2)."""
        queries = [
            "Azure OpenAIのストリーミングレスポンスの実装方法",
            "FastAPIでSSEを使う方法"
        ]
        
        payload = {
            "query": random.choice(queries),
            "top_k": 3
        }
        
        with self.client.post(
            "/query/stream",
            json=payload,
            headers=self.headers,
            catch_response=True,
            stream=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Streaming failed: {response.status_code}")


class AdminUser(HttpUser):
    """Simulates an admin user managing the system."""
    
    wait_time = between(5, 10)
    
    def on_start(self):
        """Called when admin user starts."""
        self.headers = {
            "X-Tenant-ID": "admin-tenant",
            "Content-Type": "application/json"
        }
    
    @task(1)
    def create_index(self):
        """Test index creation (admin operation)."""
        payload = {
            "index_name": f"test-index-{random.randint(1, 100)}"
        }
        
        with self.client.post(
            "/index/create",
            json=payload,
            headers=self.headers,
            catch_response=True
        ) as response:
            if response.status_code in [200, 201]:
                response.success()
            elif response.status_code == 409:
                response.success()
            else:
                response.failure(f"Index creation failed: {response.status_code}")
