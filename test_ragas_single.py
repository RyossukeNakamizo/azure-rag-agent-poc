"""RAGAS単体テスト with Azure OpenAI"""
import os
from dotenv import load_dotenv
load_dotenv()

from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings
from ragas.metrics.collections.faithfulness import Faithfulness
from ragas.metrics.collections.answer_relevancy import AnswerRelevancy
from ragas.metrics.collections.context_precision import ContextPrecision
from ragas import evaluate
from datasets import Dataset

# Azure OpenAI 設定
azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
azure_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_CHAT", "gpt-4o")
azure_embedding_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_EMBEDDING", "text-embedding-ada-002")
api_version = "2024-10-01-preview"

print(f"Azure OpenAI Endpoint: {azure_endpoint}")
print(f"Chat Deployment: {azure_deployment}")
print(f"Embedding Deployment: {azure_embedding_deployment}")

# LangChain LLM/Embeddings
llm = AzureChatOpenAI(
    azure_endpoint=azure_endpoint,
    azure_deployment=azure_deployment,
    api_version=api_version,
    temperature=0
)

embeddings = AzureOpenAIEmbeddings(
    azure_endpoint=azure_endpoint,
    azure_deployment=azure_embedding_deployment,
    api_version=api_version
)

# テストデータ
question = "Azure AI Searchとは何ですか？"
answer = "Azure AI Searchは、Azureが提供する検索サービスです。ベクトル検索とキーワード検索を組み合わせたハイブリッド検索が可能です。"
contexts = [
    "Azure AI Search（旧Cognitive Search）は、エンタープライズRAGシステムの中核を担う検索プラットフォーム。",
    "ベクトル検索、ハイブリッド検索、セマンティックランキングを統合提供。"
]
ground_truth = "Azure AI Searchはクラウドベースの検索サービスです。"

# データセット作成
data = {
    "question": [question],
    "answer": [answer],
    "contexts": [contexts],
    "ground_truth": [ground_truth]
}
dataset = Dataset.from_dict(data)

print("\nDataset created:")
print(dataset)

# Faithfulness評価
print("\n=== Testing Faithfulness ===")
try:
    faithfulness_metric = Faithfulness(llm=llm)
    result = evaluate(dataset=dataset, metrics=[faithfulness_metric])
    print(f"Success: {result}")
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

# Answer Relevancy評価
print("\n=== Testing Answer Relevancy ===")
try:
    answer_relevancy_metric = AnswerRelevancy(llm=llm, embeddings=embeddings)
    result = evaluate(dataset=dataset, metrics=[answer_relevancy_metric])
    print(f"Success: {result}")
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

# Context Precision評価
print("\n=== Testing Context Precision ===")
try:
    context_precision_metric = ContextPrecision(llm=llm)
    result = evaluate(dataset=dataset, metrics=[context_precision_metric])
    print(f"Success: {result}")
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
