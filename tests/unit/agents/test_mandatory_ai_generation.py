"""强制 AI 测试生成功能测试.

这些测试确保系统必须使用 AI 生成测试用例：
1. 有 API key 时使用 AI 生成
2. 没有 API key 时抛出异常（不再使用 fallback）
3. 规则引擎代码已被移除
"""

import os
from unittest.mock import patch

import pytest

from src.batch_mcp.agents.test_agent import TestGeneratorAgent
from src.batch_mcp.utils.csv_parser import MCPToolInfo


class TestMandatoryAIGeneration:
    """测试强制 AI 生成测试用例功能."""

    @pytest.mark.asyncio
    async def test_no_api_key_raises_exception(self):
        """验证没有 API key 时抛出异常."""
        # 清除所有 AI 相关环境变量
        with patch.dict(os.environ, {}, clear=True):
            agent = TestGeneratorAgent()

        tool_info = MCPToolInfo(
            name="测试工具",
            url="https://example.com/test",
            author="test",
            github_url="https://github.com/test/test-tool",
            description="一个测试工具",
            deployment_method="npx",
            category="test",
            package_name="test-tool",
            requires_api_key=False,
            api_requirements=[],
        )

        available_tools = [{"name": "search", "description": "搜索功能"}]

        # Act & Assert - 应该抛出异常
        with pytest.raises(RuntimeError, match="AI API key not configured"):
            await agent.generate_test_cases(tool_info, available_tools)

    def test_fallback_methods_removed(self):
        """验证 fallback 规则引擎方法已被移除."""
        agent = TestGeneratorAgent()

        # 检查 fallback 相关方法不存在
        assert not hasattr(agent, "_generate_fallback_test_cases"), (
            "_generate_fallback_test_cases 应该被移除"
        )
        assert not hasattr(agent, "_generate_smart_parameters"), (
            "_generate_smart_parameters 应该被移除"
        )
        assert not hasattr(agent, "_generate_realistic_parameters"), (
            "_generate_realistic_parameters 应该被移除"
        )
        assert not hasattr(agent, "_generate_edge_case_parameters"), (
            "_generate_edge_case_parameters 应该被移除"
        )
        assert not hasattr(agent, "_generate_boundary_parameters"), (
            "_generate_boundary_parameters 应该被移除"
        )

    @pytest.mark.skipif(
        os.getenv("OPENAI_API_KEY") is None,
        reason="需要 OPENAI_API_KEY 环境变量",
    )
    @pytest.mark.asyncio
    async def test_with_api_key_uses_ai_generation(self):
        """验证有 API key 时使用 AI 生成测试用例."""
        agent = TestGeneratorAgent()

        # 验证 AI Agent 已初始化
        assert agent.agent is not None, "AI Agent 应该已初始化"

        tool_info = MCPToolInfo(
            name="Context7",
            url="https://github.com/example/context7",
            author="test",
            github_url="https://github.com/test/context7",
            description="文档查询工具",
            deployment_method="npx",
            category="documentation",
            package_name="context7-mcp",
            requires_api_key=False,
            api_requirements=[],
        )

        available_tools = [
            {"name": "resolve-library-id", "description": "解析库ID"},
            {"name": "get-library-docs", "description": "获取文档"},
        ]

        # Act
        test_cases = await agent.generate_test_cases(tool_info, available_tools)

        # Assert - 应该返回 AI 生成的测试用例
        assert isinstance(test_cases, list)
        assert len(test_cases) > 0

        # AI 生成的测试用例应该有针对性 - 检查 tool_name 字段
        tool_names_used = [tc.tool_name for tc in test_cases]
        available_tool_names = [tool["name"] for tool in available_tools]
        assert any(
            tool_name in tool_names_used for tool_name in available_tool_names
        ), (
            f"AI 生成的测试用例应该使用可用工具。使用了: {tool_names_used}, 可用: {available_tool_names}"
        )

    @pytest.mark.asyncio
    async def test_agent_initialization_requires_api_key(self):
        """验证 Agent 初始化需要 API key."""
        # 清除所有 AI 相关环境变量
        with patch.dict(os.environ, {}, clear=True):
            agent = TestGeneratorAgent()

        # AI Agent 应该为 None（没有 API key）
        assert agent.agent is None

        # 尝试生成测试用例应该抛出异常
        tool_info = MCPToolInfo(
            name="测试工具",
            url="https://example.com/test",
            author="test",
            github_url="https://github.com/test/test-tool",
            description="一个测试工具",
            deployment_method="npx",
            category="test",
            package_name="test-tool",
            requires_api_key=False,
            api_requirements=[],
        )

        available_tools = [{"name": "search", "description": "搜索功能"}]

        with pytest.raises(RuntimeError, match="AI API key not configured"):
            await agent.generate_test_cases(tool_info, available_tools)
