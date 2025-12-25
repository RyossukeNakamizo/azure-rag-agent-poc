#!/usr/bin/env python3
"""
チャンク化ドキュメントアップロードスクリプト v1.2
D21-3: スキーマに完全準拠（content_vector使用）
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime
import time

from azure.identity import DefaultAzureCredential
from azure.search.documents import SearchClient


def get_search_client() -> SearchClient:
    """Azure AI Search クライアントを初期化"""
    endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
    index_name = os.getenv("AZURE_SEARCH_INDEX", "rag-index")
    
    if not endpoint:
        print("ERROR: AZURE_SEARCH_ENDPOINT not set")
        sys.exit(1)
    
    credential = DefaultAzureCredential()
    
    return SearchClient(
        endpoint=endpoint,
        index_name=index_name,
        credential=credential
    )


def clean_document(doc: dict) -> dict:
    """インデックススキーマに合わせてドキュメントをクリーンアップ"""
    cleaned = {
        'id': doc['id'],
        'document_id': doc.get('document_id', doc['id']),
        'content': doc['content'],
        'content_vector': doc['contentVector'],  # キャメル→スネーク
        'source': doc.get('source', ''),
        'category': doc.get('category', 'Azure AI Search'),
        'chunk_index': doc.get('chunk_index', 0),
        'token_count': doc.get('token_count', len(doc['content'].split())),
    }
    
    if 'title' in doc and doc['title']:
        cleaned['title'] = doc['title']
    
    return cleaned


def delete_all_documents(client: SearchClient) -> int:
    """インデックス内の全ドキュメントを削除"""
    print("Fetching existing documents...")
    
    results = client.search(search_text="*", select=["id"], top=1000)
    doc_ids = [{"id": r["id"]} for r in results]
    
    if not doc_ids:
        print("No existing documents found")
        return 0
    
    print(f"Deleting {len(doc_ids)} existing documents...")
    result = client.delete_documents(documents=doc_ids)
    
    succeeded = sum(1 for r in result if r.succeeded)
    failed = len(result) - succeeded
    
    print(f"Deleted: {succeeded} succeeded, {failed} failed")
    
    return succeeded


def upload_documents(client: SearchClient, documents: list) -> tuple[int, int]:
    """ドキュメントをアップロード"""
    print(f"Uploading {len(documents)} documents...")
    
    result = client.upload_documents(documents=documents)
    
    succeeded = sum(1 for r in result if r.succeeded)
    failed = len(result) - succeeded
    
    if failed > 0:
        print("\nFailed documents:")
        for r in result:
            if not r.succeeded:
                print(f"  {r.key}: {r.error_message}")
    
    return succeeded, failed


def verify_upload(client: SearchClient, expected_count: int) -> bool:
    """アップロード結果を検証"""
    print("\nVerifying upload...")
    
    time.sleep(3)
    
    results = client.search(search_text="*", select=["id"], top=expected_count + 10)
    actual_count = len(list(results))
    
    print(f"Expected: {expected_count}")
    print(f"Actual: {actual_count}")
    
    if actual_count == expected_count:
        print("✅ Verification passed")
        return True
    else:
        print(f"⚠️  Count mismatch: {actual_count} vs {expected_count}")
        return False


def process_upload(
    input_file: str = "data/chunked_documents_with_embeddings.json",
    delete_existing: bool = True
) -> None:
    """アップロード処理を実行"""
    
    input_path = Path(input_file)
    if not input_path.exists():
        print(f"ERROR: {input_file} not found")
        sys.exit(1)
    
    with open(input_path, encoding='utf-8') as f:
        raw_documents = json.load(f)
    
    print(f"Input: {len(raw_documents)} documents")
    
    if not all('contentVector' in doc for doc in raw_documents):
        print("ERROR: Some documents missing 'contentVector'")
        sys.exit(1)
    
    print(f"Vector dimensions: {len(raw_documents[0]['contentVector'])}")
    
    # ドキュメントのクリーンアップ
    print("Cleaning documents for schema compatibility...")
    documents = [clean_document(doc) for doc in raw_documents]
    print(f"Cleaned: {len(documents)} documents")
    print(f"Sample fields: {list(documents[0].keys())}")
    
    client = get_search_client()
    
    if delete_existing:
        deleted = delete_all_documents(client)
        print(f"\n{'='*50}")
    
    succeeded, failed = upload_documents(client, documents)
    
    print(f"\n{'='*50}")
    print(f"Upload results:")
    print(f"  Succeeded: {succeeded}")
    print(f"  Failed: {failed}")
    print(f"  Success rate: {succeeded/len(documents)*100:.1f}%")
    
    if succeeded > 0:
        verify_upload(client, succeeded)
    
    print(f"\n{'='*50}")
    print(f"Index updated:")
    print(f"  Old: 22 chunks (avg 1,698 chars)")
    print(f"  New: {succeeded} chunks (avg 391 chars)")
    print(f"  Ratio: {succeeded/22:.1f}x chunks")
    print(f"\n{'='*50}")
    print(f"Next: python scripts/batch_evaluation_v8.py \\")
    print(f"        --test-file data/test_qa_ai_search_only.json \\")
    print(f"        --output-dir evaluation_results/D21-3")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Upload chunked documents')
    parser.add_argument('--input', default='data/chunked_documents_with_embeddings.json')
    parser.add_argument('--no-delete', action='store_true')
    
    args = parser.parse_args()
    
    print(f"Document upload started")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    process_upload(
        input_file=args.input,
        delete_existing=not args.no_delete
    )
    
    print(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
