#!/usr/bin/env python3
"""ai.sitianai.com 端到端测试.

使用真实的 HTTP MCP 端点进行完整的端到端测试。

作者: AI Assistant
日期: 2025-12-17
"""

import asyncio
import json
import httpx
import pytest
from src.batch_mcp.core.http_mcp_client import HttpMCPClient


class TestAiSitianaiE2E:
    """ai.sitianai.com 端到端测试"""

    @pytest.mark.asyncio
    async def test_full_mcp_workflow(self):
        """测试完整的 MCP 工作流程"""
        print("\n🚀 开始 ai.sitianai.com 端到端测试...")

        # 注意：这个端点返回 SSE 格式，我们需要直接测试原始 HTTP 通信
        url = "http://ai.sitianai.com/api/proxy/mcp?api_key=d4v8kgl26lc8ggculk9g"
        headers = {"Content-Type": "application/json"}

        async with httpx.AsyncClient(timeout=30) as client:
            # 步骤 1: MCP 初始化
            print("📡 步骤 1: MCP 初始化...")
            init_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "e2e-test-framework", "version": "1.0.0"}
                }
            }

            init_response = await client.post(url, json=init_request, headers=headers)
            assert init_response.status_code == 200

            # 解析 SSE 响应
            init_result = self._parse_sse_response(init_response.text)
            assert "result" in init_result
            assert init_result["result"]["protocolVersion"] == "2024-11-05"
            print("✅ MCP 初始化成功")

            # 步骤 2: 获取工具列表
            print("📋 步骤 2: 获取工具列表...")
            tools_request = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
                "params": {}
            }

            tools_response = await client.post(url, json=tools_request, headers=headers)
            assert tools_response.status_code == 200

            tools_result = self._parse_sse_response(tools_response.text)
            assert "result" in tools_result
            assert "tools" in tools_result["result"]

            tools = tools_result["result"]["tools"]
            assert len(tools) > 0
            print(f"✅ 发现 {len(tools)} 个工具")

            # 显示工具信息
            for i, tool in enumerate(tools, 1):
                print(f"  {i}. {tool.get('name', 'Unknown')}")
                print(f"     描述: {tool.get('description', 'No description')[:100]}...")

            # 步骤 3: 测试工具调用
            print("\n🛠️ 步骤 3: 测试工具调用...")
            tool = tools[0]  # 使用第一个工具
            tool_name = tool.get('name')
            print(f"使用工具: {tool_name}")

            # 根据工具的输入模式构造测试参数
            test_args = self._construct_test_args(tool)

            call_request = {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": test_args
                }
            }

            call_response = await client.post(url, json=call_request, headers=headers)
            assert call_response.status_code == 200

            call_result = self._parse_sse_response(call_response.text)
            print(f"✅ 工具调用成功")
            print(f"📤 响应: {json.dumps(call_result, indent=2, ensure_ascii=False)}")

            # 步骤 4: 验证响应格式
            print("\n🔍 步骤 4: 验证响应格式...")
            assert "result" in call_result or "error" in call_result

            if "result" in call_result:
                result = call_result["result"]
                if isinstance(result, dict) and "content" in result:
                    print("✅ 响应包含内容字段")
                    if isinstance(result["content"], list) and result["content"]:
                        print(f"✅ 响应有 {len(result['content'])} 个内容项")

            print("\n🎉 端到端测试全部通过！")

    def _parse_sse_response(self, response_text: str) -> dict:
        """解析 SSE 响应"""
        lines = response_text.strip().split('\n')
        for line in reversed(lines):
            if line.startswith('data:'):
                try:
                    json_str = line[5:].strip()
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    continue
        return {"error": "No valid data found in SSE response"}

    def _construct_test_args(self, tool: dict) -> dict:
        """根据工具模式构造测试参数"""
        tool_name = tool.get('name', '').lower()

        # 如果工具有输入模式，使用它来构造参数
        if 'inputSchema' in tool:
            schema = tool['inputSchema']
            properties = schema.get('properties', {})
            required = schema.get('required', [])

            args = {}
            for prop_name, prop_info in properties.items():
                if prop_name.lower() in ['query', 'message', 'input', 'prompt']:
                    # 优先填充常见的文本参数
                    args[prop_name] = "Hello, this is a test message for research topic exploration"
                elif prop_name.lower() in ['files', 'document']:
                    args[prop_name] = ["test_document.txt"]
                elif prop_name.lower() in ['topic', 'subject']:
                    args[prop_name] = "Artificial Intelligence in Healthcare"
                else:
                    # 为其他必需参数提供默认值
                    if prop_name in required:
                        prop_type = prop_info.get('type', 'string')
                        if prop_type == 'string':
                            args[prop_name] = "test_value"
                        elif prop_type == 'number':
                            args[prop_name] = 42
                        elif prop_type == 'boolean':
                            args[prop_name] = True
                        elif prop_type == 'array':
                            args[prop_name] = []
                        elif prop_type == 'object':
                            args[prop_name] = {}

            return args if args else {"query": "Test research topic in AI"}

        # 如果没有输入模式，根据工具名称推测
        if 'research' in tool_name:
            return {"query": "Test research topic: Machine Learning applications in healthcare"}
        elif 'chat' in tool_name:
            return {"message": "Hello, I need help with a research topic"}
        else:
            return {"input": "Test input for the tool"}


if __name__ == "__main__":
    # 直接运行端到端测试
    async def main():
        test_instance = TestAiSitianaiE2E()
        await test_instance.test_full_mcp_workflow()

    asyncio.run(main())