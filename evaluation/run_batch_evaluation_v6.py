"""
バッチ評価 v6 - RAGAS統合版

6評価指標:
- Faithfulness (RAGAS) - 目標0.85+
- Answer Relevancy (RAGAS) - 目標0.85+
- Context Precision (RAGAS) - 目標0.85+
- Groundedness (LLM-as-Judge) - ベースライン0.76
- Coherence (Heuristic) - ベースライン0.42
- Relevance (Heuristic) - ベースライン0.09
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
from flow.nodes.retrieve import retrieve_context, get_embedding
from flow.nodes.generate_answer import generate_answer
from flow.nodes.evaluate_faithfulness import evaluate_faithfulness_node
from flow.nodes.evaluate_answer_relevancy import evaluate_answer_relevancy_node
from flow.nodes.evaluate_context_precision import evaluate_context_precision_node
from flow.nodes.evaluate_groundedness import evaluate_groundedness
from flow.nodes.evaluate_coherence import evaluate_coherence
from flow.nodes.evaluate_relevance import evaluate_relevance


def load_questions(limit: int = None) -> List[Dict[str, str]]:
    """テスト質問ロード"""
    questions = [
        {"question": "Azure AI Searchのセマンティック検索を有効化する方法は？", "ground_truth": "Azure AI SearchでセマンティックランキングはSKUによって利用可能で、Basic以上が必要です。"},
        {"question": "Managed Identityの利点を教えてください", "ground_truth": "Managed IdentityはAPI Keyが不要でセキュアな認証方式です。"},
        {"question": "RAGシステムでベクトル検索を実装する方法は？", "ground_truth": "Azure AI SearchのHNSWアルゴリズムを使用してベクトルインデックスを作成します。"},
        {"question": "Bicepでリソースをデプロイする手順は？", "ground_truth": "az deployment group createコマンドでBicepテンプレートをデプロイします。"},
        {"question": "Azure OpenAIのレート制限はどう設定しますか？", "ground_truth": "デプロイメント単位でTPM（Tokens Per Minute）を設定できます。"},
        {"question": "RBAC権限の最小権限の原則とは？", "ground_truth": "必要最小限の権限のみを付与するセキュリティ原則です。"},
        {"question": "Azure AI Searchのインデックス作成方法は？", "ground_truth": "SearchIndexClientを使用してフィールド定義とベクトル検索設定を行います。"},
        {"question": "GitHub ActionsでOIDC認証を設定する方法は？", "ground_truth": "Federated Credentialを作成してキーレス認証を実現します。"},
        {"question": "チャンキング戦略の推奨設定は？", "ground_truth": "500-1000トークン/チャンクで10-20%オーバーラップが推奨されます。"},
        {"question": "Private Endpointの利点は何ですか？", "ground_truth": "VNet内でプライベートIPを使用し、パブリックアクセスを遮断できます。"},
        {"question": "Azure AI Searchのハイブリッド検索とは？", "ground_truth": "ベクトル検索とキーワード検索を組み合わせた検索方式です。"},
        {"question": "埋め込みモデルtext-embedding-ada-002の次元数は？", "ground_truth": "1536次元です。"},
        {"question": "Bicep変数の命名規則は？", "ground_truth": "camelCaseを使用し、リソース種別を含めることが推奨されます。"},
        {"question": "Azure DevOps PipelineのWhat-if機能とは？", "ground_truth": "デプロイ前に変更内容をプレビューする機能です。"},
        {"question": "Key Vaultでシークレットをローテーションする方法は？", "ground_truth": "Event GridとFunctionsを使用して自動ローテーションを実装できます。"},
        {"question": "Azure AI SearchのSkillsetとは？", "ground_truth": "インデックス作成時のAI処理パイプラインです。"},
        {"question": "ベクトル検索のHNSWアルゴリズムとは？", "ground_truth": "高速な近似最近傍探索アルゴリズムです。"},
        {"question": "Azure OpenAIのストリーミング応答の実装方法は？", "ground_truth": "stream=Trueを設定してチャンク単位で応答を受信します。"},
        {"question": "Managed Identityの種類は？", "ground_truth": "System-assignedとUser-assignedの2種類があります。"},
        {"question": "Azure AI Searchの料金体系は？", "ground_truth": "SKU（Free/Basic/Standard）に応じて月額固定+ストレージ従量課金です。"},
    ]
    return questions[:limit] if limit else questions


def safe_evaluate(func, **kwargs):
    """評価関数の安全実行（引数自動マッチング）"""
    import inspect
    sig = inspect.signature(func)
    filtered_kwargs = {k: v for k, v in kwargs.items() if k in sig.parameters}
    try:
        return func(**filtered_kwargs)
    except Exception as e:
        return {"score": 0.0, "error": str(e)}


def run_evaluation(questions: List[Dict[str, str]]) -> Dict[str, Any]:
    """バッチ評価実行"""
    results = []
    
    for idx, item in enumerate(questions, 1):
        question = item["question"]
        ground_truth = item["ground_truth"]
        
        print(f"\n[{idx}/{len(questions)}] {question}")
        
        try:
            # 1. 検索
            retrieve_result = retrieve_context(question=question)
            contexts = [doc["content"] for doc in retrieve_result.get("context", [])]
            context_str = "\n".join(contexts)
            
            # 2. 回答生成
            answer = generate_answer(question=question, context=context_str)
            
            # 3. RAGAS評価
            faithfulness_result = safe_evaluate(
                evaluate_faithfulness_node,
                question=question,
                answer=answer,
                contexts=contexts
            )
            
            answer_relevancy_result = safe_evaluate(
                evaluate_answer_relevancy_node,
                question=question,
                answer=answer,
                contexts=contexts
            )
            
            context_precision_result = safe_evaluate(
                evaluate_context_precision_node,
                question=question,
                answer=answer,
                contexts=contexts,
                ground_truth=ground_truth
            )
            
            # 4. 既存評価（比較用）
            groundedness_score = evaluate_groundedness(answer=answer, context=context_str)
            groundedness_result = {"score": groundedness_score}
            
            coherence_score = evaluate_coherence(answer=answer)
            coherence_result = {"score": coherence_score}
            
            relevance_score = evaluate_relevance(question=question, answer=answer)
            relevance_result = {"score": relevance_score}
            
            # 結果記録
            result = {
                "question": question,
                "answer": answer,
                "contexts_count": len(contexts),
                "ground_truth": ground_truth,
                "scores": {
                    "faithfulness": faithfulness_result.get("score", 0.0),
                    "answer_relevancy": answer_relevancy_result.get("score", 0.0),
                    "context_precision": context_precision_result.get("score", 0.0),
                    "groundedness": groundedness_result.get("score", 0.0),
                    "coherence": coherence_result.get("score", 0.0),
                    "relevance": relevance_result.get("score", 0.0),
                }
            }
            results.append(result)
            
            print(f"  Faithfulness: {result['scores']['faithfulness']:.2f}")
            print(f"  Answer Relevancy: {result['scores']['answer_relevancy']:.2f}")
            print(f"  Context Precision: {result['scores']['context_precision']:.2f}")
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
            results.append({
                "question": question,
                "error": str(e),
                "scores": {k: 0.0 for k in ["faithfulness", "answer_relevancy", "context_precision", "groundedness", "coherence", "relevance"]}
            })
    
    return {"results": results, "summary": calculate_summary(results)}


def calculate_summary(results: List[Dict]) -> Dict[str, float]:
    """集計統計計算"""
    valid_results = [r for r in results if "error" not in r]
    if not valid_results:
        return {}
    
    metrics = ["faithfulness", "answer_relevancy", "context_precision", "groundedness", "coherence", "relevance"]
    summary = {}
    
    for metric in metrics:
        scores = [r["scores"][metric] for r in valid_results]
        summary[f"{metric}_avg"] = sum(scores) / len(scores)
        summary[f"{metric}_min"] = min(scores)
        summary[f"{metric}_max"] = max(scores)
    
    return summary


def main():
    parser = argparse.ArgumentParser(description="RAGAS統合バッチ評価")
    parser.add_argument("--limit", type=int, help="評価する質問数")
    args = parser.parse_args()
    
    print("=== RAGAS統合バッチ評価 v6 ===\n")
    
    questions = load_questions(args.limit)
    print(f"質問数: {len(questions)}")
    
    evaluation = run_evaluation(questions)
    
    # 結果保存
    output_dir = Path("evaluation/results")
    output_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"d21_ragas_v6_{timestamp}.json"
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(evaluation, f, ensure_ascii=False, indent=2)
    
    print(f"\n=== 結果サマリー ===")
    for key, value in evaluation["summary"].items():
        print(f"{key}: {value:.3f}")
    
    print(f"\n結果保存: {output_file}")


if __name__ == "__main__":
    main()
