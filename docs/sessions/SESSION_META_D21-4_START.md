# D21-4 Session Meta-Prompt
## Semantic Ranker Implementation for Groundedness 0.85+

---

## Session Context

```xml
<session_context>
<session_id>D21-4_SemanticRanker_Implementation</session_id>
<session_date>2025-12-25+</session_date>
<phase>Week3-Day21-Phase4</phase>

<objective>
Azure AI Search Semantic Ranker実装によるGroundedness 0.85達成
</objective>

<success_criteria>
- Groundedness ≥ 0.85（現状0.76から+0.09改善）
- Coherence ≥ 0.95（現状0.988維持）
- Relevance ≥ 0.95（現状0.963維持）
- エンドツーエンド応答時間 < 4秒
- 3-item検証→100-item評価の完遂
</success_criteria>

<current_state>
  <azure_environment>
    <resource_group>rg-kymlpbbcvcva</resource_group>
    <location>eastus</location>
    <search_service>srch-kymlpbbcvcva</search_service>
    <search_index>ragindex-kymlpbbcvcva</search_index>
    <openai_service>aoai-kymlpbbcvcva</openai_service>
    <deployment_chat>gpt-4o</deployment_chat>
    <deployment_embedding>text-embedding-ada-002</deployment_embedding>
  </azure_environment>

  <achieved_metrics>
    <groundedness>0.76</groundedness>
    <coherence>0.988</coherence>
    <relevance>0.963</relevance>
    <response_time>3.2s (平均)</response_time>
    <index_size>22 documents</index_size>
    <avg_doc_length>1698 characters (18.7x improved)</avg_doc_length>
  </achieved_metrics>

  <completed_phases>
    - D21-1: 初期インデックス作成（22 brief documents）
    - D21-2: データ拡張（91→1698文字、18.7x改善）
    - D21-3: LLM-as-Judge評価実装（batch_evaluation_v8.py）
    - Groundedness 0.167→0.76達成（+358%改善）
  </completed_phases>

  <remaining_gap>
    Groundedness 0.76 → 0.85 = +0.09改善必要
    戦略: Semantic Rankerによるコンテキスト品質向上
  </remaining_gap>
</current_state>

<implementation_plan>
  <step id="1" duration="15min">
    <title>Semantic Ranker有効化（Bicep更新）</title>
    <action>
      1. infra/main.bicepでSemanticSearch設定追加
      2. az deployment group create実行
      3. Azure Portalで設定確認
    </action>
    <verification>
      - Portal > Search Service > Semantic Rankerタブで"Free"表示確認
      - API Version 2024-06-01-preview使用確認
    </verification>
  </step>

  <step id="2" duration="20min">
    <title>Python SDK更新（semantic_search.py作成）</title>
    <action>
      1. src/semantic_search.py新規作成
      2. query_type="semantic"パラメータ追加
      3. semantic_configuration_name設定
      4. query_caption="extractive"有効化
    </action>
    <verification>
      - 単一クエリでsemantic_search.py実行
      - レスポンスにcaptionsフィールド含有確認
      - 応答時間+100-200ms増加許容
    </verification>
  </step>

  <step id="3" duration="15min">
    <title>3-Item精度検証</title>
    <action>
      1. data/qa_dataset_22.jsonlから3項目選択
      2. semantic_search.py個別実行
      3. 従来検索との比較分析
    </action>
    <verification>
      - @search.rerankerScore存在確認
      - Caption品質の視覚確認
      - Groundedness向上の定性評価
    </verification>
  </step>

  <step id="4" duration="30min">
    <title>100-Item評価パイプライン実装</title>
    <action>
      1. batch_evaluation_v9.py作成
      2. semantic=TrueパラメータでAzure AI Search呼び出し
      3. 評価実行（22項目で完全評価）
    </action>
    <verification>
      - Groundedness ≥ 0.85達成確認
      - Coherence/Relevance維持確認
      - results/evaluation_results_v9.json保存
    </verification>
  </step>

  <step id="5" duration="15min">
    <title>結果分析とDECISIONS.md更新</title>
    <action>
      1. 評価結果の統計分析
      2. Semantic Ranker採用判断をDECISIONS.md記録
      3. コスト影響分析（Free tier内確認）
    </action>
    <verification>
      - DECISIONS.md: ADR形式記録完了
      - TRADEOFFS.md: 却下オプション記録
      - Git commit完了
    </verification>
  </step>

  <step id="6" duration="10min">
    <title>D21-4完了とD22準備</title>
    <action>
      1. セッションサマリー生成
      2. 次フェーズ（D22データ拡張）への移行計画
      3. 最終Git push
    </action>
    <verification>
      - 全ての変更がGitHubに反映
      - SESSION_META_D22_START.md生成
    </verification>
  </step>
</implementation_plan>

<code_templates>
  <bicep_update>
```bicep
// infra/main.bicep - Semantic Ranker追加
resource search 'Microsoft.Search/searchServices@2024-06-01-preview' = {
  name: searchServiceName
  location: location
  sku: {
    name: 'basic'
  }
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    replicaCount: 1
    partitionCount: 1
    hostingMode: 'default'
    publicNetworkAccess: 'enabled'
    semanticSearch: 'free'  // ← 追加
    authOptions: {
      aadOrApiKey: {
        aadAuthFailureMode: 'http401WithBearerChallenge'
      }
    }
  }
}
```
  </bicep_update>

  <semantic_search_py>
```python
"""
semantic_search.py - Semantic Ranker検証スクリプト

Usage:
  python src/semantic_search.py "Azure AI Searchのセマンティックランキングとは？"
"""
import os
import sys
from azure.identity import DefaultAzureCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from openai import AzureOpenAI

