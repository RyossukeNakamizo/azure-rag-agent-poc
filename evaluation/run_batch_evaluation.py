"""Batch Evaluation Script for RAG Pipeline"""
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from evaluation.flow.nodes.retrieve import retrieve_context
from evaluation.flow.nodes.generate_answer import generate_answer
from evaluation.flow.nodes.evaluate_groundedness import evaluate_groundedness
from evaluation.flow.nodes.evaluate_coherence import evaluate_coherence
from evaluation.flow.nodes.evaluate_relevance import evaluate_relevance

def run_rag_pipeline(question: str) -> Dict[str, Any]:
    retrieve_result = retrieve_context(question)
    generate_result = generate_answer(question=question, context=retrieve_result['context'])
    groundedness = evaluate_groundedness(answer=generate_result['answer'], context=retrieve_result['context'])
    coherence = evaluate_coherence(question=question, answer=generate_result['answer'])
    relevance = evaluate_relevance(question=question, answer=generate_result['answer'])
    return {
        "question": question,
        "num_retrieved_docs": retrieve_result['num_results'],
        "answer": generate_result['answer'],
        "scores": {
            "groundedness": groundedness.get('score', 0.0),
            "coherence": coherence.get('score', 0.0),
            "relevance": relevance.get('score', 0.0)
        }
    }

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset', default='evaluation_dataset.jsonl')
    parser.add_argument('--num-samples', type=int, default=20)
    args = parser.parse_args()
    
    print(f"=== RAG Batch Evaluation ===")
    print(f"Samples: {args.num_samples}\n")
    
    questions = []
    with open(args.dataset, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if i >= args.num_samples:
                break
            data = json.loads(line)
            questions.append(data.get('question', ''))
    
    print(f"Loaded {len(questions)} questions\n")
    
    results = []
    scores_sum = {"groundedness": 0.0, "coherence": 0.0, "relevance": 0.0}
    success = 0
    
    for i, q in enumerate(questions, 1):
        print(f"[{i}/{len(questions)}] {q[:60]}...")
        try:
            result = run_rag_pipeline(q)
            print(f"  Scores: G={result['scores']['groundedness']:.2f} C={result['scores']['coherence']:.2f} R={result['scores']['relevance']:.2f}")
            results.append(result)
            for k, v in result['scores'].items():
                scores_sum[k] += v
            success += 1
        except Exception as e:
            print(f"  Error: {e}")
    
    avg_scores = {k: v / success for k, v in scores_sum.items()} if success > 0 else {}
    
    print(f"\n=== Summary ===")
    print(f"Success: {success}/{len(questions)}")
    print(f"Groundedness: {avg_scores.get('groundedness', 0):.3f}")
    print(f"Coherence: {avg_scores.get('coherence', 0):.3f}")
    print(f"Relevance: {avg_scores.get('relevance', 0):.3f}")
    
    Path("results").mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = f"results/d20_batch_{timestamp}.json"
    
    with open(output, 'w', encoding='utf-8') as f:
        json.dump({"timestamp": timestamp, "total": len(questions), "success": success, "metrics": avg_scores, "results": results}, f, indent=2, ensure_ascii=False)
    
    print(f"\nResults saved: {output}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
