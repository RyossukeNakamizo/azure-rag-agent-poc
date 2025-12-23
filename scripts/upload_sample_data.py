#!/usr/bin/env python3
"""
サンプルデータ投入スクリプト
Purpose: Markdownファイルを読み込み、ベクトル化してIndexに投入
"""

import os
import hashlib
from pathlib import Path
from azure.identity import DefaultAzureCredential
from azure.search.documents import SearchClient
from openai import AzureOpenAI

# 設定
SEARCH_ENDPOINT = "https://search-ragpoc-dev-ldt4idhueffoe.search.windows.net"
INDEX_NAME = "rag-docs-index"
OPENAI_ENDPOINT = "https://oai-ragpoc-dev-ldt4idhueffoe.openai.azure.com/"
EMBEDDING_DEPLOYMENT = "text-embedding-ada-002"
DATA_DIR = "data/sample_docs"

def get_embedding(text: str, openai_client) -> list[float]:
    """テキストをベクトル化"""
    response = openai_client.embeddings.create(
        model=EMBEDDING_DEPLOYMENT,
        input=text
    )
    return response.data[0].embedding

def extract_metadata(content: str, filename: str) -> dict:
    """Markdownからメタデータ抽出"""
    lines = content.split('\n')
    title = filename.replace('.md', '').replace('_', ' ').title()
    category = "General"
    
    # カテゴリ検索（最終行に "カテゴリ: XXX" 形式）
    for line in reversed(lines):
        if line.startswith('カテゴリ:'):
            category = line.replace('カテゴリ:', '').strip()
            break
    
    return {
        'title': title,
        'category': category
    }

def upload_documents():
    """ドキュメント投入"""
    credential = DefaultAzureCredential()
    
    # Search Client
    search_client = SearchClient(
        endpoint=SEARCH_ENDPOINT,
        index_name=INDEX_NAME,
        credential=credential
    )
    
    # OpenAI Client
    openai_client = AzureOpenAI(
        azure_endpoint=OPENAI_ENDPOINT,
        api_version="2024-10-01-preview",
        azure_ad_token_provider=lambda: credential.get_token(
            "https://cognitiveservices.azure.com/.default"
        ).token
    )
    
    # Markdownファイル読み込み
    data_path = Path(DATA_DIR)
    md_files = sorted(data_path.glob("*.md"))
    
    print(f"Found {len(md_files)} markdown files")
    
    documents = []
    for md_file in md_files:
        print(f"Processing: {md_file.name}...")
        
        # ファイル読み込み
        content = md_file.read_text(encoding='utf-8')
        
        # メタデータ抽出
        metadata = extract_metadata(content, md_file.name)
        
        # ID生成（ファイル名ベース）
        doc_id = hashlib.md5(md_file.name.encode()).hexdigest()
        
        # ベクトル化
        embedding = get_embedding(content, openai_client)
        
        # ドキュメント構築
        doc = {
            'id': doc_id,
            'content': content,
            'title': metadata['title'],
            'source': f"file:///{DATA_DIR}/{md_file.name}",
            'category': metadata['category'],
            'contentVector': embedding
        }
        documents.append(doc)
        print(f"  ✓ Vectorized ({len(embedding)} dims)")
    
    # 一括アップロード
    print(f"\nUploading {len(documents)} documents to index...")
    result = search_client.upload_documents(documents)
    
    print(f"✅ Upload complete!")
    print(f"   Total: {len(documents)} documents")
    print(f"   Success: {sum(1 for r in result if r.succeeded)} documents")
    
    # カテゴリ別集計
    categories = {}
    for doc in documents:
        cat = doc['category']
        categories[cat] = categories.get(cat, 0) + 1
    
    print(f"\nDocuments by category:")
    for cat, count in sorted(categories.items()):
        print(f"   - {cat}: {count}")

if __name__ == "__main__":
    upload_documents()
