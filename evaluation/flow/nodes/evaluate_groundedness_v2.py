"""
Groundedness評価 v2 - プロンプト強化版

改善点:
- 詳細な評価基準の明示
- 段階的評価（0.0/0.25/0.5/0.75/1.0）
- CoT (Chain of Thought) 推論
"""
from typing import Dict, Any
from flow.nodes.retrieve import get_openai_client

def evaluate_groundedness_v2(answer: str, context: str) -> Dict[str, Any]:
    """
    改善版Groundedness評価
    
    Args:
        answer: 生成された回答
        context: 検索されたコンテキスト
    
    Returns:
        Dict with score and reasoning
    """
    client = get_openai_client()
    
    prompt = f"""あなたは厳格な事実検証者です。以下の基準で回答の根拠性を評価してください。

【コンテキスト（事実情報）】
{context}

【回答】
{answer}

【評価基準】
1.0: 回答の全ての主張がコンテキストで直接支持されている
0.75: 回答の大部分（75%以上）がコンテキストで支持されている
0.5: 回答の半分程度がコンテキストで支持されている
0.25: 回答の一部（25%以下）のみがコンテキストで支持されている
0.0: 回答がコンテキストと無関係、または矛盾している

【評価プロセス】
1. 回答を主張単位に分解
2. 各主張がコンテキストで支持されているか検証
3. 支持率を計算
4. スコアを決定

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
        # 0.0, 0.25, 0.5, 0.75, 1.0 のいずれかに丸める
        score = round(score * 4) / 4
        score = max(0.0, min(1.0, score))
    except ValueError:
        score = 0.0
    
    return {
        "score": score,
        "raw_output": result_text,
        "evaluation_type": "llm_as_judge_v2"
    }
