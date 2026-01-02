"""CLI 命令处理器模块.

此模块包含 CLI 处理的核心逻辑。
"""

import time
from typing import Any

from rich import print as rprint

from src.batch_mcp.core.database_exporter import get_database_exporter
from src.batch_mcp.core.http_mcp_handler import get_http_mcp_handler
from src.batch_mcp.core.input_type_detector import get_input_type_detector
from src.batch_mcp.core.result_presenter import get_result_presenter
from src.batch_mcp.core.test_runner import get_test_runner
from src.batch_mcp.core.tester import TestConfig, get_mcp_tester
from src.batch_mcp.core.tool_finder import get_tool_finder

from .http_cli import HTTPCLIHandler
from .stdio_cli import STDIOCLIHandler


class CLIHandler:
    """CLI命令处理器 - 统一处理模式."""

    def __init__(self) -> None:
        """初始化CLI处理器."""
        self.tester = get_mcp_tester()
        self._test_runner = get_test_runner()
        self._http_handler = get_http_mcp_handler()
        self._input_detector = get_input_type_detector()
        self._tool_finder = get_tool_finder()
        self._presenter = get_result_presenter()
        self._exporter = get_database_exporter()

        # 子处理器
        self._stdio_handler = STDIOCLIHandler(
            self.tester, self._presenter, self._exporter
        )
        self._http_cli_handler = HTTPCLIHandler(
            self._http_handler, self._exporter, self._input_detector, self._tool_finder
        )

    def test_url(self, input_str: str, config: TestConfig) -> bool:
        """统一的智能测试入口 - 支持自动识别输入类型.

        支持自动识别输入类型：
        - HTTP MCP端点 (https://api.example.com/mcp)
        - GitHub URL (https://github.com/user/repo)
        - 包名 (@upstash/context7-mcp)
        - 搜索查询 (context7)

        Args:
            input_str: 用户输入字符串
            config: 测试配置

        Returns:
            bool: 测试是否成功

        """
        try:
            # 1. 智能检测输入类型
            input_type = self._input_detector.detect(input_str)

            # 2. 根据输入类型优化配置
            config = self._input_detector.adapt_config(input_type, config)

            # 3. 显示检测信息
            self._presenter.display_input_type_detection(input_str, input_type)

            # 4. 查找工具信息 (现有逻辑已包含HTTP处理)
            tool_info = self._find_tool_info(input_str)
            if not tool_info:
                return False

            # 2. 部署工具
            server_info = self._deploy_tool(tool_info, config)
            if not server_info:
                return False

            # 3. 执行测试
            success, test_results = self._run_tests(tool_info, server_info, config)

            # 3.5. 评估工具 (使用提取的方法)
            evaluation_result = self._evaluate_tool_safe(
                tool_info,
                server_info,
                test_results,
                success,
                config,
            )

            # 4. 处理测试输出 (使用提取的方法)
            self._handle_test_outputs(
                tool_info,
                server_info,
                success,
                test_results,
                config,
                evaluation_result,
                input_str,
            )

            # 5. 清理资源
            if config.cleanup:
                self._stdio_handler.cleanup_server(server_info.server_id)

            return success

        except Exception:
            rprint("[red]❌ 测试过程发生错误[/red]")
            return False

    def test_package(self, package: str, config: TestConfig) -> bool:
        """测试包 - 统一流程."""
        try:
            # 查找工具信息
            parser, _ = self.tester._get_services()
            tool_info = parser.find_tool_by_package(package)

            # 直接部署包
            server_info = self.tester.deploy_tool(package, config.timeout)
            if not server_info:
                rprint("[red]❌ MCP工具部署失败[/red]")
                return False

            self._presenter.display_deployment_success(server_info, package)

            # 执行测试 - 统一逻辑，支持smart模式
            success, test_results = self._run_tests(tool_info, server_info, config)

            # 评估工具 (使用提取的方法)
            evaluation_result = self._evaluate_tool_safe(
                tool_info,
                server_info,
                test_results,
                success,
                config,
            )

            # 处理测试输出 (使用提取的方法)
            self._handle_test_outputs(
                tool_info,
                server_info,
                success,
                test_results,
                config,
                evaluation_result,
                package,
            )

            # 清理
            if config.cleanup:
                self._stdio_handler.cleanup_server(server_info.server_id)

            return success

        except Exception:
            rprint("[red]❌ 测试过程发生错误[/red]")
            return False

    def test_http_endpoint(
        self, url: str, config: TestConfig, auth_token: str | None = None
    ) -> bool:
        """测试 HTTP MCP 端点."""
        try:
            rprint(f"[blue]🔗 准备测试 HTTP MCP 端点: {url}[/blue]")

            # 验证 URL 格式
            if not self._input_detector.is_http_mcp_endpoint(url):
                rprint("[red]❌ URL 格式不支持，必须是 HTTP MCP 端点[/red]")
                return False

            # 创建临时的 MCPToolInfo - 使用 ToolFinder
            tool_info = self._tool_finder._create_http_tool_info(url)

            # 构建HTTP配置
            http_config = {
                "url": url,
                "headers": {},
                "timeout": config.timeout,
            }

            # 添加认证令牌
            if auth_token:
                http_config["headers"]["Authorization"] = f"Bearer {auth_token}"
                rprint("[blue]🔐 已配置认证令牌[/blue]")

            # 运行测试
            import asyncio

            return asyncio.run(
                self._http_cli_handler.run_http_tests_direct(
                    tool_info, http_config, config
                )
            )

        except Exception:
            rprint("[red]❌ HTTP MCP 测试失败[/red]")
            return False

    def list_tools(
        self,
        category: str | None,
        search: str | None,
        limit: int,
        show_package: bool,
    ) -> None:
        """列出工具 - 委托给 ToolFinder."""
        self._tool_finder.list_tools(category, search, limit, show_package)

    def _find_tool_info(self, url: str):
        """查找工具信息 - 委托给 ToolFinder."""
        return self._tool_finder.find_tool_info(url)

    def _deploy_tool(self, tool_info, config: TestConfig):
        """部署工具 - 委托给 STDIO 处理器."""
        return self._stdio_handler.deploy_tool(tool_info, config)

    def _run_tests(self, tool_info, server_info, config: TestConfig):
        """执行测试 - 委托给 TestRunner."""
        return self._test_runner.run_tests(tool_info, server_info, config)

    def _evaluate_tool_safe(
        self,
        tool_info,
        server_info: Any,
        test_results: list,
        success: bool,
        config: TestConfig,
    ):
        """安全评估工具 - 统一评估入口."""
        if not config.evaluate:
            return None
        rprint("[blue]🔍 正在评估工具...[/blue]")
        if tool_info.github_url:
            return self._stdio_handler.evaluate_github_repo(tool_info, config)
        if tool_info.deployment_method == "http":
            return self._stdio_handler.evaluate_http_endpoint(
                tool_info, test_results, server_info, success, config
            )
        return None

    def _handle_test_outputs(
        self,
        tool_info,
        server_info: Any,
        success: bool,
        test_results: list,
        config: TestConfig,
        evaluation_result: dict | None,
        input_str: str,
    ) -> dict[str, str]:
        """处理测试输出."""
        report_files = {}
        if config.save_report:
            report_files = self._stdio_handler.save_report(
                input_str,
                tool_info,
                server_info,
                success,
                test_results,
                getattr(server_info, "start_time", time.time()),
                evaluation_result,
            )
        if hasattr(self, "_display_concise_summary"):
            self._display_concise_summary(report_files.get("json"))
        if config.db_export:
            self._exporter.export_to_database(
                report_files.get("concise") or report_files.get("json"),
                evaluation_result=evaluation_result,
            )
        return report_files


# 全局处理器实例
_handler = None


def get_cli_handler() -> CLIHandler:
    """获取全局CLI处理器实例."""
    global _handler
    if _handler is None:
        _handler = CLIHandler()
    return _handler
