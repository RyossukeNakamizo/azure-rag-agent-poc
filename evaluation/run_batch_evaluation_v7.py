"""
バッチ評価 v7 - LLM-as-Judge強化版

3評価指標（全てLLM-as-Judge）:
- Groundedness v2 - 目標0.85+
- Coherence v2 - 目標0.85+
- Relevance v2 - 目標0.85+

比較用（旧版）:
- Groundedness v1 - ベースライン0.76
- Coherence v1 - ベースライン0.66
- Relevance v1 - ベースライン0.23
"""
import json
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
import sys
from dotenv import load_dotenv

# 環境変数ロード
load_dotenv()

# ノードインポート
sys.path.append(str(Path(__file__).parent))
from flow.nodes.retrieve import retrieve_context
from flow.nodes.generate_answer import generate_answer
from flow.nodes.evaluate_groundedness import evaluate_groundedness
from flow.nodes.evaluate_groundedness_v2 import evaluate_groundedness_v2
from flow.nodes.evaluate_coherence import evaluate_coherence
from flow.nodes.evaluate_coherence_v2 import evaluate_coherence_v2
from flow.nodes.evaluate_relevance import evaluate_relevance
from flow.nodes.evaluate_relevance_v2 import evaluate_relevance_v2


def load_questions(limit: int = None) -> List[Dict[str, str]]:
    """テスト質問ロード"""
    questions = [
        {"question": "Azure AI Searchのセマンティック検索を有効化する方法は？"},
        {"question": "Managed Identityの利点を教えてください"},
        {"question": "RAGシステムでベクトル検索を実装する方法は？"},
        {"question": "Bicepでリソースをデプロイする手順は？"},
        {"question": "Azure OpenAIのレート制限はどう設定しますか？"},
        {"question": "RBAC権限の最小権限の原則とは？"},
        {"question": "Azure AI Searchのインデックス作成方法は？"},
        {"question": "GitHub ActionsでOIDC認証を設定する方法は？"},
        {"question": "チャンキング戦略の推奨設定は？"},
        {"question": "Private Endpointの利点は何ですか？"},
        {"question": "Azure AI Searchのハイブリッド検索とは？"},
        {"question": "埋め込みモデルtext-embedding-ada-002の次元数は？"},
        {"question": "Bicep変数の命名規則は？"},
        {"question": "Azure DevOps PipelineのWhat-if機能とは？"},
        {"question": "Key Vaultでシークレットをローテーションする方法は？"},
        {"question": "Azure AI SearchのSkillsetとは？"},
        {"question": "ベクトル検索のHNSWアルゴリズムとは？"},
        {"question": "Azure OpenAIのストリーミング応答の実装方法は？"},
        {"question": "Managed Identityの種類は？"},
        {"question": "Azure AI Searchの料金体系は？"},
    ]
    return questions[:limit] if limit else questions


def run_evaluation(questions: List[Dict[str, str]]) -> Dict[str, Any]:
    """バッチ評価実行"""
    results = []
    
    for idx, item in enumerate(questions, 1):
        question = item["question"]
        
        print(f"\n[{idx}/{len(questions)}] {question}")
        
        try:
            # 1. 検索
            retrieve_result = retrieve_context(question=question)
            contexts = [doc["content"] for doc in retrieve_result.get("context", [])]
            context_str = "\n".join(contexts)
            
            if not contexts:
                print("  ⚠️ No contexts found")
                continue
            
            # 2. 回答生成
            answer = generate_answer(question=question, context=context_str)
            
            # 3. v2評価（新版）
            groundedness_v2_result = evaluate_groundedness_v2(answer=answer, context=context_str)
            coherence_v2_result = evaluate_coherence_v2(answer=answer)
            relevance_v2_result = evaluate_relevance_v2(question=question, answer=answer)
            
            # 4. v1評価（比較用）
            groundedness_v1_score = evaluate_groundedness(answer=answer, context=context_str)
            coherence_v1_score = evaluate_coherence(answer=answer)
            relevance_v1_score = evaluate_relevance(question=question, answer=answer)
            
            # 結果記録
            result = {
                "question": question,
                "answer": answer,
                "contexts_count": len(contexts),
                "scores_v2": {
                    "groundedness": groundedness_v2_result["score"],
                    "coherence": coherence_v2_result["score"],
                    "relevance": relevance_v2_result["score"],
                },
                "scores_v1": {
                    "groundedness": groundedness_v1_score,
                    "coherence": coherence_v1_score,
                    "relevance": relevance_v1_score,
                }
            }
            results.append(result)
            
            print(f"  v2 - Groundedness: {result['scores_v2']['groundedness']:.2f}")
            print(f"  v2 - Coherence: {result['scores_v2']['coherence']:.2f}")
            print(f"  v2 - Relevance: {result['scores_v2']['relevance']:.2f}")
            print(f"  (v1: G={result['scores_v1']['groundedness']:.2f}, C={result['scores_v1']['coherence']:.2f}, R={result['scores_v1']['relevance']:.2f})")
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    return {"results": results, "summary": calculate_summary(results)}


def calculate_summary(results: List[Dict]) -> Dict[str, float]:
    """集計統計計算"""
    if not results:
        return {}
    
    summary = {}
    
    # v2スコア
    for metric in ["groundedness", "coherence", "relevance"]:
        scores = [r["scores_v2"][metric] for r in results]
        summary[f"v2_{metric}_avg"] = sum(scores) / len(scores)
        summary[f"v2_{metric}_min"] = min(scores)
        summary[f"v2_{metric}_max"] = max(scores)
    
    # v1スコア（比較用）
    for metric in ["groundedness", "coherence", "relevance"]:
        scores = [r["scores_v1"][metric] for r in results]
        summary[f"v1_{metric}_avg"] = sum(scores) / len(scores)
    
    # 改善率
    for metric in ["groundedness", "coherence", "relevance"]:
        v1_avg = summary[f"v1_{metric}_avg"]
        v2_avg = summary[f"v2_{metric}_avg"]
        if v1_avg > 0:
            improvement = ((v2_avg - v1_avg) / v1_avg) * 100
            summary[f"{metric}_improvement_pct"] = improvement
    
    return summary


def main():
    parser = argparse.ArgumentParser(description="LLM-as-Judge強化バッチ評価")
    parser.add_argument("--limit", type=int, help="評価する質問数")
    args = parser.parse_args()
    
    print("=== バッチ評価 v7 (LLM-as-Judge強化版) ===\n")
    
    questions = load_questions(args.limit)
    print(f"質問数: {len(questions)}")
    
    evaluation = run_evaluation(questions)
    
    # 結果保存
    output_dir = Path("evaluation/results")
    output_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"d21_v7_{timestamp}.json"
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(evaluation, f, ensure_ascii=False, indent=2)
    
    print(f"\n=== 結果サマリー (v2) ===")
    for key in ["v2_groundedness_avg", "v2_coherence_avg", "v2_relevance_avg"]:
        if key in evaluation["summary"]:
            print(f"{key}: {evaluation['summary'][key]:.3f}")
    
    print(f"\n=== 改善率 ===")
    for metric in ["groundedness", "coherence", "relevance"]:
        key = f"{metric}_improvement_pct"
        if key in evaluation["summary"]:
            print(f"{metric}: {evaluation['summary'][key]:+.1f}%")
    
    print(f"\n結果保存: {output_file}")


if __name__ == "__main__":
    main()
