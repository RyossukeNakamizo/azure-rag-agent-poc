"""RAGパイプライン完全診断"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from evaluation.flow.nodes.retrieve import retrieve_context
from evaluation.flow.nodes.generate_answer import generate_answer
from evaluation.flow.nodes.evaluate_groundedness import evaluate_groundedness

# テスト質問
question = "HNSWアルゴリズムのパラメータm、efConstruction、efSearchの推奨値は？"

print("=" * 70)
print("RAG Pipeline Diagnosis")
print("=" * 70)

# Step 1: 検索
print("\n[Step 1] Retrieve Context")
print(f"Question: {question}\n")

retrieve_result = retrieve_context(question)
print(f"Retrieved: {retrieve_result['num_results']} documents\n")

if retrieve_result['num_results'] == 0:
    print("❌ ERROR: No documents retrieved!")
    sys.exit(1)

# 検索結果詳細
for i, doc in enumerate(retrieve_result['context'][:3], 1):
    print(f"[Doc {i}]")
    print(f"  Title: {doc['title']}")
    print(f"  Content: {doc['content'][:150]}...")
    print(f"  Score: {doc['score']:.4f}")
    print(f"  Source: {doc['source']}\n")

# Step 2: コンテキスト整形
print("[Step 2] Format Context")
context_str = "\n\n".join([
    f"[Document {i+1}]\nTitle: {ctx['title']}\nContent: {ctx['content']}"
    for i, ctx in enumerate(retrieve_result['context'])
])
print(f"Context length: {len(context_str)} characters")
print(f"Context preview:\n{context_str[:300]}...\n")

# Step 3: 回答生成
print("[Step 3] Generate Answer")
answer_result = generate_answer(question=question, context=context_str)

# 戻り値の型確認
print(f"Answer type: {type(answer_result)}")

if isinstance(answer_result, dict):
    answer_text = answer_result.get('answer', str(answer_result))
    print(f"Answer (from dict): {answer_text[:200]}...\n")
elif isinstance(answer_result, str):
    answer_text = answer_result
    print(f"Answer (string): {answer_text[:200]}...\n")
else:
    print(f"❌ Unexpected answer type: {type(answer_result)}")
    answer_text = str(answer_result)
    print(f"Answer (forced string): {answer_text[:200]}...\n")

# Step 4: Groundedness評価
print("[Step 4] Evaluate Groundedness")
print(f"Evaluating with:")
print(f"  Answer length: {len(answer_text)} chars")
print(f"  Context length: {len(context_str)} chars\n")

groundedness_score = evaluate_groundedness(answer=answer_text, context=context_str)

print(f"Groundedness Score: {groundedness_score}")

# 判定
if groundedness_score >= 0.85:
    print("✅ PASS: Score meets target (0.85)")
elif groundedness_score >= 0.5:
    print("⚠️  WARN: Score below target but acceptable")
else:
    print("❌ FAIL: Score critically low")
    print("\nDiagnostic hints:")
    print("  - Check if answer uses information from context")
    print("  - Verify LLM is actually reading the context")
    print("  - Review evaluate_groundedness prompt")

print("\n" + "=" * 70)
