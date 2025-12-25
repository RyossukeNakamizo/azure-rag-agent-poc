import json
import os
from azure.identity import DefaultAzureCredential
from openai import AzureOpenAI

credential = DefaultAzureCredential()
openai_client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    azure_ad_token_provider=lambda: credential.get_token("https://cognitiveservices.azure.com/.default").token,
    api_version="2024-10-01-preview"
)

test_context_text = "Azure AI SearchはHNSWアルゴリズムをサポートしています。"
test_answer = "HNSWパラメータを調整できます。"

prompt = f"""以下の回答が、提供されたコンテキストに基づいているかを0-1で評価してください。
評価結果をJSON形式で返してください。

評価基準：
- コンテキストに記載されている情報のみを使用しているか

コンテキスト:
{test_context_text}

回答: {test_answer}

評価結果を以下のJSON形式で返してください：
{{"score": 0.0-1.0, "reason": "理由"}}
"""

print("=== Groundedness評価テスト ===")
print(f"コンテキスト: {test_context_text}")
print(f"回答: {test_answer}")
print("\n評価中...")

response = openai_client.chat.completions.create(
    model=os.getenv("AZURE_OPENAI_DEPLOYMENT_CHAT", "gpt-4o"),
    messages=[{"role": "user", "content": prompt}],
    temperature=0.0,
    max_tokens=200,
    response_format={"type": "json_object"}
)

print("\nLLM応答:")
print(response.choices[0].message.content)

try:
    result = json.loads(response.choices[0].message.content)
    score = float(result.get("score", -1))
    reason = result.get("reason", "")
    print(f"\n✅ 評価成功")
    print(f"  Score: {score}")
    print(f"  Reason: {reason}")
except Exception as e:
    print(f"\n❌ エラー: {e}")
