#!/usr/bin/env python3
"""智能测试生成代理.

基于 AgentScope ReActAgent 的 AI 测试用例生成器
强制使用 AI 生成测试用例，不再支持 fallback 规则引擎

作者: AI Assistant
日期: 2025-08-15
"""

# ruff: noqa: PLR0911,PLW0603

import json
import os
import re
from dataclasses import dataclass
from typing import Any

# 尝试导入 agentscope
try:
    from agentscope import init as agentscope_init
    from agentscope.agent import ReActAgent
    from agentscope.formatter import OpenAIChatFormatter
    from agentscope.message import Msg
    from agentscope.model import DashScopeChatModel, OpenAIChatModel

    AGENTSCOPE_AVAILABLE = True
except ImportError:
    AGENTSCOPE_AVAILABLE = False

from src.batch_mcp.utils.csv_parser import MCPToolInfo


@dataclass
class TestCase:
    """测试用例数据结构."""

    name: str
    description: str
    tool_name: str
    parameters: dict[str, Any]
    expected_type: str  # success, error, specific_content
    expected_result: str | None = None
    priority: str = "normal"  # high, normal, low


class TestGeneratorAgent:
    """智能测试用例生成代理 - 强制 AI 模式."""

    def __init__(self) -> None:
        """初始化测试生成代理.

        如果没有 API key，agent 会保持为 None，在调用 generate_test_cases 时抛出异常。
        """
        self.agent = None
        self._initialize_agent()

    def _initialize_agent(self) -> None:
        """初始化 AgentScope ReActAgent.

        如果没有 API key 或 agentscope 不可用，agent 保持为 None。
        """
        if not AGENTSCOPE_AVAILABLE:
            return

        # 检查是否有 API key
        openai_key = os.getenv("OPENAI_API_KEY")
        dashscope_key = os.getenv("DASHSCOPE_API_KEY")

        if not openai_key and not dashscope_key:
            return

        try:
            # 初始化 agentscope
            agentscope_init(project="mcp_test_generator", logging_level="ERROR")

            # 选择模型
            if openai_key:
                model = OpenAIChatModel(
                    model_name=os.getenv("OPENAI_MODEL", "gpt-4o"),
                    api_key=openai_key,
                )
            else:
                model = DashScopeChatModel(
                    model_name=os.getenv("DASHSCOPE_MODEL", "qwen-plus"),
                    api_key=dashscope_key,
                )

            # 创建 formatter
            formatter = OpenAIChatFormatter()

            # 创建 ReActAgent
            self.agent = ReActAgent(
                name="test_generator",
                sys_prompt=self._get_test_generator_prompt(),
                model=model,
                formatter=formatter,
            )
        except Exception:  # noqa: BLE001 - will check agent is None later
            # 初始化失败，agent 保持为 None
            self.agent = None

    def _get_test_generator_prompt(self) -> str:
        """获取测试生成代理的系统提示词."""
        return """你是一个专业的MCP(Model Context Protocol)工具测试用例生成专家。

你的任务是根据MCP工具的信息生成实用、现实的测试用例，重点验证工具的核心功能是否正常工作。

## 工具信息输入格式:
- 工具名称: [name]
- 作者: [author]
- 描述: [description]
- 类别: [category]
- 包名: [package_name]
- 可用工具列表: [available_tools]
- API密钥需求: [requires_api_key]

## 测试用例生成原则（最多3-4个测试用例）:
1. **基础功能测试** - 验证主要工具能否正常响应（使用常见、有效的参数）
2. **实际使用场景测试** - 测试工具在真实环境下的表现
3. **容错能力测试** - 测试工具对不完美输入的处理（但不必期望严格的错误返回）
4. **边界情况测试**（可选） - 测试工具在特殊情况下是否仍能工作

## 重要测试设计原则:
- **宽松的成功标准**: 只要工具响应了且返回结构化数据，通常认为成功
- **实际的参数选择**: 使用真实存在、常用的参数值（如popular libraries, common queries）
- **合理的期望**: 工具返回相关信息即可，不必完全匹配期望格式
- **避免过度严格**: 错误处理测试应该宽松，工具返回任何信息都比崩溃好

## 具体建议:
- 对于搜索类工具：使用热门、真实存在的搜索词
- 对于文档获取工具：使用知名库/项目ID
- 对于API工具：使用简单、不需要复杂配置的调用
- 错误测试：重点验证工具不会崩溃，而非期望特定错误格式

## 输出格式要求:
请以JSON格式输出测试用例列表，每个测试用例包含:
```json
{
  "test_cases": [
    {
      "name": "测试用例名称",
      "description": "详细描述，说明测试目标",
      "tool_name": "要调用的工具名称",
      "parameters": {"param1": "realistic_value", "param2": "common_value"},
      "expected_type": "success|error|any_response",
      "expected_result": "宽松的期望描述，重点是工具能响应",
      "priority": "high|normal|low"
    }
  ]
}
```

## expected_type说明:
- "success": 期望工具返回有用信息（最常用）
- "any_response": 只要工具响应且不崩溃即可（用于容错测试）
- "error": 仅在明确应该失败的情况使用（如恶意输入）

现在请为给定的MCP工具生成实用、容易通过的测试用例。"""

    def _extract_text_from_response(self, response: Any) -> str:
        """从 ReActAgent 的响应中提取文本内容.

        ReActAgent 可能返回多种格式：
        - 单个 Msg 对象
        - list[Msg]
        - list[dict] (包含 thinking 和 type 字段)
        """
        # 如果是字符串，直接返回
        if isinstance(response, str):
            return response

        # 如果是 Msg 对象，提取 content
        if hasattr(response, "content"):
            content = response.content
            if isinstance(content, str):
                return content
            # 如果 content 是 list（如 ReActAgent 的多步输出）
            if isinstance(content, list):
                # 找到最后一个 type='text' 的项目
                for item in reversed(content):
                    if isinstance(item, dict) and item.get("type") == "text":
                        return str(item.get("thinking", item.get("text", "")))
                # 如果没找到，返回最后一个项目的字符串形式
                if content:
                    return str(content[-1])

        # 如果是 list，处理最后一个元素
        if isinstance(response, list) and response:
            last_item = response[-1]
            if hasattr(last_item, "content"):
                return self._extract_text_from_response(last_item.content)
            # 如果是 dict（ReActAgent 的输出格式）
            if isinstance(last_item, dict):
                if "thinking" in last_item:
                    return str(last_item["thinking"])
                if "text" in last_item:
                    return str(last_item["text"])

        # 默认返回字符串形式
        return str(response)

    async def generate_test_cases(
        self,
        tool_info: MCPToolInfo,
        available_tools: list[dict[str, Any]],
    ) -> list[TestCase]:
        """为指定MCP工具生成测试用例.

        强制使用 AI 生成，没有 fallback 模式。

        Raises:
            RuntimeError: 如果 AI Agent 未初始化（没有 API key）

        """
        # 验证 AI Agent 已初始化
        if self.agent is None:
            msg = (
                "AI API key not configured. "
                "Please set OPENAI_API_KEY or DASHSCOPE_API_KEY environment variable."
            )
            raise RuntimeError(msg)

        # 构建工具信息提示
        tool_info_text = f"""请为以下MCP工具生成测试用例:

工具名称: {tool_info.name}
作者: {tool_info.author}
描述: {tool_info.description}
类别: {tool_info.category}
包名: {tool_info.package_name}
API密钥需求: {"是" if tool_info.requires_api_key else "否"}
API密钥列表: {tool_info.api_requirements if tool_info.requires_api_key else "无"}

可用工具列表:
{json.dumps(available_tools, indent=2, ensure_ascii=False)}

请生成3-4个最重要的测试用例来验证这个MCP工具的核心功能（严格不要超过4个）。优先选择最具代表性的测试场景。
"""

        try:
            # 调用 AI 生成测试用例
            user_msg = Msg("user", tool_info_text, role="user")
            response = await self.agent(user_msg)

            # ReActAgent 返回的格式比较复杂，需要提取最终的文本内容
            response_text = self._extract_text_from_response(response)

            # 解析响应
            test_cases = self._parse_test_cases_response(response_text)

            if test_cases:
                return test_cases

            # AI 解析失败，抛出异常
            msg = (
                "AI failed to generate valid test cases. "
                "Please check your API key and model configuration."
            )
            raise RuntimeError(msg)  # noqa: TRY301 - simple error case

        except Exception as e:
            # 任何错误都抛出异常，不使用 fallback
            if "AI API key not configured" in str(e):
                raise
            msg = (
                f"AI test generation failed: {e}. "
                "Please check your API key and model configuration."
            )
            raise RuntimeError(msg) from e

    def _parse_test_cases_response(self, response: str) -> list[TestCase]:
        """解析 AI 响应并转换为测试用例."""
        test_cases = []

        try:
            # 尝试从响应中提取 JSON
            json_match = re.search(r"```json\s*(.*?)\s*```", response, re.DOTALL)
            json_str = json_match.group(1) if json_match else response

            # 解析 JSON
            data = json.loads(json_str)

            if isinstance(data, dict) and "test_cases" in data:
                for tc_data in data["test_cases"]:
                    test_case = TestCase(
                        name=tc_data.get("name", "未命名测试"),
                        description=tc_data.get("description", ""),
                        tool_name=tc_data.get("tool_name", ""),
                        parameters=tc_data.get("parameters", {}),
                        expected_type=tc_data.get("expected_type", "success"),
                        expected_result=tc_data.get("expected_result"),
                        priority=tc_data.get("priority", "normal"),
                    )
                    test_cases.append(test_case)

        except (json.JSONDecodeError, KeyError):
            # 解析失败，返回空列表
            return []

        return test_cases


# 全局测试生成器实例
_test_generator_instance = None


def get_test_generator() -> TestGeneratorAgent:
    """获取全局测试生成器实例.

    Returns:
        TestGeneratorAgent 实例

    Raises:
        RuntimeError: 如果没有配置 AI API key

    """
    global _test_generator_instance
    if _test_generator_instance is None:
        _test_generator_instance = TestGeneratorAgent()
    return _test_generator_instance
