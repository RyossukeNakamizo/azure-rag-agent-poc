from azure.identity import DefaultAzureCredential
from azure.search.documents import SearchClient
import json
import os

credential = DefaultAzureCredential()
search_client = SearchClient(
    endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
    index_name=os.getenv("AZURE_SEARCH_INDEX"),
    credential=credential
)

# ベクトル付きドキュメント読み込み
with open('data/expanded_documents_with_vectors.json', 'r', encoding='utf-8') as f:
    docs = json.load(f)

print(f"📊 {len(docs)}件をインデックスにアップロード中...\n")

# 正しいフィールド名に修正
upload_docs = []
for doc in docs:
    if doc.get('content_vector'):
        upload_docs.append({
            "id": doc['id'],
            "title": doc['title'],
            "category": doc['category'],
            "content": doc['content'],
            "content_vector": doc['content_vector'],  # スネークケース
            # その他のフィールドはデフォルト値
            "document_id": doc['id'],
            "source": f"{doc['category']}/{doc['title']}",
            "chunk_index": 0,
            "token_count": len(doc['content'].split())
        })

print(f"アップロード準備完了: {len(upload_docs)}件\n")

# バッチアップロード
try:
    result = search_client.upload_documents(documents=upload_docs)
    
    succeeded = sum(1 for r in result if r.succeeded)
    failed = len(result) - succeeded
    
    print(f"\n{'='*60}")
    print(f"📊 アップロード結果:")
    print(f"  成功: {succeeded}/{len(upload_docs)}")
    print(f"  失敗: {failed}")
    
    if failed > 0:
        print(f"\n失敗したドキュメント:")
        for r in result:
            if not r.succeeded:
                print(f"  ID: {r.key}, Error: {r.error_message}")
    else:
        print(f"\n✅ 全22件アップロード成功")
        
except Exception as e:
    print(f"❌ アップロードエラー: {e}")
    import traceback
    traceback.print_exc()
