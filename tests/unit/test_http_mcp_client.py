#!/usr/bin/env python3
"""HTTP MCP 客户端单元测试.

遵循 TDD 原则：先写失败的测试，再实现代码让测试通过。

作者: AI Assistant
日期: 2025-12-17
"""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

# 导入目标类
from src.batch_mcp.core.http_mcp_client import HttpMCPClient


class TestHttpMCPClient:
    """HTTP MCP 客户端测试类"""

    def test_init_with_required_params(self):
        """测试：必需参数初始化"""
        # 这个测试会失败，因为 HttpMCPClient 还不存在
        client = HttpMCPClient(url="https://api.example.com/mcp")

        assert client.url == "https://api.example.com/mcp"
        assert client.headers == {}
        assert client.timeout == 30

    def test_init_with_all_params(self):
        """测试：完整参数初始化"""
        headers = {"Authorization": "Bearer token123"}
        client = HttpMCPClient(
            url="https://api.example.com/mcp", headers=headers, timeout=60
        )

        assert client.url == "https://api.example.com/mcp"
        assert client.headers == headers
        assert client.timeout == 60

    @pytest.mark.asyncio
    async def test_list_tools_success(self):
        """测试：成功获取工具列表"""
        # 模拟 HTTP 响应
        mock_init_response = AsyncMock()
        mock_init_response.status_code = 200
        mock_init_response.raise_for_status = AsyncMock()

        mock_tools_response = AsyncMock()
        mock_tools_response.status_code = 200
        mock_tools_response.raise_for_status = AsyncMock()
        mock_tools_response.json = MagicMock(
            return_value={
                "result": {
                    "tools": [
                        {
                            "name": "model_inference",
                            "description": "Run model inference",
                            "inputSchema": {
                                "type": "object",
                                "properties": {"prompt": {"type": "string"}},
                            },
                        }
                    ]
                }
            }
        )

        with patch("httpx.AsyncClient") as mock_client:
            mock_client_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_client_instance
            mock_client_instance.post.side_effect = [
                mock_init_response,
                mock_tools_response,
            ]

            client = HttpMCPClient(url="https://api.example.com/mcp")
            result = await client.list_tools()

            assert result["success"] is True
            assert len(result["tools"]) == 1
            assert result["tools"][0]["name"] == "model_inference"

    @pytest.mark.asyncio
    async def test_list_tools_http_error(self):
        """测试：获取工具列表时 HTTP 错误"""
        with patch("httpx.AsyncClient") as mock_client:
            mock_client_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_client_instance
            mock_client_instance.post.side_effect = httpx.HTTPError("Connection failed")

            client = HttpMCPClient(url="https://api.example.com/mcp")

            with pytest.raises(httpx.HTTPError):
                await client.list_tools()

    @pytest.mark.asyncio
    async def test_call_tool_success(self):
        """测试：成功调用工具"""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = AsyncMock()
        mock_response.json = MagicMock(
            return_value={
                "result": {"content": [{"type": "text", "text": "Hello, world!"}]}
            }
        )

        with patch("httpx.AsyncClient") as mock_client:
            mock_client_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_client_instance
            mock_client_instance.post.return_value = mock_response

            client = HttpMCPClient(url="https://api.example.com/mcp")
            result = await client.call_tool("model_inference", {"prompt": "Hello"})

            assert result["success"] is True
            assert result["result"]["content"][0]["text"] == "Hello, world!"

    @pytest.mark.asyncio
    async def test_call_tool_with_error_response(self):
        """测试：调用工具收到错误响应"""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = AsyncMock()
        mock_response.json = MagicMock(
            return_value={"error": {"code": -32601, "message": "Tool not found"}}
        )

        with patch("httpx.AsyncClient") as mock_client:
            mock_client_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_client_instance
            mock_client_instance.post.return_value = mock_response

            client = HttpMCPClient(url="https://api.example.com/mcp")
            result = await client.call_tool("nonexistent_tool", {})

            assert result["success"] is False
            assert result["error"]["message"] == "Tool not found"

    def test_headers_are_sent_correctly(self):
        """测试：请求头正确发送"""
        headers = {"Authorization": "Bearer token123", "X-Custom": "value"}
        client = HttpMCPClient(url="https://api.example.com/mcp", headers=headers)

        assert client.headers["Authorization"] == "Bearer token123"
        assert client.headers["X-Custom"] == "value"


# 这些测试目前会失败，因为 HttpMCPClient 类还不存在
# 接下来我们需要实现这个类让测试通过
