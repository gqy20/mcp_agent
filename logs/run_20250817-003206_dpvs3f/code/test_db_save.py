#!/usr/bin/env python3
"""
测试数据库保存功能的简单脚本
"""

import sys

sys.path.append("src")

from datetime import datetime

from src.core.enhanced_report_model import (
    EnhancedMCPTestReport,
    TestMetadata,
    TestStatus,
    ToolInfo,
)
from src.core.supabase_connector import SupabaseConnector


def test_database_save():
    """测试数据库保存功能"""
    print("🧪 开始测试数据库保存功能...")

    # 创建一个最小化的测试报告
    report = EnhancedMCPTestReport()
    report.metadata = TestMetadata(
        session_id="test-session-123", test_environment="test", trigger_source="manual"
    )
    report.tool_info = ToolInfo(
        name="Test Tool",
        author="test-author",
        github_url="https://github.com/test/test",
        package_name="test-package",
        category="testing",
        description="Test tool for database saving",
    )
    report.overall_status = TestStatus.SUCCESS
    report.total_duration_seconds = 1.5
    report.environment = {
        "platform": "Windows",
        "python_version": "3.12.0",
        "architecture": "64bit",
    }

    print(f"📝 报告ID: {report.report_id}")
    print(f"📝 元数据session_id: {report.metadata.session_id}")
    print(f"📝 工具名称: {report.tool_info.name}")

    # 测试数据库连接
    try:
        connector = SupabaseConnector()
        print("✅ Supabase连接器初始化成功")

        # 保存报告
        saved_id = connector.save_test_report(report)
        print(f"✅ 报告保存成功！ID: {saved_id}")

    except Exception as e:
        print(f"❌ 保存失败: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_database_save()
