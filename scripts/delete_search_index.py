#!/usr/bin/env python3
"""
Azure AI Search Index 削除スクリプト
"""
from azure.identity import DefaultAzureCredential
from azure.search.documents.indexes import SearchIndexClient

SEARCH_ENDPOINT = "https://search-ragpoc-dev-ldt4idhueffoe.search.windows.net"
INDEX_NAME = "rag-docs-index"

def delete_index():
    """既存インデックス削除"""
    credential = DefaultAzureCredential()
    index_client = SearchIndexClient(
        endpoint=SEARCH_ENDPOINT,
        credential=credential
    )
    
    try:
        print(f"Deleting index: {INDEX_NAME}...")
        index_client.delete_index(INDEX_NAME)
        print(f"✅ Index '{INDEX_NAME}' deleted successfully")
    except Exception as e:
        if "not found" in str(e).lower():
            print(f"ℹ️  Index '{INDEX_NAME}' does not exist (already deleted)")
        else:
            print(f"❌ Error: {e}")
            raise

if __name__ == "__main__":
    delete_index()
