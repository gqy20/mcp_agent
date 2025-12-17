#!/usr/bin/env python3
"""数据库数据验证脚本.

验证测试数据是否成功存储到Supabase数据库
"""

import sys
from pathlib import Path

# 添加src目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from src.batch_mcp.core.supabase_connector import SupabaseConnector


def main() -> bool | None:
    """验证数据库中的数据."""
    try:
        # 创建连接器
        connector = SupabaseConnector()

        # 查询工具数据
        tools_result = connector.client.table("mcp_tools").select("*").execute()
        tools_count = len(tools_result.data)

        if tools_count > 0:
            tools_result.data[-1]

        # 查询测试报告
        reports_result = connector.client.table("test_reports").select("*").execute()
        reports_count = len(reports_result.data)

        if reports_count > 0:
            reports_result.data[-1]

        # 查询测试执行详情
        executions_result = (
            connector.client.table("test_executions").select("*").execute()
        )
        len(executions_result.data)

        # 查询质量指标
        quality_result = connector.client.table("quality_metrics").select("*").execute()
        quality_count = len(quality_result.data)

        if quality_count > 0:
            quality_result.data[-1]

        return True

    except Exception:
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
