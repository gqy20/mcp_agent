#!/usr/bin/env python3
"""TestParamsGenerator 单元测试.

测试覆盖：
1. 特殊工具的精确参数映射
2. 工具名称关键词匹配
3. 从 schema 生成参数
4. 边界情况（空输入、未知类型）
"""

from src.batch_mcp.utils.test_params_generator import (
    TestParamsGenerator,
    get_test_params_generator,
)


class TestTestParamsGenerator:
    """TestParamsGenerator 测试类."""

    def setup_method(self):
        """每个测试前的设置."""
        self.generator = TestParamsGenerator()

    def test_special_tool_resolve_library_id(self):
        """测试特殊工具 resolve-library-id 生成正确参数."""
        # Arrange
        tool_info = {"name": "resolve-library-id", "inputSchema": {}}

        # Act
        result = self.generator.generate(tool_info)

        # Assert
        assert result == {"libraryName": "react"}

    def test_special_tool_get_library_docs(self):
        """测试特殊工具 get-library-docs 生成正确参数."""
        # Arrange
        tool_info = {"name": "get-library-docs", "inputSchema": {}}

        # Act
        result = self.generator.generate(tool_info)

        # Assert
        assert result == {"context7CompatibleLibraryID": "/facebook/react"}

    def test_keyword_match_library(self):
        """测试关键词 library 匹配."""
        # Arrange
        tool_info = {"name": "some-library-tool", "inputSchema": {}}

        # Act
        result = self.generator.generate(tool_info)

        # Assert
        assert result == {"library": "react"}

    def test_keyword_match_query(self):
        """测试关键词 query 匹配."""
        # Arrange
        tool_info = {"name": "data-query-tool", "inputSchema": {}}

        # Act
        result = self.generator.generate(tool_info)

        # Assert
        assert result == {"query": "test"}

    def test_keyword_match_search(self):
        """测试关键词 search 匹配."""
        # Arrange
        tool_info = {"name": "smart-search", "inputSchema": {}}

        # Act
        result = self.generator.generate(tool_info)

        # Assert
        assert result == {"query": "example"}

    def test_keyword_match_file(self):
        """测试关键词 file 匹配."""
        # Arrange
        tool_info = {"name": "file-reader", "inputSchema": {}}

        # Act
        result = self.generator.generate(tool_info)

        # Assert
        assert result == {"path": "./test_file.txt"}

    def test_schema_string_property_with_name_keyword(self):
        """测试从 schema 生成字符串参数 - name 关键词."""
        # Arrange
        tool_info = {
            "name": "unknown-tool",
            "inputSchema": {
                "properties": {
                    "userName": {"type": "string"},
                },
                "required": ["userName"],
            },
        }

        # Act
        result = self.generator.generate(tool_info)

        # Assert
        assert result == {"userName": "test"}

    def test_schema_string_property_with_id_keyword(self):
        """测试从 schema 生成字符串参数 - id 关键词."""
        # Arrange
        tool_info = {
            "name": "unknown-tool",
            "inputSchema": {
                "properties": {
                    "userId": {"type": "string"},
                },
                "required": ["userId"],
            },
        }

        # Act
        result = self.generator.generate(tool_info)

        # Assert
        assert result == {"userId": "/test/example"}

    def test_schema_string_property_with_query_keyword(self):
        """测试从 schema 生成字符串参数 - query 关键词."""
        # Arrange
        tool_info = {
            "name": "unknown-tool",
            "inputSchema": {
                "properties": {
                    "searchQuery": {"type": "string"},
                },
                "required": ["searchQuery"],
            },
        }

        # Act
        result = self.generator.generate(tool_info)

        # Assert
        assert result == {"searchQuery": "example query"}

    def test_schema_string_property_with_path_keyword(self):
        """测试从 schema 生成字符串参数 - path 关键词."""
        # Arrange
        tool_info = {
            "name": "unknown-tool",
            "inputSchema": {
                "properties": {
                    "filePath": {"type": "string"},
                },
                "required": ["filePath"],
            },
        }

        # Act
        result = self.generator.generate(tool_info)

        # Assert
        assert result == {"filePath": "./test"}

    def test_schema_string_property_default(self):
        """测试从 schema 生成字符串参数 - 默认值."""
        # Arrange
        tool_info = {
            "name": "unknown-tool",
            "inputSchema": {
                "properties": {
                    "description": {"type": "string"},
                },
                "required": ["description"],
            },
        }

        # Act
        result = self.generator.generate(tool_info)

        # Assert
        assert result == {"description": "test_value"}

    def test_schema_number_property(self):
        """测试从 schema 生成数字参数."""
        # Arrange
        tool_info = {
            "name": "unknown-tool",
            "inputSchema": {
                "properties": {
                    "count": {"type": "number"},
                },
                "required": ["count"],
            },
        }

        # Act
        result = self.generator.generate(tool_info)

        # Assert
        assert result == {"count": 1}

    def test_schema_integer_property(self):
        """测试从 schema 生成整数参数."""
        # Arrange
        tool_info = {
            "name": "unknown-tool",
            "inputSchema": {
                "properties": {
                    "limit": {"type": "integer"},
                },
                "required": ["limit"],
            },
        }

        # Act
        result = self.generator.generate(tool_info)

        # Assert
        assert result == {"limit": 1}

    def test_schema_token_property_special_value(self):
        """测试 token 属性使用特殊值 1000."""
        # Arrange
        tool_info = {
            "name": "unknown-tool",
            "inputSchema": {
                "properties": {
                    "maxTokens": {"type": "integer"},
                },
                "required": ["maxTokens"],
            },
        }

        # Act
        result = self.generator.generate(tool_info)

        # Assert
        assert result == {"maxTokens": 1000}

    def test_schema_boolean_property(self):
        """测试从 schema 生成布尔参数."""
        # Arrange
        tool_info = {
            "name": "unknown-tool",
            "inputSchema": {
                "properties": {
                    "enabled": {"type": "boolean"},
                },
                "required": ["enabled"],
            },
        }

        # Act
        result = self.generator.generate(tool_info)

        # Assert
        assert result == {"enabled": True}

    def test_schema_array_property(self):
        """测试从 schema 生成数组参数."""
        # Arrange
        tool_info = {
            "name": "unknown-tool",
            "inputSchema": {
                "properties": {
                    "items": {"type": "array"},
                },
                "required": ["items"],
            },
        }

        # Act
        result = self.generator.generate(tool_info)

        # Assert
        assert result == {"items": []}

    def test_schema_object_property(self):
        """测试从 schema 生成对象参数."""
        # Arrange
        tool_info = {
            "name": "unknown-tool",
            "inputSchema": {
                "properties": {
                    "options": {"type": "object"},
                },
                "required": ["options"],
            },
        }

        # Act
        result = self.generator.generate(tool_info)

        # Assert
        assert result == {"options": {}}

    def test_empty_tool_info_returns_empty_dict(self):
        """测试空工具信息返回空字典."""
        # Arrange
        tool_info = {}

        # Act
        result = self.generator.generate(tool_info)

        # Assert
        assert result == {}

    def test_missing_input_schema_returns_empty_dict(self):
        """测试缺少 inputSchema 返回空字典."""
        # Arrange
        tool_info = {"name": "some-tool"}

        # Act
        result = self.generator.generate(tool_info)

        # Assert
        assert result == {}

    def test_no_required_properties_returns_empty_dict(self):
        """测试没有 required 属性时返回空字典."""
        # Arrange
        tool_info = {
            "name": "unknown-tool",
            "inputSchema": {
                "properties": {"optional": {"type": "string"}},
                "required": [],
            },
        }

        # Act
        result = self.generator.generate(tool_info)

        # Assert
        assert result == {}

    def test_case_insensitive_keyword_matching(self):
        """测试关键词匹配大小写不敏感."""
        # Arrange
        tool_info = {"name": "MY-LIBRARY-Tool", "inputSchema": {}}

        # Act
        result = self.generator.generate(tool_info)

        # Assert
        assert result == {"library": "react"}

    def test_special_tool_priority_over_keywords(self):
        """测试特殊工具优先级高于关键词匹配."""
        # Arrange - "resolve-library-id" 包含 "library" 关键词，但应使用特殊工具参数
        tool_info = {"name": "resolve-library-id", "inputSchema": {}}

        # Act
        result = self.generator.generate(tool_info)

        # Assert - 应该使用特殊工具的精确参数，而不是关键词参数
        assert result == {"libraryName": "react"}
        assert "library" not in result


class TestTestParamsGeneratorGlobalInstance:
    """全局实例测试."""

    def test_get_test_params_generator_returns_instance(self):
        """测试获取全局实例."""
        # Act
        generator = get_test_params_generator()

        # Assert
        assert generator is not None
        assert isinstance(generator, TestParamsGenerator)

    def test_get_test_params_generator_returns_same_instance(self):
        """测试全局实例单例模式."""
        # Act
        gen1 = get_test_params_generator()
        gen2 = get_test_params_generator()

        # Assert
        assert gen1 is gen2
