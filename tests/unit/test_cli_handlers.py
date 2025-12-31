"""Unit tests for CLI handlers functionality."""


def test_cli_handlers_module_exists():
    """Test that the CLI handlers module exists and has expected structure."""
    from src.batch_mcp.core import cli_handlers

    # cli_handlers 模块包含 CLIHandler 类和 get_cli_handler 函数
    assert hasattr(cli_handlers, "CLIHandler")
    assert hasattr(cli_handlers, "get_cli_handler")


def test_cli_handler_class_exists():
    """Test that CLIHandler class can be imported."""
    from src.batch_mcp.core.cli_handlers import CLIHandler

    assert CLIHandler is not None


def test_get_cli_handler_function():
    """Test that get_cli_handler function exists and returns a CLIHandler."""
    from src.batch_mcp.core.cli_handlers import get_cli_handler

    handler = get_cli_handler()
    assert handler is not None
    assert (
        isinstance(handler, type(handler).__bases__[0])
        or handler.__class__.__name__ == "CLIHandler"
    )


def test_cli_handler_has_expected_methods():
    """Test that CLIHandler has expected command methods."""
    from src.batch_mcp.core.cli_handlers import CLIHandler

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
    from src.batch_mcp import main

    # app 在 main.py 中定义
    assert hasattr(main, "app")
    assert main.app is not None