# 環境変数
SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
SEARCH_INDEX = os.getenv("AZURE_SEARCH_INDEX")
OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
OPENAI_EMBEDDING = os.getenv("AZURE_OPENAI_DEPLOYMENT_EMBEDDING", "text-embedding-ada-002")

def get_embedding(text: str) -> list[float]:
    """テキストをベクトル埋め込みに変換"""
    credential = DefaultAzureCredential()
    client = AzureOpenAI(
        azure_endpoint=OPENAI_ENDPOINT,
        azure_ad_token_provider=lambda: credential.get_token(
            "https://cognitiveservices.azure.com/.default"
        ).token,
        api_version="2024-10-01-preview"
    )
    
    response = client.embeddings.create(
        model=OPENAI_EMBEDDING,
        input=text
    )
    return response.data[0].embedding

def semantic_search(query: str, top_k: int = 5):
    """Semantic Ranker有効のハイブリッド検索"""
    credential = DefaultAzureCredential()
    search_client = SearchClient(
        endpoint=SEARCH_ENDPOINT,
        index_name=SEARCH_INDEX,
        credential=credential
    )
    
    # ベクトル埋め込み生成
    query_vector = get_embedding(query)
    
    # ベクトルクエリ構成
    vector_query = VectorizedQuery(
        vector=query_vector,
        k_nearest_neighbors=top_k,
        fields="contentVector"
    )
    
    # Semantic Search実行
    results = search_client.search(
        search_text=query,
        query_type="semantic",  # ← Semantic Ranker有効
        semantic_configuration_name="default",
        query_caption="extractive",  # キャプション生成
        query_answer="extractive",   # 回答抽出
        vector_queries=[vector_query],
        select=["id", "title", "content", "category"],
        top=top_k
    )
    
    print(f"\n🔍 クエリ: {query}\n")
    print("=" * 80)
    
    for idx, result in enumerate(results, 1):
        print(f"\n【結果 {idx}】")
        print(f"タイトル: {result.get('title', 'N/A')}")
        print(f"カテゴリ: {result.get('category', 'N/A')}")
        print(f"スコア: {result.get('@search.score', 'N/A')}")
        print(f"Rerankerスコア: {result.get('@search.reranker_score', 'N/A')}")
        
        # Caption表示
        captions = result.get('@search.captions', [])
        if captions:
            print(f"キャプション:")
            for cap in captions:
                print(f"  - {cap.text}")
        
        print(f"内容（抜粋）: {result.get('content', '')[:200]}...")
        print("-" * 80)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使用方法: python src/semantic_search.py 'クエリテキスト'")
        sys.exit(1)
    
    query_text = sys.argv[1]
    semantic_search(query_text)
```
  </semantic_search_py>

  <batch_evaluation_v9>
```python
"""
batch_evaluation_v9.py - Semantic Ranker対応評価パイプライン

変更点:
- semantic=Trueパラメータ追加
- @search.reranker_scoreロギング
- Caption品質評価
"""
import os
import json
import time
from datetime import datetime
from typing import List, Dict
from azure.identity import DefaultAzureCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from openai import AzureOpenAI

# ... (get_embedding, retrieve_context_semantic関数は省略)

def retrieve_context_semantic(
    query: str,
    search_client: SearchClient,
    openai_client: AzureOpenAI,
    top_k: int = 5,
    semantic: bool = True  # ← 新パラメータ
) -> List[Dict]:
    """Semantic Ranker対応のコンテキスト取得"""
    query_vector = get_embedding(query, openai_client)
    
    vector_query = VectorizedQuery(
        vector=query_vector,
        k_nearest_neighbors=top_k,
        fields="contentVector"
    )
    
    search_params = {
        "search_text": query,
        "vector_queries": [vector_query],
        "select": ["id", "title", "content", "category"],
        "top": top_k
    }
    
    if semantic:
        search_params.update({
            "query_type": "semantic",
            "semantic_configuration_name": "default",
            "query_caption": "extractive"
        })
    
    results = search_client.search(**search_params)
    
    retrieved_docs = []
    for r in results:
        doc = {
            "title": r.get("title", ""),
            "content": r.get("content", ""),
            "category": r.get("category", ""),
            "score": r.get("@search.score", 0)
        }
        
        if semantic:
            doc["reranker_score"] = r.get("@search.reranker_score", None)
            doc["captions"] = [c.text for c in r.get("@search.captions", [])]
        
        retrieved_docs.append(doc)
    
    return retrieved_docs

