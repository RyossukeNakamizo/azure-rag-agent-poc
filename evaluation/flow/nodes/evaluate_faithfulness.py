"""
RAGAS Faithfulness評価ノード

Groundedness（0.76）をFaithfulness評価で改善
目標: 0.85以上
"""
from typing import Dict, Any
from ragas.metrics.collections.faithfulness import Faithfulness
from ragas import evaluate
from datasets import Dataset

def evaluate_faithfulness_node(
    question: str,
    answer: str,
    contexts: list[str]
) -> Dict[str, Any]:
    """
    RAGAS Faithfulness評価
    
    Args:
        question: ユーザー質問
        answer: 生成された回答
        contexts: 検索されたコンテキスト（リスト）
    
    Returns:
        Dict with score and details
    """
    # RAGAS用データセット構築
    data = {
        "question": [question],
        "answer": [answer],
        "contexts": [contexts]  # リストのリスト
    }
    dataset = Dataset.from_dict(data)
    
    # 評価実行
    result = evaluate(
        dataset=dataset,
        metrics=[Faithfulness()]
    )
    
    return {
        "score": result["faithfulness"],
        "details": {
            "question": question,
            "answer_length": len(answer),
            "contexts_count": len(contexts)
        }
    }
