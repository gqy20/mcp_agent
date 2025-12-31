#!/usr/bin/env python3
"""配置自适应功能的单元测试

测试根据不同输入类型自动调整测试配置的功能
"""

from src.batch_mcp.core.cli_handlers import CLIHandler
from src.batch_mcp.core.input_type_detector import InputType
from src.batch_mcp.core.tester import TestConfig


class TestConfigAdaptation:
    """测试配置自适应功能"""

    def setup_method(self):
        """每个测试方法前的设置"""
        self.handler = CLIHandler()
        self.base_config = TestConfig(
            timeout=600,
            verbose=False,
            smart_test=True,
            cleanup=True,
            save_report=True,
            db_export=True,
            evaluate=True,
        )

    def test_adapt_config_for_http_endpoint(self):
        """测试HTTP端点的配置适配"""
        adapted = self.handler._adapt_config_for_input_type(
            InputType.HTTP_ENDPOINT, self.base_config
        )

        # HTTP端点特定的适配
        assert adapted.timeout == 300, "HTTP端点应该有较短的超时时间"
        assert adapted.evaluate == True, "HTTP端点应该默认启用评估"
        assert adapted.cleanup == True, "HTTP端点应该启用清理"

        # 其他配置应该保持不变
        assert adapted.verbose == self.base_config.verbose
        assert adapted.smart_test == self.base_config.smart_test
        assert adapted.save_report == self.base_config.save_report
        assert adapted.db_export == self.base_config.db_export

    def test_adapt_config_for_github_url(self):
        """测试GitHub URL的配置适配"""
        adapted = self.handler._adapt_config_for_input_type(
            InputType.GITHUB_URL, self.base_config
        )

        # GitHub URL特定的适配
        assert adapted.timeout == 600, "GitHub URL应该保持较长超时时间"

        # 其他配置应该保持不变
        assert adapted.verbose == self.base_config.verbose
        assert adapted.smart_test == self.base_config.smart_test
        assert adapted.cleanup == self.base_config.cleanup
        assert adapted.save_report == self.base_config.save_report
        assert adapted.db_export == self.base_config.db_export
        assert adapted.evaluate == self.base_config.evaluate

    def test_adapt_config_for_package_name(self):
        """测试包名的配置适配"""
        adapted = self.handler._adapt_config_for_input_type(
            InputType.PACKAGE_NAME, self.base_config
        )

        # 包名特定的适配
        assert adapted.timeout == 600, "包名应该有足够的时间进行安装和测试"

        # 其他配置应该保持不变
        assert adapted.verbose == self.base_config.verbose
        assert adapted.smart_test == self.base_config.smart_test
        assert adapted.cleanup == self.base_config.cleanup
        assert adapted.save_report == self.base_config.save_report
        assert adapted.db_export == self.base_config.db_export
        assert adapted.evaluate == self.base_config.evaluate

    def test_adapt_config_for_search_query(self):
        """测试搜索查询的配置适配"""
        adapted = self.handler._adapt_config_for_input_type(
            InputType.SEARCH_QUERY, self.base_config
        )

        # 搜索查询不需要特殊适配
        assert adapted.timeout == self.base_config.timeout
        assert adapted.verbose == self.base_config.verbose
        assert adapted.smart_test == self.base_config.smart_test
        assert adapted.cleanup == self.base_config.cleanup
        assert adapted.save_report == self.base_config.save_report
        assert adapted.db_export == self.base_config.db_export
        assert adapted.evaluate == self.base_config.evaluate

    def test_config_immutability(self):
        """测试配置的不变性 - 原配置不应该被修改"""
        original_timeout = self.base_config.timeout
        original_evaluate = self.base_config.evaluate

        # 适配配置
        adapted = self.handler._adapt_config_for_input_type(
            InputType.HTTP_ENDPOINT, self.base_config
        )

        # 原配置应该保持不变
        assert self.base_config.timeout == original_timeout
        assert self.base_config.evaluate == original_evaluate

        # 适配后的配置应该不同
        assert adapted.timeout != self.base_config.timeout

    def test_adaptation_with_different_base_configs(self):
        """测试不同基础配置的适配"""
        # 测试不同的基础配置
        base_configs = [
            TestConfig(timeout=100, evaluate=False, smart_test=False),
            TestConfig(timeout=1200, evaluate=True, smart_test=True),
            TestConfig(timeout=300, evaluate=False, smart_test=True),
        ]

        for base_config in base_configs:
            adapted = self.handler._adapt_config_for_input_type(
                InputType.HTTP_ENDPOINT, base_config
            )

            # HTTP端点的超时时间应该被限制在300秒
            assert adapted.timeout <= 300, f"超时时间应该被限制: {adapted.timeout}"

            # HTTP端点应该强制启用评估
            assert adapted.evaluate == True, "HTTP端点应该强制启用评估"

    def test_edge_case_configs(self):
        """测试边界情况的配置"""
        # 极小的超时时间
        small_timeout_config = TestConfig(timeout=30, evaluate=False)
        adapted = self.handler._adapt_config_for_input_type(
            InputType.HTTP_ENDPOINT, small_timeout_config
        )
        assert adapted.timeout == 30, "极小超时时间应该保持原值"

        # 极大的超时时间
        large_timeout_config = TestConfig(timeout=3600, evaluate=False)
        adapted = self.handler._adapt_config_for_input_type(
            InputType.HTTP_ENDPOINT, large_timeout_config
        )
        assert adapted.timeout == 300, "极大超时时间应该被限制到300秒"

    def test_additional_attributes_preservation(self):
        """测试额外属性的保持"""
        # 创建带有额外属性的配置
        extended_config = TestConfig(
            timeout=600,
            verbose=False,
            smart_test=True,
            cleanup=True,
            save_report=True,
            db_export=True,
            evaluate=True,
        )

        # 添加额外的测试属性
        extended_config.custom_attr = "test_value"
        extended_config.max_smart_tests = 5

        adapted = self.handler._adapt_config_for_input_type(
            InputType.HTTP_ENDPOINT, extended_config
        )

        # 额外属性应该被保持
        assert hasattr(adapted, "custom_attr")
        assert adapted.custom_attr == "test_value"
        assert hasattr(adapted, "max_smart_tests")

        # 如果有max_smart_tests属性，HTTP端点应该限制为3
        if hasattr(adapted, "max_smart_tests"):
            assert adapted.max_smart_tests == 3, "HTTP端点的智能测试数量应该被限制"

    def test_unknown_input_type_handling(self):
        """测试未知输入类型的处理"""
        adapted = self.handler._adapt_config_for_input_type(
            InputType.UNKNOWN, self.base_config
        )

        # 未知类型不应该改变任何配置
        assert adapted.timeout == self.base_config.timeout
        assert adapted.evaluate == self.base_config.evaluate
        assert adapted.verbose == self.base_config.verbose
        assert adapted.smart_test == self.base_config.smart_test
        assert adapted.cleanup == self.base_config.cleanup
        assert adapted.save_report == self.base_config.save_report
        assert adapted.db_export == self.base_config.db_export

    def test_multiple_adaptation_calls(self):
        """测试多次适配调用的幂等性"""
        # 第一次适配
        adapted1 = self.handler._adapt_config_for_input_type(
            InputType.HTTP_ENDPOINT, self.base_config
        )

        # 第二次适配
        adapted2 = self.handler._adapt_config_for_input_type(
            InputType.HTTP_ENDPOINT, adapted1
        )

        # 结果应该相同（幂等性）
        assert adapted1.timeout == adapted2.timeout
        assert adapted1.evaluate == adapted2.evaluate
        assert adapted1.cleanup == adapted2.cleanup

    def test_configuration_context_validation(self):
        """测试配置上下文的有效性"""
        # 测试所有输入类型的适配
        for input_type in InputType:
            adapted = self.handler._adapt_config_for_input_type(
                input_type, self.base_config
            )

            # 适配后的配置应该仍然是有效的TestConfig
            assert isinstance(adapted, TestConfig), (
                f"适配结果应该是TestConfig实例: {input_type}"
            )
            assert hasattr(adapted, "timeout"), "适配结果应该有timeout属性"
            assert adapted.timeout > 0, "超时时间应该大于0"

    def test_optimization_rules_documentation(self):
        """测试优化规则的可文档性 - 确保所有优化规则都有明确的原因"""
        adaptation_rules = {
            InputType.HTTP_ENDPOINT: {
                "expected_changes": {
                    "timeout": "min(300, original)",
                    "evaluate": True,
                    "cleanup": True,
                },
                "reason": "HTTP端点通常响应更快，需要启用评估确保质量",
            },
            InputType.GITHUB_URL: {
                "expected_changes": {
                    "timeout": "max(300, original)",
                },
                "reason": "GitHub项目可能需要克隆和构建，需要更长时间",
            },
            InputType.PACKAGE_NAME: {
                "expected_changes": {
                    "timeout": "max(180, original)",
                },
                "reason": "包安装可能需要时间，确保有足够时间完成",
            },
        }

        # 验证每个输入类型的适配规则
        for input_type, rules in adaptation_rules.items():
            adapted = self.handler._adapt_config_for_input_type(
                input_type, self.base_config
            )

            # 验证预期的变化
            expected = rules["expected_changes"]
            for attr, expected_value in expected.items():
                actual_value = getattr(adapted, attr)

                if expected_value == "min(300, original)":
                    assert actual_value == min(300, getattr(self.base_config, attr))
                elif expected_value == "max(300, original)":
                    assert actual_value == max(300, getattr(self.base_config, attr))
                elif expected_value == "max(180, original)":
                    assert actual_value == max(180, getattr(self.base_config, attr))
                else:
                    assert actual_value == expected_value
