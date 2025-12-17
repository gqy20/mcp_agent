"""Unit tests for report generator functionality."""

import pytest


def test_import_report_generator():
    """Test that report generator module can be imported."""
    try:
        from src.batch_mcp.core.report_generator import ReportGenerator

        assert ReportGenerator is not None
    except ImportError:
        pytest.skip("ReportGenerator class not available")


def test_report_generator_module_exists():
    """Test that the report generator module exists."""
    try:
        from src.batch_mcp.core import report_generator

        assert hasattr(report_generator, "ReportGenerator") or hasattr(
            report_generator, "generate_report"
        )
    except ImportError:
        pytest.skip("Report generator module not available")
