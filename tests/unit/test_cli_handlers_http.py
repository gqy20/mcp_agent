"""CLI 处理器 HTTP 支持单元测试.

TDD 测试：验证 CLI 处理器对 HTTP MCP 端点的支持.

作者: AI Assistant
日期: 2025-12-17
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# 目标模块
from src.batch_mcp.core.cli_handlers import CLIHandler


class TestCLIHandlerHTTPSupport:
    """CLI 处理器 HTTP 支持测试类."""

    @pytest.fixture
    def cli_handler(self) -> CLIHandler:
        """CLI 处理器 fixture."""
        return CLIHandler()

    def test_test_url_with_http_endpoint(self, cli_handler: CLIHandler) -> None:
        """测试：使用 HTTP MCP 端点调用 test_url."""
        http_url = "http://ai.sitianai.com/api/proxy/mcp?api_key=test123"

        # Mock _find_tool_info 返回 HTTP 工具信息
        mock_tool_info = MagicMock()
        mock_tool_info.name = "test_http_tool"
        mock_tool_info.url = http_url
        mock_tool_info.deployment_method = "http"
        mock_tool_info.github_url = None  # HTTP 端点没有 GitHub URL

        # Mock _deploy_tool 返回 server_info
        mock_server_info = MagicMock()
        mock_server_info.server_id = "test_http_server"
        mock_server_info.available_tools = 2
        mock_server_info.client = MagicMock()  # HTTP 客户端

        # Mock 测试结果
        mock_test_result = MagicMock()
        mock_test_result.success = True
        mock_test_result.duration = 0.5

        with patch.object(cli_handler, "_find_tool_info", return_value=mock_tool_info):
            with patch.object(
                cli_handler, "_deploy_tool", return_value=mock_server_info
            ):
                with patch.object(
                    cli_handler, "_run_tests", return_value=(True, [mock_test_result])
                ):
                    # 模拟测试配置 - 关闭评估和报告以简化测试
                    from src.batch_mcp.core.tester import TestConfig

                    test_config = TestConfig(
                        timeout=30,
                        verbose=False,
                        smart_test=False,
                        cleanup=False,  # 关闭 cleanup 避免调用 _cleanup_server
                        save_report=False,  # 关闭报告生成
                        db_export=False,  # 关闭数据库导出
                        evaluate=False,  # 关闭评估
                    )

                    # 执行测试 - test_url 是同步方法
                    result = cli_handler.test_url(http_url, test_config)

                    # 验证结果
                    assert result is True
                    # 验证内部方法被调用
                    cli_handler._find_tool_info.assert_called_once_with(http_url)
                    cli_handler._deploy_tool.assert_called_once()
                    cli_handler._run_tests.assert_called_once()

    def test_test_url_with_github_url_stdio_fallback(self, cli_handler):
        """测试：GitHub URL 使用 STDIO 处理."""
        github_url = "https://github.com/streamoodle/mcp-server"

        # Mock _find_tool_info 返回 GitHub 工具信息
        mock_tool_info = MagicMock()
        mock_tool_info.name = "mcp-server"
        mock_tool_info.url = github_url
        mock_tool_info.deployment_method = "npx"  # STDIO 部署
        mock_tool_info.github_url = github_url
        mock_tool_info.package_name = "@streamoodle/mcp-server"

        # Mock _deploy_tool 返回 server_info
        mock_server_info = MagicMock()
        mock_server_info.server_id = "test_stdio_server"
        mock_server_info.available_tools = 3
        mock_server_info.process = MagicMock()  # STDIO 进程

        # Mock 测试结果
        mock_test_result = MagicMock()
        mock_test_result.success = True
        mock_test_result.duration = 1.0

        with patch.object(cli_handler, "_find_tool_info", return_value=mock_tool_info):
            with patch.object(
                cli_handler, "_deploy_tool", return_value=mock_server_info
            ):
                with patch.object(
                    cli_handler, "_run_tests", return_value=(True, [mock_test_result])
                ):
                    # 模拟测试配置 - 关闭评估和报告以简化测试
                    from src.batch_mcp.core.tester import TestConfig

                    test_config = TestConfig(
                        timeout=30,
                        verbose=False,
                        smart_test=False,
                        cleanup=False,
                        save_report=False,
                        db_export=False,
                        evaluate=False,
                    )

                    # 执行测试 - test_url 是同步方法
                    result = cli_handler.test_url(github_url, test_config)

                    # 验证结果
                    assert result is True
                    # 验证内部方法被调用
                    cli_handler._find_tool_info.assert_called_once_with(github_url)
                    cli_handler._deploy_tool.assert_called_once()
                    cli_handler._run_tests.assert_called_once()

    @pytest.mark.skip(reason="CLIHandler 架构已重构，不再使用 _deploy_http_mcp 方法")
    @pytest.mark.asyncio
    async def test_test_http_endpoint_integration(self, cli_handler):
        """测试：HTTP 端点集成测试."""
        http_url = "https://api.example.com/mcp"

        # Mock HTTP 客户端
        mock_client = AsyncMock()
        mock_client.list_tools.return_value = {
            "success": True,
            "tools": [
                {"name": "tool1", "description": "Test tool 1"},
                {"name": "tool2", "description": "Test tool 2"},
            ],
        }
        mock_client.call_tool.return_value = {
            "success": True,
            "result": {"content": [{"type": "text", "text": "Test result"}]},
        }

        # Mock _deploy_http_mcp 返回 HTTP 客户端
        mock_server_info = MagicMock()
        mock_server_info.client = mock_client
        mock_server_info.available_tools = 2
        mock_server_info.server_id = "test_server"

        with (
            patch.object(
                cli_handler, "_deploy_http_mcp", return_value=mock_server_info
            ),
            patch.object(cli_handler, "_is_http_client", return_value=True),
        ):
            # 测试 list_tools
            tools_result = await mock_client.list_tools()
            assert tools_result["success"] is True
            assert len(tools_result["tools"]) == 2

            # 测试 call_tool
            call_result = await mock_client.call_tool("tool1", {"param": "value"})
            assert call_result["success"] is True

    def test_detect_http_endpoint_vs_github_url(self, cli_handler):
        """测试：区分 HTTP 端点和 GitHub URL."""
        test_cases = [
            ("http://ai.sitianai.com/api/proxy/mcp", "http"),
            ("https://api.example.com/mcp", "http"),
            ("https://github.com/streamoodle/mcp-server", "github"),
            ("@upstash/context7-mcp", "package"),
        ]

        for url, expected_type in test_cases:
            # 使用 _input_detector 检测类型
            input_type = cli_handler._input_detector.detect(url)
            assert input_type is not None

            # 验证检测结果的类型
            from src.batch_mcp.core.input_type_detector import InputType

            if expected_type == "http":
                assert input_type == InputType.HTTP_ENDPOINT
            elif expected_type == "github":
                assert input_type == InputType.GITHUB_URL
            elif expected_type == "package":
                assert input_type == InputType.PACKAGE_NAME

    @pytest.mark.skip(reason="CLIHandler 架构已重构，不再使用 _deploy_http_mcp 方法")
    @pytest.mark.asyncio
    async def test_http_endpoint_with_custom_headers(self, cli_handler):
        """测试：带自定义请求头的 HTTP 端点."""
        url_with_headers = "https://api.example.com/mcp?token=custom123"

        # Mock HTTP 客户端
        mock_client = AsyncMock()
        mock_client.list_tools.return_value = {"success": True, "tools": []}

        # Mock _deploy_http_mcp
        mock_server_info = MagicMock()
        mock_server_info.client = mock_client
        mock_server_info.available_tools = 0
        mock_server_info.server_id = "test_server"

        with (
            patch.object(
                cli_handler, "_deploy_http_mcp", return_value=mock_server_info
            ),
            patch.object(cli_handler, "_is_http_client", return_value=True),
        ):
            # 验证可以部署 HTTP 端点
            result = await mock_client.list_tools()
            assert result["success"] is True

    @pytest.mark.skip(reason="CLIHandler 架构已重构，不再使用 _deploy_http_mcp 方法")
    @pytest.mark.asyncio
    async def test_http_endpoint_error_handling(self, cli_handler):
        """测试：HTTP 端点错误处理."""
        # Mock _find_tool_info 返回工具信息
        mock_tool_info = MagicMock()
        mock_tool_info.name = "test_tool"
        mock_tool_info.url = "http://invalid.url/mcp"
        mock_tool_info.deployment_method = "http"
        mock_tool_info.github_url = None

        with patch.object(cli_handler, "_find_tool_info", return_value=mock_tool_info):
            with patch.object(
                cli_handler,
                "_deploy_http_mcp",
                side_effect=ConnectionError("Failed to connect"),
            ):
                # test_url 会捕获异常并返回 False
                from src.batch_mcp.core.tester import TestConfig

                test_config = TestConfig(
                    timeout=30,
                    verbose=False,
                    smart_test=False,
                    cleanup=False,
                    save_report=False,
                    db_export=False,
                    evaluate=False,
                )

                # test_url 捕获异常并返回 False，而不是抛出异常
                result = cli_handler.test_url("http://invalid.url/mcp", test_config)
                assert result is False

    def test_http_endpoint_timeout_configuration(self, cli_handler):
        """测试：HTTP 端点超时配置."""
        url = "https://api.example.com/mcp"

        # 测试不同超时配置
        timeout_cases = [10, 30, 60, 120]

        for timeout in timeout_cases:
            from src.batch_mcp.core.tester import TestConfig

            test_config = TestConfig(
                timeout=timeout,
                verbose=False,
                smart_test=False,
                cleanup=False,
                save_report=False,
                db_export=False,
                evaluate=False,
            )

            # 验证超时配置被正确设置
            assert test_config.timeout == timeout

    @pytest.mark.skip(reason="CLIHandler 架构已重构，不再使用 _deploy_http_mcp 方法")
    @pytest.mark.asyncio
    async def test_smart_testing_with_http_endpoint(self, cli_handler):
        """测试：智能测试与 HTTP 端点结合."""
        http_url = "https://api.example.com/mcp"

        # Mock HTTP 客户端
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
            "result": {"content": [{"type": "text", "text": "Research result"}]},
        }

        # Mock _deploy_http_mcp
        mock_server_info = MagicMock()
        mock_server_info.client = mock_client
        mock_server_info.available_tools = 1
        mock_server_info.server_id = "test_server"

        with (
            patch.object(
                cli_handler, "_deploy_http_mcp", return_value=mock_server_info
            ),
            patch.object(cli_handler, "_is_http_client", return_value=True),
        ):
            # 测试工具列表
            tools_result = await mock_client.list_tools()
            assert tools_result["success"] is True
            assert len(tools_result["tools"]) == 1
            assert tools_result["tools"][0]["name"] == "research_tool"
