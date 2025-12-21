#!/usr/bin/env python3
"""TDD测试用例：Evaluator修复测试
测试 calculate_functionality_score 函数的类型安全性修复
"""

import pytest

# 导入被测试的模块
from src.batch_mcp.core.evaluator import calculate_functionality_score


class TestCalculateFunctionalityScoreFix:
    """测试 calculate_functionality_score 函数的类型安全性."""

    def test_normal_confidence_values(self):
        """测试正常的 confidence 值处理."""
        # Arrange: 包含正常 confidence 值的测试结果
        tool_tests = [
            {
                "test_name": "测试1",
                "success": True,
                "ai_confidence": 0.85,
                "test_category": "功能测试",
            },
            {
                "test_name": "测试2",
                "success": False,
                "ai_confidence": 0.75,
                "test_category": "功能测试",
            },
            {
                "test_name": "测试3",
                "success": True,
                "ai_confidence": 0.90,
                "test_category": "功能测试",
            },
        ]

        # Act: 计算功能评分
        score = calculate_functionality_score(tool_tests)

        # Assert: 验证评分计算正确
        # 成功率: 2/3 = 0.666..., 基础分: 0.666... * 70 = 46.666...
        # 平均置信度: (0.85 + 0.75 + 0.90) / 3 = 0.833..., 置信度加成: 0.833... * 30 = 25
        # 总分: 46.666... + 25 = 71.666...
        assert isinstance(score, (int, float))
        assert 70 <= score <= 75  # 允许小的浮点误差

    def test_missing_confidence_values(self):
        """测试缺少 confidence 字段的情况."""
        # Arrange: 不包含 ai_confidence 字段的测试结果
        tool_tests = [
            {
                "test_name": "测试1",
                "success": True,
                "test_category": "功能测试",
                # 缺少 ai_confidence 字段
            },
            {
                "test_name": "测试2",
                "success": False,
                "test_category": "功能测试",
                # 缺少 ai_confidence 字段
            },
        ]

        # Act: 计算功能评分
        score = calculate_functionality_score(tool_tests)

        # Assert: 验证使用默认值 0.0 进行计算
        # 成功率: 1/2 = 0.5, 基础分: 0.5 * 70 = 35
        # 平均置信度: 0.0 (使用默认值), 置信度加成: 0.0 * 30 = 0
        # 总分: 35 + 0 = 35
        assert isinstance(score, (int, float))
        assert score == 35.0

    def test_none_confidence_values(self):
        """测试 confidence 为 None 的情况."""
        # Arrange: confidence 为 None 的测试结果
        tool_tests = [
            {
                "test_name": "测试1",
                "success": True,
                "ai_confidence": None,
                "test_category": "功能测试",
            },
            {
                "test_name": "测试2",
                "success": True,
                "ai_confidence": None,
                "test_category": "功能测试",
            },
        ]

        # Act: 计算功能评分
        score = calculate_functionality_score(tool_tests)

        # Assert: 验证 None 值被正确处理
        # 成功率: 2/2 = 1.0, 基础分: 1.0 * 70 = 70
        # 平均置信度: 0.0 (None 被当作 0.0), 置信度加成: 0.0 * 30 = 0
        # 总分: 70 + 0 = 70
        assert isinstance(score, (int, float))
        assert score == 70.0

    def test_list_confidence_values(self):
        """测试 confidence 为列表类型的情况（这是导致错误的原因）."""
        # Arrange: confidence 为列表的测试结果
        tool_tests = [
            {
                "test_name": "测试1",
                "success": True,
                "ai_confidence": [0.8, 0.9, 0.7],  # 列表类型
                "test_category": "功能测试",
            },
            {
                "test_name": "测试2",
                "success": False,
                "ai_confidence": [0.6, 0.7],  # 列表类型
                "test_category": "功能测试",
            },
        ]

        # Act: 计算功能评分
        score = calculate_functionality_score(tool_tests)

        # Assert: 验证列表类型被正确处理
        # 成功率: 1/2 = 0.5, 基础分: 0.5 * 70 = 35
        # 平均置信度: ((0.8+0.9+0.7)/3 + (0.6+0.7)/2) / 2 = (0.8 + 0.65) / 2 = 0.725
        # 置信度加成: 0.725 * 30 = 21.75
        # 总分: 35 + 21.75 = 56.75
        assert isinstance(score, (int, float))
        assert abs(score - 56.75) < 1e-10

    def test_mixed_confidence_types(self):
        """测试混合类型的 confidence 值."""
        # Arrange: 包含各种类型的 confidence
        tool_tests = [
            {
                "test_name": "正常数值",
                "success": True,
                "ai_confidence": 0.85,  # 浮点数
                "test_category": "功能测试",
            },
            {
                "test_name": "整数类型",
                "success": True,
                "ai_confidence": 1,  # 整数
                "test_category": "功能测试",
            },
            {
                "test_name": "列表类型",
                "success": False,
                "ai_confidence": [0.7, 0.8, 0.6],  # 列表
                "test_category": "功能测试",
            },
            {
                "test_name": "缺失字段",
                "success": True,
                "test_category": "功能测试",
                # 缺少 ai_confidence 字段
            },
            {
                "test_name": "None值",
                "success": False,
                "ai_confidence": None,  # None
                "test_category": "功能测试",
            },
        ]

        # Act: 计算功能评分
        score = calculate_functionality_score(tool_tests)

        # Assert: 验证混合类型被正确处理
        # 成功率: 3/5 = 0.6, 基础分: 0.6 * 70 = 42
        # 平均置信度: (0.85 + 1.0 + 0.7 + 0.0 + 0.0) / 5 = 0.51, 置信度加成: 0.51 * 30 = 15.3
        # 总分: 42 + 15.3 = 57.3
        assert isinstance(score, (int, float))
        assert 57 <= score <= 58  # 允许小的浮点误差

    def test_empty_list_with_numeric_elements(self):
        """测试包含数值元素的列表."""
        # Arrange: 包含数值和字符串的混合列表
        tool_tests = [
            {
                "test_name": "混合列表测试",
                "success": True,
                "ai_confidence": [0.8, "invalid", 0.9, None, 0.7],  # 混合列表
                "test_category": "功能测试",
            },
        ]

        # Act: 计算功能评分
        score = calculate_functionality_score(tool_tests)

        # Assert: 验证只提取数值元素
        # 成功率: 1/1 = 1.0, 基础分: 1.0 * 70 = 70
        # 平均置信度: (0.8 + 0.9 + 0.7) / 3 = 0.8, 置信度加成: 0.8 * 30 = 24
        # 总分: 70 + 24 = 94
        assert isinstance(score, (int, float))
        assert score == 94.0

    def test_empty_list_confidence(self):
        """测试空列表类型的 confidence."""
        # Arrange: confidence 为空列表
        tool_tests = [
            {
                "test_name": "空列表测试",
                "success": True,
                "ai_confidence": [],  # 空列表
                "test_category": "功能测试",
            },
        ]

        # Act: 计算功能评分
        score = calculate_functionality_score(tool_tests)

        # Assert: 验证空列表被当作 0.0 处理
        # 成功率: 1/1 = 1.0, 基础分: 1.0 * 70 = 70
        # 平均置信度: 0.0 (空列表没有数值元素), 置信度加成: 0.0 * 30 = 0
        # 总分: 70 + 0 = 70
        assert isinstance(score, (int, float))
        assert score == 70.0

    def test_empty_tool_tests(self):
        """测试空的工具测试列表."""
        # Arrange: 空列表
        tool_tests = []

        # Act: 计算功能评分
        score = calculate_functionality_score(tool_tests)

        # Assert: 验证返回 0.0
        assert score == 0.0

    def test_all_failed_tests(self):
        """测试所有测试都失败的情况."""
        # Arrange: 所有测试都失败
        tool_tests = [
            {
                "test_name": "失败测试1",
                "success": False,
                "ai_confidence": 0.8,
                "test_category": "功能测试",
            },
            {
                "test_name": "失败测试2",
                "success": False,
                "ai_confidence": 0.9,
                "test_category": "功能测试",
            },
        ]

        # Act: 计算功能评分
        score = calculate_functionality_score(tool_tests)

        # Assert: 验证失败测试的评分
        # 成功率: 0/2 = 0.0, 基础分: 0.0 * 70 = 0
        # 平均置信度: (0.8 + 0.9) / 2 = 0.85, 置信度加成: 0.85 * 30 = 25.5
        # 总分: 0 + 25.5 = 25.5
        assert isinstance(score, (int, float))
        assert abs(score - 25.5) < 1e-10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
