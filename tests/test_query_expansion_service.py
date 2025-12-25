"""
Query Expansion Service単体テスト
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 環境変数読み込み
from dotenv import load_dotenv
load_dotenv()

from app.services.query_expansion_service import QueryExpansionService


def test_query_expansion_basic():
    """基本的なクエリ展開テスト"""
    print("\n=== Test 1: 基本的なクエリ展開 ===")
    service = QueryExpansionService()
    
    query = "Azure AI Searchでセマンティック検索を有効化する方法"
    expanded = service.expand_query(query, max_expansions=3)
    
    # 基本検証
    assert len(expanded) >= 1, "最低1つ（元クエリ）は返る"
    assert expanded[0] == query, "先頭は元クエリ"
    assert len(expanded) <= 4, "最大4つ（元+3展開）"
    
    print(f"元クエリ: {query}")
    print(f"展開結果: {expanded[1:]}")
    print("✅ PASS")


def test_query_expansion_multiple_cases():
    """複数パターンのクエリ展開テスト"""
    print("\n=== Test 2: 複数パターンのクエリ展開 ===")
    service = QueryExpansionService()
    
    test_cases = [
        "Azure AI Searchでセマンティック検索を有効化する方法",
        "GPT-4oの料金",
        "Bicepでストレージアカウントを作成する",
        "Managed Identityとは",
        "HNSW アルゴリズム"
    ]
    
    for query in test_cases:
        expanded = service.expand_query(query, max_expansions=3)
        
        assert len(expanded) >= 1
        assert expanded[0] == query
        
        print(f"\n{query}")
        print(f"  → {expanded[1:]}")
    
    print("\n✅ PASS")


def test_query_expansion_error_handling():
    """エラーハンドリングテスト"""
    print("\n=== Test 3: エラーハンドリング ===")
    service = QueryExpansionService()
    
    # 空文字列
    expanded = service.expand_query("", max_expansions=3)
    assert len(expanded) == 1  # 元クエリのみ返る
    assert expanded[0] == ""
    
    print("空文字列テスト: OK")
    print("✅ PASS")


if __name__ == "__main__":
    print("=== Query Expansion Service 単体テスト ===\n")
    
    # 環境変数確認
    print(f"AZURE_OPENAI_ENDPOINT: {os.getenv('AZURE_OPENAI_ENDPOINT')}")
    print(f"AZURE_OPENAI_DEPLOYMENT_CHAT: {os.getenv('AZURE_OPENAI_DEPLOYMENT_CHAT')}")
    print()
    
    try:
        test_query_expansion_basic()
        test_query_expansion_multiple_cases()
        test_query_expansion_error_handling()
        
        print("\n" + "="*50)
        print("✅ すべてのテスト完了")
        print("="*50)
    
    except AssertionError as e:
        print(f"\n❌ テスト失敗: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ エラー発生: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