# ... (評価ループでsemantic=True指定)
```
  </batch_evaluation_v9>
</code_templates>

<references>
  <microsoft_docs>
    - [Semantic Search Overview](https://learn.microsoft.com/en-us/azure/search/semantic-search-overview)
    - [Semantic Ranking Configuration](https://learn.microsoft.com/en-us/azure/search/semantic-how-to-query-request)
    - [Azure AI Search API 2024-06-01-preview](https://learn.microsoft.com/en-us/rest/api/searchservice/2024-06-01-preview/search-service)
    - [Semantic Ranker Pricing](https://azure.microsoft.com/en-us/pricing/details/search/)
  </microsoft_docs>

  <technical_insights>
    - L2 Semantic Ranker: 月1,000クエリまで無料
    - 処理対象: 検索結果Top 50をDeep Learningモデルで再ランキング
    - レイテンシ: +100-200ms（許容範囲内）
    - Caption生成: クエリとの関連性が高い箇所を自動抽出
  </technical_insights>

  <best_practices>
    1. 3-item検証を先行実施（品質確認）
    2. Free tier制限内での運用設計
    3. Rerankerスコアのロギング徹底
    4. 従来検索との比較分析
    5. DECISIONS.mdへのADR記録
  </best_practices>
</references>

<troubleshooting>
  <common_issues>
    <issue id="1">
      <symptom>Semantic Ranker設定後もreranker_scoreが返らない</symptom>
      <cause>API Version 2024-06-01-preview未使用</cause>
      <solution>
        azure-search-documents==11.6.0以上確認
        search_client作成時にapi_version明示指定
      </solution>
    </issue>

    <issue id="2">
      <symptom>"Semantic search is not enabled" エラー</symptom>
      <cause>Bicepデプロイ未完了</cause>
      <solution>
        az deployment group show実行
        provisioningState: Succeeded確認
        Portal再読み込み
      </solution>
    </issue>

    <issue id="3">
      <symptom>レイテンシが4秒超過</symptom>
      <cause>Semantic Ranker処理時間</cause>
      <solution>
        top_k=3に削減（5→3）
        並列処理検討（非同期評価）
      </solution>
    </issue>
  </common_issues>
</troubleshooting>

<expected_outcomes>
  <quantitative>
    - Groundedness: 0.76 → 0.85 (+12%)
    - Coherence: 0.988維持
    - Relevance: 0.963維持
    - Response Time: 3.2s → 3.5s (許容)
  </quantitative>

  <qualitative>
    - Caption品質の視覚的改善
    - 意味的に関連性の高いドキュメント優先表示
    - エンドユーザー満足度向上（定性評価）
  </qualitative>

  <documentation>
    - DECISIONS.md: Semantic Ranker採用ADR
    - TRADEOFFS.md: 却下オプション（Standard tier等）
    - results/evaluation_results_v9.json
  </documentation>
</expected_outcomes>

<next_session_trigger>
  <conditions>
    - Groundedness 0.85達成確認
    - 全Git変更のpush完了
    - DECISIONS.md更新完了
  </conditions>

  <next_phase>
    D22-1: データ拡張パイプライン（22→100項目）
    - Azure OpenAI Assistants APIによる自動Q&A生成
    - 品質検証とフィルタリング
    - インデックス再構築
  </next_phase>
</next_session_trigger>
</session_context>
```

---

## 使用方法

### 新セッション開始時

新しいClaudeセッションで以下のいずれかを実行：

**方法1: ファイル読み込み（推奨）**
```
「docs/sessions/SESSION_META_D21-4_START.mdを読んで、D21-4セッションを開始してください」
```

**方法2: コンテキスト直接提供**
```bash
# ローカルで表示
cat docs/sessions/SESSION_META_D21-4_START.md
```
→ 表示内容全体をコピーして新セッションに貼り付け

---

## チェックリスト

### セッション開始前
- [ ] Azure環境へのログイン確認
- [ ] VS Code起動、venv有効化
- [ ] Git状態確認（未コミットなし）
- [ ] 実装時間確保（90分目安）

### セッション実施中
- [ ] Step 1-6を順番に実施
- [ ] 各ステップの検証完了確認
- [ ] エラー発生時はTroubleshootingセクション参照

### セッション終了時
- [ ] Groundedness 0.85達成確認
- [ ] DECISIONS.md更新
- [ ] Git commit & push
- [ ] 次セッション用メタプロンプト生成

---

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-12-25 | Ryo | Initial meta-prompt creation |

---

**🎯 成功の定義**: Groundedness 0.85達成 + 判断過程の完全記録
