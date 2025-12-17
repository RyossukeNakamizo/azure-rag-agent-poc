#!/usr/bin/env python3
"""RAG検索テスト"""
import os
from dotenv import load_dotenv
load_dotenv()

from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from azure.core.credentials import AzureKeyCredential
from src.embedding import EmbeddingService

def main():
    print("\n" + "="*50)
    print("  RAG検索テスト")
    print("="*50)
    
    search_client = SearchClient(
        endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
        index_name=os.getenv("AZURE_SEARCH_INDEX"),
        credential=AzureKeyCredential(os.getenv("AZURE_SEARCH_API_KEY")),
    )
    embedding_service = EmbeddingService()
    
    queries = ["Azure AI Searchとは", "RAGアーキテクチャ"]
    
    for query in queries:
        print(f"\n📝 クエリ: {query}")
        print("-" * 40)
        
        query_vector = embedding_service.embed_text(query)
        
        vector_query = VectorizedQuery(
            vector=query_vector,
            k_nearest_neighbors=3,
            fields="content_vector",
        )
        
        results = search_client.search(
            search_text=query,
            vector_queries=[vector_query],
            select=["id", "title", "content", "category"],
            top=3,
        )
        
        for i, r in enumerate(results, 1):
            print(f"\n  [{i}] {r.get('title', 'N/A')}")
            print(f"      カテゴリ: {r.get('category', 'N/A')}")
            print(f"      スコア: {r.get('@search.score', 0):.4f}")
            print(f"      内容: {r.get('content', '')[:80]}...")
    
    print("\n✅ 検索テスト完了")

if __name__ == "__main__":
    main()
