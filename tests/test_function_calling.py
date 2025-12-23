"""
Function Calling Agent - Unit Tests

pytest実行:
    cd /home/claude
    PYTHONPATH=/home/claude pytest tests/test_function_calling.py -v
"""
import pytest
import json
import sys
sys.path.append('/home/claude')

from app.agents.tools.tool_definitions import tool_registry, ToolRegistry
from app.agents.tools.implementations import (
    calculate_impl,
    get_current_datetime_impl,
    get_equipment_status_impl
)
from app.agents.function_calling_agent_mock import MockFunctionCallingAgent


# =============================================================================
# Tool Definitions Tests
# =============================================================================

class TestToolDefinitions:
    """ツール定義スキーマのテスト"""
    
    def test_tool_registry_initialization(self):
        """ツールレジストリ初期化"""
        registry = ToolRegistry()
        assert len(registry.tools) >= 4
        assert "calculate" in registry.tools
        assert "get_current_datetime" in registry.tools
        assert "get_equipment_status" in registry.tools
    
    def test_get_all_tool_schemas(self):
        """全ツールスキーマ取得"""
        schemas = tool_registry.get_all_tool_schemas()
        assert len(schemas) >= 4
        
        # スキーマ構造検証
        for schema in schemas:
            assert "type" in schema
            assert schema["type"] == "function"
            assert "function" in schema
            assert "name" in schema["function"]
            assert "description" in schema["function"]
            assert "parameters" in schema["function"]
    
    def test_get_tool_schemas_with_filter(self):
        """特定ツールスキーマ取得"""
        schemas = tool_registry.get_tool_schemas(["calculate", "get_current_datetime"])
        assert len(schemas) == 2
        
        names = [s["function"]["name"] for s in schemas]
        assert "calculate" in names
        assert "get_current_datetime" in names
    
    def test_tool_schema_required_fields(self):
        """必須フィールド検証"""
        schema = tool_registry.get_tool_schemas(["calculate"])[0]
        params = schema["function"]["parameters"]
        
        assert "required" in params
        assert "expression" in params["required"]


# =============================================================================
# Tool Implementations Tests
# =============================================================================

class TestCalculatorTool:
    """計算ツールのテスト"""
    
    def test_basic_arithmetic(self):
        """基本的な四則演算"""
        result = calculate_impl("2 + 2")
        assert result["result"] == 4
        assert result["expression"] == "2 + 2"
    
    def test_sqrt_function(self):
        """平方根計算"""
        result = calculate_impl("sqrt(16)")
        assert result["result"] == 4.0
    
    def test_power_operation(self):
        """べき乗演算"""
        result = calculate_impl("2 ** 8")
        assert result["result"] == 256
    
    def test_pi_constant(self):
        """円周率使用"""
        result = calculate_impl("pi * 2")
        assert 6.28 < result["result"] < 6.29
    
    def test_complex_expression(self):
        """複雑な数式"""
        result = calculate_impl("sqrt(16) + 2 ** 3")
        assert result["result"] == 12.0
    
    def test_invalid_expression(self):
        """不正な数式"""
        result = calculate_impl("invalid expression")
        assert "error" in result
    
    def test_unsafe_function_blocked(self):
        """安全でない関数のブロック"""
        result = calculate_impl("__import__('os').system('ls')")
        assert "error" in result


