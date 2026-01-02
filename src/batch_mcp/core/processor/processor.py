"""URL-MCP 处理器模块.

此模块包含URL-MCP处理的核心逻辑。
"""

import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from rich.console import Console

try:
    from rich import print as rprint
except ImportError:

    def rprint(text) -> None:
        pass


from src.batch_mcp.core.deployer import get_simple_mcp_deployer
from src.batch_mcp.utils.csv_parser import MCPToolInfo, get_mcp_parser

from .models import TestReport
from .report_generator import ReportGenerator
from .url_resolver import URLResolver


class URLMCPProcessor:
    """URL-MCP智能处理器."""

    def __init__(self) -> None:
        self.console = Console()
        self.parser = get_mcp_parser()
        self.deployer = get_simple_mcp_deployer()
        self.url_resolver = URLResolver(self.parser)
        self.reports_dir = Path("data/test_results/reports")
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.report_generator = ReportGenerator(self.reports_dir)

    async def process_url(
        self,
        url: str,
        enable_smart_test: bool = False,
        timeout: int = 30,
        generate_report: bool = True,
    ) -> TestReport:
        """完整的URL处理流程."""
        session_id = str(uuid.uuid4())[:8]
        start_time = datetime.now()

        # 初始化报告
        report = TestReport(
            session_id=session_id,
            url=url,
            tool_info=None,
            start_time=start_time,
        )

        try:
            rprint(f"[bold green]🎯 开始处理URL:[/bold green] {url}")
            rprint(f"[blue]📝 会话ID: {session_id}[/blue]")

            # 第一步：URL解析和工具匹配
            tool_info = self.url_resolver.resolve_url_to_tool(url)
            if not tool_info:
                report.error_messages.append("无法从URL解析到MCP工具")
                return report

            report.tool_info = tool_info

            # 第二步：工具部署
            deployment_start = time.time()
            server_info = await self._deploy_tool(tool_info, timeout)
            deployment_time = time.time() - deployment_start

            report.deployment_time = deployment_time

            if not server_info:
                report.error_messages.append("MCP工具部署失败")
                return report

            report.deployment_success = True
            report.available_tools_count = len(server_info.available_tools)

            # 第三步：通信验证
            comm_success = await self._verify_communication(server_info)
            report.communication_success = comm_success

            # 第四步：功能测试
            if enable_smart_test:
                test_results = await self._run_smart_tests(tool_info, server_info)
            else:
                test_results = await self._run_basic_tests(server_info)

            report.test_results = test_results

            # 第五步：性能分析
            performance = await self._analyze_performance(server_info, deployment_time)
            report.performance_metrics = performance

            # 清理资源
            try:
                self.deployer.cleanup_server(server_info.server_id)
            except Exception as e:
                report.error_messages.append(f"清理失败: {e!s}")

        except Exception as e:
            report.error_messages.append(f"处理异常: {e!s}")
            rprint(f"[red]❌ 处理失败: {e}[/red]")

        finally:
            report.end_time = datetime.now()

            # 生成报告
            if generate_report:
                await self.report_generator.generate_reports(report)

        return report

    async def _deploy_tool(self, tool_info: MCPToolInfo, timeout: int):
        """部署MCP工具."""
        try:
            # 优先使用run_command，其次使用package_name
            if tool_info.run_command:
                display_name = tool_info.run_command
                rprint(f"[blue]🚀 部署MCP工具: {display_name}[/blue]")
                server_info = self.deployer.deploy_package(
                    package_name=tool_info.package_name,
                    timeout=timeout,
                    run_command=tool_info.run_command,
                )
            else:
                display_name = tool_info.package_name
                rprint(f"[blue]🚀 部署MCP工具: {display_name}[/blue]")

                if not tool_info.package_name:
                    msg = "缺少包名信息"
                    raise ValueError(msg)

                server_info = self.deployer.deploy_package(
                    tool_info.package_name,
                    timeout,
                )

            if server_info:
                rprint(f"[green]✅ {display_name} 部署成功！[/green]")
                rprint(
                    f"[green]🔧 可用工具: {[tool['name'] for tool in server_info.available_tools]}[/green]",
                )
                rprint(
                    f"[green]✅ 部署成功，工具数: {len(server_info.available_tools)}[/green]",
                )

            return server_info

        except Exception as e:
            rprint(f"[red]❌ 部署失败: {e}[/red]")
            return None

    async def _verify_communication(self, server_info) -> bool:
        """验证MCP通信."""
        try:
            rprint("[blue]📡 验证MCP通信...[/blue]")

            tools_request = {
                "jsonrpc": "2.0",
                "id": 999,
                "method": "tools/list",
                "params": {},
            }

            result = server_info.communicator.send_request(tools_request, timeout=10)

            if result["success"]:
                rprint("[green]✅ MCP通信正常[/green]")
                return True
            rprint(f"[yellow]⚠️ MCP通信异常: {result.get('error')}[/yellow]")
            return False

        except Exception as e:
            rprint(f"[red]❌ 通信验证失败: {e}[/red]")
            return False

    async def _run_basic_tests(self, server_info) -> list[dict[str, Any]]:
        """运行基础测试."""
        tests = []

        try:
            rprint("[blue]🧪 执行基础功能测试...[/blue]")

            # 工具列表测试
            test_start = time.time()
            tools_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/list",
                "params": {},
            }

            result = server_info.communicator.send_request(tools_request)
            test_time = time.time() - test_start

            tests.append(
                {
                    "name": "工具列表测试",
                    "success": result["success"],
                    "response_time": test_time,
                    "details": result,
                },
            )

            # 对每个可用工具进行简单测试
            for i, tool in enumerate(server_info.available_tools[:3], 1):
                test_start = time.time()
                tool_name = tool.get("name", "unknown")

                try:
                    # 尝试调用工具（使用空参数）
                    tool_request = {
                        "jsonrpc": "2.0",
                        "id": i + 1,
                        "method": "tools/call",
                        "params": {"name": tool_name, "arguments": {}},
                    }

                    result = server_info.communicator.send_request(
                        tool_request,
                        timeout=5,
                    )
                    test_time = time.time() - test_start

                    tests.append(
                        {
                            "name": f"工具调用测试: {tool_name}",
                            "success": result.get("success", False),
                            "response_time": test_time,
                            "details": result,
                        },
                    )

                except Exception as e:
                    tests.append(
                        {
                            "name": f"工具调用测试: {tool_name}",
                            "success": False,
                            "response_time": time.time() - test_start,
                            "error": str(e),
                        },
                    )

            passed = sum(1 for t in tests if t.get("success", False))
            rprint(f"[green]📊 基础测试完成: {passed}/{len(tests)} 通过[/green]")

        except Exception as e:
            rprint(f"[red]❌ 基础测试失败: {e}[/red]")

        return tests

    async def _run_smart_tests(
        self,
        tool_info: MCPToolInfo,
        server_info,
    ) -> list[dict[str, Any]]:
        """运行智能测试（暂时回退到基础测试）."""
        try:
            rprint("[blue]🤖 尝试智能测试...[/blue]")

            # 尝试导入智能代理
            try:
                # 智能测试逻辑（简化版）
                rprint("[yellow]⚠️ 智能测试功能开发中，使用增强基础测试[/yellow]")
                return await self._run_basic_tests(server_info)

            except Exception as agent_error:
                rprint(f"[yellow]⚠️ 智能代理不可用: {agent_error}[/yellow]")
                rprint("[blue]🔄 回退到基础测试模式[/blue]")
                return await self._run_basic_tests(server_info)

        except Exception as e:
            rprint(f"[red]❌ 智能测试失败: {e}[/red]")
            return await self._run_basic_tests(server_info)

    async def _analyze_performance(
        self,
        server_info,
        deployment_time: float,
    ) -> dict[str, float]:
        """性能分析."""
        metrics = {
            "deployment_time": deployment_time,
            "tools_count": len(server_info.available_tools),
            "startup_time": time.time() - server_info.start_time,
        }

        # 简单的响应时间测试
        try:
            start = time.time()
            tools_request = {
                "jsonrpc": "2.0",
                "id": 999,
                "method": "tools/list",
                "params": {},
            }
            server_info.communicator.send_request(tools_request, timeout=5)
            metrics["avg_response_time"] = time.time() - start
        except Exception:
            metrics["avg_response_time"] = -1

        return metrics


# 全局处理器实例
_url_processor_instance = None


def get_url_mcp_processor() -> URLMCPProcessor:
    """获取全局URL-MCP处理器实例."""
    global _url_processor_instance
    if _url_processor_instance is None:
        _url_processor_instance = URLMCPProcessor()
    return _url_processor_instance
