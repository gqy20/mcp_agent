#!/usr/bin/env python3
"""MCP CLI 命令处理器 - 简洁版.

遵循 Linus 的"好品味"原则：
- 每个命令处理器只做一件事
- 消除深度嵌套
- 统一的错误处理模式

作者: AI Assistant (Linus重构版)
日期: 2025-08-18
版本: 0.1.0 (简洁版)
"""

import asyncio
import time
import traceback
from typing import Any

from rich import print as rprint

from src.batch_mcp.core.database_exporter import get_database_exporter
from src.batch_mcp.core.evaluator import (
    evaluate_full_repository_with_comprehensive_score,
    evaluate_http_mcp_endpoint,
)
from src.batch_mcp.core.http_mcp_client import HttpMCPClient
from src.batch_mcp.core.http_mcp_handler import get_http_mcp_handler
from src.batch_mcp.core.input_type_detector import (
    get_input_type_detector,
)
from src.batch_mcp.core.report_generator import TestResult, generate_test_report
from src.batch_mcp.core.result_presenter import get_result_presenter
from src.batch_mcp.core.test_runner import get_test_runner
from src.batch_mcp.core.tester import TestConfig, get_mcp_tester
from src.batch_mcp.core.tool_finder import get_tool_finder
from src.batch_mcp.utils.csv_parser import MCPToolInfo, get_mcp_parser

try:
    from supabase import create_client

    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    create_client = None  # type: ignore[assignment]

try:
    from .config import get_config

    CONFIG_AVAILABLE = True
    config = get_config() if CONFIG_AVAILABLE else None
