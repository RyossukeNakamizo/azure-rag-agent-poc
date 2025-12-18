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
