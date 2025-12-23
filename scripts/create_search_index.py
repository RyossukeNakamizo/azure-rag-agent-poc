#!/usr/bin/env python3
"""
Azure AI Search Index 作成スクリプト
Purpose: RAG用Index Schema作成（Vector + Hybrid Search対応）
"""

import os
from azure.identity import DefaultAzureCredential
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SearchField,
    SearchFieldDataType,
    VectorSearch,
    HnswAlgorithmConfiguration,
    VectorSearchProfile,
    SimpleField,
    SearchableField,
    SemanticConfiguration,
    SemanticPrioritizedFields,
    SemanticField,
    SemanticSearch
)

# 設定
SEARCH_ENDPOINT = "https://search-ragpoc-dev-ldt4idhueffoe.search.windows.net"
INDEX_NAME = "rag-docs-index"

def create_search_index():
    """Search Index作成"""
    
    # 認証（Managed Identity / Azure CLI）
    credential = DefaultAzureCredential()
    index_client = SearchIndexClient(
        endpoint=SEARCH_ENDPOINT,
        credential=credential
    )
    
    # フィールド定義
    fields = [
        SimpleField(
            name="id",
            type=SearchFieldDataType.String,
            key=True
        ),
        SearchableField(
            name="content",
            type=SearchFieldDataType.String,
            analyzer_name="ja.microsoft"
        ),
        SearchableField(
            name="title",
            type=SearchFieldDataType.String,
            filterable=True,
            sortable=True,
            facetable=True
        ),
        SimpleField(
            name="source",
            type=SearchFieldDataType.String,
            filterable=True
        ),
        SearchableField(
            name="category",
            type=SearchFieldDataType.String,
            filterable=True,
            facetable=True
        ),
        SearchField(
            name="contentVector",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            searchable=True,
            vector_search_dimensions=1536,
            vector_search_profile_name="rag-vector-profile"
        )
    ]
    
    # Vector Search設定
    vector_search = VectorSearch(
        algorithms=[
            HnswAlgorithmConfiguration(
                name="rag-hnsw-algorithm",
                parameters={
                    "m": 4,
                    "efConstruction": 400,
                    "efSearch": 500,
                    "metric": "cosine"
                }
            )
        ],
        profiles=[
            VectorSearchProfile(
                name="rag-vector-profile",
                algorithm_configuration_name="rag-hnsw-algorithm"
            )
        ]
    )
    
    # Semantic Search設定
    semantic_search = SemanticSearch(
        configurations=[
            SemanticConfiguration(
                name="rag-semantic-config",
                prioritized_fields=SemanticPrioritizedFields(
                    title_field=SemanticField(field_name="title"),
                    content_fields=[SemanticField(field_name="content")],
                    keywords_fields=[SemanticField(field_name="category")]
                )
            )
        ]
    )
    
    # Index作成
    index = SearchIndex(
        name=INDEX_NAME,
        fields=fields,
        vector_search=vector_search,
        semantic_search=semantic_search
    )
    
    print(f"Creating index: {INDEX_NAME}...")
    result = index_client.create_or_update_index(index)
    print(f"✅ Index created successfully: {result.name}")
    print(f"   Fields: {len(result.fields)}")
    print(f"   Vector Search: {result.vector_search.algorithms[0].name}")
    print(f"   Semantic Config: {result.semantic_search.configurations[0].name}")

if __name__ == "__main__":
    create_search_index()
