"""Batch Evaluation Script - v4 (評価関数引数修正)"""
import json
import sys
import inspect
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from evaluation.flow.nodes.retrieve import retrieve_context
from evaluation.flow.nodes.generate_answer import generate_answer
from evaluation.flow.nodes.evaluate_groundedness import evaluate_groundedness
from evaluation.flow.nodes.evaluate_coherence import evaluate_coherence
from evaluation.flow.nodes.evaluate_relevance import evaluate_relevance

def format_context(context_list):
    if isinstance(context_list, str):
        return context_list
    formatted = []
    for i, ctx in enumerate(context_list, 1):
        if isinstance(ctx, dict):
            title = ctx.get("title", "")
            content = ctx.get("content", "")
            formatted.append(f"[Document {i}]\nTitle: {title}\nContent: {content}")
    return "\n\n".join(formatted)

def normalize_answer(result):
    if isinstance(result, dict):
        return result.get("answer", str(result))
    return str(result)

def safe_evaluate(func, **kwargs):
    sig = inspect.signature(func)
    params = sig.parameters
    valid_kwargs = {k: v for k, v in kwargs.items() if k in params}
    result = func(**valid_kwargs)
    if isinstance(result, dict):
        return result.get("score", 0.0)
    elif isinstance(result, (int, float)):
        return float(result)
    else:
        return 0.0

def run_rag_pipeline(question: str):
    retrieve_result = retrieve_context(question)
    if retrieve_result["num_results"] == 0:
        raise ValueError("No documents retrieved")
    context_str = format_context(retrieve_result["context"])
    generate_result = generate_answer(question=question, context=context_str)
    answer_text = normalize_answer(generate_result)
    groundedness_score = safe_evaluate(evaluate_groundedness, answer=answer_text, context=context_str, question=question)
    coherence_score = safe_evaluate(evaluate_coherence, answer=answer_text, context=context_str, question=question)
    relevance_score = safe_evaluate(evaluate_relevance, answer=answer_text, context=context_str, question=question)
    return {"question": question, "num_retrieved_docs": retrieve_result["num_results"], "answer": answer_text, "scores": {"groundedness": groundedness_score, "coherence": coherence_score, "relevance": relevance_score}}

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default="evaluation_dataset.jsonl")
    parser.add_argument("--num-samples", type=int, default=20)
    args = parser.parse_args()
    print(f"=== RAG Batch Evaluation (v4) ===")
    print(f"Samples: {args.num_samples}\n")
    questions = []
    with open(args.dataset, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i >= args.num_samples:
                break
            data = json.loads(line)
            questions.append(data.get("question", ""))
    print(f"Loaded {len(questions)} questions\n")
    results = []
    scores_sum = {"groundedness": 0.0, "coherence": 0.0, "relevance": 0.0}
    success = 0
    for i, q in enumerate(questions, 1):
        print(f"[{i}/{len(questions)}] {q[:60]}...")
        try:
            result = run_rag_pipeline(q)
            print(f"  ✅ G={result['scores']['groundedness']:.2f} C={result['scores']['coherence']:.2f} R={result['scores']['relevance']:.2f}")
            results.append(result)
            for k, v in result["scores"].items():
                scores_sum[k] += v
            success += 1
        except Exception as e:
            print(f"  ❌ {type(e).__name__}: {str(e)[:100]}")
    avg_scores = {k: v / success for k, v in scores_sum.items()} if success > 0 else {}
    print(f"\n{'='*60}")
    print(f"=== Summary ===")
    print(f"Success: {success}/{len(questions)} ({success/len(questions)*100:.1f}%)")
    print(f"Groundedness: {avg_scores.get('groundedness', 0):.3f} (target: 0.85)")
    print(f"Coherence:    {avg_scores.get('coherence', 0):.3f} (target: 0.75)")
    print(f"Relevance:    {avg_scores.get('relevance', 0):.3f} (target: 0.80)")
    Path("results").mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = f"results/d20_batch_v4_{timestamp}.json"
    with open(output, "w", encoding="utf-8") as f:
        json.dump({"timestamp": timestamp, "total": len(questions), "success": success, "metrics": avg_scores, "results": results}, f, indent=2, ensure_ascii=False)
    print(f"\n✅ Results saved: {output}")
    if success > 0:
        print(f"\n{'='*60}")
        targets = [("Groundedness", avg_scores.get("groundedness", 0), 0.85), ("Coherence", avg_scores.get("coherence", 0), 0.75), ("Relevance", avg_scores.get("relevance", 0), 0.80)]
        for name, actual, target in targets:
            status = "✅" if actual >= target else "⚠️"
            diff = actual - target
            print(f"{status} {name:15s}: {actual:.3f} (target: {target:.2f}, diff: {diff:+.3f})")
    return 0 if success > 0 else 1

if __name__ == "__main__":
    sys.exit(main())
