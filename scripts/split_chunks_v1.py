#!/usr/bin/env python3
"""
チャンク分割スクリプト v1.0
D21-3: Groundedness改善のための情報密度最適化
"""

import json
import sys
from pathlib import Path
from typing import List, Dict
from datetime import datetime


def split_into_chunks(
    content: str,
    chunk_size: int = 425,
    overlap: int = 50,
    min_chunk_size: int = 100
) -> List[str]:
    """テキストを指定サイズのチャンクに分割"""
    chunks = []
    start = 0
    
    while start < len(content):
        end = min(start + chunk_size, len(content))
        chunk = content[start:end]
        
        if len(chunk) >= min_chunk_size:
            chunks.append(chunk.strip())
        
        start = end - overlap
        
        if end >= len(content):
            break
    
    return chunks


def calculate_stats(chunks: List[Dict]) -> Dict:
    """チャンク統計を計算"""
    total_chars = sum(len(c['content']) for c in chunks)
    total_tokens = sum(c.get('token_count', len(c['content'].split())) for c in chunks)
    
    return {
        'total_chunks': len(chunks),
        'total_chars': total_chars,
        'total_tokens': total_tokens,
        'avg_chars_per_chunk': total_chars / len(chunks) if chunks else 0,
        'avg_tokens_per_chunk': total_tokens / len(chunks) if chunks else 0,
        'min_chars': min(len(c['content']) for c in chunks) if chunks else 0,
        'max_chars': max(len(c['content']) for c in chunks) if chunks else 0,
    }


def process_documents(
    input_file: str = "data/expanded_documents.json",
    output_file: str = "data/chunked_documents.json",
    chunk_size: int = 425,
    overlap: int = 50
) -> None:
    """ドキュメントをチャンク分割して保存"""
    input_path = Path(input_file)
    if not input_path.exists():
        print(f"ERROR: {input_file} not found")
        sys.exit(1)
    
    with open(input_path, encoding='utf-8') as f:
        docs = json.load(f)
    
    print(f"Input: {len(docs)} documents")
    print(f"Chunk size: {chunk_size} chars (overlap {overlap})\n")
    
    chunked_docs = []
    original_stats = calculate_stats(docs)
    
    for doc in docs:
        content = doc['content']
        doc_chunks = split_into_chunks(content, chunk_size, overlap)
        
        for i, chunk in enumerate(doc_chunks):
            chunked_docs.append({
                'id': f"{doc['id']}_chunk_{i:02d}",
                'document_id': doc['id'],
                'content': chunk,
                'source': doc.get('source', ''),
                'category': doc.get('category', 'Azure AI Search'),
                'title': doc.get('title', ''),
                'chunk_index': i,
                'total_chunks': len(doc_chunks),
                'token_count': len(chunk.split()),
                'char_count': len(chunk),
            })
    
    chunked_stats = calculate_stats(chunked_docs)
    
    print(f"Results:")
    print(f"  Original docs: {len(docs)}")
    print(f"  Chunked docs: {len(chunked_docs)}")
    print(f"  Ratio: {len(chunked_docs) / len(docs):.1f}x\n")
    
    print(f"Size stats:")
    print(f"  Total chars: {original_stats['total_chars']:,} -> {chunked_stats['total_chars']:,}")
    print(f"  Avg chars/chunk: {original_stats['avg_chars_per_chunk']:.0f} -> {chunked_stats['avg_chars_per_chunk']:.0f}")
    print(f"  Char range: {chunked_stats['min_chars']} - {chunked_stats['max_chars']}\n")
    
    print(f"Expected impact:")
    print(f"  Information density: {chunked_stats['avg_chars_per_chunk'] / original_stats['avg_chars_per_chunk']:.1%}")
    print(f"  TF-IDF improvement: +{(1 - chunked_stats['avg_chars_per_chunk'] / original_stats['avg_chars_per_chunk']) * 100:.0f}%\n")
    
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(chunked_docs, f, indent=2, ensure_ascii=False)
    
    print(f"Saved: {output_file}")
    print(f"Next: python scripts/generate_embeddings_chunked.py")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Chunk splitting script')
    parser.add_argument('--input', default='data/expanded_documents.json')
    parser.add_argument('--output', default='data/chunked_documents.json')
    parser.add_argument('--chunk-size', type=int, default=425)
    parser.add_argument('--overlap', type=int, default=50)
    
    args = parser.parse_args()
    
    print(f"Chunk splitting started")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    process_documents(
        input_file=args.input,
        output_file=args.output,
        chunk_size=args.chunk_size,
        overlap=args.overlap
    )
    
    print(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
