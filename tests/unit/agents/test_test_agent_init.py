"""Unit tests for TestGeneratorAgent initialization and agent module compatibility."""

import os
from unittest.mock import patch

import pytest

from src.batch_mcp.utils.csv_parser import MCPToolInfo


class TestTestGeneratorAgentInitialization:
    """测试 TestGeneratorAgent 初始化的正确性."""

    def test_agentscope_agent_module_has_react_agent(self):
        """验证 agentscope.agent 模块包含 ReActAgent."""
        from agentscope import agent as agentscope_agent

        assert hasattr(agentscope_agent, "ReActAgent"), (
            "agentscope.agent 模块应该包含 ReActAgent 类"
        )

    def test_agentscope_agent_module_no_dialog_agent(self):
        """验证 agentscope.agent 模块不包含已弃用的 DialogAgent."""
        from agentscope import agent as agentscope_agent

        assert not hasattr(agentscope_agent, "DialogAgent"), (
            "agentscope.agent 模块不应该包含已弃用的 DialogAgent 类"
        )

    def test_test_generator_agent_can_be_imported(self):
        """验证 TestGeneratorAgent 可以被成功导入."""
        from src.batch_mcp.agents.test_agent import TestGeneratorAgent

        assert TestGeneratorAgent is not None

    def test_test_generator_agent_initialization_without_ai_config(self):
        """验证在没有 AI 配置时，TestGeneratorAgent 能够降级到 fallback 模式."""
        with patch.dict(os.environ, {}, clear=True):
            from src.batch_mcp.agents.test_agent import TestGeneratorAgent

            agent = TestGeneratorAgent()

        assert agent is not None
        # 在没有 AI 配置时，agent 应该为 None（降级模式）
        assert agent.agent is None, "没有 AI 配置时应该降级到 fallback 模式"

    def test_test_generator_agent_generate_fallback_test_cases(self):
        """验证 fallback 测试用例生成功能正常工作."""
        from src.batch_mcp.agents.test_agent import TestCase, TestGeneratorAgent

        agent = TestGeneratorAgent()

        # 创建一个模拟的 MCP 工具信息（符合 csv_parser.MCPToolInfo 定义）
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
            {
                "name": "search",
                "description": "搜索功能",
                "inputSchema": {"type": "object"},
            }
        ]

        # Act
        test_cases = agent.generate_test_cases(tool_info, available_tools)

        # Assert
        assert isinstance(test_cases, list), "应该返回测试用例列表"
        assert len(test_cases) > 0, "fallback 模式应该生成测试用例"
        assert all(isinstance(tc, TestCase) for tc in test_cases), (
            "所有测试用例应该是 TestCase 实例"
        )

    def test_test_generator_uses_correct_import_path(self):
        """验证项目使用正确的 agentscope 导入路径."""
        from agentscope.agent import ReActAgent

        assert ReActAgent is not None

    def test_test_generator_old_import_path_fails(self):
        """验证旧的导入路径 agentscope.agents.DialogAgent 无法工作.

        这个测试标识了当前 test_agent.py 中的问题：
        代码使用了 `from agentscope.agents import DialogAgent`，
        但在 agentscope 1.0.9 中，正确的路径是 `from agentscope.agent import ReActAgent`。
        """
        # Arrange & Act & Assert
        with pytest.raises((ModuleNotFoundError, ImportError)):
            # 这是 test_agent.py:123 中使用的错误导入路径
            from agentscope.agents import DialogAgent  # noqa: F401
