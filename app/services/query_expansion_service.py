"""
Query Expansion Service

ユーザークエリをGPT-4oで3-5個の検索用クエリに展開。
検索範囲を拡大し、Relevanceを改善する。

Cost: ~$0.001/query (GPT-4o: 150 input + 50 output tokens)
"""
from typing import List
from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential
import os
import logging
import json

logger = logging.getLogger(__name__)


class QueryExpansionService:
    """クエリ展開サービス"""
    
    SYSTEM_PROMPT = """あなたは検索クエリ最適化の専門家です。
ユーザーの質問を、Azure AI Searchで効果的に検索できる3個のクエリに展開してください。

ルール:
1. 元のクエリの意図を保持する
2. 同義語、関連用語、技術的バリエーションを含める
3. 日本語と英語の両方のバリエーションを考慮
4. 各クエリは簡潔に（10ワード以内）
5. JSON形式で返す: {"queries": ["query1", "query2", "query3"]}

例:
入力: "Azure AI Searchでセマンティック検索を有効化する方法"
出力: {"queries": ["Azure AI Search セマンティック検索 有効化", "Azure Cognitive Search semantic ranker 設定", "Azure Search セマンティックランキング 手順"]}
"""
    
    def __init__(self):
        """初期化"""
        self.credential = DefaultAzureCredential()
        self.client = AzureOpenAI(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            azure_ad_token_provider=self._get_token,
            api_version="2024-10-01-preview"
        )
        self.deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_CHAT", "gpt-4o")
    
    def _get_token(self) -> str:
        """Azure AD トークン取得"""
        return self.credential.get_token(
            "https://cognitiveservices.azure.com/.default"
        ).token
    
    def expand_query(
        self,
        user_query: str,
        max_expansions: int = 3
    ) -> List[str]:
        """
        クエリを展開
        
        Args:
            user_query: ユーザーの元クエリ
            max_expansions: 最大展開数（デフォルト3）
        
        Returns:
            展開されたクエリのリスト（先頭は必ず元クエリ）
        
        Raises:
            Exception: 展開失敗時（元クエリのみ返す）
        """
        try:
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": f"展開するクエリ: {user_query}\n展開数: {max_expansions}"
                    }
                ],
                temperature=0.3,  # 低温度で安定した展開
                max_tokens=200,
                response_format={"type": "json_object"}  # JSON強制
            )
            
            # JSON解析
            content = response.choices[0].message.content
            expanded = json.loads(content)
            queries = expanded.get("queries", [])
            
            # ログ出力
            logger.info(
                f"Query expansion successful: '{user_query}' → {queries}"
            )
            
            # 元クエリを先頭に追加（フォールバック）
            result = [user_query] + queries[:max_expansions]
            
            # トークン使用量をログ
            usage = response.usage
            logger.debug(
                f"Query expansion cost: {usage.prompt_tokens} input + "
                f"{usage.completion_tokens} output tokens"
            )
            
            return result
        
        except Exception as e:
            logger.error(f"Query expansion failed: {e}", exc_info=True)
            # エラー時は元クエリのみ返す（フォールバック）
            return [user_query]
