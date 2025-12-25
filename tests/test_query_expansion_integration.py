"""
Query Expansion統合テスト（RAGエンドポイント）
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
load_dotenv()

from app.services.query_expansion_service import QueryExpansionService
from app.services.search_service import SearchService
from app.services.foundry_agent import FoundryAgentService


def test_integration():
    """統合テスト: Query Expansion + Search"""
    print("\n=== Query Expansion 統合テスト ===\n")
    
    # サービス初期化
    query_service = QueryExpansionService()
    search_service = SearchService(
        endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
        index_name=os.getenv("AZURE_SEARCH_INDEX")
    )
    agent_service = FoundryAgentService(
        azure_openai_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        azure_openai_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_CHAT", "gpt-4o")
    )
    
    # テストクエリ
    query = "Azure AI Searchでベクトル検索を実装する方法"
    
    # Step 1: Query Expansion
    print(f"元クエリ: {query}\n")
    expanded_queries = query_service.expand_query(query, max_expansions=3)
    print(f"展開クエリ:")
    for i, q in enumerate(expanded_queries, 1):
        print(f"  {i}. {q}")
    
    # Step 2: 各クエリで検索
    print(f"\n検索実行中...")
    all_results = []
    
    for exp_query in expanded_queries:
        embedding = agent_service.get_embedding(exp_query)
        results = search_service.hybrid_search(
            query=exp_query,
            embedding=embedding,
            top_k=2
        )
        all_results.extend(results)
    
    # Step 3: 重複排除
    unique_results = {}
    for doc in all_results:
        doc_id = doc.get("id", "")
        current_score = doc.get("score", 0)
        if doc_id not in unique_results:
            unique_results[doc_id] = doc
        elif current_score > unique_results[doc_id].get("score", 0):
            unique_results[doc_id] = doc
    
    final_results = sorted(
        unique_results.values(),
        key=lambda x: x.get("score", 0),
        reverse=True
    )[:5]
    
    print(f"\n検索結果（Top 5）:")
    for i, doc in enumerate(final_results, 1):
        print(f"\n{i}. {doc.get('title', 'Untitled')}")
        print(f"   Score: {doc.get('score', 0):.4f}")
        print(f"   Content: {doc.get('content', '')[:100]}...")
    
    print("\n" + "="*50)
    print("✅ 統合テスト成功")
    print("="*50)


if __name__ == "__main__":
    try:
        test_integration()
    except Exception as e:
        print(f"\n❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)