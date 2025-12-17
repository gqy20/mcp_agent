#!/usr/bin/env python3
"""
MCP Agent 统一测试脚本 - Linus风格
"Talk is cheap. Show me the code." - 一个脚本解决所有测试需求

作者: AI Assistant (Linus重构版)
日期: 2025-08-21
版本: 3.0.0 (MVP版本)

使用方法:
  python master_test.py --help
  python master_test.py db           # 数据库连接测试
  python master_test.py workflow     # 完整流程测试
  python master_test.py integration  # 集成验证
  python master_test.py all          # 运行所有测试
"""

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

# 项目配置
PROJECT_ROOT = Path(__file__).parent
SUPABASE_URL = "https://vmikqjfxbdvfpakvwoab.supabase.co"
SUPABASE_SERVICE_ROLE_KEY = os.getenv(
    "SUPABASE_SERVICE_ROLE_KEY", "your-service-role-key"
)


class MasterTester:
    """统一测试类 - 消除所有特殊情况"""

    def __init__(self):
        self.results = {}

    def run_database_test(self) -> bool:
        """数据库连接和功能测试 - 单一职责"""
        print("🗄️ 数据库功能测试")
        print("=" * 40)

        try:
            from supabase import create_client

            print("✅ Supabase库可用")
        except ImportError:
            print("❌ Supabase库未安装")
            return False

        try:
            # 连接测试
            client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
            result = (
                client.table("mcp_test_results").select("test_id").limit(1).execute()
            )
            print(f"✅ 数据库连接成功，记录数: {len(result.data)}")

            # 查询测试
            recent = (
                client.table("mcp_test_results")
                .select("*")
                .order("test_timestamp", desc=True)
                .limit(3)
                .execute()
            )
            print(f"✅ 最近测试记录: {len(recent.data)} 条")

            # 统计测试
            all_records = (
                client.table("mcp_test_results").select("test_success").execute()
            )
            success_count = sum(1 for r in all_records.data if r["test_success"])
            total = len(all_records.data)
            success_rate = (success_count / total * 100) if total > 0 else 0
            print(f"✅ 成功率统计: {success_count}/{total} ({success_rate:.1f}%)")

            self.results["database"] = True
            return True

        except Exception as e:
            print(f"❌ 数据库测试失败: {e}")
            self.results["database"] = False
            return False

    def run_workflow_test(self) -> bool:
        """完整工作流程测试 - 端到端验证"""
        print("\n🧪 完整流程测试")
        print("=" * 40)

        try:
            # 运行主程序测试
            test_url = "https://github.com/upstash/context7"
            cmd = [
                "uv",
                "run",
                "python",
                "src/main.py",
                "test-url",
                test_url,
                "--timeout",
                "120",
                "--db-export",
            ]

            print(f"🎯 测试命令: {' '.join(cmd)}")
            result = subprocess.run(
                cmd, cwd=PROJECT_ROOT, capture_output=True, text=True
            )

            success = result.returncode == 0
            print(f"📊 执行结果: {'✅ 成功' if success else '❌ 失败'}")

            if not success:
                print(f"错误输出: {result.stderr[:200]}...")

            # 验证报告文件
            reports_dir = PROJECT_ROOT / "data" / "test_results"
            json_files = list(reports_dir.glob("*.json"))
            html_files = list(reports_dir.glob("*.html"))

            print(f"📄 生成报告: JSON({len(json_files)}) HTML({len(html_files)})")

            self.results["workflow"] = success
            return success

        except Exception as e:
            print(f"❌ 流程测试失败: {e}")
            self.results["workflow"] = False
            return False

    def run_integration_test(self) -> bool:
        """集成验证测试 - 组件协作"""
        print("\n🔧 集成验证测试")
        print("=" * 40)

        try:
            # 1. 核心模块导入测试
            print("1. 核心模块测试...")
            sys.path.insert(0, str(PROJECT_ROOT / "src"))

            from batch_mcp.core.cli_handlers import get_cli_handler
            from batch_mcp.core.tester import TestConfig, get_mcp_tester
            from batch_mcp.utils.csv_parser import get_mcp_parser

            # 2. 配置测试
            config = TestConfig(timeout=120, db_export=True)
            print(f"   TestConfig: ✅ (db_export={config.db_export})")

            # 3. 组件测试
            parser = get_mcp_parser()
            tools = parser.get_all_tools()
            print(f"   MCP Parser: ✅ ({len(tools)} 工具)")

            tester = get_mcp_tester()
            handler = get_cli_handler()
            print(f"   Handler/Tester: ✅")

            # 4. 环境检查
            from dotenv import load_dotenv

            load_dotenv()

            supabase_url = os.getenv("SUPABASE_URL")
            print(f"   环境配置: {'✅' if supabase_url else '❌'}")

            self.results["integration"] = True
            return True

        except Exception as e:
            print(f"❌ 集成测试失败: {e}")
            self.results["integration"] = False
            return False

    def run_all_tests(self) -> bool:
        """运行所有测试 - 统一入口"""
        print("🚀 MCP Agent 完整测试套件")
        print("=" * 50)

        start_time = time.time()

        # 按顺序执行所有测试
        tests = [
            ("Database", self.run_database_test),
            ("Integration", self.run_integration_test),
            ("Workflow", self.run_workflow_test),
        ]

        passed = 0
        for name, test_func in tests:
            if test_func():
                passed += 1

        # 输出总结
        duration = time.time() - start_time
        print(f"\n📊 测试总结")
        print("=" * 50)
        print(f"通过测试: {passed}/{len(tests)}")
        print(f"测试用时: {duration:.1f}秒")

        # 详细结果
        for test_name, result in self.results.items():
            status = "✅" if result else "❌"
            print(f"{status} {test_name.title()}")

        success = passed == len(tests)
        print(f"\n🏁 最终结果: {'🎉 全部通过' if success else '❌ 存在失败'}")

        return success


def main():
    """主函数 - 简洁的参数处理"""
    parser = argparse.ArgumentParser(
        description="MCP Agent 统一测试脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
测试类型:
  db          数据库连接和功能测试
  workflow    完整工作流程测试
  integration 组件集成验证测试
  all         运行所有测试 (默认)
        """,
    )

    parser.add_argument(
        "test_type",
        nargs="?",
        default="all",
        choices=["db", "workflow", "integration", "all"],
        help="要运行的测试类型",
    )

    args = parser.parse_args()

    # 执行测试
    tester = MasterTester()

    if args.test_type == "db":
        success = tester.run_database_test()
    elif args.test_type == "workflow":
        success = tester.run_workflow_test()
    elif args.test_type == "integration":
        success = tester.run_integration_test()
    else:  # all
        success = tester.run_all_tests()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
