"""
RAGAS Context Precision評価ノード

Relevance（0.09）をContext Precision評価で改善
目標: 0.85以上
"""
from typing import Dict, Any
from ragas.metrics.collections.context_precision import ContextPrecision
from ragas import evaluate
from datasets import Dataset

def evaluate_context_precision_node(
    question: str,
    answer: str,
    contexts: list[str],
    ground_truth: str
) -> Dict[str, Any]:
    """
    RAGAS Context Precision評価
    
    検索されたコンテキストの精度を評価
    Ground truthが必要
    
    Args:
        question: ユーザー質問
        answer: 生成された回答（使用しない）
        contexts: 検索されたコンテキスト
        ground_truth: 正解回答
    
    Returns:
        Dict with score and details
    """
    # RAGAS用データセット構築
    data = {
        "question": [question],
        "answer": [answer],
        "contexts": [contexts],
        "ground_truth": [ground_truth]
    }
    dataset = Dataset.from_dict(data)
    
    # 評価実行
    result = evaluate(
        dataset=dataset,
        metrics=[ContextPrecision()]
    )
    
    return {
        "score": result["context_precision"],
        "details": {
            "question": question,
            "contexts_count": len(contexts),
            "has_ground_truth": bool(ground_truth)
        }
    }
