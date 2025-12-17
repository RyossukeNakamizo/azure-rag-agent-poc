# Azure RAG Agent PoC

Production-ready RAG (Retrieval-Augmented Generation) pipeline using Azure AI Search and Azure OpenAI.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        RAG Pipeline                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  User Query                                                      │
│      │                                                           │
│      ▼                                                           │
│  ┌─────────────┐    ┌──────────────────┐    ┌─────────────────┐ │
│  │ Embedding   │───▶│ Azure AI Search  │───▶│ Top-K Retrieval │ │
│  │ (ada-002)   │    │ (Hybrid Search)  │    │ + Reranking     │ │
│  └─────────────┘    └──────────────────┘    └────────┬────────┘ │
│                                                       │          │
│                                                       ▼          │
│                                              ┌────────────────┐  │
│                                              │ Context Builder│  │
│                                              └───────┬────────┘  │
│                                                      │           │
│                                                      ▼           │
│                                              ┌────────────────┐  │
│                                              │ Azure OpenAI   │  │
│                                              │ GPT-4 (Stream) │  │
│                                              └───────┬────────┘  │
│                                                      │           │
│                                                      ▼           │
│                                              ┌────────────────┐  │
│                                              │   Response     │  │
│                                              │  (+ Sources)   │  │
│                                              └────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Features

- **Hybrid Search**: Combined vector + keyword search for optimal retrieval
- **Streaming Response**: Real-time response generation with SSE
- **Multi-turn Conversation**: Session-based conversation history
- **Token-aware Chunking**: Semantic chunking with overlap for context preservation
- **Production Security**: Managed Identity authentication, RBAC authorization
- **IaC Ready**: Complete Bicep templates for Azure deployment

## Quick Start

### Prerequisites

- Python 3.10+
- Azure CLI installed and authenticated (`az login`)
- Azure subscription with required resource providers registered

### 1. Clone and Setup

```bash
git clone <repository-url>
cd azure-rag-agent-poc

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Deploy Azure Infrastructure

```bash
# Create resource group
az group create --name rg-rag-poc --location japaneast

# Deploy infrastructure
az deployment group create \
  --resource-group rg-rag-poc \
  --template-file infra/main.bicep \
  --parameters environment=dev projectName=ragpoc

# Get outputs
az deployment group show \
  --resource-group rg-rag-poc \
  --name main \
  --query properties.outputs
```

### 3. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your Azure resource values
# (Use outputs from deployment)
```

### 4. Create Search Index

```python
from src.indexer import SearchIndexManager

# Create index with vector search
manager = SearchIndexManager()
index = manager.create_index()
print(f"Index '{index.name}' created")
```

### 5. Ingest Documents

```python
from src.indexer import DocumentIngestionPipeline

pipeline = DocumentIngestionPipeline()

# Ingest from list
documents = [
    {
        "id": "doc-001",
        "content": "Azure AI Search provides enterprise search...",
        "metadata": {
            "source": "azure-docs/ai-search.md",
            "category": "azure",
            "title": "Azure AI Search Overview"
        }
    }
]
result = pipeline.ingest_documents(documents)
print(f"Ingested: {result['succeeded']} documents")

# Or ingest from Blob Storage
result = pipeline.ingest_from_blob(prefix="docs/")
```

### 6. Run RAG Queries

```python
from src.rag_pipeline import RAGPipeline

pipeline = RAGPipeline()

# Non-streaming query
response = pipeline.query(
    question="Azure AI Searchでセマンティック検索を有効化する方法は？",
    top_k=5,
    search_mode="hybrid"
)

print(response.answer)
print("Sources:", response.sources)

# Streaming query
for chunk in pipeline.query(question="...", stream=True):
    print(chunk, end="", flush=True)
```

### 7. Start API Server

```bash
# Development
uvicorn src.api:app --reload --host 0.0.0.0 --port 8000

# Production
uvicorn src.api:app --host 0.0.0.0 --port 8000 --workers 4
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/query` | POST | Execute RAG query |
| `/query/stream` | POST | Execute RAG query (streaming) |
| `/ingest` | POST | Ingest documents |
| `/index/create` | POST | Create/update search index |
| `/conversation/{id}` | DELETE | Clear conversation history |

