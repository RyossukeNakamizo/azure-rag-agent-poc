"""Groundedness評価ノード（LLM-as-a-Judge、堅牢版）"""
import os
import re
from promptflow.core import tool
from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential


@tool
def evaluate_groundedness(answer: str, context: str) -> float:
    """LLMを使用して回答の根拠性を評価（0.0-1.0）"""
    
    credential = DefaultAzureCredential()
    client = AzureOpenAI(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        azure_ad_token_provider=lambda: credential.get_token(
            "https://cognitiveservices.azure.com/.default"
        ).token,
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-01-preview")
    )
    
    evaluation_prompt = f"""あなたは厳格な評価者です。以下の回答がコンテキストに基づいているかを評価してください。

評価ルール:
- コンテキストに直接書かれている情報のみを使った回答: 0.9-1.0
- コンテキストから論理的に推論できる回答: 0.6-0.8  
- 一部のみコンテキストに基づく回答: 0.3-0.5
- ほぼコンテキスト外の回答: 0.0-0.2

コンテキスト:
{context}

回答:
{answer}

0.0から1.0の数値のみを出力してください（小数第1位まで、例: 0.7）:"""

    try:
        response = client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT_CHAT", "gpt-4o"),
            messages=[{"role": "user", "content": evaluation_prompt}],
            temperature=0.0,
            max_tokens=5
        )
        
        score_text = response.choices[0].message.content.strip()
        
        # 複数パターンで数値抽出
        # パターン1: 0.7, 0.85 など
        match = re.search(r'0?\.\d+', score_text)
        if match:
            score = float(match.group())
            return max(0.0, min(1.0, score))
        
        # パターン2: 1.0, 1, 0 など
        match = re.search(r'\b[01]\.?\d*\b', score_text)
        if match:
            score = float(match.group())
            return max(0.0, min(1.0, score))
        
        # 直接float変換試行
        score = float(score_text)
        return max(0.0, min(1.0, score))
    
    except Exception as e:
        # エラー時はキーワードベースのフォールバック
        answer_words = set(answer.lower().split())
        context_words = set(context.lower().split())
        if answer_words:
            overlap = len(answer_words & context_words) / len(answer_words)
            return min(overlap, 1.0)
        return 0.5
