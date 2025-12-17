#!/usr/bin/env python3
"""智能代理验证脚本

测试AgentScope集成是否正常工作

作者: AI Assistant
日期: 2025-08-15
"""

import os
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_agentscope_import():
    """测试AgentScope导入"""
    try:
        import agentscope
        from agentscope.agents import ReActAgent
        from agentscope.message import Msg

        print("✅ AgentScope 导入成功")
        return True
    except ImportError as e:
        print(f"❌ AgentScope 导入失败: {e}")
        return False


def test_environment_config():
    """测试环境配置"""
    env_file = project_root / ".env"
    if not env_file.exists():
        print("❌ .env 文件不存在")
        return False

    # 加载环境变量
    from dotenv import load_dotenv

    load_dotenv(env_file)

    # 检查必要的API配置
    required_keys = ["OPENAI_API_KEY", "OPENAI_BASE_URL"]
    missing_keys = []

    for key in required_keys:
        if not os.getenv(key):
            missing_keys.append(key)

    if missing_keys:
        print(f"❌ 缺少环境变量: {', '.join(missing_keys)}")
        return False

    print("✅ 环境配置检查通过")
    return True


def test_agent_initialization():
    """测试代理初始化"""
    try:
        from src.batch_mcp.agents.test_agent import get_test_generator
        from src.batch_mcp.agents.validation_agent import get_validation_agent

        print("🤖 正在初始化测试生成代理...")
        test_gen = get_test_generator()
        print("✅ 测试生成代理初始化成功")

        print("🤖 正在初始化验证代理...")
        validation = get_validation_agent()
        print("✅ 验证代理初始化成功")

        return True

    except Exception as e:
        print(f"❌ 代理初始化失败: {e}")
        return False


def test_basic_csv_parsing():
    """测试CSV解析功能"""
    try:
        from src.batch_mcp.utils.csv_parser import get_mcp_parser

        parser = get_mcp_parser()
        tools = parser.get_all_tools()

        print(f"✅ CSV解析成功，找到 {len(tools)} 个工具")

        # 获取一个简单的工具用于测试
        simple_tools = [t for t in tools[:10] if not t.requires_api_key]
        if simple_tools:
            test_tool = simple_tools[0]
            print(f"📦 测试工具: {test_tool.name} ({test_tool.package_name})")
            return test_tool
        print("⚠️ 未找到免API密钥的工具")
        return None

    except Exception as e:
        print(f"❌ CSV解析失败: {e}")
        return None


def test_smart_test_generation():
    """测试智能测试生成"""
    try:
        # 获取测试工具
        test_tool = test_basic_csv_parsing()
        if not test_tool:
            return False

        from src.batch_mcp.agents.test_agent import get_test_generator

        print("🎯 正在生成智能测试用例...")
        test_gen = get_test_generator()

        # 模拟可用工具列表
        mock_tools = [
            {"name": "test_tool", "description": "测试工具"},
            {"name": "list_tools", "description": "列出所有工具"},
        ]

        test_cases = test_gen.generate_test_cases(test_tool, mock_tools)

        if test_cases:
            print(f"✅ 成功生成 {len(test_cases)} 个测试用例")
            for i, tc in enumerate(test_cases[:3], 1):
                print(f"  {i}. {tc.name}")
            return True
        print("❌ 未生成任何测试用例")
        return False

    except Exception as e:
        print(f"❌ 智能测试生成失败: {e}")
        return False


def main():
    """主验证流程"""
    print("🔍 AgentScope 智能代理验证开始\n")

    results = []

    # 1. 基础导入测试
    print("1️⃣ 测试AgentScope导入...")
    results.append(test_agentscope_import())

    print("\n2️⃣ 测试环境配置...")
    results.append(test_environment_config())

    print("\n3️⃣ 测试CSV数据解析...")
    results.append(test_basic_csv_parsing() is not None)

    # 只有前面的测试都通过才继续
    if all(results):
        print("\n4️⃣ 测试代理初始化...")
        results.append(test_agent_initialization())

        print("\n5️⃣ 测试智能测试生成...")
        results.append(test_smart_test_generation())
    else:
        print("\n❌ 基础测试失败，跳过代理测试")
        results.extend([False, False])

    # 总结
    print("\n📊 验证结果:")
    tests = ["AgentScope导入", "环境配置", "CSV解析", "代理初始化", "智能测试生成"]

    for i, (test_name, result) in enumerate(zip(tests, results), 1):
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {i}. {test_name}: {status}")

    success_count = sum(results)
    total_count = len(results)

    print(f"\n🎯 总体结果: {success_count}/{total_count} 测试通过")

    if success_count == total_count:
        print("🎉 所有测试通过！智能代理功能可以正常使用")
        print("\n💡 可以使用以下命令测试:")
        print("  uv run python -m src.main test-package <包名> --smart")
        print("  uv run python -m src.main test-url <URL> --smart")
    elif success_count >= 3:
        print("⚠️ 部分测试通过，基础功能可用，智能代理可能有问题")
    else:
        print("❌ 多数测试失败，需要检查环境配置")

    return success_count == total_count


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
