#!/usr/bin/env python3
"""Supabase 设置验证器.

用途：验证 Supabase 配置和数据库连接是否正确配置
运行：uv run python src/tools/setup_validator.py
"""

import sys
from pathlib import Path

# 添加src目录到路径
sys.path.append(str(Path(__file__).parent.parent))

# 导入配置系统
try:
    from src.batch_mcp.core.config import get_config

    CONFIG_AVAILABLE = True
    config = get_config() if CONFIG_AVAILABLE else None
except ImportError:
    CONFIG_AVAILABLE = False
    config = None


def validate_environment() -> bool:
    """验证环境变量配置."""
    if not CONFIG_AVAILABLE:
        return False

    # 验证数据库配置
    if not config.database.has_supabase_config:
        return False

    # 显示配置信息（安全显示）
    url = config.database.supabase_url
    key = config.database.supabase_service_role_key
    url[:10] + "..." if len(url) > 10 else url
    key[:10] + "..." if len(key) > 10 else key

    return True


def validate_supabase_connection() -> bool | None:
    """验证Supabase连接."""
    try:
        from src.batch_mcp.core.supabase_connector import SupabaseConnector

        connector = SupabaseConnector()

        # 测试连接
        connector.client.table("mcp_tools").select("count").execute()
        return True

    except ImportError:
        return False
    except Exception:
        return False


def validate_database_schema() -> bool | None:
    """验证数据库表结构."""
    try:
        from src.batch_mcp.core.supabase_connector import SupabaseConnector

        connector = SupabaseConnector()

        expected_tables = [
            "mcp_tools",
            "test_reports",
            "test_executions",
            "quality_metrics",
            "performance_analysis",
            "deployment_info",
            "test_metadata",
        ]

        existing_tables = []
        missing_tables = []

        for table in expected_tables:
            try:
                (connector.client.table(table).select("count").limit(1).execute())
                existing_tables.append(table)
            except Exception:
                missing_tables.append(table)

        return not missing_tables

    except Exception:
        return False


def main() -> None:
    """主验证流程."""
    steps = [
        ("环境变量配置", validate_environment),
        ("Supabase连接", validate_supabase_connection),
        ("数据库表结构", validate_database_schema),
    ]

    results = []
    for step_name, step_func in steps:
        try:
            result = step_func()
            results.append((step_name, result))
        except Exception:
            results.append((step_name, False))

    # 汇总结果

    all_passed = True
    for _step_name, passed in results:
        if not passed:
            all_passed = False

    if all_passed:
        pass
    else:
        pass


if __name__ == "__main__":
    main()
