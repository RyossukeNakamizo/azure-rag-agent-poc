"""
Function Calling Agent - Mock Version

Azure OpenAI APIをモック化してFunction Callingの
オーケストレーションロジックを検証する。

本番環境では function_calling_agent.py を使用。
"""
import json
from typing import List, Dict, Any, Optional, Literal
from dataclasses import dataclass
import random

from app.agents.tools.implementations import (
    calculate_impl,
    get_current_datetime_impl,
    get_equipment_status_impl
)
from app.agents.tools.tool_definitions import tool_registry


@dataclass
class MockToolCall:
    """モックツール呼び出し"""
    id: str
    type: str = "function"
    function: Dict[str, str] = None


@dataclass
class MockMessage:
    """モックメッセージ"""
    content: Optional[str]
    tool_calls: Optional[List[MockToolCall]]


@dataclass
class MockChoice:
    """モック選択"""
    message: MockMessage


@dataclass
class MockResponse:
    """モックレスポンス"""
    choices: List[MockChoice]


class MockOpenAIClient:
    """Azure OpenAI モッククライアント"""
    
    def __init__(self):
        self.chat = self
        self.completions = self
        
        # ツール実装マッピング
        self.tool_implementations = {
            "calculate": calculate_impl,
            "get_current_datetime": get_current_datetime_impl,
            "get_equipment_status": get_equipment_status_impl
        }
    
    def create(self, model: str, messages: List[Dict], tools: List[Dict] = None, **kwargs):
        """
        Chat Completion API のモック実装
        
        実際のOpenAI APIと同じインターフェース。
        ユーザークエリを解析し、適切なツール呼び出しを生成。
        """
        last_message = messages[-1]
        
        # ツール結果がある場合（2回目の呼び出し）→ 最終回答生成
        if last_message["role"] == "tool":
            return self._generate_final_answer(messages)
        
        # 初回呼び出し → ツール選択
        user_content = last_message["content"]
        
        # クエリ解析してツール決定（簡易実装）
        tool_calls = self._analyze_query_and_select_tools(user_content, tools)
        
        if not tool_calls:
            # ツール不要 → 直接回答
            return MockResponse(choices=[
                MockChoice(message=MockMessage(
                    content="申し訳ございませんが、その質問には利用可能なツールがありません。",
                    tool_calls=None
                ))
            ])
        
        # ツール呼び出し返却
        return MockResponse(choices=[
            MockChoice(message=MockMessage(
                content=None,
                tool_calls=tool_calls
            ))
        ])
    
    def _analyze_query_and_select_tools(
        self,
        query: str,
        available_tools: List[Dict]
    ) -> List[MockToolCall]:
        """
        クエリを解析して必要なツールを選択
        
        実際のGPT-4oはLLMで意味解析するが、
        Mockではキーワードマッチで簡易実装。
        """
        tool_calls = []
        query_lower = query.lower()
        
        # 時刻関連
        if any(kw in query_lower for kw in ["時刻", "時間", "now", "datetime", "今", "現在"]):
            tool_calls.append(MockToolCall(
                id=f"call_{random.randint(1000, 9999)}",
                function={
                    "name": "get_current_datetime",
                    "arguments": json.dumps({"timezone": "Asia/Tokyo", "format": "japanese"})
                }
            ))
        
        # 計算関連
        if any(kw in query_lower for kw in ["計算", "平方根", "2乗", "sqrt", "**", "べき乗"]):
            # クエリから数式抽出（簡易）
            if "25の平方根" in query:
                expression = "sqrt(25)"
            elif "100の2乗" in query or "100の二乗" in query:
                expression = "100 ** 2"
            else:
                expression = "2 + 2"  # デフォルト
            
            tool_calls.append(MockToolCall(
                id=f"call_{random.randint(1000, 9999)}",
                function={
                    "name": "calculate",
                    "arguments": json.dumps({"expression": expression})
                }
            ))
        
        # 設備状態関連
        if any(kw in query_lower for kw in ["設備", "equipment", "line", "robot", "状態"]):
            # 設備ID抽出
            equipment_id = "LINE-A-01"  # デフォルト
            if "line-a-01" in query_lower:
                equipment_id = "LINE-A-01"
            elif "robot-b-03" in query_lower:
                equipment_id = "ROBOT-B-03"
            
            tool_calls.append(MockToolCall(
                id=f"call_{random.randint(1000, 9999)}",
                function={
                    "name": "get_equipment_status",
                    "arguments": json.dumps({
                        "equipment_id": equipment_id,
                        "include_history": False
                    })
                }
            ))
        
        return tool_calls
    
    def _generate_final_answer(self, messages: List[Dict]) -> MockResponse:
        """
        ツール実行結果から最終回答を生成
        
        実際のGPT-4oは自然言語生成するが、
        Mockではテンプレートベースで生成。
        """
        # ツール結果を収集
        tool_results = {}
        for msg in reversed(messages):
            if msg["role"] == "tool":
                tool_name = msg.get("name")
                result_data = json.loads(msg["content"])
                tool_results[tool_name] = result_data
        
        # 結果を整形して回答生成
        answer_parts = []
        
        if "get_current_datetime" in tool_results:
            dt = tool_results["get_current_datetime"]
            answer_parts.append(f"現在時刻は{dt['datetime']}です。")
        
        if "calculate" in tool_results:
            calc = tool_results["calculate"]
            answer_parts.append(
                f"{calc['expression']} の計算結果は {calc['result']} です。"
            )
        
        if "get_equipment_status" in tool_results:
            eq = tool_results["get_equipment_status"]
            status_ja = {
                "running": "稼働中",
                "warning": "警告",
                "stopped": "停止中"
            }
            answer_parts.append(
                f"{eq['equipment_id']} の状態は{status_ja.get(eq['status'], eq['status'])}です。"
                f"稼働時間は{eq['uptime_hours']}時間、生産数は{eq['production_count']}個です。"
            )
        
        final_answer = "\n".join(answer_parts) if answer_parts else "ツール実行完了しました。"
        
        return MockResponse(choices=[
            MockChoice(message=MockMessage(
                content=final_answer,
                tool_calls=None
            ))
        ])


