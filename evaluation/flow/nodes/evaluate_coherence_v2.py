"""
Coherence評価 v2 - LLM-as-Judge版

改善点:
- ヒューリスティック（単語数）廃止
- LLMによる意味的一貫性評価
- 論理構造の評価
"""
from typing import Dict, Any
from flow.nodes.retrieve import get_openai_client

def evaluate_coherence_v2(answer: str) -> Dict[str, Any]:
    """
    改善版Coherence評価
    
    Args:
        answer: 生成された回答
    
    Returns:
        Dict with score and reasoning
    """
    client = get_openai_client()
    
    prompt = f"""あなたは文章品質評価者です。以下の回答の一貫性を評価してください。

【回答】
{answer}

【評価基準】
1.0: 完全に一貫性があり、論理的に完璧
0.75: おおむね一貫性があり、論理的
0.5: 一部に矛盾や論理の飛躍があるが理解可能
0.25: 矛盾が多く、論理構造が不明瞭
0.0: 全く一貫性がない、支離滅裂

【評価観点】
- 文と文のつながりの自然さ
- 論理展開の妥当性
- 矛盾の有無
- 結論の適切性

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
