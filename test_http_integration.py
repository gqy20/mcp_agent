#!/usr/bin/env python3
"""HTTP MCP 集成测试脚本.

直接测试 HTTP MCP 端点的完整流程。

作者: AI Assistant
日期: 2025-12-17
"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.batch_mcp.core.http_mcp_client import HttpMCPClient
from src.batch_mcp.core.simple_mcp_deployer import SimpleMCPDeployer
from rich import print as rprint


async def test_http_mcp_endpoint(url: str):
    """测试 HTTP MCP 端点的完整流程"""
    rprint(f"🎯 开始测试 HTTP MCP 端点: {url}")

    try:
        # 1. 创建 HTTP MCP 客户端
        rprint("📡 正在创建 HTTP MCP 客户端...")

        client = HttpMCPClient(url)
        rprint("✅ HTTP MCP 客户端创建成功")

        # 2. 测试工具列表获取
        rprint("🔍 正在获取工具列表...")

        tools_result = await client.list_tools()

        if not tools_result['success']:
            rprint(f"❌ 获取工具列表失败: {tools_result.get('error', 'Unknown error')}")
            return False

        tools = tools_result.get('tools', [])
        rprint(f"✅ 成功获取 {len(tools)} 个工具")

        # 3. 显示工具信息
        if tools:
            rprint("🛠️ 可用工具:")
            for i, tool in enumerate(tools, 1):
                tool_name = tool.get('name', 'Unknown')
                tool_desc = tool.get('description', 'No description')
                rprint(f"  {i}. {tool_name}")
                rprint(f"     描述: {tool_desc[:100]}...")

        # 4. 测试工具调用（如果有工具）
        if tools:
            rprint("🧪 正在测试工具调用...")

            # 选择第一个工具进行测试
            test_tool = tools[0]
            tool_name = test_tool.get('name')

            if tool_name:
                # 构造测试参数
                input_schema = test_tool.get('inputSchema', {})
                properties = input_schema.get('properties', {})

                test_args = {}
                for prop_name, prop_info in properties.items():
                    prop_type = prop_info.get('type', 'string')

                    if prop_type == 'string':
                        if 'query' in prop_name.lower() or 'prompt' in prop_name.lower():
                            test_args[prop_name] = "Hello, this is a test message from HTTP MCP integration test"
                        elif prop_name in input_schema.get('required', []):
                            test_args[prop_name] = "test_value"
                    elif prop_type == 'number':
                        test_args[prop_name] = 42
                    elif prop_type == 'boolean':
                        test_args[prop_name] = True
                    elif prop_type == 'array':
                        test_args[prop_name] = []

                # 如果没有构造出参数，使用默认参数
                if not test_args:
                    test_args = {"input": "Test input from HTTP MCP integration test"}

                rprint(f"📤 测试调用工具: {tool_name}")
                rprint(f"📋 测试参数: {test_args}")

                call_result = await client.call_tool(tool_name, test_args)

                if call_result['success']:
                    rprint("✅ 工具调用成功")
                    rprint(f"📤 调用结果: {call_result.get('result')}")
                else:
                    rprint(f"❌ 工具调用失败: {call_result.get('error')}")

        rprint("🎉 HTTP MCP 端点测试完成！")
        return True

    except Exception as e:
        rprint(f"❌ 测试过程发生错误: {str(e)}")
        import traceback
        rprint("📋 错误详情:")
        rprint(traceback.format_exc())
        return False


async def test_deployer_integration():
    """测试部署器集成"""
    rprint("\n🔧 测试部署器 HTTP 集成...")

    url = "http://ai.sitianai.com/api/proxy/mcp?api_key=d4v8kgl26lc8ggculk9g"

    try:
        # 1. 检测部署方法
        deployer = SimpleMCPDeployer()

        method, config = deployer.detect_deployment_method(url)

        rprint(f"📋 检测到部署方法: {method}")
        rprint(f"⚙️ 解析的配置: {config}")

        # 2. 部署客户端
        if method == 'http':
            rprint("🚀 正在部署 HTTP 客户端...")
            client = deployer.deploy_http_mcp(config)
            rprint("✅ HTTP 客户端部署成功")

            # 3. 测试客户端
            success = await test_http_mcp_endpoint(url)
            return success
        else:
            rprint(f"❌ 未预期的部署方法: {method}")
            return False

    except Exception as e:
        rprint(f"❌ 部署器集成测试失败: {str(e)}")
        return False


async def main():
    """主函数"""
    rprint("🚀 HTTP MCP 集成测试开始")
    rprint("=" * 50)

    # 测试URL
    test_url = "http://ai.sitianai.com/api/proxy/mcp?api_key=d4v8kgl26lc8ggculk9g"

    # 直接测试HTTP客户端
    rprint("📊 测试 1: 直接 HTTP 客户端测试")
    success1 = await test_http_mcp_endpoint(test_url)

    # 测试部署器集成
    rprint("\n📊 测试 2: 部署器集成测试")
    success2 = await test_deployer_integration()

    # 总结
    rprint("\n" + "=" * 50)
    rprint("📊 测试结果总结:")
    rprint(f"  直接HTTP客户端测试: {'✅ 通过' if success1 else '❌ 失败'}")
    rprint(f"  部署器集成测试: {'✅ 通过' if success2 else '❌ 失败'}")

    if success1 and success2:
        rprint("🎉 所有测试通过！HTTP MCP 集成成功！")
        return True
    else:
        rprint("❌ 部分测试失败，需要检查实现")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)