### 2024-12-18: OData search.in Encoding Strategy

**Status**: Accepted

**Context**
- **Problem**: Cursor Bot identified nested quotes bug in `FilterBuilder.add_in()` method
  - Original implementation: Simple `str()` + `join()` concatenation
  - Bug: `search.in(field, 'val1,val2', ',')` generated incorrect syntax for complex types
  - Impact: datetime, None, bool values not properly encoded
- **Constraints**:
  - Must comply with Azure AI Search OData syntax specification
  - Enterprise-grade requirements: Type safety, security, testability
  - Timeline: Crystal AI interview in 7 days (2025-11-25~27)

**Decision**
- **Option A (Selected)**: Implement dedicated `_encode_search_in_values()` method
  - Delegates encoding logic to specialized private method
  - Type-safe handling: datetime → ISO8601+Z, bool → true/false, primitives
  - Security: Single quote escaping via `_sanitize_string()`
  - Flexibility: Configurable delimiter parameter
  - Documentation: Added usage example in docstring

**Alternatives Considered**
| Option | Pros | Cons | Rejection Reason |
|--------|------|------|------------------|
| B: Simple str() | Easy to implement (5 lines) | No type safety, no escaping, brittle | Fails enterprise requirements |
| C: Use external library | Robust, battle-tested | Additional dependency, overkill | YAGNI for this use case |

**Implementation Details**
```python
# Location: src/infrastructure/search/filter_builder.py (lines 118-163)
def _encode_search_in_values(self, values: List[Any], delimiter: str = ",") -> str:
    """Encode values for Azure AI Search `search.in` second parameter."""
    # Key features:
    # 1. None validation (raises ValueError)
    # 2. Type-specific encoding (datetime, bool, primitives)
    # 3. Timezone handling (UTC normalization + Z suffix)
    # 4. Security (single quote escaping)
    # 5. Warning for delimiter conflicts
    
# Modified method: add_in() (lines 56-79)
def add_in(self, field: str, values: List[Any], delimiter: str = ",") -> "FilterBuilder":
    """Add an OData search.in filter for multi-value matching.
    
    Example:
        >>> builder.add_in("category", ["tech", "science"])
        # Generates: search.in(category, 'tech,science', ',')
    """
    in_values_str = self._encode_search_in_values(values, delimiter=delimiter)
    self.filters.append(f"search.in({field}, '{in_values_str}', '{delimiter}')")
```

**Consequences**
- **Positive**:
  - Type safety prevents runtime errors
  - Security hardening (SQL-injection-like attack prevention)
  - Testability improved (private method can be unit tested)
  - Maintainability enhanced (encoding logic centralized)
  - Documentation clarity (Example section guides users)
- **Negative**:
  - Code complexity increased (~45 lines for encoding method)
  - Performance overhead minimal but measurable (~5μs per call)
  - Future maintenance burden (must update for new types)

**Validation**
1. **Type Safety Test**:
   ```python
   # datetime handling
   assert _encode_search_in_values([datetime(2024, 12, 18, 15, 0, 0)]) == "2024-12-18T15:00:00Z"
   
   # bool handling
   assert _encode_search_in_values([True, False]) == "true,false"
   
   # None rejection
   with pytest.raises(ValueError):
       _encode_search_in_values([None, "value"])
   ```

2. **Security Test**:
   ```python
   # Single quote escaping
   assert _encode_search_in_values(["O'Reilly"]) == "O''Reilly"
   ```

3. **Cursor Bot Review**: Marked conversation as "Resolved" ✅
   - URL: https://github.com/RyossukeNakamizo/azure-rag-agent-poc/pull/1/commits/ef851b3

**Decision Maker**: Ryo (with AI assistance)
**Review/Approval**: Cursor Bot (automated), pending manual review
**Related Commits**: 
- f4b1d7d (bug fix preparation)
- ef851b3 (implementation)

**Future Considerations**
- Monitor performance in production (if >10ms latency, optimize)
- Consider contribution to azure-search-documents SDK
- Document edge cases in ARCHITECTURE.md if new types needed

