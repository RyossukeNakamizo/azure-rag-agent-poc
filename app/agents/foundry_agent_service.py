"""
Azure AI Foundry Agent Service

Azure AI Foundry (Assistants API) を使用したAgent実装。
Thread/Run/Message管理とFunction Calling統合。
"""
import os
import json
import time
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential

# ツール実装のインポート
from app.agents.tools.implementations import (
    search_documents_impl,
    calculate_impl,
    get_current_datetime_impl,
    get_equipment_status_impl
)
from app.agents.tools.tool_definitions import tool_registry

load_dotenv()


class FoundryAgentService:
    """Azure AI Foundry Agent サービス"""
    
    def __init__(self):
        """初期化"""
        # Azure OpenAI クライアント（Managed Identity）
        credential = DefaultAzureCredential()
        self.client = AzureOpenAI(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            azure_ad_token_provider=self._get_token,
            api_version="2024-05-01-preview"  # Assistants API
        )
        
        # ツール実装マッピング
        self.tool_implementations = {
            "search_documents": search_documents_impl,
            "calculate": calculate_impl,
            "get_current_datetime": get_current_datetime_impl,
            "get_equipment_status": get_equipment_status_impl
        }
        
        self.assistant_id = None
        self.thread_id = None
    
    def _get_token(self) -> str:
        """Azure AD トークン取得"""
        credential = DefaultAzureCredential()
        return credential.get_token(
            "https://cognitiveservices.azure.com/.default"
        ).token
    
    def create_assistant(self, name: str = "function-calling-assistant") -> str:
        """
        Assistantを作成
        
        Args:
            name: Assistant名
        
        Returns:
            Assistant ID
        """
        # ツールスキーマ取得
        tools = tool_registry.get_all_tool_schemas()
        
        # Assistant作成
        assistant = self.client.beta.assistants.create(
            name=name,
            instructions="""あなたは工場向けAIアシスタントです。
以下のツールを使用して、ユーザーの質問に正確に回答してください。

利用可能なツール:
- search_documents: 社内ドキュメント検索
- calculate: 数値計算
- get_current_datetime: 現在日時取得
- get_equipment_status: 工場設備状態確認

重要なガイドライン:
1. 必要なツールを適切に選択して使用する
2. 複数ツールが必要な場合は並列実行を活用する
3. ツール実行結果を基に、わかりやすく回答する""",
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT_CHAT", "gpt-4o"),
            tools=tools
        )
        
        self.assistant_id = assistant.id
        print(f"✅ Assistant作成完了: {self.assistant_id}")
        
        return self.assistant_id
    
    def create_thread(self) -> str:
        """
        会話スレッド作成
        
        Returns:
            Thread ID
        """
        thread = self.client.beta.threads.create()
        self.thread_id = thread.id
        print(f"✅ Thread作成完了: {self.thread_id}")
        
        return self.thread_id
    
    def add_message(self, content: str, role: str = "user") -> str:
        """
        メッセージ追加
        
        Args:
            content: メッセージ内容
            role: ロール（user/assistant）
        
        Returns:
            Message ID
        """
        message = self.client.beta.threads.messages.create(
            thread_id=self.thread_id,
            role=role,
            content=content
        )
        
        return message.id
    
    def run_assistant(self, instructions: Optional[str] = None) -> str:
        """
        Assistant実行
        
        Args:
            instructions: 追加指示
        
        Returns:
            Run ID
        """
        run = self.client.beta.threads.runs.create(
            thread_id=self.thread_id,
            assistant_id=self.assistant_id,
            instructions=instructions
        )
        
        return run.id
    
    def wait_for_run_completion(self, run_id: str, timeout: int = 60) -> Dict[str, Any]:
        """
        Run完了待機
        
        Args:
            run_id: Run ID
            timeout: タイムアウト（秒）
        
        Returns:
            Run詳細
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            run = self.client.beta.threads.runs.retrieve(
                thread_id=self.thread_id,
                run_id=run_id
            )
            
            print(f"[Run Status] {run.status}")
            
            if run.status == "completed":
                return run
            
            elif run.status == "requires_action":
                # Function Calling実行
                self._handle_required_actions(run)
            
            elif run.status in ["failed", "cancelled", "expired"]:
                raise Exception(f"Run failed: {run.status}")
            
            time.sleep(1)
        
        raise TimeoutError("Run timeout")
    
    def _handle_required_actions(self, run):
        """Function Calling処理"""
        tool_outputs = []
        
        for tool_call in run.required_action.submit_tool_outputs.tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)
            
            print(f"[Tool Call] {function_name}({function_args})")
            
            # ツール実行
            if function_name in self.tool_implementations:
                result = self.tool_implementations[function_name](**function_args)
                output = json.dumps(result, ensure_ascii=False)
            else:
                output = json.dumps({"error": f"Unknown tool: {function_name}"})
            
            print(f"[Tool Result] {output[:100]}...")
            
            tool_outputs.append({
                "tool_call_id": tool_call.id,
                "output": output
            })
        
        # ツール結果を送信
        self.client.beta.threads.runs.submit_tool_outputs(
            thread_id=self.thread_id,
            run_id=run.id,
            tool_outputs=tool_outputs
        )
    
    def get_messages(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        メッセージ一覧取得
        
        Args:
            limit: 取得件数
        
        Returns:
            メッセージリスト
        """
        messages = self.client.beta.threads.messages.list(
            thread_id=self.thread_id,
            limit=limit
        )
        
        return [
            {
                "role": m.role,
                "content": m.content[0].text.value if m.content else ""
            }
            for m in messages.data
        ]
    
    def chat(self, user_message: str) -> str:
        """
        チャット実行（簡易インターフェース）
        
        Args:
            user_message: ユーザーメッセージ
        
        Returns:
            Assistant回答
        """
        # Thread未作成なら作成
        if not self.thread_id:
            self.create_thread()
        
        # メッセージ追加
        self.add_message(user_message)
        
        # Run実行
        run_id = self.run_assistant()
        
        # 完了待機
        self.wait_for_run_completion(run_id)
        
        # 最新メッセージ取得
        messages = self.get_messages(limit=1)
        
        return messages[0]["content"] if messages else "エラー: 回答取得失敗"


if __name__ == "__main__":
    print("=" * 60)
    print("Azure AI Foundry Agent Service - Test")
    print("=" * 60)
    
    # Agent初期化
    agent = FoundryAgentService()
    
    # Assistant作成
    assistant_id = agent.create_assistant()
    
    # テストクエリ
    test_queries = [
        "現在時刻を教えてください",
        "25の平方根を計算してください",
        "LINE-A-01の設備状態を確認してください"
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print(f"{'='*60}")
        
        answer = agent.chat(query)
        print(f"\nAnswer: {answer}\n")
