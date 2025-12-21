#!/usr/bin/env python3
"""TDD测试用例：CLI handlers修复测试
测试 ai_confidence 字段类型问题的修复
"""

from unittest.mock import Mock

import pytest

from src.batch_mcp.core.cli_handlers import _convert_test_results_to_dict

# 导入被测试的模块
from src.batch_mcp.core.report_generator import TestResult


class TestConvertTestResultsToDict:
    """测试 _convert_test_results_to_dict 函数的 ai_confidence 字段处理."""

    def test_normal_ai_confidence_handling(self):
        """测试正常的 ai_confidence 字段处理."""
        # Arrange: 创建包含正常 ai_confidence 的 TestResult 对象
        test_results = [
            TestResult(
                test_name="测试1",
                success=True,
                duration=1.0,
                test_category="功能测试",
                ai_confidence=0.85,
            ),
            TestResult(
                test_name="测试2",
                success=False,
                duration=2.0,
                test_category="错误处理测试",
                ai_confidence=0.75,
            ),
        ]

        # Act: 转换测试结果
        result = _convert_test_results_to_dict(test_results)

        # Assert: 验证转换结果
        assert len(result) == 2
        assert result[0]["ai_confidence"] == 0.85
        assert result[1]["ai_confidence"] == 0.75
        assert isinstance(result[0]["ai_confidence"], (int, float))
        assert isinstance(result[1]["ai_confidence"], (int, float))

    def test_missing_ai_confidence_field(self):
        """测试缺少 ai_confidence 字段的情况."""
        # Arrange: 创建不包含 ai_confidence 的 Mock 对象
        mock_test = Mock()
        mock_test.success = True
        mock_test.test_name = "Mock测试"
        mock_test.duration = 1.5
        mock_test.error_message = None
        mock_test.test_category = "功能测试"
        mock_test.to_concise_dict.return_value = {
            "test_name": "Mock测试",
            "success": True,
            "duration": 1.5,
            "test_category": "功能测试",
        }

        test_results = [mock_test]

        # Act: 转换测试结果
        result = _convert_test_results_to_dict(test_results)

        # Assert: 验证转换结果包含默认的 ai_confidence 值
        assert len(result) == 1
        assert result[0]["ai_confidence"] == 0.0  # 默认值应该是 0.0

    def test_none_ai_confidence_handling(self):
        """测试 ai_confidence 为 None 的情况."""
        # Arrange: 创建 ai_confidence 为 None 的 TestResult
        test_result = TestResult(
            test_name="None测试",
            success=True,
            duration=1.0,
            test_category="功能测试",
            ai_confidence=None,  # None 值
        )

        test_results = [test_result]

        # Act: 转换测试结果
        result = _convert_test_results_to_dict(test_results)

        # Assert: 验证 None 值被正确处理
        assert len(result) == 1
        assert result[0]["ai_confidence"] == 0.0  # None 应该被转换为 0.0

    def test_abnormal_ai_confidence_types(self):
        """测试异常类型的 ai_confidence 字段处理."""
        # Arrange: 创建包含异常类型 ai_confidence 的 TestResult
        test_result = TestResult(
            test_name="异常类型测试",
            success=True,
            duration=1.0,
            test_category="功能测试",
            ai_confidence=0.85,  # 正常值
        )

        # 模拟异常：通过 __dict__ 修改为列表类型
        test_result.__dict__["ai_confidence"] = [0.8, 0.9, 0.7]

        test_results = [test_result]

        # Act: 转换测试结果
        result = _convert_test_results_to_dict(test_results)

        # Assert: 验证异常类型被正确处理
        assert len(result) == 1
        # 修复后的代码应该能正确处理列表类型，可能取平均值或转换为数值
        assert isinstance(result[0]["ai_confidence"], (int, float))
        # 如果是列表，应该取平均值: (0.8 + 0.9 + 0.7) / 3 = 0.8
        assert abs(result[0]["ai_confidence"] - 0.8) < 1e-10

    def test_mixed_test_results(self):
        """测试混合类型的测试结果处理."""
        # Arrange: 创建包含各种情况的混合测试结果
        normal_test = TestResult(
            test_name="正常测试",
            success=True,
            duration=1.0,
            test_category="功能测试",
            ai_confidence=0.85,
        )

        none_test = TestResult(
            test_name="None测试",
            success=True,
            duration=1.5,
            test_category="功能测试",
            ai_confidence=None,
        )

        list_test = TestResult(
            test_name="列表测试",
            success=False,
            duration=2.0,
            test_category="功能测试",
            ai_confidence=0.75,
        )
        list_test.__dict__["ai_confidence"] = [0.7, 0.8, 0.6]

        mock_test = Mock()
        mock_test.success = True
        mock_test.test_name = "Mock测试"
        mock_test.duration = 1.2
        mock_test.error_message = None
        mock_test.test_category = "功能测试"
        mock_test.to_concise_dict.return_value = {
            "test_name": "Mock测试",
            "success": True,
            "duration": 1.2,
            "test_category": "功能测试",
        }

        test_results = [normal_test, none_test, list_test, mock_test]

        # Act: 转换测试结果
        result = _convert_test_results_to_dict(test_results)

        # Assert: 验证所有类型都被正确处理
        assert len(result) == 4
        assert result[0]["ai_confidence"] == 0.85  # 正常数值
        assert result[1]["ai_confidence"] == 0.0  # None 转换为 0.0
        assert (
            abs(result[2]["ai_confidence"] - 0.7) < 1e-10
        )  # 列表取平均值: (0.7+0.8+0.6)/3=0.7
        assert result[3]["ai_confidence"] == 0.0  # Mock对象使用默认值

        # 确保所有 ai_confidence 都是数值类型
        for i, test_dict in enumerate(result):
            assert isinstance(test_dict["ai_confidence"], (int, float)), (
                f"结果{i}的ai_confidence应该是数值类型，实际是: {type(test_dict['ai_confidence'])}"
            )

    def test_empty_test_results(self):
        """测试空测试结果列表."""
        # Arrange: 空列表
        test_results = []

        # Act: 转换测试结果
        result = _convert_test_results_to_dict(test_results)

        # Assert: 验证返回空列表
        assert result == []

    def test_invalid_objects_handling(self):
        """测试无效对象的处理."""
        # Arrange: 包含无效对象的测试结果
        test_results = [
            TestResult(
                test_name="有效测试",
                success=True,
                duration=1.0,
                test_category="功能测试",
                ai_confidence=0.85,
            ),
            "无效字符串",  # 无效对象
            None,  # None 对象
            123,  # 数字对象
        ]

        # Act: 转换测试结果
        result = _convert_test_results_to_dict(test_results)

        # Assert: 验证只处理有效对象
        assert len(result) == 1
        assert result[0]["test_name"] == "有效测试"
        assert result[0]["ai_confidence"] == 0.85


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
