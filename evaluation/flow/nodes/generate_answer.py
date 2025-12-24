import os
from promptflow.core import tool
from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential
@tool
def generate_answer(question: str, context: str) -> str:
    credential = DefaultAzureCredential()
    client = AzureOpenAI(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        azure_ad_token_provider=lambda: credential.get_token("https://cognitiveservices.azure.com/.default").token,
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-01-preview")
    )
    try:
        response = client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT_CHAT", "gpt-4o"),
            messages=[
                {"role": "system", "content": "あなたはAzure技術の専門家です。提供されたコンテキストのみを使用して回答してください。"},
                {"role": "user", "content": f"コンテキスト:\n{context}\n\n質問: {question}"}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"[ERROR] {str(e)}"
