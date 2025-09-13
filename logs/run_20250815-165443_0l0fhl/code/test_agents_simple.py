#!/usr/bin/env python3
"""
验证智能代理是否能正确调用大模型的简单测试脚本
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


# 简化的测试工具信息
class MockToolInfo:
    def __init__(self):
        self.name = "测试工具"
        self.author = "测试作者"
        self.description = "这是一个用于测试的MCP工具"
        self.category = "测试"
        self.package_name = "@test/mcp-tool"
        self.requires_api_key = False
        self.api_requirements = []


async def test_agents():
    """测试智能代理的基本功能"""
    print("🔧 测试智能代理功能...")

    try:
        # 测试导入
        print("📦 导入代理模块...")
        from src.agents.test_agent import get_test_generator
        from src.agents.validation_agent import get_validation_agent

        print("✅ 代理模块导入成功")

        # 测试代理初始化
        print("🤖 初始化代理...")
        test_generator = get_test_generator()
        validation_agent = get_validation_agent()

        if test_generator.agent is None:
            print("⚠️ 测试生成代理初始化失败")
            return False

        if validation_agent.agent is None:
            print("⚠️ 验证代理初始化失败")
            return False

        print("✅ 代理初始化成功")

        # 测试用例生成
        print("🎯 测试用例生成...")
        tool_info = MockToolInfo()
        available_tools = [
            {"name": "test_tool", "description": "测试工具"},
            {"name": "echo", "description": "回声测试"},
        ]

        # 这里会调用大模型
        test_cases = test_generator.generate_test_cases(tool_info, available_tools)

        if not test_cases:
            print("⚠️ 未生成任何测试用例")
            return False

        print(f"✅ 成功生成 {len(test_cases)} 个测试用例")
        for i, case in enumerate(test_cases[:3], 1):  # 显示前3个
            print(f"  {i}. {case.name}: {case.description}")

        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback

        print(f"详细错误: {traceback.format_exc()}")
        return False


def main():
    """主函数"""
    print("🚀 开始验证智能代理...")

    result = asyncio.run(test_agents())

    if result:
        print("\n✅ 智能代理验证成功！大模型调用正常工作")
    else:
        print("\n❌ 智能代理验证失败")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
