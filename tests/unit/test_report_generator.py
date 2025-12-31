"""Unit tests for report generator functionality."""


def test_import_report_generator():
    """Test that report generator module can be imported."""
    from src.batch_mcp.core.report_generator import MCPReportGenerator

    assert MCPReportGenerator is not None


def test_report_generator_module_exists():
    """Test that the report generator module exists."""
    from src.batch_mcp.core import report_generator

    # report_generator 模块包含 MCPReportGenerator 类和 generate_test_report 函数
    assert hasattr(report_generator, "MCPReportGenerator")
    assert hasattr(report_generator, "generate_test_report")
    assert hasattr(report_generator, "TestResult")
    assert hasattr(report_generator, "MCPTestReport")


def test_report_generator_has_expected_classes():
    """Test that MCPReportGenerator has expected methods."""
    from src.batch_mcp.core.report_generator import MCPReportGenerator

    # MCPReportGenerator 应该有保存报告的方法
    expected_methods = [
        "save_json",
        "save_concise_json",
        "save_html",
        "print_concise_summary",
        "_convert_numpy_types",
        "_get_process_pid",
    ]

    for method in expected_methods:
        assert hasattr(MCPReportGenerator, method), (
            f"MCPReportGenerator should have {method} method"
        )


def test_generate_test_report_function():
    """Test that generate_test_report function exists."""
    from src.batch_mcp.core.report_generator import generate_test_report

    assert generate_test_report is not None
    assert callable(generate_test_report)
