### Simple str() Implementation (Option B)

**Category**: Implementation Pattern

**Considered For**: OData search.in filter encoding

**Original Approach (Pre-fix)**
```python
def add_in(self, field: str, values: List[Any]) -> "FilterBuilder":
    """Add an OData search.in filter for multi-value matching."""
    if not values:
        logger.warning("empty_values_for_in_filter", field=field)
        return self
    
    self._validate_field_name(field)
    # Simple str() concatenation (REJECTED)
    str_values = [str(v) for v in values]
    values_str = ",".join(str_values)
    self.filters.append(f"search.in({field}, '{values_str}', ',')")
    return self
```

**Rejection Factors**
| Factor | Weight | Score | Notes |
|--------|--------|-------|-------|
| Type Safety | High | 1/5 | datetime → broken ISO format, bool → "True"/"False" |
| Security | High | 1/5 | No single quote escaping (injection risk) |
| Testability | Medium | 2/5 | Encoding logic coupled with filter construction |
| Maintainability | High | 2/5 | Adding new types requires modifying add_in() |
| Documentation | Low | 3/5 | No clear guidance on supported types |
| Performance | Low | 5/5 | Slightly faster (~5μs/call) than Option A |
| Simplicity | Medium | 5/5 | Only 5 lines of code |

**Detailed Analysis**

1. **Type Safety Issues** (Critical)
   ```python
   # datetime handling (BROKEN)
   from datetime import datetime
   dt = datetime(2024, 12, 18, 15, 0, 0)
   str(dt)  # → "2024-12-18 15:00:00" (missing 'Z', wrong format)
   # Expected: "2024-12-18T15:00:00Z"
   
   # bool handling (BROKEN)
   str(True)   # → "True" (Python capitalization)
   str(False)  # → "False"
   # Expected: "true", "false" (OData lowercase)
   
   # None handling (SILENT FAILURE)
   str(None)  # → "None" (string literal, not null)
   # Expected: Raise ValueError or skip
   ```

2. **Security Vulnerabilities** (Critical)
   ```python
   # Single quote injection
   values = ["O'Reilly", "McDonald's"]
   result = ",".join([str(v) for v in values])
   # → search.in(field, 'O'Reilly,McDonald's', ',')
   #                       ^ unescaped quote breaks syntax
   
   # Correct (Option A):
   # → search.in(field, 'O''Reilly,McDonald''s', ',')
   ```

3. **Testability Issues** (Medium)
   - Encoding logic embedded in `add_in()` method
   - Cannot unit test encoding without full FilterBuilder instantiation
   - Mocking becomes complex for edge case testing

4. **Maintainability Issues** (High)
   - Adding support for new types (e.g., UUID, Decimal) requires:
     1. Modifying `add_in()` directly (violates SRP)
     2. Increasing cyclomatic complexity
     3. Risk of regression bugs in existing logic

**Final Verdict**: 
Rejected due to **critical type safety and security failures**. While simpler, it fails enterprise-grade requirements and creates technical debt that would require future refactoring.

**Revisit Trigger**
- **Prototype/Demo Use Cases**: If building a quick proof-of-concept where:
  - Only string values are used
  - No user input (no injection risk)
  - Short lifespan (<1 week)
  - Not production-bound

- **Performance-Critical Path**: If profiling reveals encoding is a bottleneck (unlikely):
  - Current overhead: ~5μs per call
  - Would need >1000 calls/request to matter
  - Optimization should target algorithm, not implementation

**Comparison Summary**

| Aspect | Option A (Selected) | Option B (Rejected) |
|--------|---------------------|---------------------|
| Lines of Code | ~65 | ~10 |
| Type Safety | ✅ Full | ❌ None |
| Security | ✅ Escaping | ❌ Vulnerable |
| Testability | ✅ Isolated | ⚠️ Coupled |
| Performance | 100μs | 95μs |
| Enterprise Ready | ✅ Yes | ❌ No |

**Historical Context**
- **Original Implementation**: Option B (simple str())
- **Bug Discovery**: Cursor Bot review (2024-12-18)
- **Fix Timeline**: 30 minutes of analysis → 2 hours implementation
- **Decision Process**: Documented in DECISIONS.md#2024-12-18

**Related Decisions**
- DECISIONS.md: "2024-12-18: OData search.in Encoding Strategy"
- ARCHITECTURE.md: "Security First" principle (Managed Identity priority)

**References**
- [Azure AI Search OData Filter Syntax](https://learn.microsoft.com/en-us/azure/search/query-odata-filter-orderby-syntax)
- [Python str() Gotchas](https://docs.python.org/3/library/stdtypes.html#str)
- [OWASP Injection Prevention](https://cheatsheetseries.owasp.org/cheatsheets/Injection_Prevention_Cheat_Sheet.html)

---

### .bicepparam形式

**Category**: Configuration Format

**Considered For**: Bicepパラメータファイル形式

**Rejection Factors**
| Factor | Weight | Score | Notes |
|--------|--------|-------|-------|
| Azure CLI互換性 | High | 2/5 | `using`構文エラー継続、解決不能 |
| 開発効率 | High | 1/5 | トラブルシューティングに45分消費 |
| 安定性 | High | 2/5 | 本番環境で未検証、リスク高 |
| 型安全性 | Medium | 5/5 | 理論上は優位だが実用不可 |

**Final Verdict**: JSON形式が確実性・互換性・実績で圧倒的優位

**Revisit Trigger**: 
- Azure CLI 2.60.0+で.bicepparam完全サポート確認
- Microsoft公式ドキュメントで本番推奨時

---

### 全リソース削除して再作成

**Category**: Deployment Strategy

**Considered For**: RBAC重複エラー解決方法

**Rejection Factors**
| Factor | Weight | Score | Notes |
|--------|--------|-------|-------|
| データ保護 | High | 1/5 | Hub/Projectメタデータ喪失リスク |
| 実装時間 | Medium | 2/5 | 再作成に10-15分必要 |
| 運用リスク | High | 1/5 | 本番環境で同様の操作は危険 |

**Final Verdict**: 既存リソース参照アプローチでリスク回避

**Revisit Trigger**: 完全にクリーンな環境が必要な場合のみ

---

### API Key認証

**Category**: Authentication Method

**Considered For**: Azure AI Search Connection認証

**Rejection Factors**
| Factor | Weight | Score | Notes |
|--------|--------|-------|-------|
| セキュリティ | High | 1/5 | キー漏洩リスク、ローテーション負荷 |
| 監査性 | High | 2/5 | アクセス追跡困難 |
| ベストプラクティス | High | 1/5 | Microsoftが非推奨 |
| 即効性 | Low | 5/5 | 唯一の利点だが不十分 |

**Final Verdict**: Managed Identity認証で最大10分待機する価値あり

**Revisit Trigger**: ローカル開発環境での一時使用のみ

---

### インデックス即座作成（Day 15内完了）

**Category**: Implementation Scope

**Considered For**: Azure AI Search Index作成タイミング

**Rejection Factors**
| Factor | Weight | Score | Notes |
|--------|--------|-------|-------|
| 複雑性 | High | 2/5 | Schema設計、データ準備で30-60分必要 |
| Day 15目標達成 | High | 3/5 | Hub/Project/Connections完了で十分 |
| 段階的実装 | Medium | 5/5 | Day 16で集中実施の方が効率的 |

**Final Verdict**: Day 16でIndex作成に集中する方が品質向上

**Revisit Trigger**: なし（適切な判断）
