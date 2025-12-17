"""HTTP MCP 客户端实现.

基于 TDD 原则实现，让单元测试通过.

作者: AI Assistant
日期: 2025-12-17
"""

from __future__ import annotations

import json
from typing import Any

import httpx


class HttpMCPClient:
    """简化的 HTTP MCP 客户端 - 无状态，每次调用新建连接."""

    def __init__(
        self, url: str, headers: dict[str, str] | None = None, timeout: float = 30
    ) -> None:
        """初始化 HTTP MCP 客户端."""
        self.url = url
        self.headers = headers or {}
        self.timeout = timeout

    async def list_tools(self) -> dict[str, Any]:
        """获取工具列表."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            # MCP 标准初始化请求
            init_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "mcp-test-framework", "version": "1.0.0"},
                },
            }

            init_response = await client.post(
                self.url, json=init_request, headers=self.headers
            )
            init_response.raise_for_status()

            # 获取工具列表
            tools_request = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
                "params": {},
            }

            tools_response = await client.post(
                self.url, json=tools_request, headers=self.headers
            )
            tools_response.raise_for_status()

            # 尝试解析响应，支持标准JSON和SSE格式
            try:
                result = tools_response.json()
                return {
                    "success": True,
                    "tools": result.get("result", {}).get("tools", []),
                    "raw": result,
                }
            except json.JSONDecodeError:
                # 如果JSON解析失败，尝试SSE格式
                sse_result = self._parse_sse_response(tools_response.text)
                if "result" in sse_result:
                    return {
                        "success": True,
                        "tools": sse_result.get("result", {}).get("tools", []),
                        "raw": sse_result,
                    }
                return {
                    "success": False,
                    "error": f"无法解析响应: {sse_result}",
                    "raw": tools_response.text,
                }

    async def call_tool(
        self, name: str, arguments: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """调用工具."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            call_request = {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {"name": name, "arguments": arguments or {}},
            }

            response = await client.post(
                self.url, json=call_request, headers=self.headers
            )
            response.raise_for_status()

            # 尝试解析响应，支持标准JSON和SSE格式
            try:
                result = response.json()
                return {
                    "success": "error" not in result,
                    "result": result.get("result"),
                    "error": result.get("error"),
                    "raw": result,
                }
            except json.JSONDecodeError:
                # 如果JSON解析失败，尝试SSE格式
                sse_result = self._parse_sse_response(response.text)
                if "error" in sse_result:
                    return {
                        "success": False,
                        "error": sse_result["error"],
                        "raw": sse_result,
                    }
                return {
                    "success": True,
                    "result": sse_result.get("result"),
                    "raw": sse_result,
                }

    def _parse_sse_response(self, response_text: str) -> dict:
        """解析 SSE 响应格式."""
        lines = response_text.strip().split("\n")
        for line in reversed(lines):
            if line.startswith("data:"):
                try:
                    json_str = line[5:].strip()
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    continue
        return {"error": "No valid data found in SSE response"}
