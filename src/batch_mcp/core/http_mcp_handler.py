"""HTTPMCPHandler - HTTP MCP 端点处理器.

从 cli_handlers.py 提取的 HTTP MCP 处理逻辑，负责：
- 部署 HTTP MCP 端点
- 运行 HTTP 测试
- 运行 HTTP 智能测试
- 构造测试参数

作者: AI Assistant
日期: 2025-12-31
"""

import time
from types import SimpleNamespace
from typing import Any

from rich import print as rprint

from src.batch_mcp.core.report_generator import TestResult
from src.batch_mcp.core.tester import TestConfig
from src.batch_mcp.utils.csv_parser import MCPToolInfo


class HTTPMCPHandler:
    """HTTP MCP 端点处理器."""

    def __init__(self) -> None:
        """初始化 HTTP MCP 处理器."""

    def deploy_http_mcp(
        self, tool_info: MCPToolInfo, config: TestConfig
    ) -> SimpleNamespace | None:
        """部署 HTTP MCP 端点.

        Args:
            tool_info: 工具信息
            config: 测试配置

        Returns:
            SimpleNamespace | None: server_info 对象或 None

        """
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

            # 创建一个兼容的 server_info 对象
            server_info = SimpleNamespace()
            server_info.server_id = f"http-mcp-{tool_info.name}"
            server_info.client = client
            server_info.available_tools = []  # 将在测试时填充

            return server_info

        except Exception as e:
            rprint(f"[red]❌ HTTP MCP 端点部署失败: {e}[/red]")
            return None

    async def run_http_tests_direct(
        self,
        tool_info: MCPToolInfo | None,
        http_config: dict[str, Any],
        config: TestConfig,
    ) -> bool:
        """运行 HTTP MCP 测试的专用方法.

        Args:
            tool_info: 工具信息
            http_config: HTTP 配置
            config: 测试配置

        Returns:
            bool: 测试是否成功

        """
        try:
            from .http_mcp_client import HttpMCPClient

            # 创建 HTTP MCP 客户端
            client = HttpMCPClient(
                url=http_config["url"],
                headers=http_config["headers"],
                timeout=http_config["timeout"],
            )

            # 创建 server_info 对象来包装 client
            server_info = type("ServerInfo", (), {"client": client})()

            # 运行基础测试
            success, test_results = await self._run_http_tests(
                tool_info, server_info, config
            )

            # 获取工具列表 (用于智能测试和评估)
            tools_result = await client.list_tools()
            tools_list = tools_result.get("tools", [])
            tools_count = len(tools_list)

            # 如果启用智能测试，运行 AI 测试
            if config.smart_test and success:
                rprint("[blue]🤖 开始 AI 智能测试...[/blue]")

                smart_results = await self.run_http_smart_tests(
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

            # 评估和报告生成逻辑已在 cli_handlers 中处理
            return success

        except Exception as e:
            rprint(f"[red]❌ HTTP 测试执行失败: {e}[/red]")
            if config.verbose:
                import traceback

                rprint(f"[red]{traceback.format_exc()}[/red]")
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

            # 1. 获取工具列表
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

            # 2. 创建测试结果
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

            # 3. 工具调用测试
            if tools:
                first_tool = tools[0]
                tool_name = first_tool.get("name", "unknown")

                rprint(f"[blue]🧪 测试工具调用: {tool_name}[/blue]")

                start_time = time.time()

                # 生成测试参数
                arguments = self.construct_test_args(first_tool)

                # 调用工具
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

            # 返回结果
            return True, {
                "basic_tests": test_results,
                "connection": True,
                "tools_found": len(tools),
                "tools": tools,
            }

        except Exception as e:
            rprint(f"[red]❌ HTTP MCP 测试失败: {e}[/red]")
            return False, {"error": str(e)}

    async def run_http_smart_tests(
        self, client: Any, tools: list[dict[str, Any]], _config: TestConfig
    ) -> list[dict[str, Any]]:
        """运行 HTTP 智能测试.

        Args:
            client: HTTP MCP 客户端
            tools: 工具列表
            _config: 测试配置（未使用）

        Returns:
            list[dict]: 智能测试结果列表

        """
        smart_results = []

        for tool in tools[:3]:  # 限制测试前3个工具
            tool_name = tool.get("name")
            if not tool_name:
                continue

            try:
                rprint(f"[blue]🧪 测试工具: {tool_name}[/blue]")

                # 构造测试参数
                test_args = self.construct_test_args(tool)

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

    def construct_test_args(self, tool: dict[str, Any]) -> dict[str, Any]:
        """为工具构造测试参数.

        Args:
            tool: 工具信息字典

        Returns:
            dict: 测试参数

        """
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


# 全局 HTTP MCP 处理器实例
_handler = None


def get_http_mcp_handler() -> HTTPMCPHandler:
    """获取全局 HTTP MCP 处理器实例."""
    global _handler
    if _handler is None:
        _handler = HTTPMCPHandler()
    return _handler