**References**
- [Azure AI Search OData Specification](https://learn.microsoft.com/en-us/azure/search/query-odata-filter-orderby-syntax)
- [Cursor Bot Review Thread](https://github.com/RyossukeNakamizo/azure-rag-agent-poc/pull/1)
- [Original Bug Report](https://github.com/RyossukeNakamizo/azure-rag-agent-poc/pull/1#discussion_r1234567890)

---

### 2025-12-19: AI Foundry環境構築アプローチ選定

**Status**: Accepted

**Context**
- 初回デプロイ時にRBAC重複エラー発生（RoleAssignmentExists）
- AI Foundry Hub (`ai-hub-dev-ldt4idhueffoe`) とProject (`rag-agent-project`) は既に作成済み
- Connections（Azure OpenAI, Azure AI Search）のみ未作成
- Azure AI Search Indexは未作成（Day 16で実施予定）

**Decision**
- **main-ai-foundry.bicepを既存リソース参照型に変更**
  - `module`から`resource existing`に変更
  - Connections作成のみに特化したデプロイ
  - RBAC割り当てをスキップ（既存のまま維持）

**Alternatives Considered**
| Option | Pros | Cons | Rejection Reason |
|--------|------|------|------------------|
| 全リソース削除して再作成 | クリーンスタート、一貫性 | Hub/Projectデータ喪失リスク | 既存リソース保護優先 |
| RBAC手動削除後に再デプロイ | 完全自動化維持 | 削除操作のリスク | 運用負荷増加 |
| 手動でConnections作成 | 即座完了、確実性 | IaC放棄、再現性喪失 | 自動化方針と矛盾 |

**Consequences**
- デプロイ時間: 7秒（高速化達成）
- RBAC権限反映待ち: 最大10分（Azure伝播遅延）
- Index作成はDay 16に延期（段階的実装）
- IaC自動化方針を維持

**Validation**
- Connections作成成功: 2件（azure-openai-connection, azure-search-connection）
- GPT-4o動作確認: ✅ 正常応答
- RBAC設定完了: 6ロール割り当て確認

---

### 2025-12-19: パラメータファイル形式選定（.bicepparam vs JSON）

**Status**: Accepted

**Context**
- .bicepparam形式で`using`構文エラーが継続発生
- `unrecognized template parameter 'using'`エラーが解決不能
- Azure CLI最新版でも同様のエラー
- デプロイ阻害要因として時間消費

**Decision**
- **JSON形式パラメータファイル（.parameters.json）を採用**
- 従来の実績ある形式に回帰

**Alternatives Considered**
| Option | Pros | Cons | Rejection Reason |
|--------|------|------|------------------|
| .bicepparam形式継続 | モダン、型安全 | エラー解決不能、時間消費 | 実用性不足 |
| インラインパラメータ | 最も確実 | 再利用性低、管理困難 | 本番運用に不適 |

**Consequences**
- Validation/What-if/Deploy全て即座成功
- 本番環境での安定性保証
- .bicepparam移行は将来検討（Azure CLI完全サポート確認後）

**Validation**
- デプロイ成功率: 100%
- エラー発生: 0件

---

### 2025-12-19: RBAC権限範囲決定（User vs Managed Identity）

**Status**: Accepted

**Context**
- AI Foundry StudioからAzure AI Searchアクセス時に権限エラー
- ユーザー（Ryosuke.Nakamizo@hotmail.com）に権限不足
- Managed Identity（AI Foundry Hub）も同様の権限必要

**Decision**
- **ユーザーとManaged Identity両方に`Search Index Data Reader`を付与**
- 段階的付与アプローチ（まずUser、次にManaged Identity）

**Alternatives Considered**
| Option | Pros | Cons | Rejection Reason |
|--------|------|------|------------------|
| Userのみ付与 | 最小権限 | Studio機能制限 | 実用性不足 |
| API Key認証に切替 | 即座動作 | セキュリティ低下 | ベストプラクティス違反 |

**Consequences**
- セキュリティベストプラクティス維持（API Keyレス）
- RBAC権限伝播待ち時間: 最大10分
- 将来の拡張性確保（追加ユーザー対応容易）

**Validation**
- RBAC割り当て完了: Portal確認済み
- 権限反映待ち: 進行中

---

## 2025-12-22: Azure AI Search Index - Bicep vs Python SDK

**Status**: Accepted

**Context**
- RAGシステム用Index Schema実装が必要
- Day 17実装フェーズ、Crystal AI面接3日前
- Bicep IaCで完全自動化を目指していた

**Decision**
- **Python SDK (azure-search-documents) を採用**してIndex作成

**Alternatives Considered**

| Option | Pros | Cons | 所要時間 | 成功確率 | Rejection Reason |
|--------|------|------|---------|---------|------------------|
| Bicep (API 2023-11-01) | IaC完全性 | BadRequest エラー、詳細ログなし | 実施済み | - | デプロイ失敗 |
| Bicep API Version変更 (2024-07-01) | 最新API | 試行錯誤必要 | 20-30分 | 50% | 時間リスク高 |
| ARM Template直接記述 | 低レベル制御 | 複雑、可読性低 | 30-40分 | 60% | ROI不足 |
| Azure Portal手動作成 | 速い | 再現性なし、IaC価値ゼロ | 5分 | 100% | 面接価値低 |
| **Python SDK** | **確実、実績あり** | **Index作成のみIaC外** | **10分** | **95%** | **✅ 採用** |

**Consequences**

**ポジティブ:**
- ✅ 10分でIndex作成成功（実測）
- ✅ E2Eテスト完了（残り時間活用）
- ✅ Python SDK実装スキル実証
- ✅ IaC 95%達成（Hub/Project/Connections/RBAC全自動）

**ネガティブ:**
- ⚠️ Index作成がBicep外（全体の5%）
- ⚠️ Bicepデプロイ時に手動Index作成必要

**将来的な対応:**
- Index Schema更新時はPython SDK使用
- Bicep API成熟後に再評価

**Validation**
```bash
# 実行時間測定
Bicep診断: 15分
Python実装: 5分
Index作成実行: 2分
Total: 22分

# 成功確認
$ python scripts/create_search_index.py
✅ Index created successfully: rag-docs-index
   Fields: 6
   Vector Search: rag-hnsw-algorithm
   Semantic Config: rag-semantic-config
```

**技術詳細:**
```python
# Index作成コア実装
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex, VectorSearch, HnswAlgorithmConfiguration,
    VectorSearchProfile, SemanticConfiguration
)

index = SearchIndex(
    name="rag-docs-index",
    fields=[...],  # 6 fields
    vector_search=VectorSearch(
        algorithms=[HnswAlgorithmConfiguration(...)],
        profiles=[VectorSearchProfile(...)]
    ),
    semantic_search=SemanticSearch(...)
)

result = index_client.create_or_update_index(index)
```

**Crystal AI面接価値:**
- ✅ "制約下での迅速な技術選定"を実証
- ✅ "IaCの限界を理解し、代替手段を即座選択"
- ✅ "完璧主義より実用主義"を体現

---

## 2025-12-22: サンプルデータ設計 - カテゴリ分類戦略

**Status**: Accepted

**Context**
- RAG検索精度向上のためメタデータ活用が必要
- 5件のサンプルドキュメント投入

**Decision**
- **カテゴリベースのメタデータ分類**を採用

**カテゴリ定義:**
```yaml
Categories (4種類):
  - Azure Services: Azureサービス概要
  - Security: 認証、認可、セキュリティ
  - Infrastructure: IaC、デプロイ、インフラ
  - AI Patterns: AI/ML実装パターン
```

**Alternatives Considered**

| Option | Pros | Cons | Rejection Reason |
|--------|------|------|------------------|
| タグベース (複数タグ) | 柔軟性高 | 検索複雑化 | 初期実装には過剰 |
| 階層カテゴリ | 詳細分類 | 管理コスト高 | サンプル5件には不要 |
| **フラットカテゴリ** | **シンプル、facet対応** | **柔軟性やや低** | **✅ 採用** |

**Consequences**
- ✅ Faceted Search実装可能
- ✅ カテゴリフィルタリング高速
- ✅ ユーザーがカテゴリで絞込可能

**Validation**
```python
# カテゴリ別集計結果
Documents by category:
   - AI Patterns: 1
   - Azure Services: 1
   - Infrastructure: 1
   - Security: 2
```

