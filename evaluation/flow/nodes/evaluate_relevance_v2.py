"""
Relevance評価 v2 - LLM-as-Judge版

改善点:
- ヒューリスティック（単語重複率）廃止
- LLMによる意味的関連性評価
- 質問への直接的回答度評価
"""
from typing import Dict, Any
from flow.nodes.retrieve import get_openai_client

def evaluate_relevance_v2(question: str, answer: str) -> Dict[str, Any]:
    """
    改善版Relevance評価
    
    Args:
        question: ユーザー質問
        answer: 生成された回答
    
    Returns:
        Dict with score and reasoning
    """
    client = get_openai_client()
    
    prompt = f"""あなたは質問-回答評価者です。回答が質問にどれだけ適切に答えているかを評価してください。

【質問】
{question}

【回答】
{answer}

【評価基準】
1.0: 質問に完全かつ直接的に回答している
0.75: 質問に十分回答しているが、一部不足がある
0.5: 質問に部分的に回答しているが、重要な点が欠けている
0.25: 質問との関連性は薄いが、わずかに関連する情報がある
0.0: 質問と全く無関係な回答

【評価観点】
- 質問の意図への適合度
- 必要な情報の網羅性
- 回答の具体性
- 余分な情報の少なさ

【出力形式】（数値のみ）
0.0 または 0.25 または 0.5 または 0.75 または 1.0"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=10
    )
    
    result_text = response.choices[0].message.content.strip()
    
    try:
        score = float(result_text)
        score = round(score * 4) / 4
        score = max(0.0, min(1.0, score))
    except ValueError:
        score = 0.5
    
    return {
        "score": score,
        "raw_output": result_text,
        "evaluation_type": "llm_as_judge_v2"
    }
