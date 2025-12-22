"""
Function Calling Agent Implementation

Azure OpenAI Function Callingを使用したエージェント基盤。
ツール呼び出しのオーケストレーション、エラーハンドリング、
並列実行を管理する。
"""
import os
import json
from typing import List, Dict, Any, Optional, Literal
from dataclasses import dataclass, field
from datetime import datetime
import asyncio

from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

# ツール実装のインポート（後で実装）
from app.agents.tools.implementations import (
    search_documents_impl,
    calculate_impl,
    get_current_datetime_impl,
    get_equipment_status_impl
)
from app.agents.tools.tool_definitions import tool_registry

load_dotenv()


@dataclass
class Message:
    """会話メッセージ"""
    role: Literal["system", "user", "assistant", "tool"]
    content: str
    name: Optional[str] = None  # tool role用
    tool_calls: Optional[List[Dict[str, Any]]] = None  # assistant role用
    tool_call_id: Optional[str] = None  # tool role用


@dataclass
class AgentConfig:
    """エージェント設定"""
    model: str = "gpt-4o"
    temperature: float = 0.7
    max_tokens: int = 2000
    max_iterations: int = 5  # 無限ループ防止
    parallel_tool_calls: bool = True  # 並列実行許可


class FunctionCallingAgent:
    """Function Calling Agent"""
    
    def __init__(
        self,
        config: AgentConfig = None,
        system_prompt: str = None
    ):
        """
        Args:
            config: エージェント設定
            system_prompt: システムプロンプト
        """
        self.config = config or AgentConfig()
        self.system_prompt = system_prompt or self._default_system_prompt()
        
        # Azure OpenAI クライアント（Managed Identity認証）
        self.credential = DefaultAzureCredential()
        self.client = AzureOpenAI(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            azure_ad_token_provider=self._get_token,
            api_version="2024-10-01-preview"
        )
        
        # ツール実装マッピング
        self.tool_implementations = {
            "search_documents": search_documents_impl,
            "calculate": calculate_impl,
            "get_current_datetime": get_current_datetime_impl,
            "get_equipment_status": get_equipment_status_impl
        }
        
        # 会話履歴
        self.messages: List[Message] = [
            Message(role="system", content=self.system_prompt)
        ]
    
    def _get_token(self) -> str:
        """Azure AD トークン取得"""
        return self.credential.get_token(
            "https://cognitiveservices.azure.com/.default"
        ).token
    
    def _default_system_prompt(self) -> str:
        """デフォルトシステムプロンプト"""
        return """あなたは有能なAIアシスタントです。
以下のツールを使用して、ユーザーの質問に正確に回答してください。

利用可能なツール:
- search_documents: 社内ドキュメント検索
- calculate: 数値計算
- get_current_datetime: 現在日時取得
- get_equipment_status: 工場設備状態確認

重要なガイドライン:
1. 必要なツールを適切に選択して使用する
2. 複数ツールが必要な場合は並列実行を活用する
3. ツール実行結果を基に、わかりやすく回答する
4. 不確実な情報は推測せず、ツールで確認する
"""
    
    def _execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """
        ツール実行
        
        Args:
            tool_name: ツール名
            arguments: ツール引数
        
        Returns:
            実行結果（JSON文字列）
        """
        if tool_name not in self.tool_implementations:
            return json.dumps({
                "error": f"Unknown tool: {tool_name}",
                "available_tools": list(self.tool_implementations.keys())
            })
        
        try:
            impl = self.tool_implementations[tool_name]
            result = impl(**arguments)
            return json.dumps(result, ensure_ascii=False)
        
        except Exception as e:
            return json.dumps({
                "error": str(e),
                "tool": tool_name,
                "arguments": arguments
            })
    
    def run(
        self,
        user_message: str,
        tools: List[str] = None,
        tool_choice: Literal["auto", "required", "none"] = "auto"
    ) -> str:
        """
        エージェント実行（同期版）
        
        Args:
            user_message: ユーザーメッセージ
            tools: 使用するツール名リスト（Noneの場合は全ツール）
            tool_choice: ツール選択戦略
        
        Returns:
            最終回答
        """
        # ユーザーメッセージ追加
        self.messages.append(Message(role="user", content=user_message))
        
        # ツールスキーマ取得
        tool_schemas = tool_registry.get_tool_schemas(tools)
        
        # 反復実行（ツール呼び出しループ）
        for iteration in range(self.config.max_iterations):
            # OpenAI API呼び出し
            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {
                        "role": m.role,
                        "content": m.content,
                        **({"name": m.name} if m.name else {}),
                        **({"tool_calls": m.tool_calls} if m.tool_calls else {}),
                        **({"tool_call_id": m.tool_call_id} if m.tool_call_id else {})
                    }
                    for m in self.messages
                ],
                tools=tool_schemas if tool_schemas else None,
                tool_choice=tool_choice if tool_schemas else None,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                parallel_tool_calls=self.config.parallel_tool_calls
            )
            
            message = response.choices[0].message
            
            # ツール呼び出しなし → 最終回答
            if not message.tool_calls:
                final_answer = message.content
                self.messages.append(Message(
                    role="assistant",
                    content=final_answer
                ))
                return final_answer
            
            # Assistantメッセージ追加（ツール呼び出し含む）
            self.messages.append(Message(
                role="assistant",
                content=message.content or "",
                tool_calls=[
                    {
                        "id": tc.id,
                        "type": tc.type,
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    for tc in message.tool_calls
                ]
            ))
            
            # 各ツール呼び出しを実行
            for tool_call in message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                print(f"[Tool Call] {function_name}({function_args})")
                
                # ツール実行
                tool_result = self._execute_tool(function_name, function_args)
                
                print(f"[Tool Result] {tool_result[:200]}...")
                
                # ツール結果追加
                self.messages.append(Message(
                    role="tool",
                    name=function_name,
                    content=tool_result,
                    tool_call_id=tool_call.id
                ))
        
        # 最大反復回数到達
        return "最大反復回数に達しました。処理を中断します。"
    
    def reset(self):
        """会話履歴リセット"""
        self.messages = [
            Message(role="system", content=self.system_prompt)
        ]


if __name__ == "__main__":
    # 基本動作確認（Azure認証不要ツールのみ）
    agent = FunctionCallingAgent()
    
    # テストクエリ（認証不要ツールのみ使用）
    queries = [
        "現在時刻を教えてください",
        "25の平方根を計算してください",
        "現在時刻と、100の2乗を計算して教えてください",  # 並列実行テスト
        "LINE-A-01の設備状態を確認してください"  # 工場向けツール
    ]
    
    # 使用ツール制限（search_documents除外）
    available_tools = ["calculate", "get_current_datetime", "get_equipment_status"]
    
    for query in queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print(f"{'='*60}")
        
        answer = agent.run(query, tools=available_tools)
        print(f"\nAnswer: {answer}\n")
        
        agent.reset()
