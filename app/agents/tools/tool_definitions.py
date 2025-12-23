"""
Function Calling Tool Definitions

Azure OpenAI Function Callingで使用するツール定義スキーマ。
各ツールはJSON Schemaに準拠した定義を持つ。
"""
from typing import List, Dict, Any, Literal


class ToolDefinition:
    """ツール定義の基底クラス"""
    
    @staticmethod
    def get_schema() -> Dict[str, Any]:
        """JSON Schema形式のツール定義を返す"""
        raise NotImplementedError


class SearchDocumentsTool(ToolDefinition):
    """ドキュメント検索ツール（Azure AI Search統合）"""
    
    @staticmethod
    def get_schema() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "search_documents",
                "description": "社内ドキュメントを検索し、関連情報を取得します。質問に答えるための情報が必要な場合に使用してください。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "検索クエリ（自然言語）"
                        },
                        "top_k": {
                            "type": "integer",
                            "description": "取得する結果数（デフォルト: 5）",
                            "default": 5,
                            "minimum": 1,
                            "maximum": 20
                        },
                        "filters": {
                            "type": "object",
                            "description": "検索フィルター（オプション）",
                            "properties": {
                                "category": {
                                    "type": "string",
                                    "description": "カテゴリーフィルター",
                                    "enum": ["技術文書", "業務手順", "安全規則", "保全マニュアル"]
                                },
                                "department": {
                                    "type": "string",
                                    "description": "部門フィルター"
                                }
                            }
                        }
                    },
                    "required": ["query"]
                }
            }
        }


class CalculatorTool(ToolDefinition):
    """数値計算ツール"""
    
    @staticmethod
    def get_schema() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "calculate",
                "description": "数式を評価して結果を返します。加減乗除、べき乗、平方根などの基本的な数学計算に使用してください。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expression": {
                            "type": "string",
                            "description": "評価する数式（例: '2 + 2', 'sqrt(16)', '10 ** 3'）"
                        }
                    },
                    "required": ["expression"]
                }
            }
        }


class DateTimeTool(ToolDefinition):
    """日時取得ツール"""
    
    @staticmethod
    def get_schema() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "get_current_datetime",
                "description": "現在の日時を取得します。今日の日付や現在時刻が必要な場合に使用してください。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "timezone": {
                            "type": "string",
                            "description": "タイムゾーン（デフォルト: Asia/Tokyo）",
                            "default": "Asia/Tokyo",
                            "enum": ["Asia/Tokyo", "UTC", "America/New_York", "Europe/London"]
                        },
                        "format": {
                            "type": "string",
                            "description": "出力フォーマット",
                            "enum": ["iso", "japanese", "unix"],
                            "default": "japanese"
                        }
                    },
                    "required": []
                }
            }
        }


class EquipmentStatusTool(ToolDefinition):
    """設備状態確認ツール（工場向け、スタブ実装）"""
    
    @staticmethod
    def get_schema() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "get_equipment_status",
                "description": "工場設備の現在の稼働状態を取得します。設備の状態、稼働率、エラー情報などを確認できます。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "equipment_id": {
                            "type": "string",
                            "description": "設備ID（例: 'LINE-A-01', 'ROBOT-B-03'）"
                        },
                        "include_history": {
                            "type": "boolean",
                            "description": "過去24時間の履歴を含めるか",
                            "default": False
                        }
                    },
                    "required": ["equipment_id"]
                }
            }
        }


class ToolRegistry:
    """利用可能なツールの登録・管理"""
    
    def __init__(self):
        self.tools: Dict[str, ToolDefinition] = {
            "search_documents": SearchDocumentsTool(),
            "calculate": CalculatorTool(),
            "get_current_datetime": DateTimeTool(),
            "get_equipment_status": EquipmentStatusTool()
        }
    
    def get_tool_schemas(self, tool_names: List[str] = None) -> List[Dict[str, Any]]:
        """
        指定されたツールのスキーマリストを取得
        
        Args:
            tool_names: 取得するツール名のリスト（Noneの場合は全ツール）
        
        Returns:
            ツールスキーマのリスト
        """
        if tool_names is None:
            tool_names = list(self.tools.keys())
        
        return [
            self.tools[name].get_schema()
            for name in tool_names
            if name in self.tools
        ]
    
    def get_all_tool_schemas(self) -> List[Dict[str, Any]]:
        """全ツールのスキーマを取得"""
        return self.get_tool_schemas()


# グローバルレジストリインスタンス
tool_registry = ToolRegistry()


if __name__ == "__main__":
    # スキーマ検証用
    import json
    
    print("=== Available Tools ===")
    schemas = tool_registry.get_all_tool_schemas()
    for schema in schemas:
        print(f"\n{schema['function']['name']}:")
        print(json.dumps(schema, indent=2, ensure_ascii=False))
