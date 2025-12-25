from azure.identity import DefaultAzureCredential
from openai import AzureOpenAI
import json
import os

credential = DefaultAzureCredential()
openai_client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    azure_ad_token_provider=lambda: credential.get_token("https://cognitiveservices.azure.com/.default").token,
    api_version="2024-10-01-preview"
)

# 拡充済みドキュメント読み込み
with open('data/expanded_documents.json', 'r', encoding='utf-8') as f:
    docs = json.load(f)

print(f"📊 {len(docs)}件のベクトル埋め込みを生成します...\n")

for i, doc in enumerate(docs, 1):
    print(f"[{i}/{len(docs)}] {doc['title']}...")
    
    try:
        response = openai_client.embeddings.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT_EMBEDDING", "text-embedding-ada-002"),
            input=doc['content']
        )
        
        doc['content_vector'] = response.data[0].embedding
        print(f"  ✅ Vector: {len(doc['content_vector'])} dimensions")
        
    except Exception as e:
        print(f"  ❌ エラー: {e}")
        doc['content_vector'] = None

# 保存
with open('data/expanded_documents_with_vectors.json', 'w', encoding='utf-8') as f:
    json.dump(docs, f, ensure_ascii=False, indent=2)

successful = sum(1 for d in docs if d.get('content_vector'))
print(f"\n{'='*60}")
print(f"💾 保存完了: data/expanded_documents_with_vectors.json")
print(f"✅ {successful}/{len(docs)} 件成功")
