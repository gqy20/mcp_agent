#!/usr/bin/env python3
"""简化的数据库保存测试."""

import sys
from datetime import datetime
from pathlib import Path

# 添加src目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from src.batch_mcp.core.supabase_connector import SupabaseConnector


def test_direct_db_save() -> bool | None:
    """直接测试数据库保存功能."""
    try:
        # 创建连接器
        connector = SupabaseConnector()

        # 插入一个测试工具
        tool_data = {
            "name": "Direct Test Tool",
            "author": "Test System",
            "github_url": "https://github.com/test/direct-test",
            "package_name": "direct-test-tool",
            "category": "testing",
            "description": "A tool to test direct database insertion",
            "version": "0.1.0",
            "requires_api_key": False,
            "language": "Python",
            "license": "MIT",
            "stars": 50,
        }

        result = connector.client.table("mcp_tools").insert(tool_data).execute()
        tool_id = result.data[0]["id"]

        # 插入一个测试报告
        report_data = {
            "test_run_id": "direct-test-123",
            "timestamp": datetime.now().isoformat(),
            "total_tools": 1,
            "tools_tested": 1,
            "tools_successful": 1,
            "overall_status": "SUCCESS",
            "execution_time_seconds": 2.5,
            "python_version": "3.12.0",
            "platform": "Windows",
            "test_environment": "direct-test",
        }

        result = connector.client.table("test_reports").insert(report_data).execute()
        report_id = result.data[0]["id"]

        # 插入一个测试执行记录
        execution_data = {
            "report_id": report_id,
            "tool_id": tool_id,
            "status": "SUCCESS",
            "execution_time_seconds": 1.5,
            "memory_usage_mb": 30.0,
            "test_data": {"test_type": "basic", "result": "passed"},
        }

        result = (
            connector.client.table("test_executions").insert(execution_data).execute()
        )
        result.data[0]["id"]

        # 验证数据
        len(connector.client.table("mcp_tools").select("*").execute().data)
        len(connector.client.table("test_reports").select("*").execute().data)
        len(connector.client.table("test_executions").select("*").execute().data)

        return True

    except Exception:
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_direct_db_save()
    sys.exit(0 if success else 1)
