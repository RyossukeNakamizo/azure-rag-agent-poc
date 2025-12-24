"""
Retrieve node for Prompt Flow - Production Implementation
SearchService + OpenAI Embedding統合版
"""
import os
import sys
from pathlib import Path
from typing import Dict, Any, List
from promptflow.core import tool

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(project_root))

from app.services.search_service import SearchService
from azure.identity import DefaultAzureCredential
from openai import AzureOpenAI

# グローバルインスタンス
_search_service: SearchService = None
_openai_client: AzureOpenAI = None
_credential: DefaultAzureCredential = None


def get_credential() -> DefaultAzureCredential:
    """共通認証情報取得"""
    global _credential
    if _credential is None:
        _credential = DefaultAzureCredential()
    return _credential


def get_openai_client() -> AzureOpenAI:
    """OpenAIクライアント取得（Embedding生成用）"""
    global _openai_client
    
    if _openai_client is None:
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-01-preview")
        
        if not endpoint:
            raise ValueError("AZURE_OPENAI_ENDPOINT not set")
        
        credential = get_credential()
        
        _openai_client = AzureOpenAI(
            azure_endpoint=endpoint,
            azure_ad_token_provider=lambda: credential.get_token(
                "https://cognitiveservices.azure.com/.default"
            ).token,
            api_version=api_version
        )
    
    return _openai_client


def get_search_service() -> SearchService:
    """SearchServiceシングルトン取得"""
    global _search_service
    
    if _search_service is None:
        endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
        index_name = os.getenv("AZURE_SEARCH_INDEX")
        
        if not endpoint or not index_name:
            raise ValueError(
                f"Missing environment variables:\n"
                f"AZURE_SEARCH_ENDPOINT: {endpoint or 'NOT SET'}\n"
                f"AZURE_SEARCH_INDEX: {index_name or 'NOT SET'}"
            )
        
        credential = get_credential()
        
        _search_service = SearchService(
            endpoint=endpoint,
            index_name=index_name,
            credential=credential
        )
    
    return _search_service


def get_embedding(text: str) -> List[float]:
    """テキストをベクトル埋め込みに変換"""
    client = get_openai_client()
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_EMBEDDING", "text-embedding-ada-002")
    
    try:
        response = client.embeddings.create(
            model=deployment,
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        raise RuntimeError(f"Embedding generation failed: {e}") from e


@tool
def retrieve_context(question: str) -> Dict[str, Any]:
    """Prompt Flow Tool: Azure AI Searchからコンテキスト取得"""
    try:
        query_embedding = get_embedding(question)
        service = get_search_service()
        results = service.hybrid_search(
            query=question,
            embedding=query_embedding,
            top_k=5
        )
        
        normalized_results = []
        for r in results:
            if isinstance(r, dict):
                normalized_results.append({
                    "title": r.get("title", r.get("Title", "")),
                    "content": r.get("content", r.get("Content", r.get("text", ""))),
                    "source": r.get("source", r.get("Source", r.get("url", ""))),
                    "score": r.get("score", r.get("@search.score", 0.0))
                })
            else:
                normalized_results.append({
                    "title": getattr(r, "title", ""),
                    "content": getattr(r, "content", getattr(r, "text", "")),
                    "source": getattr(r, "source", getattr(r, "url", "")),
                    "score": getattr(r, "score", 0.0)
                })
        
        return {
            "context": normalized_results,
            "query": question,
            "num_results": len(normalized_results)
        }
    except Exception as e:
        print(f"⚠️ Search failed: {type(e).__name__}: {e}")
        return {
            "context": [],
            "query": question,
            "num_results": 0,
            "error": str(e)
        }


if __name__ == "__main__":
    print("=== Environment Variables ===")
    required_vars = {
        "AZURE_SEARCH_ENDPOINT": os.getenv("AZURE_SEARCH_ENDPOINT"),
        "AZURE_SEARCH_INDEX": os.getenv("AZURE_SEARCH_INDEX"),
        "AZURE_OPENAI_ENDPOINT": os.getenv("AZURE_OPENAI_ENDPOINT"),
        "AZURE_OPENAI_DEPLOYMENT_EMBEDDING": os.getenv("AZURE_OPENAI_DEPLOYMENT_EMBEDDING")
    }
    
    for var, value in required_vars.items():
        if value and "https://" in value:
            masked = value[:20] + "..." + value[-20:]
        else:
            masked = value or "NOT SET"
        print(f"{var}: {masked}")
    
    print("\n=== Component Initialization ===")
    try:
        print("Initializing OpenAI Client...")
        openai_client = get_openai_client()
        print("✅ OpenAI Client ready")
        
        print("Initializing SearchService...")
        search_service = get_search_service()
        print("✅ SearchService ready")
        
        print("\nTesting embedding generation...")
        test_embedding = get_embedding("テスト")
        print(f"✅ Embedding generated: {len(test_embedding)} dimensions")
    except Exception as e:
        print(f"❌ Initialization failed: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print("\n=== Retrieval Test (5 Questions) ===")
    test_questions = [
        "Azure AI Searchでセマンティック検索を有効化する方法",
        "RAGシステムのチャンキング戦略",
        "Managed Identityの設定手順",
        "BicepでRBAC割り当てを行う方法",
        "ハイブリッド検索のパラメータ最適化"
    ]
    
    success_count = 0
    error_count = 0
    
    for i, q in enumerate(test_questions, 1):
        print(f"\n[Q{i}] {q[:60]}...")
        try:
            result = retrieve_context(q)
            if result['num_results'] > 0:
                print(f"✅ Retrieved: {result['num_results']} docs")
                top = result['context'][0]
                print(f"   Top Score: {top['score']:.3f}")
                print(f"   Title: {top['title'][:50]}...")
                print(f"   Content: {top['content'][:60]}...")
                success_count += 1
            else:
                if 'error' in result:
                    print(f"⚠️  Error: {result['error'][:100]}")
                else:
                    print(f"⚠️  No results (0 documents)")
                error_count += 1
        except Exception as e:
            print(f"❌ Exception: {type(e).__name__}: {e}")
            error_count += 1
    
    print(f"\n=== Test Summary ===")
    print(f"Success: {success_count}/{len(test_questions)}")
    print(f"Errors: {error_count}/{len(test_questions)}")
    
    if success_count > 0:
        print("\n✅ Integration successful - Ready for batch evaluation")
        sys.exit(0)
    else:
        print("\n❌ All tests failed")
        sys.exit(1)
