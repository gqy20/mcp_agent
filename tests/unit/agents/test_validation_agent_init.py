"""Unit tests for ValidationAgent initialization and agent module compatibility."""

import os
from unittest.mock import patch

from agentscope import agent as agentscope_agent

from src.batch_mcp.agents.test_agent import TestCase
from src.batch_mcp.agents.validation_agent import (
    ValidationAgent,
)


# 验证 agentscope.agents 模块不存在 DialogAgent
def test_agentscope_agents_module_no_dialog_agent():
    """验证 agentscope.agents 模块不包含已弃用的 DialogAgent.

    在 agentscope 1.0.9 中，DialogAgent 已不存在。
    """
    try:
        import agentscope.agents  # type: ignore[import-not-found]  # noqa: PLC0415

        assert not hasattr(agentscope.agents, "DialogAgent"), (
            "agentscope.agents 模块不应该包含 DialogAgent"
        )
    except (ModuleNotFoundError, ImportError):
        # agentscope.agents 模块不存在是预期行为
        pass


class TestValidationAgentInitialization:
    """测试 ValidationAgent 初始化的正确性."""

    def test_validation_agent_can_be_imported(self):
        """验证 ValidationAgent 可以被成功导入."""
        assert ValidationAgent is not None

    def test_validation_agent_initialization_without_ai_config(self):
        """验证在没有 AI 配置时，ValidationAgent 能够降级到 fallback 模式."""
        with patch.dict(os.environ, {}, clear=True):
            agent = ValidationAgent()

        assert agent is not None
        # 在没有 AI 配置时，agent 应该为 None（降级模式）
        assert agent.agent is None, "没有 AI 配置时应该降级到 fallback 模式"

    def test_validation_agent_basic_result_analysis(self):
        """验证 fallback 模式下的基础结果分析功能正常工作."""
        agent = ValidationAgent()

        # 创建模拟的测试结果
        test_case = TestCase(
            name="测试用例",
            description="测试描述",
            tool_name="test_tool",
            parameters={"query": "test"},
            expected_type="success",
        )

        response = {"success": True, "data": "test response"}

        # Act - 调用基础分析
        result = agent._basic_result_analysis(  # noqa: SLF001
            test_case,
            response,
            0.5,
        )

        # Assert
        assert isinstance(result, dict), "应该返回字典结果"
        assert "status" in result, "结果应该包含 status 字段"
        assert "confidence" in result, "结果应该包含 confidence 字段"
        assert "analysis" in result, "结果应该包含 analysis 字段"

    def test_agentscope_agents_module_structure(self):
        """验证 agentscope.agents 模块结构.

        标识当前 validation_agent.py 使用了错误的导入路径。
        """
        # 在 agentscope 1.0.9 中，应该使用 ReActAgent 而非 DialogAgent
        assert hasattr(agentscope_agent, "ReActAgent"), (
            "agentscope.agent 模块应该包含 ReActAgent"
        )

        # DialogAgent 在 agentscope 1.0.9 中已被移除
        assert not hasattr(agentscope_agent, "DialogAgent"), (
            "agentscope.agent 模块不应该包含已弃用的 DialogAgent"
        )
