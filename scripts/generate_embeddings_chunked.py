#!/usr/bin/env python3
"""
チャンク埋め込み生成スクリプト v1.0
D21-3: 分割されたチャンクのベクトル埋め込みを生成
"""

import json
import os
import sys
from pathlib import Path
from typing import List
from datetime import datetime
import time

from azure.identity import DefaultAzureCredential
from openai import AzureOpenAI


def get_azure_openai_client() -> AzureOpenAI:
    """Azure OpenAI クライアントを初期化"""
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    if not endpoint:
        print("ERROR: AZURE_OPENAI_ENDPOINT not set")
        sys.exit(1)
    
    credential = DefaultAzureCredential()
    
    def get_token():
        return credential.get_token(
            "https://cognitiveservices.azure.com/.default"
        ).token
    
    return AzureOpenAI(
        azure_endpoint=endpoint,
        azure_ad_token_provider=get_token,
        api_version="2024-10-01-preview"
    )


def generate_embedding(client: AzureOpenAI, text: str) -> List[float]:
    """テキストの埋め込みベクトルを生成"""
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_EMBEDDING", "text-embedding-ada-002")
    
    response = client.embeddings.create(
        model=deployment,
        input=text
    )
    
    return response.data[0].embedding


def process_chunks(
    input_file: str = "data/chunked_documents.json",
    output_file: str = "data/chunked_documents_with_embeddings.json",
    batch_size: int = 10
) -> None:
    """チャンクの埋め込みを生成"""
    
    input_path = Path(input_file)
    if not input_path.exists():
        print(f"ERROR: {input_file} not found")
        sys.exit(1)
    
    with open(input_path, encoding='utf-8') as f:
        chunks = json.load(f)
    
    print(f"Input: {len(chunks)} chunks")
    print(f"Batch size: {batch_size}\n")
    
    client = get_azure_openai_client()
    
    processed = 0
    start_time = time.time()
    
    for i, chunk in enumerate(chunks):
        try:
            embedding = generate_embedding(client, chunk['content'])
            chunk['contentVector'] = embedding
            
            processed += 1
            
            if (i + 1) % batch_size == 0:
                elapsed = time.time() - start_time
                rate = processed / elapsed
                remaining = (len(chunks) - processed) / rate if rate > 0 else 0
                
                print(f"Progress: {processed}/{len(chunks)} "
                      f"({processed/len(chunks)*100:.1f}%) "
                      f"- ETA: {remaining:.0f}s")
            
            if (i + 1) % batch_size == 0:
                time.sleep(0.5)
        
        except Exception as e:
            print(f"ERROR at chunk {i} ({chunk['id']}): {e}")
            continue
    
    elapsed = time.time() - start_time
    
    print(f"\nCompleted:")
    print(f"  Total chunks: {len(chunks)}")
    print(f"  Processed: {processed}")
    print(f"  Failed: {len(chunks) - processed}")
    print(f"  Time: {elapsed:.1f}s ({processed/elapsed:.1f} chunks/s)")
    if processed > 0:
        print(f"  Vector dimensions: {len(chunks[0]['contentVector'])}")
    
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(chunks, f, indent=2, ensure_ascii=False)
    
    print(f"\nSaved: {output_file}")
    print(f"Next: python scripts/upload_chunked_documents.py")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate embeddings for chunks')
    parser.add_argument('--input', default='data/chunked_documents.json')
    parser.add_argument('--output', default='data/chunked_documents_with_embeddings.json')
    parser.add_argument('--batch-size', type=int, default=10)
    
    args = parser.parse_args()
    
    print(f"Embedding generation started")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    process_chunks(
        input_file=args.input,
        output_file=args.output,
        batch_size=args.batch_size
    )
    
    print(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