except ImportError:
    CONFIG_AVAILABLE = False
    config = None


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

    def evaluate_tools(self, db_export: bool) -> None:
        """评估所有工具 - 包含综合评分."""
        try:
            parser = get_mcp_parser()
            tools = parser.get_all_tools()
            if not tools:
                rprint("[red]❌ 没有找到可评估的工具。[/red]")
                return

            # 创建Supabase客户端供评估使用
            supabase_client = None
            if db_export and CONFIG_AVAILABLE and config.database.has_supabase_config:
                try:
                    if SUPABASE_AVAILABLE and create_client is not None:
                        supabase_client = create_client(
                            config.database.supabase_url,
                            config.database.supabase_service_role_key,
                        )
                except Exception as e:  # noqa: BLE001
                    rprint(f"[yellow]⚠️ Supabase客户端创建失败: {e}[/yellow]")

            for tool in tools:
                if not tool.github_url:
                    continue

                rprint(f"[blue]🔍 正在评估: {tool.name}[/blue]")
                evaluation_result = evaluate_full_repository_with_comprehensive_score(
                    tool.github_url,
                    supabase_client,
                )

                if evaluation_result["status"] == "success":
                    final_score = evaluation_result["final_score"]
                    comprehensive_score = evaluation_result.get(
                        "final_comprehensive_score",
                        final_score,
                    )
                    rprint(
                        f"[green]✅ 评估完成: {tool.name} - "
                        f"GitHub评分: {final_score}/100, "
                        f"综合评分: {comprehensive_score}/100[/green]",
                    )
                    if db_export:
                        self._exporter.export_evaluation_to_database(
                            tool.github_url,
                            evaluation_result,
                        )
                else:
                    rprint(
                        f"[red]❌ 评估失败: {tool.name} - "
                        f"{evaluation_result['message']}[/red]",
                    )

        except Exception as e:  # noqa: BLE001
            rprint(f"[red]❌ 评估过程发生错误: {e}[/red]")

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

            # 3.5. 评估工具
            evaluation_result = None
            if config.evaluate:
                rprint("[blue]🔍 正在评估工具...[/blue]")

                # 根据工具类型选择评估方法
                if tool_info.github_url:
                    # GitHub 仓库评估
                    supabase_client = None
                    if (
                        config.db_export
                        and CONFIG_AVAILABLE
                        and hasattr(config, "database")
                        and config.database
                        and hasattr(config.database, "has_supabase_config")
                        and config.database.has_supabase_config
                    ):
                        try:
                            if SUPABASE_AVAILABLE and create_client is not None:
                                supabase_client = create_client(
                                    config.database.supabase_url,
                                    config.database.supabase_service_role_key,
                                )
                        except Exception:  # noqa: BLE001
                            pass

                    evaluation_result = (
                        evaluate_full_repository_with_comprehensive_score(
                            tool_info.github_url,
                            supabase_client,
                        )
                    )
                    if (
                        evaluation_result
                        and evaluation_result.get("status") == "success"
                    ):
                        self._presenter.display_evaluation_result(evaluation_result)

                elif tool_info.deployment_method == "http":
                    # HTTP MCP 端点评估
                    # 计算测试结果统计
                    basic_tests = test_results or []
                    tools_count = server_info.available_tools if server_info else 0

                    # 确保tools_count是数值类型
                    if isinstance(tools_count, list):
                        tools_count = len(tools_count)
                    elif not isinstance(tools_count, (int, float)):
                        tools_count = 0

                    avg_response_time = (
                        sum(t.duration for t in basic_tests) / len(basic_tests)
                        if basic_tests
                        else 0.0
                    )

                    evaluation_result = evaluate_http_mcp_endpoint(
                        test_results={
                            "deployment_success": True,  # HTTP部署总是成功
                            "communication_success": success,  # 通信成功率
                            "test_results": _convert_test_results_to_dict(basic_tests),
                        },
                        tools_count=tools_count,
                        response_time=avg_response_time,
                        tool_info={"name": tool_info.name, "url": tool_info.url},
                    )
                    if (
                        evaluation_result
                        and evaluation_result.get("status") == "success"
                    ):
                        self._presenter.display_http_evaluation_result(
                            evaluation_result
                        )

            # 4. 生成报告
            report_files = {}
            if config.save_report:
                report_files = self._save_report(
                    input_str,
                    tool_info,
                    server_info,
                    success,
                    test_results,
                    getattr(server_info, "start_time", time.time()),
                    evaluation_result,
                )

            # 4.25. 显示精简摘要
            if hasattr(self, "_display_concise_summary"):
                self._display_concise_summary(report_files.get("json"))

            # 4.5. 数据库导出 - 使用精简版本
            if config.db_export:
                concise_report = report_files.get("concise") or report_files.get("json")
                self._exporter.export_to_database(
                    concise_report,
                    evaluation_result=evaluation_result,
                )

            # 5. 清理资源
            if config.cleanup:
                self._cleanup_server(server_info.server_id)

            return success

        except Exception as e:  # noqa: BLE001
            rprint(f"[red]❌ 测试过程发生错误: {e}[/red]")
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

            # 评估工具
            evaluation_result = None
            if config.evaluate and tool_info:
                rprint("[blue]🔍 正在评估工具...[/blue]")

                # 根据工具类型选择评估方法
                if tool_info.github_url:
                    # GitHub 仓库评估
                    supabase_client = None
                    if (
                        config.db_export
                        and CONFIG_AVAILABLE
                        and hasattr(config, "database")
                        and config.database
                        and hasattr(config.database, "has_supabase_config")
                        and config.database.has_supabase_config
                    ):
                        try:
                            if SUPABASE_AVAILABLE and create_client is not None:
                                supabase_client = create_client(
                                    config.database.supabase_url,
                                    config.database.supabase_service_role_key,
                                )
                        except Exception:  # noqa: BLE001
                            pass

                    evaluation_result = (
                        evaluate_full_repository_with_comprehensive_score(
                            tool_info.github_url,
                            supabase_client,
                        )
                    )
                    if (
                        evaluation_result
                        and evaluation_result.get("status") == "success"
                    ):
                        self._presenter.display_evaluation_result(evaluation_result)

                elif tool_info.deployment_method == "http":
                    # HTTP MCP 端点评估
                    # 计算测试结果统计
                    basic_tests = test_results or []
                    tools_count = server_info.available_tools if server_info else 0

                    # 确保tools_count是数值类型
                    if isinstance(tools_count, list):
                        tools_count = len(tools_count)
                    elif not isinstance(tools_count, (int, float)):
                        tools_count = 0

                    avg_response_time = (
                        sum(t.duration for t in basic_tests) / len(basic_tests)
                        if basic_tests
                        else 0.0
                    )

                    evaluation_result = evaluate_http_mcp_endpoint(
                        test_results={
                            "deployment_success": True,  # HTTP部署总是成功
                            "communication_success": success,  # 通信成功率
                            "test_results": _convert_test_results_to_dict(basic_tests),
                        },
                        tools_count=tools_count,
                        response_time=avg_response_time,
                        tool_info={"name": tool_info.name, "url": tool_info.url},
                    )
                    if (
                        evaluation_result
                        and evaluation_result.get("status") == "success"
                    ):
                        self._presenter.display_http_evaluation_result(
                            evaluation_result
                        )

            # 生成报告（如果需要）
            report_files = {}
            if config.save_report:
                report_files = self._save_report(
                    package,
                    tool_info,
                    server_info,
                    success,
                    test_results,
                    getattr(server_info, "start_time", time.time()),
                    evaluation_result,
                )

            # 数据库导出
            if config.db_export:
                self._exporter.export_to_database(
                    report_files.get("json"),
                    evaluation_result=evaluation_result,
                )

            # 清理
            if config.cleanup:
                self._cleanup_server(server_info.server_id)

            return success

        except Exception as e:  # noqa: BLE001
            rprint(f"[red]❌ 测试过程发生错误: {e}[/red]")
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
            return asyncio.run(
                self._run_http_tests_direct(tool_info, http_config, config)
            )

        except Exception as e:  # noqa: BLE001
            rprint(f"[red]❌ HTTP MCP 测试失败: {e}[/red]")
            if config.verbose:
                rprint(f"[red]{traceback.format_exc()}[/red]")
            return False

    async def _run_http_tests_direct(
        self,
        tool_info: MCPToolInfo | None,
        http_config: dict[str, Any],
        config: TestConfig,
    ) -> bool:
        """运行 HTTP MCP 测试的专用方法 - 委托给 HTTPMCPHandler."""
        try:
            # 创建 HTTP MCP 客户端
            client = HttpMCPClient(
                url=http_config["url"],
                headers=http_config["headers"],
                timeout=http_config["timeout"],
            )

            # 创建 server_info 对象来包装 client
            server_info = type("ServerInfo", (), {"client": client})()

            # 运行基础测试
            success, test_results = await self._http_handler._run_http_tests(
                tool_info, server_info, config
            )

            # 获取工具列表 - 用于智能测试和评估
            tools_result = await client.list_tools()
            tools_list = tools_result.get("tools", [])
            tools_count = len(tools_list)

            # 如果启用智能测试，运行 AI 测试
            if config.smart_test and success:
                rprint("[blue]🤖 开始 AI 智能测试...[/blue]")

                smart_results = await self._http_handler.run_http_smart_tests(
                    client, tools_list, config
                )

                # 将智能测试结果转换为 TestResult 对象并添加到 basic_tests 中
                for smart_result in smart_results:
                    # 确保 smart_result 是字典类型，防止意外类型混入
                    if not isinstance(smart_result, dict):
                        rprint(
                            f"[yellow]⚠️ 跳过无效的智能测试结果: {type(smart_result)}[/yellow]"
                        )
                        continue

                    smart_test_result = TestResult(
                        test_name=f"AI智能测试: {smart_result.get('tool_name', 'unknown')}",
                        success=smart_result.get("success", False),
                        duration=0.0,  # 智能测试暂不计算耗时
                        test_category="AI智能测试",
                        parameters={"smart_test": True},
                        tool_name=smart_result.get("tool_name"),
                        actual_response=smart_result.get("result"),
                        error_message=smart_result.get("error"),
                        ai_analysis=f"AI智能测试 {smart_result.get('tool_name', 'unknown')} {'成功' if smart_result.get('success') else '失败'}",
                        ai_confidence=0.8 if smart_result.get("success") else 0.2,
                    )
                    # 将智能测试结果添加到 basic_tests 中
                    test_results["basic_tests"].append(smart_test_result)

                # 计算智能测试成功率
                if smart_results:
                    smart_success = all(
                        result.get("success", False) for result in smart_results
                    )
                    success = success and smart_success
                else:
                    smart_success = False

            # 评估和报告生成逻辑保持不变
            evaluation_result = None
            if config.evaluate:
                rprint("[blue]🔍 正在评估HTTP MCP端点...[/blue]")

                # 计算平均响应时间
                basic_tests = test_results.get("basic_tests", [])
                total_duration = sum(
                    getattr(test, "duration", 0) for test in basic_tests
                )
                avg_response_time = (
                    total_duration / len(basic_tests) if basic_tests else 0
                )

                # 将 TestResult 对象转换为字典用于评估
                evaluation_test_results = {
                    "deployment_success": True,
                    "communication_success": success,
                    "test_results": [
                        {
                            "test_name": getattr(test, "test_name", ""),
                            "success": getattr(test, "success", False),
                            "duration": getattr(test, "duration", 0),
                            "test_category": getattr(test, "test_category", ""),
                            "ai_confidence": self._safe_ai_confidence(
                                getattr(test, "ai_confidence", 0.0)
                            ),
                        }
                        for test in basic_tests
                    ],
                }

                # 调用 HTTP MCP 评估
                evaluation_result = evaluate_http_mcp_endpoint(
                    test_results=evaluation_test_results,
                    tools_count=tools_count,
                    response_time=avg_response_time,
                    tool_info=tool_info.__dict__ if tool_info else None,
                )

                # 显示评估结果
                self._display_http_evaluation_result(evaluation_result)

            # 生成报告
            report_files = {}
            if config.save_report:
                # 直接传递 TestResult 对象列表，保持数据格式统一
                basic_tests_list = test_results.get("basic_tests", [])

                report_files = generate_test_report(
                    url=http_config["url"],
                    tool_info=tool_info,
                    server_info=client,
                    test_success=success,
                    duration=0.0,  # 这里可以计算实际持续时间
                    test_results=basic_tests_list,
                    evaluation_result=evaluation_result,
                )

            # 数据库导出
            if config.db_export and success:
                json_report = report_files.get("json")
                if json_report:
                    self._exporter.export_to_database(
                        json_report,
                        evaluation_result=evaluation_result,
                    )

            return success

        except Exception as e:  # noqa: BLE001
            rprint(f"[red]❌ HTTP 测试执行失败: {e}[/red]")
            if config.verbose:
                rprint(f"[red]{traceback.format_exc()}[/red]")
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

    def _find_tool_info(self, url: str) -> MCPToolInfo | None:
        """查找工具信息 - 委托给 ToolFinder."""
        return self._tool_finder.find_tool_info(url)

    def _deploy_tool(self, tool_info: MCPToolInfo, config: TestConfig):
        """部署工具 - 单一职责."""
        # 检查是否为 HTTP MCP 端点
        if getattr(tool_info, "deployment_method", None) == "http":
            return self._deploy_http_mcp(tool_info, config)

        # 尝试从run_command中提取包名（如果package_name为空）
        package_name = tool_info.package_name
        run_command = getattr(tool_info, "run_command", None)

        if not package_name and run_command:
            # 从run_command中提取包名
            cmd_parts = run_command.split()
            if len(cmd_parts) >= 2:
                # 对于 "uvx excel-mcp-server stdio" 这样的命令，包名是第二个部分
                package_name = cmd_parts[1]
                rprint(f"[blue]📋 从运行命令中提取包名: {package_name}[/blue]")

        if not package_name:
            rprint("[red]❌ 该工具缺少包名信息且无法从运行命令中提取，无法部署[/red]")
            return None

        if tool_info.requires_api_key:
            rprint(
                f"[yellow]🔑 该工具需要API密钥: {', '.join(tool_info.api_requirements)}[/yellow]",
            )
            rprint("[yellow]⚠️ 请确保已在.env文件中配置相应的API密钥[/yellow]")

        rprint("[blue]🚀 正在部署MCP工具...[/blue]")
        # 传递run_command给deploy_tool方法
        server_info = self.tester.deploy_tool(package_name, config.timeout, run_command)

        if not server_info:
            rprint("[red]❌ MCP工具部署失败[/red]")
            return None

        self._presenter.display_deployment_success(server_info)
        return server_info

    def _run_tests(
        self,
        tool_info: MCPToolInfo | None,
        server_info,
        config: TestConfig,
    ):
        """执行测试 - 委托给 TestRunner."""
        return self._test_runner.run_tests(tool_info, server_info, config)

    def _save_report(
        self,
        url: str,
        tool_info: MCPToolInfo,
        server_info,
        success: bool,
        test_results,
        start_time,
        evaluation_result: dict | None = None,
    ):
        """保存报告 - 单一职责."""
        try:
            rprint("[blue]📊 生成测试报告...[/blue]")

            # 🔧 修复评分字段同步问题
            # 将 evaluation_result 中的评分信息同步到 tool_info
            if evaluation_result and evaluation_result.get("status") == "success":
                # 同步综合评分
                if "final_comprehensive_score" in evaluation_result:
                    tool_info.final_score = evaluation_result[
                        "final_comprehensive_score"
                    ]
                elif "final_score" in evaluation_result:
                    tool_info.final_score = evaluation_result["final_score"]

                # 同步可持续性评分
                if "sustainability" in evaluation_result:
                    tool_info.sustainability_score = evaluation_result[
                        "sustainability"
                    ].get("total_score")

                # 同步人气评分
                if "popularity" in evaluation_result:
                    tool_info.popularity_score = evaluation_result["popularity"].get(
                        "total_score",
                    )

                rprint("[dim]✅ 评分信息已同步到 tool_info[/dim]")

            report_files = generate_test_report(
                url=url,
                tool_info=tool_info,
                server_info=server_info,
                test_success=success,
                duration=time.time() - start_time,
                test_results=test_results,
                evaluation_result=evaluation_result,
                formats=["json", "html"],
            )

            for format_name, file_path in report_files.items():
                rprint(
                    f"[green]✅ {format_name.upper()} 报告已保存: {file_path}[/green]",
                )

            return report_files

        except Exception as e:  # noqa: BLE001
            rprint(f"[red]❌ 报告生成失败: {e}[/red]")
            return {}

    def _cleanup_server(self, server_id: str) -> None:
        """清理服务器 - 单一职责."""
        try:
            rprint("[yellow]🧹 清理测试环境...[/yellow]")
            self.tester.cleanup_server(server_id)
            rprint("[green]✅ 清理完成[/green]")
        except Exception as e:  # noqa: BLE001
            rprint(f"[yellow]⚠️ 清理异常: {e}[/yellow]")

    def _safe_ai_confidence(self, confidence: Any) -> float:
        """安全处理ai_confidence值，确保返回数值类型."""
        if isinstance(confidence, (int, float)):
            return float(confidence)
        if isinstance(confidence, list):
            # 如果是列表，计算平均值
            numeric_values = [c for c in confidence if isinstance(c, (int, float))]
            if numeric_values:
                return sum(numeric_values) / len(numeric_values)
            return 0.0
        if confidence is None:
            return 0.0
        # 其他类型转换为0.0
        return 0.0

    def _deploy_http_mcp(self, tool_info: MCPToolInfo, config: TestConfig) -> Any:
        """部署 HTTP MCP 端点 - 委托给 HTTPMCPHandler."""
        return self._http_handler.deploy_http_mcp(tool_info, config)

    def _is_http_client(self, server_info: Any) -> bool:
        """检测是否为 HTTP MCP 客户端."""
        try:
            # 检查是否为HTTP部署的server_info对象
            if hasattr(server_info, "client"):
                return isinstance(server_info.client, HttpMCPClient)

            # 直接检查是否为HTTP客户端（兼容性）
            return isinstance(server_info, HttpMCPClient)
        except Exception:  # noqa: BLE001
            return False


