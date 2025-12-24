"""Azure AI Search サンプルデータ投入"""
import os
from azure.identity import DefaultAzureCredential
from azure.search.documents import SearchClient
from openai import AzureOpenAI

credential = DefaultAzureCredential()
endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
index_name = os.getenv("AZURE_SEARCH_INDEX")

openai_client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    azure_ad_token_provider=lambda: credential.get_token("https://cognitiveservices.azure.com/.default").token,
    api_version="2024-10-01-preview"
)

def get_embedding(text: str):
    response = openai_client.embeddings.create(
        model=os.getenv("AZURE_OPENAI_DEPLOYMENT_EMBEDDING"),
        input=text
    )
    return response.data[0].embedding

sample_docs = [
    {
        "id": "doc003",
        "title": "ベクトル検索のフィールド定義",
        "content": "ベクトル検索を有効にするには、SearchFieldのtypeをCollection(Edm.Single)に設定し、vector_search_dimensionsに埋め込み次元数（1536など）、vector_search_profile_nameにプロファイル名を指定します。",
        "source": "Azure公式ドキュメント",
        "category": "インデックス設計"
    },
    {
        "id": "doc004",
        "title": "SimpleFieldとSearchableFieldの違い",
        "content": "SimpleFieldはフィルタリング・ソート専用で検索対象外。SearchableFieldはフルテキスト検索が可能で、アナライザーを指定できます。keyフィールドは必ずSimpleFieldです。",
        "source": "Azure公式ドキュメント",
        "category": "フィールド定義"
    },
    {
        "id": "doc005",
        "title": "インデックススキーマ変更のダウンタイム回避",
        "content": "インデックスのalias機能を使用します。新インデックスを作成→データ移行→aliasを切り替え→旧インデックス削除の順で実行すれば、ダウンタイムゼロで移行できます。",
        "source": "Azure Best Practices",
        "category": "運用管理"
    },
    {
        "id": "doc006",
        "title": "大規模インデックス再構築の最適化",
        "content": "10万ドキュメントの再構築では、バッチサイズ1000、並列度4-8、IndexingParametersのmaxFailedItemsを-1に設定します。indexingScheduleで夜間実行も推奨。",
        "source": "Azure公式ドキュメント",
        "category": "パフォーマンス最適化"
    },
    {
        "id": "doc007",
        "title": "インデックス削除コマンド（Python SDK）",
        "content": "SearchIndexClient.delete_index(index_name)で削除可能。または、az search index delete --name <index> --service-name <service> --resource-group <rg>でも削除できます。",
        "source": "Azure公式ドキュメント",
        "category": "運用管理"
    },
    {
        "id": "doc008",
        "title": "マルチテナント向けインデックス分離戦略",
        "content": "テナントごとに専用インデックスを作成する方式と、単一インデックスでtenantIdフィールドでフィルタリングする方式があります。前者はセキュリティ強固、後者はコスト効率的。",
        "source": "Azure Architecture Center",
        "category": "アーキテクチャ設計"
    },
    {
        "id": "doc009",
        "title": "インデックス統計情報の取得",
        "content": "SearchIndexClient.get_index_statistics(index_name)でドキュメント数とストレージサイズを取得可能。Azure PortalのMetricsでも確認できます。",
        "source": "Azure公式ドキュメント",
        "category": "運用管理"
    },
    {
        "id": "doc010",
        "title": "HNSWパラメータの推奨値",
        "content": "m=4（グラフ接続数）、efConstruction=400（インデックス構築品質）、efSearch=500（検索品質）が標準。大規模データではm=8、efConstruction=800に増やすと精度向上。",
        "source": "Azure Best Practices",
        "category": "ベクトル検索最適化"
    },
    {
        "id": "doc011",
        "title": "コサイン類似度とユークリッド距離の使い分け",
        "content": "コサイン類似度は方向の類似性を測定し、正規化された埋め込み（テキスト）に最適。ユークリッド距離は絶対距離を測定し、非正規化埋め込み（画像）に適します。",
        "source": "機械学習ガイド",
        "category": "ベクトル検索理論"
    },
    {
        "id": "doc012",
        "title": "k値（k_nearest_neighbors）の最適化",
        "content": "k値は用途により調整。要約タスクではk=3-5、質問応答ではk=5-10が推奨。k値が大きいほどリコール向上、レイテンシ増加。A/Bテストで決定すべき。",
        "source": "Azure公式ドキュメント",
        "category": "ベクトル検索最適化"
    },
    {
        "id": "doc013",
        "title": "Exhaustive KNN vs HNSWの性能比較",
        "content": "10万ドキュメントでExhaustive KNNは精度100%だがレイテンシ3000ms、HNSWは精度99.5%でレイテンシ180ms。本番ではHNSW推奨。",
        "source": "Azure公式ドキュメント",
        "category": "ベクトル検索最適化"
    },
    {
        "id": "doc014",
        "title": "埋め込みモデル変更時の対応",
        "content": "埋め込みモデルを変更する場合、インデックス再構築が必須。次元数が異なる場合は新インデックス作成が必要。aliasを使用すればダウンタイム回避可能。",
        "source": "Azure公式ドキュメント",
        "category": "運用管理"
    },
    {
        "id": "doc015",
        "title": "@search.scoreの解釈方法",
        "content": "ベクトル検索の@search.scoreは0-1の範囲で、1に近いほど類似度が高い。ハイブリッド検索では正規化後の統合スコア。0.7以上が高品質な結果の目安。",
        "source": "Azure公式ドキュメント",
        "category": "ベクトル検索理論"
    },
    {
        "id": "doc016",
        "title": "ハイブリッド検索のスコアバランス調整",
        "content": "search_textとvector_queriesの両方を指定するとハイブリッド検索に。Reciprocal Rank Fusion（RRF）でスコア統合。キーワード重視ならsearch_modeをallに設定。",
        "source": "Azure公式ドキュメント",
        "category": "ハイブリッド検索"
    },
    {
        "id": "doc017",
        "title": "セマンティック検索の有効化",
        "content": "Standard以上のSKUでsemantic_searchをfreeまたはstandardに設定。クエリ時にquery_typeをsemanticに指定すると、BM25+ベクトル+セマンティックの3層検索に。",
        "source": "Azure公式ドキュメント",
        "category": "高度な検索機能"
    },
    {
        "id": "doc018",
        "title": "Skillsetによるチャンキング自動化",
        "content": "SplitSkillでtextSplitMode=pagesとmaximumPageLength=2000に設定すると、2000文字ごとにチャンキング。pageOverlapLength=200でオーバーラップ追加。",
        "source": "Azure公式ドキュメント",
        "category": "データインジェスト"
    },
    {
        "id": "doc019",
        "title": "Managed Identityでの認証設定",
        "content": "検索サービスにSystem-assigned Managed Identityを有効化し、RBACで「Search Index Data Contributor」ロールを付与。API KeyよりMI推奨。",
        "source": "Azure公式ドキュメント",
        "category": "セキュリティ"
    },
    {
        "id": "doc020",
        "title": "インデックスのバックアップとリストア",
        "content": "Azure AI SearchにはネイティブなバックアップAPIなし。Python SDKでドキュメント全件取得→JSONファイル保存→新インデックスにアップロードする方法が一般的。",
        "source": "Azure Best Practices",
        "category": "運用管理"
    },
    {
        "id": "doc021",
        "title": "インデックスのレプリカとパーティション",
        "content": "レプリカは可用性向上、パーティションはストレージ・スループット向上。Standard SKUではレプリカ12、パーティション12まで。料金は両者の積で計算。",
        "source": "Azure公式ドキュメント",
        "category": "スケーリング"
    },
    {
        "id": "doc022",
        "title": "クエリのデバッグ方法",
        "content": "Azure Portalの「Search explorer」でクエリテスト可能。Python SDKではsearch()の結果を直接print()して@search.scoreやハイライトを確認。",
        "source": "Azure公式ドキュメント",
        "category": "デバッグ"
    }
]

for doc in sample_docs:
    print(f"Generating embedding for: {doc['title']}")
    doc["content_vector"] = get_embedding(doc["content"])
    doc["document_id"] = doc["id"]
    doc["chunk_index"] = 0
    doc["token_count"] = len(doc["content"].split())

search_client = SearchClient(endpoint=endpoint, index_name=index_name, credential=credential)
result = search_client.upload_documents(documents=sample_docs)

print(f"\n✅ Uploaded {len(sample_docs)} documents")
success = sum(1 for r in result if r.succeeded)
print(f"Success: {success}/{len(sample_docs)}")
