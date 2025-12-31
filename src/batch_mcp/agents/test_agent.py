#!/usr/bin/env python3
"""智能测试生成代理.

基于规则的测试用例生成器
根据MCP工具的功能和参数自动生成测试用例

作者: AI Assistant
日期: 2025-08-15
"""

# ruff: noqa: PLR0911,PLW0603

from dataclasses import dataclass
from typing import Any

from src.batch_mcp.utils.csv_parser import MCPToolInfo

# 常量定义
_MAX_FALLBACK_TEST_CASES = 15


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
    """智能测试用例生成代理."""

    def __init__(self) -> None:
        """初始化测试生成代理."""
        self.agent = None

    def generate_test_cases(
        self,
        tool_info: MCPToolInfo,
        available_tools: list[dict[str, Any]],
    ) -> list[TestCase]:
        """为指定MCP工具生成测试用例.

        使用基于规则的模式生成测试用例。
        """
        return self._generate_fallback_test_cases(tool_info, available_tools)

    def _generate_fallback_test_cases(
        self,
        tool_info: MCPToolInfo,
        available_tools: list[dict[str, Any]],
    ) -> list[TestCase]:
        """生成备选的基础测试用例 - 通用版，适用于所有MCP工具."""
        test_cases = []

        # 基础连通性测试
        test_cases.append(
            TestCase(
                name="基础连通性测试",
                description="验证MCP工具是否正常响应",
                tool_name="tools/list",
                parameters={},
                expected_type="success",
                priority="high",
            ),
        )

        # 为每个可用工具生成针对性的测试用例
        for tool in available_tools:
            tool_name = tool.get("name", "unknown")
            tool.get("description", "")

            # 生成基础功能测试用例
            test_cases.append(
                TestCase(
                    name=f"{tool_name}基础功能测试",
                    description=f"测试{tool_name}工具的基础功能是否正常工作",
                    tool_name=tool_name,
                    parameters=self._generate_smart_parameters(tool),
                    expected_type="success",
                    priority="high",
                ),
            )

            # 生成实际使用场景测试用例
            test_cases.append(
                TestCase(
                    name=f"{tool_name}实际使用场景测试",
                    description=f"模拟真实使用场景测试{tool_name}工具的实用性",
                    tool_name=tool_name,
                    parameters=self._generate_realistic_parameters(tool),
                    expected_type="success",
                    priority="normal",
                ),
            )

            # 生成容错能力测试用例
            test_cases.append(
                TestCase(
                    name=f"{tool_name}容错能力测试",
                    description=f"测试{tool_name}工具对异常输入的处理能力",
                    tool_name=tool_name,
                    parameters=self._generate_edge_case_parameters(tool),
                    expected_type="any_response",  # 容错测试，只要响应即可
                    priority="normal",
                ),
            )

            # 生成边界情况测试用例
            test_cases.append(
                TestCase(
                    name=f"{tool_name}边界情况测试",
                    description=f"测试{tool_name}工具在边界条件下的表现",
                    tool_name=tool_name,
                    parameters=self._generate_boundary_parameters(tool),
                    expected_type="success",
                    priority="low",
                ),
            )

        # API密钥配置检查
        if tool_info.requires_api_key and tool_info.api_requirements:
            test_cases.append(
                TestCase(
                    name="API密钥配置检查",
                    description="验证所需的API密钥是否正确配置",
                    tool_name="config_check",
                    parameters={"api_keys": tool_info.api_requirements},
                    expected_type="success",
                    priority="high",
                ),
            )

        # 确保测试用例数量合理（限制最多15个）
        if len(test_cases) > _MAX_FALLBACK_TEST_CASES:
            # 保留高优先级的测试用例
            test_cases = sorted(
                test_cases,
                key=lambda x: (x.priority != "high", x.priority != "normal"),
            )
            test_cases = test_cases[:_MAX_FALLBACK_TEST_CASES]

        return test_cases

    def _generate_smart_parameters(self, tool: dict[str, Any]) -> dict[str, Any]:
        """为工具生成智能的基础参数 - 适用于所有MCP工具."""
        tool_name = tool.get("name", "").lower()
        tool.get("description", "").lower()

        # 根据工具类型生成基础参数
        if any(keyword in tool_name for keyword in ["search", "find", "query"]):
            return {"query": "test"}
        if any(
            keyword in tool_name for keyword in ["get", "fetch", "retrieve", "read"]
        ):
            return {"id": "test"}
        if any(keyword in tool_name for keyword in ["create", "add", "new", "make"]):
            return {"name": "test"}
        if any(keyword in tool_name for keyword in ["update", "edit", "modify"]):
            return {"id": "test", "data": {"field": "value"}}
        if any(keyword in tool_name for keyword in ["delete", "remove"]):
            return {"id": "test"}
        if any(keyword in tool_name for keyword in ["list", "enum", "show"]):
            return {"limit": 5}
        if any(keyword in tool_name for keyword in ["resolve", "identify", "lookup"]):
            return {"target": "test"}
        return {"value": "test"}

    def _generate_realistic_parameters(self, tool: dict[str, Any]) -> dict[str, Any]:
        """生成实际使用场景的参数 - 使用真实的常用值."""
        tool_name = tool.get("name", "").lower()
        tool_description = tool.get("description", "").lower()

        # 根据工具类型生成实际场景参数
        if any(keyword in tool_name for keyword in ["search", "find", "query"]):
            # 常见搜索词
            return {"query": "react", "limit": 10}
        if any(
            keyword in tool_name for keyword in ["get", "fetch", "retrieve", "read"]
        ):
            # 常见ID格式
            if "library" in tool_description:
                return {"context7CompatibleLibraryID": "/facebook/react"}
            if "package" in tool_description:
                return {"packageName": "react"}
            return {"id": "react"}
        if any(keyword in tool_name for keyword in ["create", "add", "new", "make"]):
            # 实际创建参数
            return {
                "name": "example-project",
                "description": "示例项目",
                "tags": ["test"],
            }
        if any(keyword in tool_name for keyword in ["list", "enum", "show"]):
            # 实际分页参数
            return {"limit": 20, "offset": 0, "sort": "name"}
        if any(keyword in tool_name for keyword in ["resolve", "identify", "lookup"]):
            # 实际解析参数
            if "library" in tool_description:
                return {"libraryName": "react"}
            return {"target": "react"}
        return {"input": "realistic-data", "options": {"optimized": True}}

    def _generate_edge_case_parameters(self, tool: dict[str, Any]) -> dict[str, Any]:
        """生成容错测试的边界参数."""
        tool_name = tool.get("name", "").lower()

        # 根据工具类型生成边界参数
        if any(keyword in tool_name for keyword in ["search", "find", "query"]):
            return {"query": "", "limit": 0}  # 空查询
        if any(
            keyword in tool_name for keyword in ["get", "fetch", "retrieve", "read"]
        ):
            return {"id": "nonexistent-id-12345"}  # 不存在的ID
        if any(keyword in tool_name for keyword in ["create", "add", "new", "make"]):
            return {"name": "", "data": None}  # 空数据
        if any(keyword in tool_name for keyword in ["list", "enum", "show"]):
            return {"limit": 999999}  # 极大值
        if any(keyword in tool_name for keyword in ["resolve", "identify", "lookup"]):
            return {"target": "unknown-target-12345"}  # 未知目标
        return {"invalid": "data"}  # 无效数据

    def _generate_boundary_parameters(self, tool: dict[str, Any]) -> dict[str, Any]:
        """生成边界测试参数."""
        tool_name = tool.get("name", "").lower()

        # 根据工具类型生成边界参数
        if any(keyword in tool_name for keyword in ["search", "find", "query"]):
            return {"query": "a", "limit": 1}  # 最小值
        if any(
            keyword in tool_name for keyword in ["get", "fetch", "retrieve", "read"]
        ):
            return {"id": "a"}  # 最短ID
        if any(keyword in tool_name for keyword in ["create", "add", "new", "make"]):
            return {"name": "a"}  # 最短名称
        if any(keyword in tool_name for keyword in ["list", "enum", "show"]):
            return {"limit": 1, "offset": 0}  # 最小分页
        if any(keyword in tool_name for keyword in ["resolve", "identify", "lookup"]):
            return {"target": "a"}  # 最短目标
        return {"input": "minimal"}  # 最小输入


# 全局测试生成器实例
_test_generator_instance = None


def get_test_generator() -> TestGeneratorAgent:
    """获取全局测试生成器实例."""
    global _test_generator_instance
    if _test_generator_instance is None:
        _test_generator_instance = TestGeneratorAgent()
    return _test_generator_instance
