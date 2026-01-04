"""
RAGAS Answer Relevancy評価ノード

Coherence（0.42）をAnswer Relevancy評価で改善
目標: 0.85以上
"""
from typing import Dict, Any
from ragas.metrics.collections.answer_relevancy import AnswerRelevancy
from ragas import evaluate
from datasets import Dataset

def evaluate_answer_relevancy_node(
    question: str,
    answer: str,
    contexts: list[str]
) -> Dict[str, Any]:
    """
    RAGAS Answer Relevancy評価
    
    質問と回答の意味的一致度を評価
    
    Args:
        question: ユーザー質問
        answer: 生成された回答
        contexts: 検索されたコンテキスト（必須だが使用しない）
    
    Returns:
        Dict with score and details
    """
    # RAGAS用データセット構築
    data = {
        "question": [question],
        "answer": [answer],
        "contexts": [contexts]  # 必須パラメータ
    }
    dataset = Dataset.from_dict(data)
    
    # 評価実行
    result = evaluate(
        dataset=dataset,
        metrics=[AnswerRelevancy()]
    )
    
    return {
        "score": result["answer_relevancy"],
        "details": {
            "question": question,
            "answer_length": len(answer),
            "evaluation_type": "semantic_similarity"
        }
    }
