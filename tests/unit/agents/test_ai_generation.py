"""AI 测试生成功能测试.

这些测试确保 AI 测试生成功能正常工作：
1. 没有 API key 时使用 fallback（规则引擎）
2. 有 API key 时使用 AI 生成
3. AI Agent 正确创建和调用
"""

import os
from unittest.mock import patch

import pytest

from src.batch_mcp.agents.test_agent import (
    TestCase,
    TestGeneratorAgent,
)
from src.batch_mcp.utils.csv_parser import MCPToolInfo


class TestTestGeneratorAIFallback:
    """测试没有 API key 时的 fallback 行为（确保当前功能不破坏）."""

    def test_no_api_key_uses_fallback(self):
        """验证没有 API key 时使用 fallback 规则引擎."""
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

        available_tools = [
            {"name": "search", "description": "搜索功能"},
        ]

        # Act - 应该使用 fallback，不会尝试调用 AI
        test_cases = agent.generate_test_cases(tool_info, available_tools)

        # Assert - 应该返回 fallback 生成的测试用例
        assert isinstance(test_cases, list)
        assert len(test_cases) > 0
        assert all(isinstance(tc, TestCase) for tc in test_cases)

        # 验证包含基础测试用例
        connectivity_tests = [tc for tc in test_cases if "连通性" in tc.name]
        assert len(connectivity_tests) > 0

    def test_fallback_includes_all_test_types(self):
        """验证 fallback 模式包含所有测试类型."""
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

        available_tools = [{"name": "test_tool", "description": "测试"}]

        test_cases = agent.generate_test_cases(tool_info, available_tools)

        # 验证包含不同类型的测试
        test_names = [tc.name for tc in test_cases]

        # 应该包含基础连通性测试
        assert any("连通性" in name for name in test_names)

        # 应该包含基础功能测试
        assert any("基础功能" in name for name in test_names)

        # 应该包含实际使用场景测试
        assert any("实际使用场景" in name for name in test_names)


class TestTestGeneratorAIGeneration:
    """测试有 API key 时的 AI 生成功能."""

    @pytest.mark.skipif(
        os.getenv("OPENAI_API_KEY") is None,
        reason="需要 OPENAI_API_KEY 环境变量",
    )
    def test_with_api_key_uses_ai_generation(self):
        """验证有 API key 时使用 AI 生成测试用例."""
        # 这个测试需要真实的 API key
        # 仅在有 API key 时运行
        agent = TestGeneratorAgent()

        # 检查 agent 是否有 AI agent 实例
        # 注意：这个测试假设 AI Agent 会被初始化
        # 如果 agent.agent 为 None，说明 AI 初始化失败

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
        test_cases = agent.generate_test_cases(tool_info, available_tools)

        # Assert - 应该返回 AI 生成的测试用例
        assert isinstance(test_cases, list)
        assert len(test_cases) > 0
        assert all(isinstance(tc, TestCase) for tc in test_cases)

        # AI 生成的测试用例应该更有针对性
        # 这里我们检查至少有一个测试用例提到了具体工具
        test_descriptions = " ".join([tc.description for tc in test_cases])
        assert any(
            tool_name in test_descriptions
            for tool in available_tools
            for tool_name in [tool["name"], tool["description"]]
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
