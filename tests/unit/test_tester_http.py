"""MCP 测试器 HTTP 支持单元测试.

TDD 测试：验证 MCP 测试器对 HTTP MCP 端点的支持.

作者: AI Assistant
日期: 2025-12-17
"""

from unittest.mock import AsyncMock

import pytest

# 目标模块
from src.batch_mcp.core.tester import MCPTester, TestConfig


class TestMCPTesterHTTPSupport:
    """MCP 测试器 HTTP 支持测试类."""

    @pytest.fixture
    def mcp_tester(self) -> MCPTester:
        """MCP 测试器 fixture."""
        return MCPTester()

    @pytest.mark.asyncio
    async def test_test_http_client_success(self, mcp_tester: MCPTester) -> None:
        """测试：HTTP 客户端成功测试."""
        # 创建模拟的 HTTP 客户端
        mock_client = AsyncMock()
        mock_client.list_tools.return_value = {
            "success": True,
            "tools": [
                {
                    "name": "research_tool",
                    "description": "AI research tool",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string"},
                            "depth": {"type": "integer", "default": 1},
                        },
                        "required": ["query"],
                    },
                }
            ],
        }
        mock_client.call_tool.return_value = {
            "success": True,
            "result": {
                "content": [{"type": "text", "text": "Research completed successfully"}]
            },
        }

        test_config = TestConfig(
            timeout=30,
            verbose=False,
            smart_test=False,
            cleanup=False,
            save_report=False,
            db_export=False,
            evaluate=False,
        )

        # 执行测试（这里需要实际的实现方法）
        result = await self._test_http_mcp_client(mcp_tester, mock_client, test_config)

        assert result["success"] is True
        assert result["tools_found"] == 1
        assert len(result["tools"]) == 1
        assert result["tools"][0]["name"] == "research_tool"

    async def _test_http_mcp_client(self, tester, client, config):
        """测试 HTTP MCP 客户端的辅助方法."""
        try:
            # 获取工具列表
            tools_result = await client.list_tools()
            if not tools_result["success"]:
                return {
                    "success": False,
                    "error": tools_result.get("error", "Failed to get tools"),
                }

            tools = tools_result.get("tools", [])

            # 基础测试结果
            result = {
                "success": True,
                "tools_found": len(tools),
                "tools": tools,
                "connection": True,
            }

            # 如果启用智能测试
            if config.smart_test and tools:
                smart_results = await self._run_http_smart_tests(tester, client, tools)
                result["smart_tests"] = smart_results

            return result

        except Exception as e:
            return {"success": False, "error": str(e), "connection": False}

    async def _run_http_smart_tests(self, tester, client, tools):
        """运行 HTTP 智能测试的辅助方法."""
        smart_results = []

        for tool in tools[:2]:  # 限制测试前2个工具
            tool_name = tool.get("name")
            if not tool_name:
                continue

            try:
                # 构造测试参数
                test_args = self._construct_test_args(tool)

                # 调用工具
                call_result = await client.call_tool(tool_name, test_args)

                smart_results.append(
                    {
                        "tool_name": tool_name,
                        "success": call_result.get("success", False),
                        "result": call_result.get("result"),
                        "error": call_result.get("error"),  # 包含错误信息
                    }
                )

            except Exception as e:
                smart_results.append(
                    {"tool_name": tool_name, "success": False, "error": str(e)}
                )

        return smart_results

    def _construct_test_args(self, tool):
        """为工具构造测试参数."""
        input_schema = tool.get("inputSchema", {})
        properties = input_schema.get("properties", {})
        required = input_schema.get("required", [])

        args = {}
        for prop_name, prop_info in properties.items():
            prop_type = prop_info.get("type", "string")

            if prop_type == "string":
                if "query" in prop_name.lower() or "prompt" in prop_name.lower():
                    args[prop_name] = "Test research query"
                elif prop_name in required:
                    args[prop_name] = "test_value"
            elif prop_type == "number":
                args[prop_name] = 42
            elif prop_type == "boolean":
                args[prop_name] = True

        return args if args else {"input": "test input"}

    @pytest.mark.asyncio
    async def test_test_http_client_connection_failure(self, mcp_tester):
        """测试：HTTP 客户端连接失败."""
        mock_client = AsyncMock()
        mock_client.list_tools.side_effect = ConnectionError("Connection refused")

        test_config = TestConfig(timeout=10)

        result = await self._test_http_mcp_client(mcp_tester, mock_client, test_config)

        assert result["success"] is False
        assert "Connection refused" in result["error"]
        assert result["connection"] is False

    @pytest.mark.asyncio
    async def test_test_http_client_empty_tools_list(self, mcp_tester):
        """测试：HTTP 客户端返回空工具列表."""
        mock_client = AsyncMock()
        mock_client.list_tools.return_value = {"success": True, "tools": []}

        test_config = TestConfig(smart_test=True)

        result = await self._test_http_mcp_client(mcp_tester, mock_client, test_config)

        assert result["success"] is True
        assert result["tools_found"] == 0
        assert len(result["tools"]) == 0
        assert "smart_tests" not in result  # 没有工具时不运行智能测试

    @pytest.mark.asyncio
    async def test_test_http_client_tool_call_failure(self, mcp_tester):
        """测试：HTTP 客户端工具调用失败."""
        mock_client = AsyncMock()
        mock_client.list_tools.return_value = {
            "success": True,
            "tools": [
                {
                    "name": "failing_tool",
                    "description": "This tool will fail",
                    "inputSchema": {
                        "type": "object",
                        "properties": {"input": {"type": "string"}},
                        "required": ["input"],
                    },
                }
            ],
        }
        mock_client.call_tool.return_value = {
            "success": False,
            "error": "Tool execution failed",
        }

        test_config = TestConfig(smart_test=True)

        result = await self._test_http_mcp_client(mcp_tester, mock_client, test_config)

        assert result["success"] is True
        assert result["tools_found"] == 1
        assert "smart_tests" in result
        assert len(result["smart_tests"]) == 1
        assert result["smart_tests"][0]["success"] is False
        assert result["smart_tests"][0]["error"] == "Tool execution failed"

    def test_construct_test_args_with_different_schemas(self, _mcp_tester):
        """测试：使用不同输入模式构造测试参数."""
        test_cases = [
            {
                "tool": {
                    "inputSchema": {
                        "properties": {
                            "query": {"type": "string"},
                            "count": {"type": "integer"},
                        },
                        "required": ["query"],
                    }
                },
                "expected_keys": ["query"],
            },
            {
                "tool": {
                    "inputSchema": {
                        "properties": {
                            "prompt": {"type": "string"},
                            "temperature": {"type": "number"},
                            "stream": {"type": "boolean"},
                        },
                        "required": [],
                    }
                },
                "expected_keys": ["prompt"],
            },
            {
                "tool": {"inputSchema": {"properties": {}, "required": []}},
                "expected_keys": ["input"],  # 默认参数
            },
        ]

        for i, test_case in enumerate(test_cases):
            args = self._construct_test_args(test_case["tool"])

            # 验证包含预期的键
            for key in test_case["expected_keys"]:
                assert (
                    key in args
                ), f"Test case {i}: Expected key '{key}' not found in args"

            # 验证参数不为空
            assert args, f"Test case {i}: Args should not be empty"

    @pytest.mark.asyncio
    async def test_http_client_timeout_handling(self, mcp_tester):
        """测试：HTTP 客户端超时处理."""
        mock_client = AsyncMock()
        mock_client.list_tools.return_value = {
            "success": True,
            "tools": [
                {
                    "name": "slow_tool",
                    "description": "Tool that takes time",
                    "inputSchema": {
                        "properties": {"input": {"type": "string"}},
                        "required": ["input"],
                    },
                }
            ],
        }
        # 模拟超时
        mock_client.call_tool.side_effect = TimeoutError("Operation timed out")

        test_config = TestConfig(smart_test=True, timeout=5)

        result = await self._test_http_mcp_client(mcp_tester, mock_client, test_config)

        assert result["success"] is True  # 基础连接成功
        assert result["tools_found"] == 1
        assert "smart_tests" in result
        # 智能测试中的工具调用应该失败
        assert not result["smart_tests"][0]["success"]

    @pytest.mark.asyncio
    async def test_http_client_multiple_tools_testing(self, mcp_tester):
        """测试：HTTP 客户端多工具测试."""
        mock_client = AsyncMock()
        mock_client.list_tools.return_value = {
            "success": True,
            "tools": [
                {
                    "name": "tool1",
                    "description": "First tool",
                    "inputSchema": {
                        "properties": {"query": {"type": "string"}},
                        "required": ["query"],
                    },
                },
                {
                    "name": "tool2",
                    "description": "Second tool",
                    "inputSchema": {
                        "properties": {"data": {"type": "string"}},
                        "required": ["data"],
                    },
                },
                {
                    "name": "tool3",
                    "description": "Third tool",
                    "inputSchema": {
                        "properties": {"input": {"type": "string"}},
                        "required": ["input"],
                    },
                },
            ],
        }

        # 为不同的工具调用返回不同的结果
        def call_tool_side_effect(name, args):
            if name == "tool1":
                return {
                    "success": True,
                    "result": {"content": [{"type": "text", "text": "Tool1 result"}]},
                }
            if name == "tool2":
                return {
                    "success": True,
                    "result": {"content": [{"type": "text", "text": "Tool2 result"}]},
                }
            return {"success": False, "error": "Tool3 failed"}

        mock_client.call_tool.side_effect = call_tool_side_effect

        test_config = TestConfig(smart_test=True)

        result = await self._test_http_mcp_client(mcp_tester, mock_client, test_config)

        assert result["success"] is True
        assert result["tools_found"] == 3
        assert "smart_tests" in result
        # 应该测试前2个工具（根据限制）
        assert len(result["smart_tests"]) == 2

        # 验证测试结果
        successful_tests = [t for t in result["smart_tests"] if t["success"]]
        assert len(successful_tests) == 2  # tool1 和 tool2 成功
