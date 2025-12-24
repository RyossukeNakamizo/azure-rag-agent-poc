import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from evaluation.flow.nodes.evaluate_groundedness import evaluate_groundedness

# テスト実行
answer = "Azure AI Searchでベクトル検索可能なインデックスを作成するには、vector属性を設定します。"
context = "[Document 1]\nTitle: Vector Search\nContent: ベクトル検索を有効にするにはvector属性が必要です。"

print("Testing evaluate_groundedness...")
print(f"Answer: {answer}")
print(f"Context: {context[:100]}...")

result = evaluate_groundedness(answer=answer, context=context)

print(f"\nResult type: {type(result)}")
print(f"Result value: {result}")

if isinstance(result, dict):
    print(f"Score: {result.get('score', 'N/A')}")
