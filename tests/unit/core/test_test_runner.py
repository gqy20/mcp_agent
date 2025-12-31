"""TestRunner 单元测试.

测试覆盖：
1. run_tests() - 基础测试模式
2. run_tests() - 智能测试模式
3. run_tests() - HTTP MCP 测试
4. run_tests() - 无 tool_info 场景
5. is_http_client() - 检测 HTTP 客户端
6. get_test_runner() - 单例模式
"""

from unittest.mock import AsyncMock, MagicMock, patch

from src.batch_mcp.core.tester import TestConfig
from src.batch_mcp.utils.csv_parser import MCPToolInfo


class TestTestRunner:
    """TestRunner 测试类."""

    def setup_method(self):
        """每个测试前的设置."""
        from src.batch_mcp.core.test_runner import TestRunner

        # 创建 mock tester
        self.mock_tester = MagicMock()

        # 创建独立的 TestRunner 实例用于测试
        self.runner = TestRunner(self.mock_tester)

    # ===== run_tests() 基础测试模式 =====

    def test_run_tests_basic_mode(self):
        """测试基础测试模式."""
        # 准备测试数据
        tool_info = MCPToolInfo(
            name="test-tool",
            url="https://github.com/test/tool",
            author="test",
            github_url="https://github.com/test/tool",
            description="Test tool",
            deployment_method="npx",
            package_name="@test/tool",
        )

        # 创建 mock server_info - STDIO 类型
        mock_server_info = MagicMock()
        mock_server_info.available_tools = [
            {"name": "test_tool", "description": "A test tool"}
        ]
        mock_server_info.client = None  # 非 HTTP 客户端

        # 配置测试为非智能模式
        config = TestConfig(smart_test=False, timeout=30)

        # Mock tester.run_basic_test 返回值
        self.mock_tester.run_basic_test.return_value = (True, [])

        # 执行测试
        success, test_results = self.runner.run_tests(
            tool_info, mock_server_info, config
        )

        # 验证结果
        assert success is True
        assert test_results == []
        self.mock_tester.run_basic_test.assert_called_once_with(mock_server_info, 30)

    # ===== run_tests() 智能测试模式 =====

    @patch("asyncio.run")
    def test_run_tests_smart_mode_with_tool_info(self, mock_asyncio_run):
        """测试智能测试模式 - 有 tool_info."""
        # 准备测试数据
        tool_info = MCPToolInfo(
            name="test-tool",
            url="https://github.com/test/tool",
            author="test",
            github_url="https://github.com/test/tool",
            description="Test tool",
            deployment_method="npx",
            package_name="@test/tool",
        )

        mock_server_info = MagicMock()
        mock_server_info.client = None

        # 配置测试为智能模式
        config = TestConfig(smart_test=True, timeout=30)

        # Mock asyncio.run 和 tester.run_smart_test
        self.mock_tester.run_smart_test = AsyncMock(return_value=(True, []))
        mock_asyncio_run.return_value = (True, [])

        # 执行测试
        success, test_results = self.runner.run_tests(
            tool_info, mock_server_info, config
        )

        # 验证结果
        assert success is True
        assert test_results == []

    # ===== run_tests() HTTP MCP 测试 =====

    @patch("asyncio.run")
    def test_run_tests_http_mcp(self, mock_asyncio_run):
        """测试 HTTP MCP 测试."""
        # 准备测试数据
        tool_info = MCPToolInfo(
            name="http-mcp-tool",
            url="http://localhost:8080/mcp",
            author="test",
            github_url=None,
            description="HTTP MCP tool",
            deployment_method="http",
        )

        # 创建 HTTP server_info
        from src.batch_mcp.core.http_mcp_client import HttpMCPClient

        mock_http_client = MagicMock(spec=HttpMCPClient)
        mock_server_info = MagicMock()
        mock_server_info.client = mock_http_client

        config = TestConfig(smart_test=False, timeout=30)

        # Mock HTTP 测试返回
        mock_asyncio_run.return_value = (
            True,
            {"basic_tests": [], "connection": True, "tools_found": 0, "tools": []},
        )

        # 执行测试
        success, test_results = self.runner.run_tests(
            tool_info, mock_server_info, config
        )

        # 验证结果
        assert success is True
        assert test_results == []

    # ===== run_tests() 无 tool_info 场景 =====

    def test_run_tests_without_tool_info_smart_mode(self):
        """测试无 tool_info 时智能模式回退到基础测试."""
        mock_server_info = MagicMock()
        mock_server_info.client = None

        config = TestConfig(smart_test=True, timeout=30)

        # Mock 基础测试
        self.mock_tester.run_basic_test.return_value = (True, [])

        # 执行测试 - tool_info 为 None
        success, test_results = self.runner.run_tests(None, mock_server_info, config)

        # 验证 - 应该回退到基础测试
        assert success is True
        assert test_results == []
        self.mock_tester.run_basic_test.assert_called_once_with(mock_server_info, 30)

    # ===== is_http_client() 测试 =====

    def test_is_http_client_with_http_client_in_server_info(self):
        """测试检测 HTTP 客户端 - server_info.client 是 HttpMCPClient."""
        from src.batch_mcp.core.http_mcp_client import HttpMCPClient

        mock_server_info = MagicMock()
        mock_http_client = MagicMock(spec=HttpMCPClient)
        mock_server_info.client = mock_http_client

        result = self.runner.is_http_client(mock_server_info)

        assert result is True

    def test_is_http_client_with_direct_http_client(self):
        """测试检测 HTTP 客户端 - 直接传入 HttpMCPClient."""
        from src.batch_mcp.core.http_mcp_client import HttpMCPClient

        mock_http_client = MagicMock(spec=HttpMCPClient)

        result = self.runner.is_http_client(mock_http_client)

        assert result is True

    def test_is_http_client_with_stdio_client(self):
        """测试检测 STDIO 客户端 - 返回 False."""
        mock_server_info = MagicMock()
        mock_server_info.client = None  # 不是 HTTP 客户端

        result = self.runner.is_http_client(mock_server_info)

        assert result is False

    def test_is_http_client_without_client_attribute(self):
        """测试 server_info 没有 client 属性时返回 False."""
        mock_server_info = MagicMock(spec=[])  # 没有 client 属性

        result = self.runner.is_http_client(mock_server_info)

        assert result is False

    # ===== get_test_runner() 单例测试 =====

    def test_get_test_runner_singleton(self):
        """测试 get_test_runner 返回单例."""
        from src.batch_mcp.core.test_runner import get_test_runner

        runner1 = get_test_runner()
        runner2 = get_test_runner()

        # 应该是同一个实例
        assert runner1 is runner2

    # ===== 边界情况测试 =====

    def test_run_tests_with_no_available_tools(self):
        """测试没有可用工具时运行测试."""
        tool_info = MCPToolInfo(
            name="test-tool",
            url="https://github.com/test/tool",
            author="test",
            github_url="https://github.com/test/tool",
            description="Test tool",
            deployment_method="npx",
            package_name="@test/tool",
        )

        mock_server_info = MagicMock()
        mock_server_info.client = None
        mock_server_info.available_tools = []  # 没有可用工具

        config = TestConfig(smart_test=False, timeout=30)

        # Mock 基础测试返回 True（没有工具时也测试通信）
        self.mock_tester.run_basic_test.return_value = (True, [])

        success, test_results = self.runner.run_tests(
            tool_info, mock_server_info, config
        )

        assert success is True
        self.mock_tester.run_basic_test.assert_called_once()
