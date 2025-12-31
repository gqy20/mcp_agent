"""TestRunner - 测试运行器.

从 cli_handlers.py 提取的测试运行逻辑，负责：
- 执行基础测试
- 执行智能测试
- 检测 HTTP MCP 客户端
- 路由到不同的测试方法

作者: AI Assistant
日期: 2025-12-31
"""

import asyncio
from typing import Any

from rich import print as rprint

from src.batch_mcp.core.tester import TestConfig
from src.batch_mcp.utils.csv_parser import MCPToolInfo


class TestRunner:
    """测试运行器 - 统一测试执行入口."""

    def __init__(self, tester) -> None:
        """初始化测试运行器.

        Args:
            tester: MCPTester 实例

        """
        self.tester = tester

    def run_tests(
        self,
        tool_info: MCPToolInfo | None,
        server_info: Any,
        config: TestConfig,
    ):
        """执行测试 - 支持无 tool_info 场景.

        Args:
            tool_info: 工具信息
            server_info: 服务器信息
            config: 测试配置

        Returns:
            tuple[bool, list]: (测试是否成功, 测试结果列表)

        """
        rprint("[yellow]🧪 执行基础连通性测试...[/yellow]")

        # 检查是否为 HTTP MCP 客户端
        if self.is_http_client(server_info):
            http_success, http_test_results = asyncio.run(
                self._run_http_tests(tool_info, server_info, config)
            )
            # 提取 basic_tests 列表以保持与其他测试路径的一致性
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

    def is_http_client(self, server_info: Any) -> bool:
        """检测是否为 HTTP MCP 客户端.

        Args:
            server_info: 服务器信息对象

        Returns:
            bool: 是否为 HTTP MCP 客户端

        """
        try:
            # 检查是否为 HTTP 部署的 server_info 对象
            if hasattr(server_info, "client"):
                from .http_mcp_client import HttpMCPClient

                return isinstance(server_info.client, HttpMCPClient)

            # 直接检查是否为 HTTP 客户端（兼容性）
            from .http_mcp_client import HttpMCPClient

            return isinstance(server_info, HttpMCPClient)
        except ImportError:
            return False

    async def _run_http_tests(
        self, _tool_info: MCPToolInfo | None, server_info: Any, config: TestConfig
    ) -> tuple[bool, dict[str, Any]]:
        """运行 HTTP MCP 测试 - 与STDIO测试保持一致.

        Args:
            _tool_info: 工具信息（未使用）
            server_info: 服务器信息
            config: 测试配置

        Returns:
            tuple[bool, dict]: (测试是否成功, 测试结果字典)

        """
        try:
            rprint("[blue]🔗 测试 HTTP MCP 连接...[/blue]")

            # 获取 HTTP 客户端
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

            # 更新 server_info 的 available_tools
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
        from src.batch_mcp.utils.test_params_generator import get_test_params_generator

        params_generator = get_test_params_generator()
        return params_generator.generate(tool_info)


# 全局测试运行器实例
_runner = None


def get_test_runner() -> TestRunner:
    """获取全局测试运行器实例."""
    global _runner
    if _runner is None:
        from src.batch_mcp.core.tester import get_mcp_tester

        _runner = TestRunner(get_mcp_tester())
    return _runner
