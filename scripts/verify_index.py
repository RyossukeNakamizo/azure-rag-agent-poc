#!/usr/bin/env python3
"""インデックススキーマ確認"""
from azure.identity import DefaultAzureCredential
from azure.search.documents.indexes import SearchIndexClient

SEARCH_ENDPOINT = "https://search-ragpoc-dev-ldt4idhueffoe.search.windows.net"
INDEX_NAME = "rag-docs-index"

def verify_index():
    credential = DefaultAzureCredential()
    index_client = SearchIndexClient(endpoint=SEARCH_ENDPOINT, credential=credential)
    
    index = index_client.get_index(INDEX_NAME)
    print(f"Index: {index.name}")
    print(f"Fields:")
    for field in index.fields:
        print(f"  - {field.name}: {field.type}")

if __name__ == "__main__":
    verify_index()
