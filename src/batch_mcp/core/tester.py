#!/usr/bin/env python3
"""MCP 测试核心逻辑 - 简洁版.

遵循 Linus 的"好品味"原则：
- 消除所有特殊情况
- 每个函数只做一件事
- 无3层以上缩进

作者: AI Assistant (Linus重构版)
日期: 2025-08-18
版本: 0.1.0 (简洁版)
"""

import time
from dataclasses import dataclass

from src.batch_mcp.core.report_generator import TestResult
from src.batch_mcp.utils.csv_parser import MCPToolInfo
from src.batch_mcp.utils.test_params_generator import get_test_params_generator


@dataclass
class TestConfig:
    """测试配置 - 统一数据结构."""

    timeout: int = 600
    verbose: bool = False
    smart_test: bool = False
    cleanup: bool = True
    save_report: bool = True
    db_export: bool = False
    evaluate: bool = True


class MCPTester:
    """MCP测试器 - 核心测试逻辑."""

    def __init__(self) -> None:
        self.parser = None
        self.deployer = None

    def _get_services(self):
        """延迟加载服务 - 避免循环导入."""
        if not self.parser:
            from src.batch_mcp.core.deployer import get_simple_mcp_deployer
            from src.batch_mcp.utils.csv_parser import get_mcp_parser

            self.parser = get_mcp_parser()
            self.deployer = get_simple_mcp_deployer()
        return self.parser, self.deployer

    def find_tool_by_url(self, url: str) -> MCPToolInfo | None:
        """根据URL查找工具信息."""
        parser, _ = self._get_services()
        return parser.find_tool_by_url(url)

    def deploy_tool(
        self,
        package_name: str,
        timeout: int,
        run_command: str | None = None,
    ):
        """部署MCP工具."""
        parser, deployer = self._get_services()

        # 如果没有提供run_command，尝试从CSV中查找工具信息获取正确的运行命令
        if not run_command:
            tool_info = parser.find_tool_by_package(package_name)
            if (
                tool_info
                and hasattr(tool_info, "run_command")
                and tool_info.run_command
            ):
                run_command = tool_info.run_command

        return deployer.deploy_package(package_name, timeout, run_command)

    def cleanup_server(self, server_id: str):
        """清理服务器."""
        _, deployer = self._get_services()
        return deployer.cleanup_server(server_id)

    def run_basic_test(
        self,
        server_info,
        timeout: int = 10,
    ) -> tuple[bool, list[TestResult]]:
        """基础连通性测试 - 简化版."""
        test_results = []

        # 1. MCP协议通信测试
        comm_result = self._test_mcp_communication(server_info, timeout)
        test_results.append(comm_result)

        if not comm_result.success:
            return False, test_results

        # 2. 工具调用测试（如果有工具）
        if server_info.available_tools:
            tool_result = self._test_first_tool(server_info, timeout)
            test_results.append(tool_result)

        return True, test_results

    def _test_mcp_communication(self, server_info, timeout: int) -> TestResult:
        """MCP协议通信测试 - 单一职责."""
        start_time = time.time()

        request = {"jsonrpc": "2.0", "id": 999, "method": "tools/list", "params": {}}

        result = server_info.communicator.send_request(request, timeout=timeout)
        duration = time.time() - start_time

        return TestResult(
            test_name="MCP协议通信测试",
            success=result["success"],
            duration=duration,
            error_message=result.get("error") if not result["success"] else None,
        )

    def _test_first_tool(self, server_info, timeout: int) -> TestResult:
        """测试第一个可用工具 - 智能参数生成."""
        first_tool = server_info.available_tools[0]
        tool_name = first_tool.get("name", "unknown")

        start_time = time.time()

        # 生成基本测试参数（使用统一的参数生成器）
        params_generator = get_test_params_generator()
        arguments = params_generator.generate(first_tool)

        request = {
            "jsonrpc": "2.0",
            "id": 1000,
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": arguments},
        }

        result = server_info.communicator.send_request(request, timeout=timeout)
        duration = time.time() - start_time

        return TestResult(
            test_name=f"工具调用测试: {tool_name}",
            success=result["success"],
            duration=duration,
            error_message=result.get("error") if not result["success"] else None,
        )

    async def run_smart_test(
        self,
        tool_info: MCPToolInfo,
        server_info,
        verbose: bool,
    ) -> tuple[bool, list[TestResult]]:
        """智能测试 - 简化版."""
        try:
            # 动态导入，避免强依赖
            from src.batch_mcp.agents.test_agent import get_test_generator
            from src.batch_mcp.agents.validation_agent import get_validation_agent
            from src.batch_mcp.core.async_mcp_client import AsyncMCPClient

            test_generator = get_test_generator()
            validation_agent = get_validation_agent()

            # 生成测试用例（AI 或 fallback）
            test_cases = await test_generator.generate_test_cases(
                tool_info,
                server_info.available_tools,
            )

            if not test_cases:
                # 如果没有生成测试用例，运行基础测试
                success, results = self.run_basic_test(server_info)
                return success, results

            # 执行智能验证
            mcp_client = AsyncMCPClient(server_info.communicator)
            ai_results = await validation_agent.execute_test_suite(
                test_cases,
                mcp_client,
            )

            # 转换结果格式 - 增强版，包含详细信息
            test_results = []
            for r in ai_results:
                # 确定测试类别
                test_category = "基础功能"
                if "容错" in r.test_case.name:
                    test_category = "容错能力"
                elif "边界" in r.test_case.name:
                    test_category = "边界情况"
                elif "实际使用" in r.test_case.name:
                    test_category = "实际使用场景"

                test_results.append(
                    TestResult(
                        test_name=r.test_case.name,
                        success=(r.status.value == "pass"),
                        duration=r.execution_time,
                        error_message=r.error_message,
                        tool_name=r.test_case.tool_name,
                        parameters=r.test_case.parameters,
                        actual_response=r.response,
                        ai_analysis=r.analysis,
                        ai_confidence=0.95,  # 默认置信度，AI分析成功时会更新
                        test_category=test_category,
                    ),
                )

            passed = sum(1 for r in ai_results if r.status.value == "pass")
            success_rate = passed / len(ai_results) if ai_results else 0

            return (success_rate >= 0.7), test_results

        except ImportError:
            # 智能测试不可用，回退到基础测试
            return self.run_basic_test(server_info)


# 全局测试器实例
_tester = MCPTester()


def get_mcp_tester() -> MCPTester:
    """获取全局测试器实例."""
    return _tester
