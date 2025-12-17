#!/usr/bin/env python3
"""验证脚本 - 检查src layout迁移后的功能完整性

用于验证 src/batch_mcp/ 结构的正确性和功能完整性。
"""

import sys
import traceback
from pathlib import Path


class MigrationValidator:
    """迁移验证器"""

    def __init__(self):
        self.test_results = []
        self.failed_tests = []
        self.warnings = []

    def log_test(self, name: str, success: bool, message: str = "") -> None:
        """记录测试结果"""
        status = "✅" if success else "❌"
        full_message = f"{status} {name}"
        if message:
            full_message += f": {message}"

        print(full_message)

        test_result = {"name": name, "success": success, "message": message}

        self.test_results.append(test_result)

        if not success:
            self.failed_tests.append(test_result)

    def log_warning(self, message: str) -> None:
        """记录警告"""
        print(f"⚠️  {message}")
        self.warnings.append(message)

    def test_file_structure(self) -> bool:
        """验证文件结构"""
        print("🏗️  验证文件结构...")

        required_files = [
            "src/batch_mcp/__init__.py",
            "src/batch_mcp/__main__.py",
            "src/batch_mcp/main.py",
            "src/batch_mcp/core/__init__.py",
            "src/batch_mcp/agents/__init__.py",
            "src/batch_mcp/utils/__init__.py",
            "src/batch_mcp/tools/__init__.py",
        ]

        missing_files = []
        for file_path in required_files:
            if not Path(file_path).exists():
                missing_files.append(file_path)

        if missing_files:
            self.log_test("文件结构检查", False, f"缺失 {len(missing_files)} 个文件")
            for file_path in missing_files:
                print(f"    - {file_path}")
            return False

        self.log_test("文件结构检查", True, f"所有 {len(required_files)} 个文件存在")
        return True

    def test_imports(self) -> bool:
        """验证关键导入"""
        print("\n📦 验证Python导入...")

        test_imports = [
            ("核心测试器", "from src.batch_mcp.core.tester import MCPTester"),
            (
                "部署器",
                "from src.batch_mcp.core.simple_mcp_deployer import SimpleMCPDeployer",
            ),
            ("CSV解析器", "from src.batch_mcp.utils.csv_parser import MCPDataParser"),
            ("测试代理", "from src.batch_mcp.agents.test_agent import TestAgent"),
            (
                "验证代理",
                "from src.batch_mcp.agents.validation_agent import ValidationAgent",
            ),
            (
                "异步客户端",
                "from src.batch_mcp.core.async_mcp_client import AsyncMCPClient",
            ),
            (
                "URL处理器",
                "from src.batch_mcp.core.url_mcp_processor import URLMCPProcessor",
            ),
            ("评估器模块", "import src.batch_mcp.core.evaluator"),
        ]

        success_count = 0
        for name, import_stmt in test_imports:
            try:
                exec(import_stmt)
                self.log_test(name, True)
                success_count += 1
            except Exception as e:
                self.log_test(name, False, str(e))

        self.log_test(
            "导入检查",
            success_count == len(test_imports),
            f"{success_count}/{len(test_imports)} 成功",
        )
        return success_count == len(test_imports)

    def test_package_info(self) -> bool:
        """验证包信息"""
        print("\n📋 验证包信息...")

        try:
            from src.batch_mcp import __author__, __version__

            self.log_test("包版本", True, f"v{__version__}")
            self.log_test("包作者", True, __author__)
            return True
        except Exception as e:
            self.log_test("包信息", False, str(e))
            return False

    def test_main_entry(self) -> bool:
        """验证主入口点"""
        print("\n🚀 验证主入口点...")

        try:
            # 测试模块导入
            import src.batch_mcp.main

            self.log_test("主模块导入", True)

            # 测试app对象
            app = src.batch_mcp.main.app
            self.log_test("app对象", True, type(app).__name__)

            return True
        except Exception as e:
            self.log_test("主入口点", False, str(e))
            return False

    def test_cli_help(self) -> bool:
        """验证CLI帮助"""
        print("\n💬 验证CLI帮助...")

        try:
            import subprocess

            result = subprocess.run(
                [sys.executable, "-m", "src.batch_mcp", "--help"],
                check=False,
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                help_text = result.stdout
                success = "Usage:" in help_text and "Commands:" in help_text
                self.log_test("CLI帮助", success, f"返回码: {result.returncode}")
                return success
            self.log_test("CLI帮助", False, f"返回码: {result.returncode}")
            return False
        except subprocess.TimeoutExpired:
            self.log_test("CLI帮助", False, "命令超时")
            return False
        except Exception as e:
            self.log_test("CLI帮助", False, str(e))
            return False

    def test_external_imports(self) -> bool:
        """验证外部文件的导入更新"""
        print("\n🔗 验证外部文件导入...")

        # 检查关键的外部文件是否正确更新了导入路径
        critical_files = [
            "scripts/select_simple_tools.py",
            "scripts/update_csv_package_names.py",
            "tests/unit/utils/test_utils.py",
        ]

        success_count = 0
        for file_path in critical_files:
            if Path(file_path).exists():
                try:
                    with open(file_path, encoding="utf-8") as f:
                        content = f.read()

                    # 检查是否包含新的导入路径
                    if "src.batch_mcp." in content:
                        self.log_test(f"外部导入检查 ({file_path})", True)
                        success_count += 1
                    else:
                        self.log_test(
                            f"外部导入检查 ({file_path})", False, "未找到新的导入路径"
                        )
                except Exception as e:
                    self.log_test(f"外部导入检查 ({file_path})", False, str(e))
            else:
                self.log_warning(f"外部导入检查 ({file_path}): 文件不存在")

        self.log_test(
            "外部导入检查",
            success_count == len(critical_files),
            f"{success_count}/{len(critical_files)} 个文件已更新",
        )
        return True

    def test_file_pathing(self) -> bool:
        """验证文件路径关系"""
        print("\n📍 验证文件路径关系...")

        try:
            from src.batch_mcp.utils.csv_parser import get_mcp_parser

            # 测试CSV解析器是否能找到正确的文件路径
            parser = get_mcp_parser()
            if hasattr(parser, "csv_path"):
                expected_path = "src/batch_mcp/../../../data/mcp_database/mcp.csv"
                actual_path = str(parser.csv_path)
                if "mcp_database/mcp.csv" in actual_path:
                    self.log_test("文件路径检查", True, "CSV文件路径正确")
                    return True
                self.log_test("文件路径检查", False, f"路径错误: {actual_path}")
                return False
            self.log_warning("文件路径检查: 无法访问csv_path")
            return True

        except Exception as e:
            self.log_test("文件路径检查", False, str(e))
            return False

    def run_all_tests(self) -> bool:
        """运行所有验证测试"""
        print("🔍 开始src layout迁移验证...\n")

        tests = [
            ("文件结构", self.test_file_structure),
            ("Python导入", self.test_imports),
            ("包信息", self.test_package_info),
            ("主入口点", self.test_main_entry),
            ("CLI帮助", self.test_cli_help),
            ("外部导入", self.test_external_imports),
            ("文件路径", self.test_file_pathing),
        ]

        all_passed = True
        for test_name, test_func in tests:
            try:
                result = test_func()
                if not result:
                    all_passed = False
            except Exception as e:
                self.log_test(test_name, False, f"测试执行异常: {e}")
                traceback.print_exc()
                all_passed = False

        return all_passed

    def print_summary(self) -> None:
        """打印验证摘要"""
        print("\n" + "=" * 50)
        print("📊 验证摘要")
        print("=" * 50)

        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["success"]])
        failed_tests = len(self.failed_tests)

        print(f"总测试数: {total_tests}")
        print(f"✅ 通过: {passed_tests}")
        print(f"❌ 失败: {failed_tests}")

        if self.warnings:
            print(f"⚠️  警告: {len(self.warnings)}")

        print(f"成功率: {passed_tests / total_tests * 100:.1f}%")

        if failed_tests > 0:
            print("\n❌ 失败的测试:")
            for test in self.failed_tests:
                print(f"  - {test['name']}: {test['message']}")


def main():
    """主函数"""
    validator = MigrationValidator()
    success = validator.run_all_tests()
    validator.print_summary()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
