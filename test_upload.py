from src.indexer import SearchIndexManager
from src.embedding import EmbeddingService

docs = [
    {
        "id": "doc1",
        "title": "Azure AI Searchの概要",
        "content": "Azure AI Searchは、Microsoftが提供するクラウドベースの検索サービスです。",
        "category": "Azure",
        "source": "azure-docs"
    },
    {
        "id": "doc2",
        "title": "RAGアーキテクチャ",
        "content": "RAGは検索と生成を組み合わせたAIアーキテクチャです。",
        "category": "AI",
        "source": "ai-patterns"
    }
]

manager = SearchIndexManager()
embedder = EmbeddingService()

for doc in docs:
    doc["content_vector"] = embedder.embed_text(doc["content"])

result = manager.upload_documents(docs)
print("Upload completed!")
