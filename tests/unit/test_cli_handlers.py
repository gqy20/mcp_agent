"""Unit tests for CLI handlers functionality."""

from unittest.mock import Mock

from src.batch_mcp import main
from src.batch_mcp.core import cli_handlers
from src.batch_mcp.core.cli_handlers import (
    CLIHandler,
    _convert_test_results_to_dict,
    get_cli_handler,
)
from src.batch_mcp.core.report_generator import TestResult


def test_cli_handlers_module_exists():
    """Test that the CLI handlers module exists and has expected structure."""
    # cli_handlers 模块包含 CLIHandler 类和 get_cli_handler 函数
    assert hasattr(cli_handlers, "CLIHandler")
    assert hasattr(cli_handlers, "get_cli_handler")


def test_cli_handler_class_exists():
    """Test that CLIHandler class can be imported."""
    assert CLIHandler is not None


def test_get_cli_handler_function():
    """Test that get_cli_handler function exists and returns a CLIHandler."""
    handler = get_cli_handler()
    assert handler is not None
    assert (
        isinstance(handler, type(handler).__bases__[0])
        or handler.__class__.__name__ == "CLIHandler"
    )


def test_cli_handler_has_expected_methods():
    """Test that CLIHandler has expected command methods."""
    # CLIHandler 的核心方法
    expected_methods = [
        "test_url",
        "test_package",
        "evaluate_tools",
    ]

    for method in expected_methods:
        assert hasattr(CLIHandler, method), f"CLIHandler should have {method} method"


def test_main_module_has_app():
    """Test that main module has the Typer app."""
    # app 在 main.py 中定义
    assert hasattr(main, "app")
    assert main.app is not None


class TestConvertTestResultsToDict:
    """Test _convert_test_results_to_dict function ai_confidence handling."""

    def test_normal_ai_confidence_handling(self):
        """Test normal ai_confidence field handling."""
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

        result = _convert_test_results_to_dict(test_results)

        assert len(result) == 2
        assert result[0]["ai_confidence"] == 0.85
        assert result[1]["ai_confidence"] == 0.75
        assert isinstance(result[0]["ai_confidence"], (int, float))
        assert isinstance(result[1]["ai_confidence"], (int, float))

    def test_missing_ai_confidence_field(self):
        """Test missing ai_confidence field."""
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

        result = _convert_test_results_to_dict(test_results)

        assert len(result) == 1
        assert result[0]["ai_confidence"] == 0.0

    def test_none_ai_confidence_handling(self):
        """Test ai_confidence is None."""
        test_result = TestResult(
            test_name="None测试",
            success=True,
            duration=1.0,
            test_category="功能测试",
            ai_confidence=None,
        )

        test_results = [test_result]

        result = _convert_test_results_to_dict(test_results)

        assert len(result) == 1
        assert result[0]["ai_confidence"] == 0.0

    def test_abnormal_ai_confidence_types(self):
        """Test abnormal ai_confidence types."""
        test_result = TestResult(
            test_name="异常类型测试",
            success=True,
            duration=1.0,
            test_category="功能测试",
            ai_confidence=0.85,
        )

        test_result.__dict__["ai_confidence"] = [0.8, 0.9, 0.7]

        test_results = [test_result]

        result = _convert_test_results_to_dict(test_results)

        assert len(result) == 1
        assert isinstance(result[0]["ai_confidence"], (int, float))
        assert abs(result[0]["ai_confidence"] - 0.8) < 1e-10

    def test_mixed_test_results(self):
        """Test mixed test results handling."""
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

        result = _convert_test_results_to_dict(test_results)

        assert len(result) == 4
        assert result[0]["ai_confidence"] == 0.85
        assert result[1]["ai_confidence"] == 0.0
        assert abs(result[2]["ai_confidence"] - 0.7) < 1e-10
        assert result[3]["ai_confidence"] == 0.0

        for _i, test_dict in enumerate(result):
            assert isinstance(test_dict["ai_confidence"], (int, float))

    def test_empty_test_results(self):
        """Test empty test results list."""
        test_results = []

        result = _convert_test_results_to_dict(test_results)

        assert result == []

    def test_invalid_objects_handling(self):
        """Test invalid objects handling."""
        test_results = [
            TestResult(
                test_name="有效测试",
                success=True,
                duration=1.0,
                test_category="功能测试",
                ai_confidence=0.85,
            ),
            "无效字符串",
            None,
            123,
        ]

        result = _convert_test_results_to_dict(test_results)

        assert len(result) == 1
        assert result[0]["test_name"] == "有效测试"
        assert result[0]["ai_confidence"] == 0.85
