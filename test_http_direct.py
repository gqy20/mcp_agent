#!/usr/bin/env python3
"""独立的 HTTP MCP 直接测试脚本.

直接测试 ai.sitianai.com HTTP MCP 端点。

作者: AI Assistant
日期: 2025-12-17
"""

import asyncio
import json
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.batch_mcp.core.http_mcp_client import HttpMCPClient
import httpx


class DirectHTTPTester:
    """直接 HTTP MCP 测试器"""

    def __init__(self, url: str):
        self.url = url
        self.client = None

    async def test_connection(self):
        """测试基础连接 - 使用 POST 方法"""
        print("🔗 测试基础连接...")

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                # 发送一个简单的 POST 请求测试连接
                test_request = {
                    "jsonrpc": "2.0",
                    "id": 0,
                    "method": "ping",
                    "params": {}
                }

                response = await client.post(self.url, json=test_request, headers={"Content-Type": "application/json"})
                print(f"📡 HTTP 状态码: {response.status_code}")
                print(f"📋 响应头 Content-Type: {response.headers.get('content-type', 'Unknown')}")

                # 即使返回错误，只要有响应就说明连接正常
                if response.status_code in [200, 400, 404]:  # 这些状态码表示服务器正常响应
                    print("✅ 服务器响应正常")
                    return True
                else:
                    print(f"⚠️ 服务器状态码: {response.status_code}")
                    return response.status_code < 500  # 小于500的都算连接正常

        except Exception as e:
            print(f"❌ 连接失败: {str(e)}")
            return False

    async def test_mcp_protocol(self):
        """测试 MCP 协议"""
        print("\n🔬 测试 MCP 协议...")

        # 由于这是 SSE 格式，我们需要手动测试
        headers = {"Content-Type": "application/json"}

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                # 1. 初始化
                init_request = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "clientInfo": {"name": "direct-test", "version": "1.0.0"}
                    }
                }

                print("📡 发送初始化请求...")
                init_response = await client.post(self.url, json=init_request, headers=headers)
                print(f"📊 初始化状态: {init_response.status_code}")

                if init_response.status_code == 200:
                    # 解析 SSE 响应
                    init_result = self._parse_sse_response(init_response.text)
                    if "result" in init_result:
                        print("✅ MCP 初始化成功")
                        print(f"📋 服务器信息: {init_result['result'].get('serverInfo', {})}")
                    else:
                        print(f"❌ MCP 初始化失败: {init_result}")
                        return False

                # 2. 获取工具列表
                tools_request = {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/list",
                    "params": {}
                }

                print("\n📋 获取工具列表...")
                tools_response = await client.post(self.url, json=tools_request, headers=headers)
                print(f"📊 工具列表状态: {tools_response.status_code}")

                if tools_response.status_code == 200:
                    tools_result = self._parse_sse_response(tools_response.text)
                    if "result" in tools_result and "tools" in tools_result["result"]:
                        tools = tools_result["result"]["tools"]
                        print(f"✅ 发现 {len(tools)} 个工具:")

                        for i, tool in enumerate(tools, 1):
                            print(f"  {i}. {tool.get('name', 'Unknown')}")
                            print(f"     描述: {tool.get('description', 'No description')[:100]}...")

                        # 3. 测试工具调用（如果有工具）
                        if tools:
                            await self._test_tool_call(client, self.url, tools[0], headers)

                        return True
                    else:
                        print(f"❌ 获取工具列表失败: {tools_result}")
                        return False
                else:
                    print(f"❌ 工具列表请求失败")
                    return False

            except Exception as e:
                print(f"❌ MCP 协议测试失败: {str(e)}")
                import traceback
                traceback.print_exc()
                return False

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

    async def _test_tool_call(self, client, url, tool, headers):
        """测试工具调用"""
        tool_name = tool.get('name')
        print(f"\n🛠️ 测试工具调用: {tool_name}")

        # 构造测试参数
        test_args = self._construct_test_args(tool)
        print(f"📤 测试参数: {test_args}")

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
        print(f"📊 工具调用状态: {call_response.status_code}")

        if call_response.status_code == 200:
            call_result = self._parse_sse_response(call_response.text)
            print(f"✅ 工具调用完成")
            print(f"📤 调用结果: {json.dumps(call_result, indent=2, ensure_ascii=False)}")
            return True
        else:
            print(f"❌ 工具调用失败")
            return False

    def _construct_test_args(self, tool):
        """构造测试参数"""
        tool_name = tool.get('name', '').lower()

        if 'inputSchema' in tool:
            schema = tool['inputSchema']
            properties = schema.get('properties', {})
            required = schema.get('required', [])

            args = {}
            for prop_name, prop_info in properties.items():
                if prop_name.lower() in ['query', 'message', 'input', 'prompt']:
                    args[prop_name] = "Hello, this is a test message from direct HTTP test"
                elif prop_name.lower() in ['files', 'document']:
                    args[prop_name] = ["test_file.txt"]
                elif prop_name in required:
                    prop_type = prop_info.get('type', 'string')
                    if prop_type == 'string':
                        args[prop_name] = "test_value"
                    elif prop_type == 'number':
                        args[prop_name] = 42
                    elif prop_type == 'boolean':
                        args[prop_name] = True
                    elif prop_type == 'array':
                        args[prop_name] = []

            return args if args else {"query": "Direct HTTP test query"}

        if 'research' in tool_name:
            return {"query": "Test research topic: AI applications in healthcare"}
        else:
            return {"input": "Test input from direct HTTP test"}

    async def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始直接 HTTP MCP 端点测试...")
        print(f"🎯 目标 URL: {self.url}")

        # 测试连接
        if not await self.test_connection():
            print("❌ 基础连接失败，停止测试")
            return False

        # 测试 MCP 协议
        if not await self.test_mcp_protocol():
            print("❌ MCP 协议测试失败")
            return False

        print("\n🎉 所有测试完成！")
        return True


async def main():
    """主函数"""
    url = "http://ai.sitianai.com/api/proxy/mcp?api_key=d4v8kgl26lc8ggculk9g"

    tester = DirectHTTPTester(url)
    success = await tester.run_all_tests()

    if success:
        print("\n✅ 直接 HTTP MCP 测试成功！")
        sys.exit(0)
    else:
        print("\n❌ 直接 HTTP MCP 测试失败！")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())