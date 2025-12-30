"""测试参数生成器 - 统一参数生成逻辑.

遵循 Linus 原则：
- 简单的 if-elif 链
- 无嵌套
- 易于扩展

解决 cli_handlers.py 和 tester.py 中的代码重复问题。
"""

from typing import Any, ClassVar


class TestParamsGenerator:
    """测试参数生成器.

    负责为 MCP 工具生成合理的测试参数。
    """

    # 特殊工具的精确参数映射
    SPECIAL_TOOL_PARAMS: ClassVar[dict[str, dict[str, Any]]] = {
        "resolve-library-id": {"libraryName": "react"},
        "get-library-docs": {"context7CompatibleLibraryID": "/facebook/react"},
        "get-library-docs-context7": {"context7CompatibleLibraryID": "/facebook/react"},
    }

    # 复合关键词工具的特殊映射（需要同时包含多个关键词）
    COMPOSITE_KEYWORD_PARAMS: ClassVar[dict[tuple[str, ...], dict[str, Any]]] = {
        ("topic", "research"): {
            "Query": "请帮我分析人工智能在医疗领域的应用前景，包括当前的技术发展状况、潜在的挑战和未来的机遇。"
        },
    }

    # 工具名称关键词到参数的映射
    KEYWORD_PARAMS: ClassVar[dict[str, dict[str, Any]]] = {
        "library": {"library": "react"},
        "query": {"query": "test"},
        "search": {"query": "example"},
        "file": {"path": "./test_file.txt"},
    }

    # 属性名称的启发式映射
    PROPERTY_HEURISTICS: ClassVar[dict[str, str]] = {
        "name": "test",
        "id": "/test/example",
        "query": "example query",
        "path": "./test",
        "topic": "test topic",
        "prompt": "test prompt",
    }

    # 类型默认值
    TYPE_DEFAULTS: ClassVar[dict[str, Any]] = {
        "string": "test_value",
        "number": 1,
        "integer": 1,
        "boolean": True,
        "array": [],
        "object": {},
    }

    @classmethod
    def generate(cls, tool_info: dict[str, Any]) -> dict[str, Any]:
        """生成测试参数.

        Args:
            tool_info: 工具信息字典

        Returns:
            测试参数字典

        """
        tool_name = tool_info.get("name", "")
        input_schema = tool_info.get("inputSchema", {})
        properties = input_schema.get("properties", {})
        required = input_schema.get("required", [])

        # 1. 检查特殊工具
        if tool_name in cls.SPECIAL_TOOL_PARAMS:
            return cls.SPECIAL_TOOL_PARAMS[tool_name].copy()

        # 2. 检查复合关键词匹配（优先级高于单个关键词）
        tool_name_lower = tool_name.lower()
        for keywords, params in cls.COMPOSITE_KEYWORD_PARAMS.items():
            if all(kw in tool_name_lower for kw in keywords):
                return params.copy()

        # 3. 检查单个关键词匹配
        for keyword, params in cls.KEYWORD_PARAMS.items():
            if keyword in tool_name_lower:
                return params.copy()

        # 4. 根据 schema 生成参数
        return cls._generate_from_schema(properties, required)

    @classmethod
    def _generate_from_schema(
        cls, properties: dict, required: list[str]
    ) -> dict[str, Any]:
        """从 schema 生成参数.

        Args:
            properties: 属性定义
            required: 必需属性列表

        Returns:
            生成的参数字典

        """
        arguments = {}

        for prop_name in required:
            prop_info = properties.get(prop_name, {})
            prop_type = prop_info.get("type", "string")

            # 字符串类型的启发式
            if prop_type == "string":
                value = cls._get_string_value(prop_name)
            # 数字类型特殊处理
            elif prop_type in {"number", "integer"}:
                value = (
                    1000
                    if "token" in prop_name.lower()
                    else cls.TYPE_DEFAULTS[prop_type]
                )
            # 其他类型使用默认值
            else:
                value = cls.TYPE_DEFAULTS.get(prop_type, "test_value")

            arguments[prop_name] = value

        return arguments

    @classmethod
    def _get_string_value(cls, prop_name: str) -> str:
        """获取字符串属性的值（基于启发式）.

        Args:
            prop_name: 属性名称

        Returns:
            属性值

        """
        prop_lower = prop_name.lower()

        for keyword, value in cls.PROPERTY_HEURISTICS.items():
            if keyword in prop_lower:
                return value

        return "test_value"


# 全局实例（保持项目风格）
_generator = TestParamsGenerator()


def get_test_params_generator() -> TestParamsGenerator:
    """获取测试参数生成器实例.

    Returns:
        TestParamsGenerator 实例

    """
    return _generator
