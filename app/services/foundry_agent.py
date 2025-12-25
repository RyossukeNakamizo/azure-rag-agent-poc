"""
Azure AI Foundry Agent Service

Azure OpenAI 直接統合版
D22-1: get_embeddingメソッド追加
"""

from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from typing import AsyncGenerator
import logging

logger = logging.getLogger(__name__)


class FoundryAgentService:
    """Azure OpenAI 直接統合版"""
    
    def __init__(
        self,
        azure_openai_endpoint: str,
        azure_openai_deployment: str,
        api_version: str = "2024-10-01-preview"
    ):
        self.deployment = azure_openai_deployment
        self.credential = DefaultAzureCredential()
        
        try:
            token_provider = get_bearer_token_provider(
                self.credential,
                "https://cognitiveservices.azure.com/.default"
            )
            
            self.openai_client = AzureOpenAI(
                azure_endpoint=azure_openai_endpoint,
                azure_ad_token_provider=token_provider,
                api_version=api_version
            )
            
            logger.info(
                f"AzureOpenAI client initialized: "
                f"endpoint={azure_openai_endpoint}, "
                f"deployment={azure_openai_deployment}"
            )
            
        except Exception as e:
            logger.error(f"Failed to initialize AzureOpenAI: {e}")
            raise
    
    def get_embedding(self, text: str) -> list[float]:
        """
        テキストをベクトル埋め込みに変換
        
        Args:
            text: 埋め込み対象テキスト
        
        Returns:
            埋め込みベクトル（1536次元）
        """
        try:
            response = self.openai_client.embeddings.create(
                model="text-embedding-ada-002",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            return None
    
    async def chat_stream(
        self,
        query: str,
        system_prompt: str = "You are a helpful assistant.",
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> AsyncGenerator[str, None]:
        try:
            response = self.openai_client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query}
                ],
                stream=True,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        
        except Exception as e:
            logger.error(f"Chat stream error: {e}")
            yield f"Error: {str(e)}"
    
    async def chat(
        self,
        query: str,
        system_prompt: str = "You are a helpful assistant.",
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> str:
        try:
            response = self.openai_client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        
        except Exception as e:
            logger.error(f"Chat error: {e}")
            return f"Error: {str(e)}"
    
    def get_available_tools(self) -> list[dict]:
        """利用可能なツール一覧（現在は空）"""
        return []
