from promptflow.core import tool
@tool
def retrieve_context(question: str) -> str:
    return f"""【Azure AI Search ベクトル検索】
Azure AI Searchでベクトル検索を有効化するには：
1. インデックス定義でvector_searchセクションを追加
2. HNSWアルゴリズムを設定
3. vector_search_profileを作成
検索クエリ: {question}"""
