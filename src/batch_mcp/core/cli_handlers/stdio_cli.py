"""STDIO MCP CLI 处理模块.

此模块包含 STDIO MCP 工具的 CLI 命令处理逻辑。
"""

import time
from typing import Any

from rich import print as rprint

from src.batch_mcp.core.evaluator import (
    evaluate_full_repository_with_comprehensive_score,
)
from src.batch_mcp.core.http_mcp_client import HttpMCPClient
from src.batch_mcp.core.report_generator import generate_test_report
from src.batch_mcp.core.tester import TestConfig
from src.batch_mcp.utils.csv_parser import MCPToolInfo

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

from .utils import convert_test_results_to_dict


class STDIOCLIHandler:
    """STDIO MCP CLI 命令处理器."""

    def __init__(self, tester, presenter, exporter) -> None:
        self.tester = tester
        self._presenter = presenter
        self._exporter = exporter

    def evaluate_tools(self, db_export: bool) -> None:
        """评估所有工具 - 包含综合评分."""
        try:
            parser = self.tester._get_services()[0]
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
                except Exception:
                    rprint("[yellow]⚠️ Supabase客户端创建失败[/yellow]")

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

        except Exception:
            rprint("[red]❌ 评估过程发生错误[/red]")

    def deploy_tool(self, tool_info: MCPToolInfo, config: TestConfig):
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

    def save_report(
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

        except Exception:
            rprint("[red]❌ 报告生成失败[/red]")
            return {}

    def cleanup_server(self, server_id: str) -> None:
        """清理服务器 - 单一职责."""
        try:
            rprint("[yellow]🧹 清理测试环境...[/yellow]")
            self.tester.cleanup_server(server_id)
            rprint("[green]✅ 清理完成[/green]")
        except Exception:
            rprint("[yellow]⚠️ 清理异常[/yellow]")

    def evaluate_github_repo(
        self, tool_info: MCPToolInfo, config: TestConfig
    ) -> dict[str, Any] | None:
        """评估 GitHub 仓库 - 单一职责."""
        supabase_client = self._create_supabase_client(config)

        evaluation_result = evaluate_full_repository_with_comprehensive_score(
            tool_info.github_url,
            supabase_client,
        )

        if evaluation_result and evaluation_result.get("status") == "success":
            self._presenter.display_evaluation_result(evaluation_result)

        return evaluation_result

    def evaluate_http_endpoint(
        self,
        tool_info: MCPToolInfo,
        test_results: list,
        server_info: Any,
        success: bool,
        config: TestConfig,
    ) -> dict[str, Any] | None:
        """评估 HTTP MCP 端点 - 单一职责."""
        from src.batch_mcp.core.evaluator import evaluate_http_mcp_endpoint

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
                "test_results": convert_test_results_to_dict(basic_tests),
            },
            tools_count=tools_count,
            response_time=avg_response_time,
            tool_info={"name": tool_info.name, "url": tool_info.url},
        )

        if evaluation_result and evaluation_result.get("status") == "success":
            self._presenter.display_http_evaluation_result(evaluation_result)

        return evaluation_result

    def _create_supabase_client(self, config: TestConfig) -> Any:
        """创建 Supabase 客户端 - 单一职责."""
        if not (
            config.db_export
            and CONFIG_AVAILABLE
            and hasattr(config, "database")
            and config.database
            and hasattr(config.database, "has_supabase_config")
            and config.database.has_supabase_config
        ):
            return None

        try:
            if SUPABASE_AVAILABLE and create_client is not None:
                return create_client(
                    config.database.supabase_url,
                    config.database.supabase_service_role_key,
                )
        except Exception:
            pass

        return None

    def _deploy_http_mcp(self, tool_info: MCPToolInfo, config: TestConfig) -> Any:
        """部署 HTTP MCP 端点 - 委托给 HTTPMCPHandler."""
        from src.batch_mcp.core.http_mcp_handler import get_http_mcp_handler

        http_handler = get_http_mcp_handler()
        return http_handler.deploy_http_mcp(tool_info, config)

    def _is_http_client(self, server_info: Any) -> bool:
        """检测是否为 HTTP MCP 客户端."""
        try:
            # 检查是否为HTTP部署的server_info对象
            if hasattr(server_info, "client"):
                return isinstance(server_info.client, HttpMCPClient)

            # 直接检查是否为HTTP客户端（兼容性）
            return isinstance(server_info, HttpMCPClient)
        except Exception:
            return False