# 全局处理器实例
_handler = CLIHandler()


def _convert_test_results_to_dict(test_results: list) -> list[dict]:
    """将TestResult对象列表转换为字典格式，供HTTP评估使用."""
    test_results_dict = []
    for t in test_results:
        if hasattr(t, "success"):
            # 使用to_concise_dict方法获取基本信息
            test_dict = t.to_concise_dict() if hasattr(t, "to_concise_dict") else {}
            # 确保包含必要的字段，包括ai_confidence
            test_dict.update(
                {
                    "test_name": getattr(t, "test_name", "Unknown Test"),
                    "success": getattr(t, "success", False),
                    "duration": getattr(t, "duration", 0.0),
                    "error_message": getattr(t, "error_message", None),
                    "test_category": getattr(t, "test_category", "未知"),
                    "ai_confidence": getattr(
                        t, "ai_confidence", 0.0
                    ),  # 关键修复：包含ai_confidence字段
                }
            )

            # 处理异常类型的ai_confidence值
            ai_confidence = test_dict["ai_confidence"]
            if isinstance(ai_confidence, list):
                # 如果是列表，计算平均值
                numeric_values = [
                    c for c in ai_confidence if isinstance(c, (int, float))
                ]
                if numeric_values:
                    test_dict["ai_confidence"] = sum(numeric_values) / len(
                        numeric_values
                    )
                else:
                    test_dict["ai_confidence"] = 0.0
            elif ai_confidence is None:
                # 如果是None，转换为0.0
                test_dict["ai_confidence"] = 0.0
            elif not isinstance(ai_confidence, (int, float)):
                # 如果是其他类型，转换为0.0
                test_dict["ai_confidence"] = 0.0
            else:
                # 确保是数值类型
                test_dict["ai_confidence"] = float(ai_confidence)

            test_results_dict.append(test_dict)
    return test_results_dict


def get_cli_handler() -> CLIHandler:
    """获取全局CLI处理器实例."""
    return _handler
