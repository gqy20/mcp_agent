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
import json
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from rich import print as rprint

from src.batch_mcp.core.evaluator import (
    evaluate_full_repository_with_comprehensive_score,
)
from src.batch_mcp.core.input_type_detector import (
    InputType,
    get_input_type_detector,
)
from src.batch_mcp.core.report_generator import generate_test_report
from src.batch_mcp.core.tester import TestConfig, get_mcp_tester
from src.batch_mcp.core.tool_finder import get_tool_finder
from src.batch_mcp.utils.csv_parser import MCPToolInfo, get_mcp_parser
from src.batch_mcp.utils.test_params_generator import get_test_params_generator

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
        self._input_detector = get_input_type_detector()
        self._tool_finder = get_tool_finder()

    def _display_input_type_detection(
        self, input_str: str, input_type: InputType
    ) -> None:
        """显示输入类型检测结果"""
        type_descriptions = {
            InputType.HTTP_ENDPOINT: "HTTP MCP端点",
            InputType.GITHUB_URL: "GitHub仓库",
            InputType.PACKAGE_NAME: "MCP包名",
            InputType.SEARCH_QUERY: "搜索查询",
            InputType.UNKNOWN: "未知格式",
        }

        type_icons = {
            InputType.HTTP_ENDPOINT: "🌐",
            InputType.GITHUB_URL: "📦",
            InputType.PACKAGE_NAME: "📋",
            InputType.SEARCH_QUERY: "🔍",
            InputType.UNKNOWN: "❓",
        }

        description = type_descriptions.get(input_type, "未知格式")
        icon = type_icons.get(input_type, "❓")

        rprint(f"[blue]{icon} 检测到{description}: {input_str}[/blue]")

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
                    from supabase import create_client

                    supabase_client = create_client(
                        config.database.supabase_url,
                        config.database.supabase_service_role_key,
                    )
                except ImportError:
                    rprint("[yellow]⚠️ Supabase库未安装，跳过数据库导出[/yellow]")
                except Exception as e:
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
                        self._export_evaluation_to_database(
                            tool.github_url,
                            evaluation_result,
                        )
                else:
                    rprint(
                        f"[red]❌ 评估失败: {tool.name} - "
                        f"{evaluation_result['message']}[/red]",
                    )

        except Exception as e:
            rprint(f"[red]❌ 评估过程发生错误: {e}[/red]")

    def _export_evaluation_to_database(
        self,
        github_url: str,
        evaluation_result: dict[str, Any],
    ) -> None:
        """导出评估结果到数据库 - 包含综合评分."""
        if not CONFIG_AVAILABLE or not config.database.has_supabase_config:
            rprint("[yellow]⚠️ 数据库配置未设置，跳过数据库导出[/yellow]")
            return

        try:
            from supabase import create_client

            client = create_client(
                config.database.supabase_url,
                config.database.supabase_service_role_key,
            )

            # 获取综合评分数据
            test_success_info = evaluation_result.get("test_success_rate", {})
            comprehensive_info = evaluation_result.get("comprehensive_scoring", {})

            record = {
                "github_url": github_url,
                "final_score": evaluation_result["final_score"],
                "sustainability_score": evaluation_result["sustainability"][
                    "total_score"
                ],
                "popularity_score": evaluation_result["popularity"]["total_score"],
                "sustainability_details": evaluation_result["sustainability"][
                    "details"
                ],
                "popularity_details": evaluation_result["popularity"]["details"],
                "last_evaluated_at": datetime.now(UTC).isoformat(),
                # 新增字段
                "success_rate": test_success_info.get("success_rate"),
                "test_count": test_success_info.get("test_count", 0),
                "total_score": comprehensive_info.get("total_score"),
                "last_calculated_at": datetime.now(UTC).isoformat(),
            }

            client.table("mcp_repository_evaluations").upsert(record).execute()
            rprint(f"[green]✅ 成功导出评估结果到数据库: {github_url}[/green]")

        except ImportError:
            rprint("[yellow]⚠️ Supabase库未安装，跳过数据库导出[/yellow]")
        except Exception as e:
            rprint(f"[yellow]⚠️ 数据库导出异常: {e}[/yellow]")

    def test_url(self, input_str: str, config: TestConfig) -> bool:
        """统一的智能测试入口 - 支持自动识别输入类型

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
            self._display_input_type_detection(input_str, input_type)

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
                            from supabase import create_client

                            supabase_client = create_client(
                                config.database.supabase_url,
                                config.database.supabase_service_role_key,
                            )
                        except Exception:
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
                        self._display_evaluation_result(evaluation_result)

                elif tool_info.deployment_method == "http":
                    # HTTP MCP 端点评估
                    from .evaluator import evaluate_http_mcp_endpoint

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
                        self._display_http_evaluation_result(evaluation_result)

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

            # 4.5. 数据库导出 (可选) - 使用精简版本
            if config.db_export:
                concise_report = report_files.get("concise") or report_files.get("json")
                self._export_to_database(
                    concise_report,
                    evaluation_result=evaluation_result,
                )

            # 5. 清理资源
            if config.cleanup:
                self._cleanup_server(server_info.server_id)

            return success

        except Exception as e:
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

            self._display_deployment_success(server_info, package)

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
                            from supabase import create_client

                            supabase_client = create_client(
                                config.database.supabase_url,
                                config.database.supabase_service_role_key,
                            )
                        except Exception:
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
                        self._display_evaluation_result(evaluation_result)

                elif tool_info.deployment_method == "http":
                    # HTTP MCP 端点评估
                    from .evaluator import evaluate_http_mcp_endpoint

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
                        self._display_http_evaluation_result(evaluation_result)

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

            # 数据库导出 (如果需要)
            if config.db_export:
                self._export_to_database(
                    report_files.get("json"),
                    evaluation_result=evaluation_result,
                )

            # 清理
            if config.cleanup:
                self._cleanup_server(server_info.server_id)

            return success

        except Exception as e:
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

        except Exception as e:
            rprint(f"[red]❌ HTTP MCP 测试失败: {e}[/red]")
            if config.verbose:
                import traceback

                rprint(f"[red]{traceback.format_exc()}[/red]")
            return False

    async def _run_http_tests_direct(
        self,
        tool_info: MCPToolInfo | None,
        http_config: dict[str, Any],
        config: TestConfig,
    ) -> bool:
        """运行 HTTP MCP 测试的专用方法."""
        try:
            from .http_mcp_client import HttpMCPClient

            # 创建 HTTP MCP 客户端
            client = HttpMCPClient(
                url=http_config["url"],
                headers=http_config["headers"],
                timeout=http_config["timeout"],
            )

            # 创建server_info对象来包装client
            server_info = type("ServerInfo", (), {"client": client})()

            # 运行基础测试
            success, test_results = await self._run_http_tests(
                tool_info, server_info, config
            )

            # 获取工具列表 (用于智能测试和评估)
            tools_result = await client.list_tools()
            tools_list = tools_result.get("tools", [])
            tools_count = len(tools_list)

            # 如果启用智能测试，运行AI测试
            if config.smart_test and success:
                rprint("[blue]🤖 开始 AI 智能测试...[/blue]")

                smart_results = await self._run_http_smart_tests(
                    client, tools_list, config
                )

                # 将智能测试结果转换为TestResult对象并添加到basic_tests中
                from .report_generator import TestResult

                for smart_result in smart_results:
                    # 确保smart_result是字典类型，防止意外类型混入
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
                    # 将智能测试结果添加到basic_tests中
                    test_results["basic_tests"].append(smart_test_result)

                # 计算智能测试成功率
                if smart_results:
                    smart_success = all(
                        result.get("success", False) for result in smart_results
                    )
                    success = success and smart_success
                else:
                    smart_success = False

            # 3.5. 评估HTTP MCP端点
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

                # 将TestResult对象转换为字典用于评估
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

                # 调用HTTP MCP评估
                from .evaluator import evaluate_http_mcp_endpoint

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
                from .report_generator import generate_test_report

                # 直接传递TestResult对象列表，保持数据格式统一
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
                    self._export_to_database(
                        json_report,
                        evaluation_result=evaluation_result,
                    )

            return success

        except Exception as e:
            rprint(f"[red]❌ HTTP 测试执行失败: {e}[/red]")
            if config.verbose:
                import traceback

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

        self._display_deployment_success(server_info)
        return server_info

    def _run_tests(
        self,
        tool_info: MCPToolInfo | None,
        server_info,
        config: TestConfig,
    ):
        """执行测试 - 支持无tool_info场景."""
        rprint("[yellow]🧪 执行基础连通性测试...[/yellow]")

        # 检查是否为 HTTP MCP 客户端
        if self._is_http_client(server_info):
            http_success, http_test_results = asyncio.run(
                self._run_http_tests(tool_info, server_info, config)
            )
            # 提取basic_tests列表以保持与其他测试路径的一致性
            basic_tests_list = http_test_results.get("basic_tests", [])
            return http_success, basic_tests_list

        if config.smart_test and tool_info:
            try:
                rprint("[blue]🤖 启用AI智能测试模式...[/blue]")
                return asyncio.run(
                    self.tester.run_smart_test(tool_info, server_info, config.verbose),
                )
            except ImportError:
                rprint("[yellow]⚠️ AgentScope不可用，使用基础测试模式[/yellow]")
        elif config.smart_test and not tool_info:
            rprint("[yellow]⚠️ 包测试暂不支持AI智能模式，使用基础测试[/yellow]")

        return self.tester.run_basic_test(server_info, config.timeout)

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

        except Exception as e:
            rprint(f"[red]❌ 报告生成失败: {e}[/red]")
            return {}

    def _get_tool_identifier(self, json_data: dict, tool_info: dict) -> str:
        """获取工具标识符，确保不为空.

        问题分析：
        1. 在to_concise_dict中，精简的tool_info不包含github_url字段
        2. 在数据库导出时，当tool_info存在但没有github_url时，返回空字符串
        3. 应该在这种情况下尝试从test_url或其他方式获取正确的tool_identifier

        解决方案：
        1. 如果tool_info存在且有github_url，直接使用
        2. 如果tool_info存在但没有github_url，尝试从CSV中查找完整工具信息
        3. 如果无法从CSV中找到，尝试从test_url推断GitHub URL
        4. 如果tool_info不存在，直接使用test_url
        """
        # 首先尝试从tool_info获取github_url
        if tool_info and isinstance(tool_info, dict):
            tool_identifier = tool_info.get("github_url", "")
            if tool_identifier:
                return tool_identifier

        # 如果tool_info中没有github_url，尝试从CSV中查找完整工具信息
        tool_identifier = self._tool_finder.lookup_github_url_from_csv(json_data)
        if tool_identifier:
            return tool_identifier

        # 如果无法从CSV中找到，尝试从test_url推断
        test_url = json_data.get("test_url", "")
        tool_identifier = self._tool_finder.infer_github_url_from_test_url(test_url)
        if tool_identifier:
            return tool_identifier

        # 如果无法推断，回退到test_url
        return test_url

    def _export_to_database(
        self,
        json_report_path: str,
        evaluation_result: dict | None = None,
    ) -> None:
        """导出到数据库 - 使用精简版数据."""
        if not json_report_path:
            rprint("[yellow]⚠️ 没有JSON报告，跳过数据库导出[/yellow]")
            return

        try:
            rprint("[blue]🗄️ 导出精简版结果到数据库...[/blue]")

            if not CONFIG_AVAILABLE or not config.database.has_supabase_config:
                rprint(
                    "[yellow]⚠️ 数据库配置未设置 (SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)，跳过数据库导出[/yellow]",
                )
                return

            from datetime import datetime

            from supabase import create_client

            client = create_client(
                config.database.supabase_url,
                config.database.supabase_service_role_key,
            )

            # 检查是否为精简版报告，如果不是则尝试加载精简版
            with open(json_report_path, encoding="utf-8") as f:
                json_data = json.load(f)

            # 如果是完整版报告，尝试查找对应的精简版
            if "actual_response" in str(json_data):  # 简单判断是否为完整版
                concise_path = json_report_path.replace(".json", "_concise.json")
                if Path(concise_path).exists():
                    rprint("[blue]📄 发现精简版报告，使用精简数据导出[/blue]")
                    with open(concise_path, encoding="utf-8") as f:
                        json_data = json.load(f)
                else:
                    rprint("[yellow]⚠️ 未找到精简版报告，使用完整数据导出[/yellow]")

            deployment_ok = json_data.get("deployment_success", False)
            communication_ok = json_data.get("communication_success", False)
            test_results = json_data.get("test_results", [])

            if test_results:
                passed_tests = sum(
                    1 for test in test_results if test.get("success", False)
                )
                success_rate = (passed_tests / len(test_results)) * 100
                tests_successful = success_rate >= 50.0
            else:
                tests_successful = False

            overall_success = deployment_ok and communication_ok and tests_successful

            # 获取工具信息（如果存在）
            tool_info = json_data.get("tool_info", {})

            # 修复tool_identifier计算逻辑，确保不为空
            tool_identifier = self._get_tool_identifier(json_data, tool_info)

            record = {
                "test_timestamp": datetime.now().isoformat(),
                "tool_identifier": tool_identifier,
                "tool_name": (
                    tool_info.get("name", "Unknown")
                    if tool_info
                    else json_data.get("tool_name", "Unknown")
                ),
                "tool_author": tool_info.get("author", "") if tool_info else "",
                "tool_category": tool_info.get("category", "") if tool_info else "",
                "test_success": overall_success,
                "deployment_success": json_data.get("deployment_success", False),
                "communication_success": json_data.get("communication_success", False),
                "available_tools_count": json_data.get("available_tools_count", 0),
                "test_duration_seconds": json_data.get("test_duration_seconds", 0),
                "error_messages": json_data.get("error_messages", []),
                "test_details": json_data.get("test_results", []),
                "environment_info": {
                    "platform": json_data.get("platform_info", "Unknown"),
                },
            }

            # 添加LobeHub评分信息（如果工具信息中有）
            if tool_info:
                record.update(
                    {
                        "lobehub_url": tool_info.get("lobehub_url"),
                        "lobehub_evaluate": tool_info.get("lobehub_evaluate"),
                        "lobehub_score": tool_info.get("lobehub_score"),
                        "lobehub_star_count": tool_info.get("lobehub_star_count"),
                        "lobehub_fork_count": tool_info.get("lobehub_fork_count"),
                    },
                )

            if evaluation_result and evaluation_result.get("status") == "success":
                record["final_score"] = int(evaluation_result["final_score"])
                record["sustainability_score"] = int(
                    evaluation_result["sustainability"]["total_score"]
                )
                record["popularity_score"] = int(
                    evaluation_result["popularity"]["total_score"]
                )
                record["sustainability_details"] = evaluation_result["sustainability"][
                    "details"
                ]
                record["popularity_details"] = evaluation_result["popularity"][
                    "details"
                ]
                record["evaluation_timestamp"] = datetime.now().isoformat()

                # 使用当前测试的成功率计算综合评分
                if evaluation_result and evaluation_result.get("status") == "success":
                    evaluator_score = evaluation_result.get("final_score", 93)

                    # 使用当前测试的成功率，而不是历史数据
                    current_success_rate = success_rate  # 当前测试的成功率
                    current_test_count = len(test_results)  # 当前测试的数量
                    current_passed_tests = passed_tests  # 当前测试的通过数

                    # 计算综合评分 (当前测试成功率 + GitHub评估器评分)
                    comprehensive_score = int(
                        (current_success_rate * 1 + evaluator_score * 2) / 3,
                    )

                    record["comprehensive_score"] = comprehensive_score
                    record["calculation_method"] = "current_test_weighted"

                    rprint(
                        f"[cyan]💾 计算综合评分: (当前测试成功率{current_success_rate:.1f} × 1 + GitHub评估器评分{evaluator_score} × 2) ÷ 3 = {comprehensive_score}[/cyan]",
                    )
                    rprint(
                        f"[cyan]📊 当前测试: {current_passed_tests}/{current_test_count} = {current_success_rate:.1f}%[/cyan]",
                    )

                    # 插入完整记录（包含综合评分）
                    response = client.table("mcp_test_results").insert(record).execute()

                    if response.data:
                        record_id = response.data[0]["test_id"]
                        rprint(
                            f"[green]✅ 完整记录已保存到数据库: {record_id[:8]}...[/green]",
                        )
                        rprint(
                            f"[green]🎉 综合评分 {comprehensive_score} 已包含在记录中! (基于当前测试)[/green]",
                        )
                        return  # 成功，提前返回
                    rprint("[red]❌ 记录保存失败[/red]")
                else:
                    rprint("[yellow]⚠️ 评估结果不可用，跳过综合评分计算[/yellow]")

            rprint(f"[dim]Dumping to database: {record}[/dim]")
            response = client.table("mcp_test_results").insert(record).execute()

            if response.data:
                rprint(
                    "[green]✅ 数据库导出成功 - 记录已保存到 mcp_test_results 表[/green]",
                )
            else:
                rprint(
                    f"[red]❌ 数据库导出失败: {response.error.message if response.error else '未知错误'}[/red]",
                )

        except Exception as e:
            rprint(f"[red]❌ 数据库导出异常: {e}[/red]")
            rprint(
                "[dim]   检查 SUPABASE_URL 和 SUPABASE_SERVICE_ROLE_KEY 环境变量[/dim]",
            )

    def _cleanup_server(self, server_id: str) -> None:
        """清理服务器 - 单一职责."""
        try:
            rprint("[yellow]🧹 清理测试环境...[/yellow]")
            self.tester.cleanup_server(server_id)
            rprint("[green]✅ 清理完成[/green]")
        except Exception as e:
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

    def _display_evaluation_result(self, evaluation_result: dict) -> None:
        """显示评估结果 - 包含综合评分."""
        from rich.console import Console
        from rich.table import Table

        console = Console()
        table = Table(title="MCP 工具评估结果")

        table.add_column("类别", style="cyan", width=20)
        table.add_column("指标", style="magenta", width=25)
        table.add_column("分数", style="green", width=10)
        table.add_column("原因", style="white", width=50)

        sustainability = evaluation_result.get("sustainability", {})
        popularity = evaluation_result.get("popularity", {})
        test_success_info = evaluation_result.get("test_success_rate", {})
        evaluation_result.get("comprehensive_scoring", {})

        # 显示综合评分
        final_comprehensive_score = evaluation_result.get(
            "final_comprehensive_score",
            evaluation_result.get("final_score"),
        )
        table.add_row(
            "[bold red]综合评分[/bold red]",
            "",
            f"[bold red]{final_comprehensive_score}[/bold red]",
            "GitHub评估 + 测试成功率综合",
        )

        # 显示GitHub评估分数
        table.add_row(
            "GitHub评分",
            "",
            f"[bold]{evaluation_result.get('final_score')}[/bold]",
            "仓库可持续性和受欢迎程度",
        )

        # 显示测试成功率
        if test_success_info.get("success_rate") is not None:
            success_rate = test_success_info["success_rate"]
            test_count = test_success_info.get("test_count", 0)
            table.add_row(
                "测试成功率",
                "",
                f"[bold]{success_rate}%[/bold]",
                f"基于 {test_count} 次测试记录",
            )
        else:
            table.add_row("测试成功率", "", "[dim]暂无数据[/dim]", "无测试记录")

        table.add_section()
        table.add_row(
            "[bold]可持续性[/bold]",
            "",
            f"[bold]{sustainability.get('total_score')}[/bold]",
            "",
        )
        for metric, data in sustainability.get("details", {}).items():
            table.add_row("", metric, str(data.get("score")), data.get("reason"))

        table.add_section()
        table.add_row(
            "[bold]受欢迎程度[/bold]",
            "",
            f"[bold]{popularity.get('total_score')}[/bold]",
            "",
        )
        for metric, data in popularity.get("details", {}).items():
            table.add_row("", metric, str(data.get("score")), data.get("reason"))

        console.print(table)

    def _display_deployment_success(self, server_info, package_name=None) -> None:
        """显示部署成功信息 - 统一格式."""
        rprint(f"[green]✅ 部署成功！服务器ID: {server_info.server_id}[/green]")

        if package_name:
            rprint(f"[blue]📦 包名: {package_name}[/blue]")

        if server_info.available_tools:
            rprint(
                f"[green]🛠️ 可用工具 ({len(server_info.available_tools)} 个):[/green]",
            )
            for i, tool in enumerate(server_info.available_tools, 1):
                tool_name = tool.get("name", "unknown")
                tool_desc = tool.get("description", "无描述")
                rprint(f"  {i}. [cyan]{tool_name}[/cyan] - {tool_desc[:60]}...")

    def _deploy_http_mcp(self, tool_info: MCPToolInfo, config: TestConfig) -> Any:
        """部署 HTTP MCP 端点."""
        rprint("[blue]🚀 正在部署 HTTP MCP 端点...[/blue]")

        try:
            from .simple_mcp_deployer import SimpleMCPDeployer

            deployer = SimpleMCPDeployer()

            # 从 URL 重新解析配置
            _method, http_config = deployer.detect_deployment_method(tool_info.url)

            # 合并配置参数
            http_config["timeout"] = config.timeout

            # 部署 HTTP 客户端
            client = deployer.deploy_http_mcp(http_config)

            rprint("[green]✅ HTTP MCP 端点部署成功！[/green]")

            # 创建一个兼容的server_info对象
            from types import SimpleNamespace

            server_info = SimpleNamespace()
            server_info.server_id = f"http-mcp-{tool_info.name}"
            server_info.client = client
            server_info.available_tools = []  # 将在测试时填充

            return server_info

        except Exception as e:
            rprint(f"[red]❌ HTTP MCP 端点部署失败: {e}[/red]")
            return None

    def _is_http_client(self, server_info: Any) -> bool:
        """检测是否为 HTTP MCP 客户端."""
        try:
            # 检查是否为HTTP部署的server_info对象
            if hasattr(server_info, "client"):
                from .http_mcp_client import HttpMCPClient

                return isinstance(server_info.client, HttpMCPClient)

            # 直接检查是否为HTTP客户端（兼容性）
            from .http_mcp_client import HttpMCPClient

            return isinstance(server_info, HttpMCPClient)
        except ImportError:
            return False

    async def _run_http_tests(
        self, _tool_info: MCPToolInfo | None, server_info: Any, config: TestConfig
    ) -> tuple[bool, dict[str, Any]]:
        """运行 HTTP MCP 测试 - 与STDIO测试保持一致."""
        try:
            rprint("[blue]🔗 测试 HTTP MCP 连接...[/blue]")

            # 获取HTTP客户端
            client = (
                server_info.client if hasattr(server_info, "client") else server_info
            )

            # 1. 获取工具列表 - 类似STDIO的_test_mcp_communication
            tools_result = await client.list_tools()
            if not tools_result["success"]:
                rprint(
                    f"[red]❌ 获取工具列表失败: {tools_result.get('error', 'Unknown error')}[/red]"
                )
                return False, {}

            tools = tools_result.get("tools", [])
            rprint(f"[green]✅ 找到 {len(tools)} 个工具[/green]")

            # 更新server_info的available_tools
            if hasattr(server_info, "available_tools"):
                server_info.available_tools = tools

            # 显示工具列表
            if tools:
                rprint("[blue]🛠️ 可用工具:[/blue]")
                for i, tool in enumerate(tools, 1):
                    tool_name = tool.get("name", "Unknown")
                    tool_desc = tool.get("description", "No description")[:50]
                    rprint(f"  {i}. {tool_name} - {tool_desc}...")

            # 2. 创建真正的测试结果，复用TestResult结构
            import time

            from .report_generator import TestResult

            test_results = []

            # 添加MCP协议通信测试结果
            test_results.append(
                TestResult(
                    test_name="MCP协议通信测试",
                    success=True,
                    duration=0.0,
                    test_category="通信测试",
                    parameters={"method": "tools/list"},
                    tool_name=None,
                    ai_analysis=f"HTTP MCP通信成功，发现{len(tools)}个工具",
                    ai_confidence=1.0,
                )
            )

            # 3. 工具调用测试 - 类似STDIO的_test_first_tool
            if tools:
                first_tool = tools[0]
                tool_name = first_tool.get("name", "unknown")

                rprint(f"[blue]🧪 测试工具调用: {tool_name}[/blue]")

                start_time = time.time()

                # 复用STDIO的参数生成逻辑
                arguments = self._generate_test_arguments(first_tool)

                # 使用HTTP客户端的call_tool方法
                call_result = await client.call_tool(tool_name, arguments)
                duration = time.time() - start_time

                tool_test_success = call_result.get("success", False)

                test_results.append(
                    TestResult(
                        test_name=f"工具调用测试: {tool_name}",
                        success=tool_test_success,
                        duration=duration,
                        test_category="功能测试",
                        parameters=arguments,
                        tool_name=tool_name,
                        actual_response=call_result,
                        error_message=call_result.get("error")
                        if not tool_test_success
                        else None,
                        ai_analysis=f"工具 {tool_name} {'调用成功' if tool_test_success else '调用失败'}",
                        ai_confidence=0.9 if tool_test_success else 0.1,
                    )
                )

                if tool_test_success:
                    rprint(f"[green]✅ 工具 {tool_name} 调用成功[/green]")
                else:
                    rprint(
                        f"[yellow]⚠️ 工具 {tool_name} 调用失败: {call_result.get('error', 'Unknown error')}[/yellow]"
                    )

            rprint("[green]✅ HTTP MCP 基础测试完成！[/green]")

            # 返回与STDIO格式一致的结果
            return True, {
                "basic_tests": test_results,
                "connection": True,
                "tools_found": len(tools),
                "tools": tools,
            }

        except Exception as e:
            rprint(f"[red]❌ HTTP MCP 测试失败: {e}[/red]")
            return False, {"error": str(e)}

    def _generate_test_arguments(self, tool_info: dict) -> dict:
        """为工具生成基本测试参数 - 使用统一的参数生成器."""
        params_generator = get_test_params_generator()
        return params_generator.generate(tool_info)

    async def _run_http_smart_tests(
        self, client: Any, tools: list[dict[str, Any]], _config: TestConfig
    ) -> list[dict[str, Any]]:
        """运行 HTTP 智能测试."""
        smart_results = []

        for tool in tools[:3]:  # 限制测试前3个工具
            tool_name = tool.get("name")
            if not tool_name:
                continue

            try:
                rprint(f"[blue]🧪 测试工具: {tool_name}[/blue]")

                # 构造测试参数
                test_args = self._construct_test_args(tool)

                # 调用工具
                call_result = await client.call_tool(tool_name, test_args)

                test_success = call_result.get("success", False)
                smart_results.append(
                    {
                        "tool_name": tool_name,
                        "success": test_success,
                        "result": call_result.get("result"),
                        "error": call_result.get("error"),
                    }
                )

                if test_success:
                    rprint(f"[green]  ✅ {tool_name} 测试成功[/green]")
                else:
                    rprint(
                        f"[red]  ❌ {tool_name} 测试失败: {call_result.get('error')}[/red]"
                    )

            except Exception as e:
                smart_results.append(
                    {"tool_name": tool_name, "success": False, "error": str(e)}
                )
                rprint(f"[red]  ❌ {tool_name} 测试异常: {e}[/red]")

        return smart_results

    def _construct_test_args(self, tool: dict[str, Any]) -> dict[str, Any]:
        """为工具构造测试参数."""
        input_schema = tool.get("inputSchema", {})
        properties = input_schema.get("properties", {})
        required = input_schema.get("required", [])

        args: dict[str, Any] = {}
        for prop_name, prop_info in properties.items():
            prop_type = prop_info.get("type", "string")

            if prop_type == "string":
                if (
                    "query" in prop_name.lower()
                    or "prompt" in prop_name.lower()
                    or "input" in prop_name.lower()
                ):
                    args[prop_name] = "Hello, this is a test message"
                elif prop_name in required:
                    args[prop_name] = "test_value"
            elif prop_type == "number":
                args[prop_name] = 42
            elif prop_type == "boolean":
                args[prop_name] = True
            elif prop_type == "array":
                args[prop_name] = []

        # 如果没有构造出参数，使用默认参数
        if not args:
            return {"input": "test input from HTTP MCP test"}

        return args

    def _display_http_evaluation_result(self, evaluation_result: dict) -> None:
        """显示HTTP MCP端点评估结果."""
        from rich.console import Console
        from rich.panel import Panel
        from rich.progress import BarColumn, Progress, TextColumn
        from rich.table import Table

        console = Console()

        # 显示总体评分
        scoring_breakdown = evaluation_result.get("scoring_breakdown", {})
        final_score = scoring_breakdown.get("final_score", 0)
        quality_grade = evaluation_result.get("quality_grade", "N/A")

        # 创建评分面板
        score_text = "[bold green]HTTP MCP 端点评估结果[/bold green]\n\n"
        score_text += f"🎯 综合评分: [bold cyan]{final_score}[/bold cyan]/100\n"
        score_text += f"🏆 质量等级: [bold yellow]{quality_grade}[/bold yellow]\n\n"

        score_text += "[bold]详细评分:[/bold]\n"
        score_text += f"🔗 连通性: {scoring_breakdown.get('connectivity_score', 0)}/100 (权重30%)\n"
        score_text += f"⚙️  功能性: {scoring_breakdown.get('functionality_score', 0)}/100 (权重40%)\n"
        score_text += (
            f"⚡ 性能: {scoring_breakdown.get('performance_score', 0)}/100 (权重20%)\n"
        )
        score_text += (
            f"📊 工具数量: {scoring_breakdown.get('quantity_score', 0)}/100 (权重10%)"
        )

        console.print(Panel(score_text, title="🔍 评估报告", border_style="green"))

        # 创建详细评分表格
        table = Table(title="评分明细")
        table.add_column("评估维度", style="cyan", width=15)
        table.add_column("得分", style="green", width=10)
        table.add_column("权重", style="yellow", width=10)
        table.add_column("说明", style="white", width=50)

        # 连通性评分
        connectivity_score = scoring_breakdown.get("connectivity_score", 0)
        connectivity_desc = (
            "服务连通性和稳定性" if connectivity_score == 100 else "服务连接存在问题"
        )
        table.add_row("连通性", f"{connectivity_score}/100", "30%", connectivity_desc)

        # 功能性评分
        functionality_score = scoring_breakdown.get("functionality_score", 0)
        functionality_desc = (
            "工具功能完整性" if functionality_score >= 80 else "工具功能需要改进"
        )
        table.add_row("功能性", f"{functionality_score}/100", "40%", functionality_desc)

        # 性能评分
        performance_score = scoring_breakdown.get("performance_score", 0)
        if performance_score >= 85:
            performance_desc = "响应速度优秀"
        elif performance_score >= 70:
            performance_desc = "响应速度良好"
        elif performance_score >= 50:
            performance_desc = "响应速度一般"
        else:
            performance_desc = "响应速度需要优化"
        table.add_row("性能", f"{performance_score}/100", "20%", performance_desc)

        # 工具数量评分
        quantity_score = scoring_breakdown.get("quantity_score", 0)
        details = scoring_breakdown.get("details", {})
        tools_count = details.get("tools_count", 0)
        quantity_desc = f"提供{tools_count}个工具" if tools_count > 0 else "未提供工具"
        table.add_row("工具数量", f"{quantity_score}/100", "10%", quantity_desc)

        console.print(table)

        # 显示改进建议
        recommendations = evaluation_result.get("recommendations", [])
        if recommendations:
            console.print("\n[bold yellow]💡 改进建议:[/bold yellow]")
            for i, rec in enumerate(recommendations, 1):
                console.print(f"  {i}. {rec}")

        # 显示详细信息
        if details:
            console.print("\n[bold]📈 统计信息:[/bold]")
            console.print(
                f"  • 功能测试数量: {details.get('functional_tests_count', 0)}"
            )
            console.print(
                f"  • 功能测试成功: {details.get('functional_tests_success', 0)}"
            )
            console.print(
                f"  • 平均响应时间: {details.get('response_time_seconds', 0):.2f}秒"
            )

        # 显示评分进度条
        console.print("\n[bold]📊 综合评分构成:[/bold]")
        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        ) as progress:
            # 连通性进度条
            connectivity_task = progress.add_task("连通性", total=100)
            progress.update(connectivity_task, completed=connectivity_score)

            # 功能性进度条
            functionality_task = progress.add_task("功能性", total=100)
            progress.update(functionality_task, completed=functionality_score)

            # 性能进度条
            performance_task = progress.add_task("性能", total=100)
            progress.update(performance_task, completed=performance_score)

            # 工具数量进度条
            quantity_task = progress.add_task("工具数量", total=100)
            progress.update(quantity_task, completed=quantity_score)


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
