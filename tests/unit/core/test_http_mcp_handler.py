"""HTTPMCPHandler 单元测试.

测试覆盖：
1. deploy_http_mcp() - 部署 HTTP MCP 端点
2. run_http_tests_direct() - 运行 HTTP 测试的专用方法
3. run_http_smart_tests() - 运行 HTTP 智能测试
4. construct_test_args() - 构造测试参数
5. get_http_mcp_handler() - 单例模式
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.batch_mcp.core.tester import TestConfig
from src.batch_mcp.utils.csv_parser import MCPToolInfo


class TestHTTPMCPHandler:
    """HTTPMCPHandler 测试类."""

    def setup_method(self):
        """每个测试前的设置."""
        from src.batch_mcp.core.http_mcp_handler import HTTPMCPHandler

        # 创建独立的 HTTPMCPHandler 实例用于测试
        self.handler = HTTPMCPHandler()

    # ===== deploy_http_mcp() 测试 =====

    @patch("src.batch_mcp.core.simple_mcp_deployer.SimpleMCPDeployer")
    def test_deploy_http_mcp_success(self, mock_deployer_class):
        """测试成功部署 HTTP MCP 端点."""
        # 准备测试数据
        tool_info = MCPToolInfo(
            name="http-mcp-tool",
            url="http://localhost:8080/mcp",
            author="test",
            github_url=None,
            description="HTTP MCP tool",
            deployment_method="http",
        )

        config = TestConfig(timeout=30)

        # Mock deployer
        mock_deployer = MagicMock()
        mock_deployer.detect_deployment_method.return_value = (
            "http",
            {"url": tool_info.url},
        )
        mock_deployer.deploy_http_mcp.return_value = MagicMock()  # HTTP 客户端
        mock_deployer_class.return_value = mock_deployer

        # 执行部署
        result = self.handler.deploy_http_mcp(tool_info, config)

        # 验证结果
        assert result is not None
        assert result.server_id == "http-mcp-http-mcp-tool"
        assert hasattr(result, "client")
        assert result.available_tools == []

    @patch("src.batch_mcp.core.simple_mcp_deployer.SimpleMCPDeployer")
    def test_deploy_http_mcp_failure(self, mock_deployer_class):
        """测试部署 HTTP MCP 失败."""
        tool_info = MCPToolInfo(
            name="http-mcp-tool",
            url="http://localhost:8080/mcp",
            author="test",
            github_url=None,
            description="HTTP MCP tool",
            deployment_method="http",
        )

        config = TestConfig(timeout=30)

        # Mock deployer 抛出异常
        mock_deployer = MagicMock()
        mock_deployer.detect_deployment_method.side_effect = Exception("Deploy failed")
        mock_deployer_class.return_value = mock_deployer

        # 执行部署
        result = self.handler.deploy_http_mcp(tool_info, config)

        # 验证结果
        assert result is None

    # ===== run_http_tests_direct() 测试 =====

    @pytest.mark.asyncio
    async def test_run_http_tests_direct_success(self):
        """测试运行 HTTP 测试成功."""
        tool_info = MCPToolInfo(
            name="http-mcp-tool",
            url="http://localhost:8080/mcp",
            author="test",
            github_url=None,
            description="HTTP MCP tool",
            deployment_method="http",
        )

        http_config = {"url": "http://localhost:8080/mcp", "headers": {}, "timeout": 30}
        config = TestConfig(
            timeout=30,
            smart_test=False,
            evaluate=False,
            save_report=False,
            db_export=False,
        )

        # Mock HTTP 客户端
        mock_client = MagicMock()
        mock_client.list_tools = AsyncMock(return_value={"success": True, "tools": []})

        with patch(
            "src.batch_mcp.core.http_mcp_client.HttpMCPClient", return_value=mock_client
        ):
            result = await self.handler.run_http_tests_direct(
                tool_info, http_config, config
            )

            # 验证结果
            assert result is True

    # ===== run_http_smart_tests() 测试 =====

    @pytest.mark.asyncio
    async def test_run_http_smart_tests(self):
        """测试运行 HTTP 智能测试."""
        mock_client = MagicMock()
        mock_client.call_tool = AsyncMock(
            return_value={"success": True, "result": "test result"}
        )

        tools = [
            {"name": "tool1", "inputSchema": {"properties": {}, "required": []}},
            {"name": "tool2", "inputSchema": {"properties": {}, "required": []}},
        ]

        config = TestConfig(timeout=30)

        # 执行智能测试
        result = await self.handler.run_http_smart_tests(mock_client, tools, config)

        # 验证结果
        assert len(result) == 2
        assert result[0]["tool_name"] == "tool1"
        assert result[1]["tool_name"] == "tool2"
        assert all(r["success"] for r in result)

    @pytest.mark.asyncio
    async def test_run_http_smart_tests_limit(self):
        """测试智能测试限制为前 3 个工具."""
        mock_client = MagicMock()
        mock_client.call_tool = AsyncMock(return_value={"success": True})

        # 创建 5 个工具
        tools = [
            {"name": f"tool{i}", "inputSchema": {"properties": {}, "required": []}}
            for i in range(5)
        ]

        config = TestConfig(timeout=30)

        # 执行智能测试
        result = await self.handler.run_http_smart_tests(mock_client, tools, config)

        # 验证只测试了前 3 个
        assert len(result) == 3
        mock_client.call_tool.assert_called()  # 至少调用了一次

    @pytest.mark.asyncio
    async def test_run_http_smart_tests_tool_failure(self):
        """测试智能测试中工具调用失败."""
        mock_client = MagicMock()
        mock_client.call_tool = AsyncMock(
            return_value={"success": False, "error": "Test error"}
        )

        tools = [
            {"name": "tool1", "inputSchema": {"properties": {}, "required": []}},
        ]

        config = TestConfig(timeout=30)

        # 执行智能测试
        result = await self.handler.run_http_smart_tests(mock_client, tools, config)

        # 验证结果
        assert len(result) == 1
        assert result[0]["success"] is False
        assert result[0]["error"] == "Test error"

    # ===== construct_test_args() 测试 =====

    def test_construct_test_args_string_type(self):
        """测试构造 string 类型参数."""
        tool = {
            "name": "test_tool",
            "inputSchema": {
                "properties": {
                    "query": {"type": "string"},
                    "prompt": {"type": "string"},
                },
                "required": ["query"],
            },
        }

        result = self.handler.construct_test_args(tool)

        # query 和 prompt 应该有测试值
        assert "query" in result
        assert "prompt" in result

    def test_construct_test_args_number_type(self):
        """测试构造 number 类型参数."""
        tool = {
            "name": "test_tool",
            "inputSchema": {
                "properties": {
                    "count": {"type": "number"},
                },
                "required": ["count"],
            },
        }

        result = self.handler.construct_test_args(tool)

        assert result["count"] == 42

    def test_construct_test_args_boolean_type(self):
        """测试构造 boolean 类型参数."""
        tool = {
            "name": "test_tool",
            "inputSchema": {
                "properties": {
                    "enabled": {"type": "boolean"},
                },
                "required": ["enabled"],
            },
        }

        result = self.handler.construct_test_args(tool)

        assert result["enabled"] is True

    def test_construct_test_args_array_type(self):
        """测试构造 array 类型参数."""
        tool = {
            "name": "test_tool",
            "inputSchema": {
                "properties": {
                    "items": {"type": "array"},
                },
                "required": ["items"],
            },
        }

        result = self.handler.construct_test_args(tool)

        assert result["items"] == []

    def test_construct_test_args_no_properties(self):
        """测试没有属性时返回默认参数."""
        tool = {
            "name": "test_tool",
            "inputSchema": {"properties": {}, "required": []},
        }

        result = self.handler.construct_test_args(tool)

        # 应该返回默认参数
        assert "input" in result

    # ===== get_http_mcp_handler() 单例测试 =====

    def test_get_http_mcp_handler_singleton(self):
        """测试 get_http_mcp_handler 返回单例."""
        from src.batch_mcp.core.http_mcp_handler import get_http_mcp_handler

        handler1 = get_http_mcp_handler()
        handler2 = get_http_mcp_handler()

        # 应该是同一个实例
        assert handler1 is handler2

    # ===== 边界情况测试 =====

    def test_construct_test_args_missing_tool_schema(self):
        """测试缺少 inputSchema 的情况."""
        tool = {"name": "test_tool"}

        result = self.handler.construct_test_args(tool)

        # 应该返回默认参数
        assert "input" in result

    def test_construct_test_args_optional_params(self):
        """测试可选参数不被添加."""
        tool = {
            "name": "test_tool",
            "inputSchema": {
                "properties": {
                    "optional_field": {"type": "string"},
                },
                "required": [],
            },
        }

        result = self.handler.construct_test_args(tool)

        # 可选参数不应该被添加
        assert "optional_field" not in result
