"""Azure AI Search 疎通確認スクリプト"""
import asyncio
from src.core.config import get_settings
from src.services.search_service import SearchService
from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential, get_bearer_token_provider

async def test_search():
    settings = get_settings()
    
    print(f"🔍 Search Endpoint: {settings.AZURE_SEARCH_ENDPOINT}")
    print(f"📚 Index Name: {settings.AZURE_SEARCH_INDEX}")
    
    search_service = SearchService(
        endpoint=settings.AZURE_SEARCH_ENDPOINT,
        index_name=settings.AZURE_SEARCH_INDEX,
        use_key_credential=False
    )
    
    query = "Azure"
    print(f"\n📝 Test Query: '{query}'")
    
    # 1. キーワード検索
    print("\n--- Keyword Search ---")
    try:
        results = search_service.keyword_search(
            query=query,
            top_k=3,
            select_fields=["id", "content", "filename"]
        )
        print(f"✅ Found {len(results)} documents")
        for i, doc in enumerate(results, 1):
            print(f"\n{i}. Score: {doc['score']:.4f}")
            print(f"   ID: {doc.get('id', 'N/A')}")
            print(f"   Filename: {doc.get('filename', 'N/A')}")
            print(f"   Content: {doc.get('content', 'N/A')[:150]}...")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # 2. ハイブリッド検索
    print("\n--- Hybrid Search ---")
    try:
        token_provider = get_bearer_token_provider(
            DefaultAzureCredential(),
            "https://cognitiveservices.azure.com/.default"
        )
        
        openai_client = AzureOpenAI(
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            azure_ad_token_provider=token_provider,
            api_version=settings.AZURE_OPENAI_API_VERSION
        )
        
        response = openai_client.embeddings.create(
            model=settings.AZURE_OPENAI_DEPLOYMENT_EMBEDDING,
            input=query
        )
        query_embedding = response.data[0].embedding
        print(f"✅ Generated embedding: {len(query_embedding)} dimensions")
        
        results = search_service.hybrid_search(
            query=query,
            query_vector=query_embedding,
            top_k=3,
            select_fields=["id", "content", "filename"]
        )
        print(f"✅ Found {len(results)} documents (hybrid)")
        for i, doc in enumerate(results, 1):
            print(f"\n{i}. Score: {doc['score']:.4f}")
            print(f"   ID: {doc.get('id', 'N/A')}")
            print(f"   Filename: {doc.get('filename', 'N/A')}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_search())
