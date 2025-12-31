"""AI 测试生成功能测试.

这些测试确保 AI 测试生成功能正常工作：
1. 有 API key 时使用 AI 生成
2. TestCase 数据结构正确
"""

import os

import pytest

from src.batch_mcp.agents.test_agent import (
    TestCase,
    TestGeneratorAgent,
)
from src.batch_mcp.utils.csv_parser import MCPToolInfo


class TestTestGeneratorAIGeneration:
    """测试有 API key 时的 AI 生成功能."""

    @pytest.mark.skipif(
        os.getenv("OPENAI_API_KEY") is None,
        reason="需要 OPENAI_API_KEY 环境变量",
    )
    @pytest.mark.asyncio
    async def test_with_api_key_uses_ai_generation(self):
        """验证有 API key 时使用 AI 生成测试用例."""
        agent = TestGeneratorAgent()

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
        assert all(isinstance(tc, TestCase) for tc in test_cases)

        # AI 生成的测试用例应该有针对性
        tool_names_used = [tc.tool_name for tc in test_cases]
        available_tool_names = [tool["name"] for tool in available_tools]
        assert any(
            tool_name in tool_names_used for tool_name in available_tool_names
        ), (
            f"AI 生成的测试用例应该使用可用工具。使用了: {tool_names_used}, 可用: {available_tool_names}"
        )

    @pytest.mark.skip("等待 AI 初始化代码实现")
    def test_ai_agent_initialization(self):
        """测试 AI Agent 的初始化逻辑."""
        # 这个测试使用 mock 来验证 AI Agent 的创建
        # 实现后启用此测试


class TestTestCaseStructure:
    """测试 TestCase 数据结构."""

    def test_test_case_creation(self):
        """验证 TestCase 可以正确创建."""
        test_case = TestCase(
            name="测试用例",
            description="测试描述",
            tool_name="test_tool",
            parameters={"query": "test"},
            expected_type="success",
            priority="high",
        )

        assert test_case.name == "测试用例"
        assert test_case.description == "测试描述"
        assert test_case.tool_name == "test_tool"
        assert test_case.parameters == {"query": "test"}
        assert test_case.expected_type == "success"
        assert test_case.priority == "high"

    def test_test_case_optional_fields(self):
        """验证 TestCase 的可选字段."""
        test_case = TestCase(
            name="测试用例",
            description="测试描述",
            tool_name="test_tool",
            parameters={},
            expected_type="success",
        )

        # expected_result 应该默认为 None
        assert test_case.expected_result is None

        # priority 应该默认为 "normal"
        assert test_case.priority == "normal"