class MockFunctionCallingAgent:
    """Mock版 Function Calling Agent"""
    
    def __init__(self):
        self.client = MockOpenAIClient()
        self.messages = []
        
        self.tool_implementations = {
            "calculate": calculate_impl,
            "get_current_datetime": get_current_datetime_impl,
            "get_equipment_status": get_equipment_status_impl
        }
    
    def _execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """ツール実行"""
        if tool_name not in self.tool_implementations:
            return json.dumps({"error": f"Unknown tool: {tool_name}"})
        
        try:
            impl = self.tool_implementations[tool_name]
            result = impl(**arguments)
            return json.dumps(result, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": str(e)})
    
    def run(self, user_message: str, tools: List[str] = None) -> str:
        """エージェント実行"""
        # システムプロンプト + ユーザーメッセージ
        self.messages = [
            {"role": "system", "content": "あなたは有能なAIアシスタントです。"},
            {"role": "user", "content": user_message}
        ]
        
        # ツールスキーマ取得
        tool_schemas = tool_registry.get_tool_schemas(tools)
        
        # 最大2回のイテレーション（ツール呼び出し → 最終回答）
        for iteration in range(2):
            print(f"\n[Iteration {iteration + 1}]")
            
            # OpenAI API呼び出し（Mock）
            response = self.client.create(
                model="gpt-4o",
                messages=self.messages,
                tools=tool_schemas
            )
            
            message = response.choices[0].message
            
            # ツール呼び出しなし → 最終回答
            if not message.tool_calls:
                return message.content
            
            # Assistantメッセージ追加
            self.messages.append({
                "role": "assistant",
                "content": message.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": tc.type,
                        "function": tc.function
                    }
                    for tc in message.tool_calls
                ]
            })
            
            # 各ツール実行
            for tool_call in message.tool_calls:
                function_name = tool_call.function["name"]
                function_args = json.loads(tool_call.function["arguments"])
                
                print(f"  [Tool Call] {function_name}({function_args})")
                
                # ツール実行
                tool_result = self._execute_tool(function_name, function_args)
                print(f"  [Tool Result] {tool_result[:100]}...")
                
                # ツール結果追加
                self.messages.append({
                    "role": "tool",
                    "name": function_name,
                    "content": tool_result,
                    "tool_call_id": tool_call.id
                })
        
        return "最大反復回数に達しました。"
    
    def reset(self):
        """リセット"""
        self.messages = []


if __name__ == "__main__":
    print("=" * 60)
    print("Function Calling Agent - Mock Version")
    print("=" * 60)
    
    agent = MockFunctionCallingAgent()
    
    # テストクエリ
    test_cases = [
        {
            "query": "現在時刻を教えてください",
            "tools": ["get_current_datetime"]
        },
        {
            "query": "25の平方根を計算してください",
            "tools": ["calculate"]
        },
        {
            "query": "現在時刻と、100の2乗を計算して教えてください",
            "tools": ["get_current_datetime", "calculate"]  # 並列実行
        },
        {
            "query": "LINE-A-01の設備状態を確認してください",
            "tools": ["get_equipment_status"]
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{'='*60}")
        print(f"Test {i}: {test['query']}")
        print(f"{'='*60}")
        
        answer = agent.run(test['query'], tools=test['tools'])
        
        print(f"\n[Final Answer]")
        print(answer)
        print()
        
        agent.reset()
