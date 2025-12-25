"""D21-4 Prompt Engineering改善効果の簡易テスト"""
import os
import sys
from dotenv import load_dotenv
from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.search_service import SearchService

load_dotenv()

# Azure OpenAI クライアント初期化
credential = DefaultAzureCredential()
openai_client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    azure_ad_token_provider=lambda: credential.get_token("https://cognitiveservices.azure.com/.default").token,
    api_version="2024-10-01-preview"
)

# サービス初期化
search_service = SearchService(
    endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
    index_name=os.getenv("AZURE_SEARCH_INDEX"),
)

def get_embedding(text: str) -> list[float]:
    """テキストを埋め込みベクトルに変換"""
    response = openai_client.embeddings.create(
        model=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-ada-002"),
        input=text
    )
    return response.data[0].embedding

# テストクエリ
test_queries = [
    "Azure AI Searchでベクトル検索を有効にする方法を教えてください",
    "Bicepでストレージアカウントを作成するコードを教えて",
]

def test_rag(query: str):
    """RAGテスト実行"""
    print(f"\n{'='*80}")
    print(f"質問: {query}")
    print(f"{'='*80}\n")
    
    # 埋め込みベクトル生成
    embedding = get_embedding(query)
    
    # 検索実行
    results = search_service.hybrid_search(
        query=query,
        embedding=embedding,
        top_k=3
    )
    
    # コンテキスト構築
    context_text = "\n\n".join([
        f"【{doc.get('title', 'タイトルなし')}】\n{doc.get('content', '')}"
        for doc in results
    ])
    
    # app/api/routes/rag.pyからプロンプトをインポート
    from app.api.routes.rag import DEFAULT_RAG_SYSTEM_PROMPT
    
    user_message = f"""以下のコンテキストを参照して、質問に回答してください。

【コンテキスト】
{context_text}

【質問】
{query}"""
    
    messages = [
        {"role": "system", "content": DEFAULT_RAG_SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]
    
    # LLM呼び出し（OpenAIクライアント直接使用）
    response = openai_client.chat.completions.create(
        model=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o"),
        messages=messages,
        temperature=0.3,
        max_tokens=1000,
    )
    
    answer = response.choices[0].message.content
    
    print(f"回答:\n{answer}\n")
    print(f"検索結果数: {len(results)}")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    print("🚀 D21-4 Prompt Engineering改善テスト開始\n")
    for query in test_queries:
        try:
            test_rag(query)
        except Exception as e:
            print(f"❌ エラー: {e}\n")
            import traceback
            traceback.print_exc()
    print("✅ テスト完了")
