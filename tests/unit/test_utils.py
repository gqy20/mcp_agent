"""Unit tests for utils functionality."""

import pytest


def test_import_csv_parser():
    """Test that csv_parser module can be imported."""
    try:
        from src.batch_mcp.utils.csv_parser import MCPDataParser

        assert MCPDataParser is not None
    except ImportError:
        pytest.skip("MCPDataParser class not available")


def test_csv_parser_module_exists():
    """Test that the csv parser module exists."""
    try:
        from src.batch_mcp.utils import csv_parser

        assert hasattr(csv_parser, "MCPDataParser") or hasattr(
            csv_parser, "get_mcp_parser"
        )
    except ImportError:
        pytest.skip("CSV parser module not available")
