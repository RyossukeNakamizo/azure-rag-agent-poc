#!/usr/bin/env python3
"""
RAG E2Eテスト
Purpose: ハイブリッド検索 → LLM回答生成の動作確認
"""

import time
from azure.identity import DefaultAzureCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from openai import AzureOpenAI

# 設定
SEARCH_ENDPOINT = "https://search-ragpoc-dev-ldt4idhueffoe.search.windows.net"
INDEX_NAME = "rag-docs-index"
OPENAI_ENDPOINT = "https://oai-ragpoc-dev-ldt4idhueffoe.openai.azure.com/"
EMBEDDING_DEPLOYMENT = "text-embedding-ada-002"
CHAT_DEPLOYMENT = "gpt-4o"

def test_hybrid_search(query: str, search_client, openai_client):
    """ハイブリッド検索テスト"""
    print(f"\n{'='*60}")
    print(f"Query: {query}")
    print(f"{'='*60}")
    
    # 1. クエリベクトル化
    start = time.time()
    embedding_response = openai_client.embeddings.create(
        model=EMBEDDING_DEPLOYMENT,
        input=query
    )
    embedding = embedding_response.data[0].embedding
    embedding_time = time.time() - start
    print(f"✅ Embedding generated: {embedding_time:.3f}s")
    
    # 2. ハイブリッド検索
    start = time.time()
    vector_query = VectorizedQuery(
        vector=embedding,
        k_nearest_neighbors=3,
        fields="contentVector"
    )
    
    results = search_client.search(
        search_text=query,
        vector_queries=[vector_query],
        select=["title", "content", "source", "category"],
        top=3
    )
    
    results_list = list(results)
    search_time = time.time() - start
    print(f"✅ Search completed: {search_time:.3f}s")
    print(f"   Found: {len(results_list)} documents")
    
    # 検索結果表示
    for i, result in enumerate(results_list, 1):
        print(f"\n   [{i}] {result['title']}")
        print(f"       Source: {result['source']}")
        print(f"       Category: {result['category']}")
        print(f"       Score: {result['@search.score']:.4f}")
        print(f"       Preview: {result['content'][:100]}...")
    
    return results_list

def test_rag_generation(query: str, context_docs: list, openai_client):
    """RAG回答生成テスト"""
    print(f"\n{'='*60}")
    print("RAG Response Generation")
    print(f"{'='*60}")
    
    # コンテキスト構築
    context = "\n\n".join([
        f"【{doc['title']}】\n{doc['content']}"
        for doc in context_docs
    ])
    
    # System Prompt
    system_prompt = """あなたはAzure技術の専門家です。
提供されたコンテキストのみを使用して、正確かつ実用的な回答をしてください。"""
    
    # LLM呼び出し
    start = time.time()
    response = openai_client.chat.completions.create(
        model=CHAT_DEPLOYMENT,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"コンテキスト:\n{context}\n\n質問: {query}"}
        ],
        temperature=0.7,
        max_tokens=500
    )
    generation_time = time.time() - start
    
    answer = response.choices[0].message.content
    print(f"✅ Response generated: {generation_time:.3f}s")
    print(f"\n【回答】\n{answer}")
    
    return answer

def run_tests():
    """テスト実行"""
    credential = DefaultAzureCredential()
    
    # クライアント初期化
    search_client = SearchClient(
        endpoint=SEARCH_ENDPOINT,
        index_name=INDEX_NAME,
        credential=credential
    )
    
    openai_client = AzureOpenAI(
        azure_endpoint=OPENAI_ENDPOINT,
        api_version="2024-10-01-preview",
        azure_ad_token_provider=lambda: credential.get_token(
            "https://cognitiveservices.azure.com/.default"
        ).token
    )
    
    # テストクエリ
    test_queries = [
        "Azure AI Searchのセマンティック検索について教えてください",
        "Managed Identityの利点は何ですか？",
        "RAGシステムの実装方法を教えてください"
    ]
    
    print("\n" + "="*60)
    print("RAG E2E Test Start")
    print("="*60)
    
    for query in test_queries:
        # ハイブリッド検索
        results = test_hybrid_search(query, search_client, openai_client)
        
        # RAG回答生成
        test_rag_generation(query, results, openai_client)
        
        print("\n" + "-"*60)
    
    print("\n✅ All tests completed successfully!")

if __name__ == "__main__":
    run_tests()
