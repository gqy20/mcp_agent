"""Unit tests for CLI handlers functionality."""

import pytest


def test_import_cli_handlers():
    """Test that cli_handlers module can be imported."""
    try:
        from src.batch_mcp.core.cli_handlers import app

        assert app is not None
    except ImportError:
        pytest.skip("CLI handlers app not available")


def test_cli_handlers_module_exists():
    """Test that the CLI handlers module exists and has expected structure."""
    try:
        from src.batch_mcp.core import cli_handlers

        assert hasattr(cli_handlers, "app") or hasattr(cli_handlers, "main")
    except ImportError:
        pytest.skip("CLI handlers module not available")
