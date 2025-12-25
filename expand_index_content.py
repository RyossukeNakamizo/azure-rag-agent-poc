from azure.identity import DefaultAzureCredential
from azure.search.documents import SearchClient
from openai import AzureOpenAI
import os
import json

credential = DefaultAzureCredential()
search_client = SearchClient(
    endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
    index_name=os.getenv("AZURE_SEARCH_INDEX"),
    credential=credential
)

openai_client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    azure_ad_token_provider=lambda: credential.get_token("https://cognitiveservices.azure.com/.default").token,
    api_version="2024-10-01-preview"
)

results = list(search_client.search(search_text="*", select=["id", "title", "category", "content"], top=100))
print(f"📊 {len(results)}件のドキュメントを拡充します（推定5-10分）...\n")

expanded_docs = []

for i, doc in enumerate(results, 1):
    title = doc.get('title', '')
    category = doc.get('category', '')
    short_content = doc.get('content', '')
    
    print(f"[{i}/{len(results)}] {title}...")
    
    prompt = f"""以下のAzure技術トピックについて、500-800文字の詳細な技術解説を日本語で作成してください。

タイトル: {title}
カテゴリ: {category}
現在の要約: {short_content}

要件:
- 具体的なコード例、パラメータ値、設定方法を含める
- 実務で使える実践的な内容
- ベストプラクティスと注意点を明記
- 「です・ます」調の技術文書スタイル
- Azure公式ドキュメントレベルの品質
"""
    
    try:
        response = openai_client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT_CHAT", "gpt-4o"),
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1200
        )
        
        detailed_content = response.choices[0].message.content
        
        expanded_docs.append({
            "id": doc.get('id'),
            "title": title,
            "category": category,
            "content": detailed_content,
            "content_length": len(detailed_content)
        })
        
        print(f"  ✅ {len(detailed_content)} chars")
        
    except Exception as e:
        print(f"  ❌ エラー: {e}")
        # 元のコンテンツを保持
        expanded_docs.append({
            "id": doc.get('id'),
            "title": title,
            "category": category,
            "content": short_content,
            "content_length": len(short_content)
        })

# 結果保存
with open('data/expanded_documents.json', 'w', encoding='utf-8') as f:
    json.dump(expanded_docs, f, ensure_ascii=False, indent=2)

avg_length = sum(d['content_length'] for d in expanded_docs) / len(expanded_docs)
min_length = min(d['content_length'] for d in expanded_docs)
max_length = max(d['content_length'] for d in expanded_docs)

print(f"\n{'='*60}")
print(f"💾 保存完了: data/expanded_documents.json")
print(f"\n📊 拡充後の統計:")
print(f"  ドキュメント数: {len(expanded_docs)}")
print(f"  平均コンテンツ長: {avg_length:.0f} chars")
print(f"  最小: {min_length} chars")
print(f"  最大: {max_length} chars")
print(f"\n✅ 目標達成: {avg_length >= 500}")
