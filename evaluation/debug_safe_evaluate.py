import sys
from pathlib import Path
import inspect

sys.path.insert(0, str(Path(__file__).parent.parent))

from evaluation.flow.nodes.evaluate_groundedness import evaluate_groundedness

def safe_evaluate_debug(func, **kwargs):
    """デバッグ版safe_evaluate"""
    sig = inspect.signature(func)
    params = sig.parameters
    valid_kwargs = {k: v for k, v in kwargs.items() if k in params}
    
    print(f"Function: {func.__name__}")
    print(f"Valid kwargs: {list(valid_kwargs.keys())}")
    
    result = func(**valid_kwargs)
    
    print(f"Result type: {type(result)}")
    print(f"Result value: {result}")
    
    if isinstance(result, dict):
        score = result.get('score', 0.0)
        print(f"Extracted score from dict: {score}")
        return score
    elif isinstance(result, (int, float)):
        print(f"Returning float directly: {result}")
        return float(result)
    else:
        print(f"Unknown type, returning 0.0")
        return 0.0

# テスト
answer = "ベクトル検索にはvector属性が必要です。"
context = "ベクトル検索を有効にするにはvectorフィールドを定義します。"

score = safe_evaluate_debug(
    evaluate_groundedness,
    answer=answer,
    context=context,
    question="テスト質問"
)

print(f"\nFinal score: {score}")
