#!/usr/bin/env python3
"""RAGパイプライン統合テスト"""
import sys
sys.path.insert(0, '/workspaces/azure-rag-agent-poc')

import os
from dotenv import load_dotenv
load_dotenv()

from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from azure.core.credentials import AzureKeyCredential
from azure.identity import AzureCliCredential
from openai import AzureOpenAI
from src.embedding import EmbeddingService

def main():
    print("\n" + "="*50)
    print("  RAGパイプライン統合テスト")
    print("="*50)
    
    # クライアント初期化
    search_client = SearchClient(
        endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
        index_name=os.getenv("AZURE_SEARCH_INDEX"),
        credential=AzureKeyCredential(os.getenv("AZURE_SEARCH_API_KEY")),
    )
    embedding_service = EmbeddingService()
    
    credential = AzureCliCredential()
    openai_client = AzureOpenAI(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        azure_ad_token_provider=lambda: credential.get_token(
            "https://cognitiveservices.azure.com/.default"
        ).token,
        api_version="2024-10-01-preview",
    )
    
    query = "Azure AI Searchとは何ですか？"
    print(f"\n📝 質問: {query}")
    
    # 1. 検索
    print("\n🔍 コンテキスト検索中...")
    query_vector = embedding_service.embed_text(query)
    vector_query = VectorizedQuery(
        vector=query_vector,
        k_nearest_neighbors=3,
        fields="content_vector",
    )
    results = list(search_client.search(
        search_text=query,
        vector_queries=[vector_query],
        select=["title", "content"],
        top=3,
    ))
    
    context = "\n".join([f"- {r['title']}: {r['content']}" for r in results])
    print(f"   ✅ {len(results)}件取得")
    
    # 2. LLM回答生成
    print("\n🤖 回答生成中...")
    response = openai_client.chat.completions.create(
        model=os.getenv("AZURE_OPENAI_DEPLOYMENT_CHAT"),
        messages=[
            {"role": "system", "content": "コンテキストのみを使用して簡潔に回答してください。"},
            {"role": "user", "content": f"コンテキスト:\n{context}\n\n質問: {query}"},
        ],
        temperature=0.7,
        max_tokens=300,
    )
    
    answer = response.choices[0].message.content
    print(f"\n💬 回答:\n{answer}")
    print("\n✅ 統合テスト完了")

if __name__ == "__main__":
    main()