class TestDateTimeTool:
    """日時ツールのテスト"""
    
    def test_default_timezone(self):
        """デフォルトタイムゾーン"""
        result = get_current_datetime_impl()
        assert result["timezone"] == "Asia/Tokyo"
        assert "datetime" in result
        assert "timestamp" in result
    
    def test_utc_timezone(self):
        """UTCタイムゾーン"""
        result = get_current_datetime_impl(timezone="UTC")
        assert result["timezone"] == "UTC"
    
    def test_iso_format(self):
        """ISO形式"""
        result = get_current_datetime_impl(format="iso")
        assert "T" in result["datetime"]  # ISO形式にはT含まれる
    
    def test_japanese_format(self):
        """日本語形式"""
        result = get_current_datetime_impl(format="japanese")
        assert "年" in result["datetime"]
        assert "月" in result["datetime"]
        assert "日" in result["datetime"]
    
    def test_unix_format(self):
        """Unix timestamp形式"""
        result = get_current_datetime_impl(format="unix")
        assert result["datetime"].isdigit()
    
    def test_day_of_week(self):
        """曜日情報"""
        result = get_current_datetime_impl()
        assert "day_of_week" in result
        assert "day_of_week_ja" in result
        assert result["day_of_week_ja"] in ["月", "火", "水", "木", "金", "土", "日"]


class TestEquipmentStatusTool:
    """設備状態ツールのテスト"""
    
    def test_running_equipment(self):
        """稼働中設備"""
        result = get_equipment_status_impl("LINE-A-01")
        assert result["equipment_id"] == "LINE-A-01"
        assert result["status"] == "running"
        assert result["error_count"] == 0
    
    def test_warning_equipment(self):
        """警告状態設備"""
        result = get_equipment_status_impl("ROBOT-B-03")
        assert result["equipment_id"] == "ROBOT-B-03"
        assert result["status"] == "warning"
        assert result["error_count"] > 0
        assert "last_error" in result
    
    def test_stopped_equipment(self):
        """停止中設備"""
        result = get_equipment_status_impl("PRESS-C-05")
        assert result["equipment_id"] == "PRESS-C-05"
        assert result["status"] == "stopped"
        assert "stopped_at" in result
    
    def test_unknown_equipment(self):
        """未知の設備"""
        result = get_equipment_status_impl("UNKNOWN-99")
        assert "error" in result
        assert "available_equipment" in result
    
    def test_include_history(self):
        """履歴含む"""
        result = get_equipment_status_impl("LINE-A-01", include_history=True)
        assert "history_24h" in result
        assert len(result["history_24h"]) > 0


# =============================================================================
# Mock Agent Tests
# =============================================================================

class TestMockAgent:
    """Mock Agent動作テスト"""
    
    def setup_method(self):
        """各テスト前に実行"""
        self.agent = MockFunctionCallingAgent()
    
    def test_single_tool_call(self):
        """単一ツール呼び出し"""
        answer = self.agent.run(
            "現在時刻を教えてください",
            tools=["get_current_datetime"]
        )
        assert "時" in answer or "現在" in answer
    
    def test_parallel_tool_calls(self):
        """並列ツール呼び出し"""
        answer = self.agent.run(
            "現在時刻と、100の2乗を計算して教えてください",
            tools=["get_current_datetime", "calculate"]
        )
        assert "10000" in answer  # 100 ** 2
        assert ("時" in answer or "現在" in answer)
    
    def test_equipment_status_query(self):
        """設備状態クエリ"""
        answer = self.agent.run(
            "LINE-A-01の設備状態を確認してください",
            tools=["get_equipment_status"]
        )
        assert "LINE-A-01" in answer
        assert ("稼働" in answer or "running" in answer)
    
    def test_agent_reset(self):
        """エージェントリセット"""
        self.agent.run("テスト", tools=["get_current_datetime"])
        assert len(self.agent.messages) > 0
        
        self.agent.reset()
        assert len(self.agent.messages) == 0


# =============================================================================
# Integration Tests
# =============================================================================

class TestIntegration:
    """統合テスト"""
    
    def test_all_tools_available(self):
        """全ツール利用可能"""
        agent = MockFunctionCallingAgent()
        
        # 各ツールが正常動作するか
        queries = [
            ("25の平方根を計算してください", ["calculate"]),
            ("現在時刻を教えてください", ["get_current_datetime"]),
            ("LINE-A-01の状態を確認してください", ["get_equipment_status"])
        ]
        
        for query, tools in queries:
            answer = agent.run(query, tools=tools)
            assert answer is not None
            assert len(answer) > 0
            agent.reset()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
