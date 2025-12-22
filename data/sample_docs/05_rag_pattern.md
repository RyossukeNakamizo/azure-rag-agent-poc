# Azure OpenAI RAGパターン

Retrieval-Augmented Generation (RAG)の実装パターン。

## アーキテクチャ
```
User Query → Embedding → Vector Search → Top-K → LLM → Response
```

## コンポーネント
1. Embedding Model: text-embedding-ada-002
2. Vector Store: Azure AI Search
3. LLM: GPT-4o

## Python実装例
```python
from azure.search.documents import SearchClient
from openai import AzureOpenAI

# 1. クエリベクトル化
embedding = openai_client.embeddings.create(...)

# 2. 検索
results = search_client.search(vector_queries=[...])

# 3. LLM回答生成
response = openai_client.chat.completions.create(...)
```

カテゴリ: AI Patterns
