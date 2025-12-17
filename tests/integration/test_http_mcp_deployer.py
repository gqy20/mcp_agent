#!/usr/bin/env python3
"""HTTP MCP 部署器集成测试.

TDD 测试：验证 HTTP MCP 部署功能。

作者: AI Assistant
日期: 2025-12-17
"""

from unittest.mock import MagicMock, patch

import pytest

# 目标模块 - 目前这些方法还不存在，测试会失败
# from src.batch_mcp.core.simple_mcp_deployer import SimpleMCPDeployer
# from src.batch_mcp.core.http_mcp_client import HttpMCPClient


class TestHttpMCPDeployer:
    """HTTP MCP 部署器测试类"""

    def test_deploy_http_mcp_creates_client(self):
        """测试：部署 HTTP MCP 创建正确的客户端"""
        deployer = SimpleMCPDeployer()

        config = {
            "url": "https://api.streamoodle.com/mcp",
            "headers": {"Authorization": "Bearer test-token"},
            "timeout": 45,
        }

        with patch(
            "src.batch_mcp.core.http_mcp_client.HttpMCPClient"
        ) as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client

            result = deployer.deploy_http_mcp(config)

            # 验证客户端被正确创建
            mock_client_class.assert_called_once_with(
                url="https://api.streamoodle.com/mcp",
                headers={"Authorization": "Bearer test-token"},
                timeout=45,
            )
            assert result == mock_client

    def test_deploy_http_mcp_with_minimal_config(self):
        """测试：最小配置部署 HTTP MCP"""
        deployer = SimpleMCPDeployer()

        config = {"url": "https://api.example.com/mcp"}

        with patch(
            "src.batch_mcp.core.http_mcp_client.HttpMCPClient"
        ) as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client

            result = deployer.deploy_http_mcp(config)

            # 验证使用默认值
            mock_client_class.assert_called_once_with(
                url="https://api.example.com/mcp", headers={}, timeout=30
            )
            assert result == mock_client

    def test_detect_http_deployment_method(self):
        """测试：检测 HTTP 部署方法"""
        deployer = SimpleMCPDeployer()

        # 测试包含 'http' 的 URL 被识别为 HTTP
        method, _ = deployer.detect_deployment_method(
            github_url="https://api.streamoodle.com/mcp"
        )
        assert method == "http"

        # 测试包含 'api' 的 URL 被识别为 HTTP
        method, _ = deployer.detect_deployment_method(
            github_url="https://github.com/streamoodle/api-endpoint"
        )
        assert method == "http"

    def test_detect_stdio_method_fallback(self):
        """测试：STDIO 方法检测回退"""
        deployer = SimpleMCPDeployer()

        # 测试不包含 HTTP 关键词的 URL 回退到 STDIO
        method, _ = deployer.detect_deployment_method(
            github_url="https://github.com/streamoodle/normal-package"
        )
        assert method in ["npx", "uvx"]  # 现有的 STDIO 方法

    def test_deploy_http_mcp_missing_url_raises_error(self):
        """测试：缺少 URL 配置时抛出错误"""
        deployer = SimpleMCPDeployer()

        config = {"headers": {"Auth": "token"}}  # 缺少 url

        with pytest.raises(KeyError, match="url"):
            deployer.deploy_http_mcp(config)


# 端到端集成测试
class TestHttpMCPEndToEnd:
    """HTTP MCP 端到端测试"""

    @pytest.mark.asyncio
    async def test_streamoodle_http_integration(self):
        """测试：streamoodle HTTP 集成"""
        deployer = SimpleMCPDeployer()

        # 模拟 streamoodle 配置
        config = {
            "url": "https://api.streamoodle.com/mcp",
            "headers": {"Authorization": "Bearer test-streamoodle-token"},
            "timeout": 60,
        }

        with patch(
            "src.batch_mcp.core.http_mcp_client.HttpMCPClient"
        ) as mock_client_class:
            # 模拟 HTTP 客户端行为
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client

            # 模拟 list_tools 返回值
            mock_client.list_tools = MagicMock()
            mock_client.list_tools.return_value = {
                "success": True,
                "tools": [
                    {
                        "name": "model_inference",
                        "description": "Run AI model inference",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "prompt": {"type": "string"},
                                "max_tokens": {"type": "integer", "default": 100},
                            },
                        },
                    }
                ],
            }

            # 部署客户端
            client = deployer.deploy_http_mcp(config)

            # 验证部署成功
            assert client is not None
            mock_client_class.assert_called_once()

            # 测试获取工具列表
            tools_result = await client.list_tools()
            assert tools_result["success"] is True
            assert len(tools_result["tools"]) == 1
            assert tools_result["tools"][0]["name"] == "model_inference"

    @pytest.mark.asyncio
    async def test_http_vs_stdio_client_compatibility(self):
        """测试：HTTP 客户端与 STDIO 客户端接口兼容"""
        deployer = SimpleMCPDeployer()

        # 模拟 HTTP 客户端
        with patch(
            "src.batch_mcp.core.http_mcp_client.HttpMCPClient"
        ) as mock_http_class:
            mock_http_client = MagicMock()
            mock_http_client.list_tools.return_value = {"success": True, "tools": []}
            mock_http_client.call_tool.return_value = {"success": True, "result": "ok"}
            mock_http_class.return_value = mock_http_client

            http_client = deployer.deploy_http_mcp({"url": "https://api.test.com/mcp"})

            # 模拟 STDIO 客户端 (现有实现)
            with patch(
                "src.batch_mcp.core.simple_mcp_deployer.SimpleMCPCommunicator"
            ) as mock_stdio_class:
                mock_stdio_client = MagicMock()
                mock_stdio_class.send_request.return_value = {
                    "success": True,
                    "data": {"tools": []},
                }
                mock_stdio_class.return_value = mock_stdio_client

                stdio_client = deployer._deploy_npx({"package_name": "test-package"})

                # 验证两种客户端都有相同的接口
                assert hasattr(http_client, "list_tools")
                assert hasattr(http_client, "call_tool")
                assert hasattr(stdio_client, "send_request")

                # HTTP 客户端应该是异步方法
                import inspect

                assert inspect.iscoroutinefunction(http_client.list_tools)
                assert inspect.iscoroutinefunction(http_client.call_tool)


# 这些测试目前会失败，因为相关方法还不存在
# 接下来我们需要实现这些方法让测试通过
