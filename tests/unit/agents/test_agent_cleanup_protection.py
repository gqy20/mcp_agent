"""AI 功能测试 - 确保 AI 模式正常工作.

这些测试确保 TestGeneratorAgent 的 AI 功能正常工作：
1. 可以在没有 AI 配置时创建实例（agent 为 None）
2. 调用 generate_test_cases 时需要 API key
3. ValidationAgent 的基础分析功能正常
4. agentscope 兼容性
"""

import os
from unittest.mock import patch

import pytest
from agentscope import agent as agentscope_agent

from src.batch_mcp.agents.test_agent import TestCase, TestGeneratorAgent
from src.batch_mcp.agents.validation_agent import ValidationAgent
from src.batch_mcp.utils.csv_parser import MCPToolInfo


class TestTestGeneratorAgentAIFunctionality:
    """测试 TestGeneratorAgent AI 功能."""

    def test_can_create_instance_without_ai_config(self):
        """验证没有 AI 配置时可以创建实例（agent 为 None）."""
        with patch.dict(os.environ, {}, clear=True):
            agent = TestGeneratorAgent()

        assert agent is not None
        # 没有 AI 配置时 agent 应该为 None
        assert agent.agent is None

    @pytest.mark.asyncio
    async def test_generate_test_cases_requires_api_key(self):
        """验证 generate_test_cases 需要 API key."""
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
            {
                "name": "search",
                "description": "搜索功能",
                "inputSchema": {"type": "object"},
            }
        ]

        # Act & Assert - 没有 API key 应该抛出异常
        with pytest.raises(RuntimeError, match="AI API key not configured"):
            await agent.generate_test_cases(tool_info, available_tools)


class TestValidationAgentCoreFunctionality:
    """测试 ValidationAgent 核心功能（不依赖 AI 配置）."""

    def test_can_create_instance_without_ai_config(self):
        """验证没有 AI 配置时可以创建实例."""
        with patch.dict(os.environ, {}, clear=True):
            agent = ValidationAgent()

        assert agent is not None
        # 在 fallback 模式下 agent 应该为 None
        assert agent.agent is None

    def test_basic_result_analysis_works_in_fallback_mode(self):
        """验证 fallback 模式下基础结果分析正常工作."""
        agent = ValidationAgent()

        test_case = TestCase(
            name="测试用例",
            description="测试描述",
            tool_name="test_tool",
            parameters={"query": "test"},
            expected_type="success",
        )

        response = {"success": True, "data": "test response"}

        # Act
        result = agent._basic_result_analysis(  # noqa: SLF001
            test_case,
            response,
            0.5,
        )

        # Assert
        assert isinstance(result, dict)
        assert "status" in result
        assert "confidence" in result
        assert "analysis" in result
        # 正常响应应该通过
        assert result["status"] == "pass"

    def test_basic_result_analysis_handles_slow_response(self):
        """验证基础分析能正确处理慢速响应."""
        agent = ValidationAgent()

        test_case = TestCase(
            name="测试用例",
            description="测试描述",
            tool_name="test_tool",
            parameters={"query": "test"},
            expected_type="success",
        )

        response = {"success": True, "data": "response"}

        # 模拟慢速响应（超过30秒）
        result = agent._basic_result_analysis(  # noqa: SLF001
            test_case,
            response,
            35.0,
        )

        # 应该标记为通过但有性能问题
        assert result["status"] == "pass"
        assert len(result["issues"]) > 0
        assert any("响应时间" in issue for issue in result["issues"])


class TestAgentscopeAgentCompatibility:
    """验证 agentscope.agent 模块兼容性."""

    def test_agentscope_agent_module_has_react_agent(self):
        """验证 agentscope.agent 模块包含 ReActAgent."""
        assert hasattr(agentscope_agent, "ReActAgent"), (
            "agentscope.agent 模块应该包含 ReActAgent"
        )

    def test_agentscope_agent_module_no_dialog_agent(self):
        """验证 agentscope.agent 模块不包含已弃用的 DialogAgent."""
        assert not hasattr(agentscope_agent, "DialogAgent"), (
            "agentscope.agent 模块不应该包含已弃用的 DialogAgent"
        )