### Example API Call

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Azure AI Searchの料金体系は？",
    "top_k": 5,
    "search_mode": "hybrid"
  }'
```

## Project Structure

```
azure-rag-agent-poc/
├── src/
│   ├── __init__.py
│   ├── config.py              # Environment configuration
│   ├── embedding.py           # Text chunking & embedding
│   ├── indexer.py             # Index management & ingestion
│   ├── retriever.py           # Hybrid search retrieval
│   ├── rag_pipeline.py        # Core RAG orchestration
│   └── api.py                 # FastAPI endpoints
├── tests/
│   └── test_rag_pipeline.py
├── infra/
│   └── main.bicep             # Azure IaC
├── .env.example
├── requirements.txt
└── README.md
```

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `AZURE_SEARCH_ENDPOINT` | AI Search service endpoint | Yes |
| `AZURE_SEARCH_INDEX` | Index name | Yes |
| `AZURE_OPENAI_ENDPOINT` | OpenAI service endpoint | Yes |
| `AZURE_OPENAI_DEPLOYMENT_CHAT` | Chat model deployment name | Yes |
| `AZURE_OPENAI_DEPLOYMENT_EMBEDDING` | Embedding model deployment | Yes |
| `AZURE_AUTH_METHOD` | Authentication method | No (default: azure_cli) |
| `RAG_TOP_K` | Number of results to retrieve | No (default: 5) |
| `CHUNK_SIZE` | Token size per chunk | No (default: 500) |

### Authentication Methods

1. **Managed Identity** (Production): Set `AZURE_AUTH_METHOD=managed_identity`
2. **Azure CLI** (Development): Set `AZURE_AUTH_METHOD=azure_cli`, run `az login`
3. **Service Principal** (CI/CD): Set credentials via environment variables

## Performance Tuning

### Chunking Strategy

```python
# Adjust in .env or config
CHUNK_SIZE=500      # Tokens per chunk
CHUNK_OVERLAP=100   # Overlap between chunks
```

- Larger chunks: Better context, fewer retrievals needed
- Smaller chunks: More precise matching, may lose context

### Search Configuration

```python
# In retriever.py - HNSW parameters
"m": 4,               # Graph connectivity (higher = more accurate, slower)
"efConstruction": 400, # Index build quality
"efSearch": 500        # Query-time quality
```

### Recommended Settings by Use Case

| Use Case | Chunk Size | Top-K | Search Mode |
|----------|------------|-------|-------------|
| Q&A | 500 | 3-5 | hybrid |
| Document Summary | 1000 | 5-10 | vector |
| Code Search | 300 | 5 | keyword |

## Comparison: Azure AI Search vs Pinecone

| Feature | Azure AI Search | Pinecone |
|---------|-----------------|----------|
| Managed Service | ✅ | ✅ |
| Hybrid Search | ✅ Native | ❌ Requires workaround |
| Semantic Reranking | ✅ Built-in | ❌ External |
| Japanese Analyzer | ✅ ja.lucene | Limited |
| RBAC Integration | ✅ Azure AD | API Key only |
| Private Endpoint | ✅ | ✅ |
| Skillset (AI Pipeline) | ✅ | ❌ |
| Cost Model | Per-service | Per-vector |

**Recommendation**: Azure AI Search for enterprise Azure workloads with hybrid search requirements; Pinecone for simple vector-only use cases or multi-cloud deployments.

## Next Steps

1. **Step 2**: Add LangChain Agent integration with Tools (Calculator, SQL, Custom)
2. **Step 3**: Implement evaluation framework (RAGAS, custom metrics)
3. **Step 4**: Production deployment with Container Apps

## License

MIT

## References

- [Azure AI Search Documentation](https://learn.microsoft.com/en-us/azure/search/)
- [Azure OpenAI Service](https://learn.microsoft.com/en-us/azure/ai-services/openai/)
- [RAG Pattern Overview](https://learn.microsoft.com/en-us/azure/search/retrieval-augmented-generation-overview)
