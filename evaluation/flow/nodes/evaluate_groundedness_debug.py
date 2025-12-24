"""Groundedness評価（デバッグ版）"""
import os
from azure.identity import DefaultAzureCredential
from openai import AzureOpenAI

def evaluate_groundedness(answer: str, context: str) -> float:
    credential = DefaultAzureCredential()
    client = AzureOpenAI(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        azure_ad_token_provider=lambda: credential.get_token("https://cognitiveservices.azure.com/.default").token,
        api_version="2024-10-01-preview"
    )
    
    prompt = f"""以下の回答が、提供されたコンテキストに基づいているかを0.0-1.0のスコアで評価してください。

評価基準:
- 1.0: 回答の全ての情報がコンテキストに含まれている
- 0.7-0.9: 回答の大部分がコンテキストに基づいている
- 0.4-0.6: 回答の一部がコンテキストに基づいている
- 0.0-0.3: 回答がコンテキストとほとんど無関係

コンテキスト:
{context}

回答:
{answer}

スコアのみを数値で返してください（例: 0.9）。説明は不要です。"""

    try:
        print(f"\n[DEBUG] Calling LLM...")
        response = client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT_CHAT", "gpt-4o"),
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=10
        )
        result_text = response.choices[0].message.content.strip()
        print(f"[DEBUG] LLM response: {result_text}")
        score = float(result_text)
        print(f"[DEBUG] Parsed score: {score}")
        return max(0.0, min(1.0, score))
    except Exception as e:
        print(f"[DEBUG] ERROR: {type(e).__name__}: {str(e)}")
        return 0.0

if __name__ == "__main__":
    answer = "HNSWのパラメータ推奨値はm=4、efConstruction=400、efSearch=500です。"
    context = "HNSWパラメータの推奨値: m=4（グラフ接続数）、efConstruction=400（構築品質）、efSearch=500（検索品質）"
    score = evaluate_groundedness(answer=answer, context=context)
    print(f"\nFinal score: {score}")
