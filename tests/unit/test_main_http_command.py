"""Unit tests for test-http CLI command - TDD approach.

Tests for the new test-http CLI command implementation.

作者: AI Assistant
日期: 2025-12-17
"""

import sys
from pathlib import Path
from unittest.mock import ANY, Mock, patch

import pytest
from typer.testing import CliRunner

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.batch_mcp.main import app


class TestHttpCommandTDD:
    """TDD tests for test-http CLI command."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """CLI test runner fixture."""
        return CliRunner()

    @pytest.fixture
    def mock_cli_handler(self) -> Mock:
        """Mock CLI handler fixture.

        我们需要 mock src.batch_mcp.main.handler 而不是 get_cli_handler，
        因为 handler 是在模块级别创建的。
        """
        with patch("src.batch_mcp.main.handler") as mock_handler:
            yield mock_handler

    def test_test_http_command_exists(self, runner: CliRunner) -> None:
        """TDD Test: Verify test-http command exists in CLI."""
        result = runner.invoke(app, ["--help"])

        # Check that test-http command is listed in help
        assert result.exit_code == 0
        assert "test-http" in result.stdout

    def test_test_http_command_basic_usage(
        self, runner: CliRunner, mock_cli_handler: Mock
    ) -> None:
        """TDD Test: Basic test-http command execution."""
        # Mock successful test execution
        mock_cli_handler.test_http_endpoint.return_value = True

        result = runner.invoke(
            app,
            [
                "test-http",
                "http://localhost:8080/mcp",
                "--no-save-report",  # 禁用报告生成以避免依赖外部服务
            ],
        )

        assert result.exit_code == 0
        mock_cli_handler.test_http_endpoint.assert_called_once()

    def test_test_http_command_with_auth_token(
        self, runner: CliRunner, mock_cli_handler: Mock
    ) -> None:
        """TDD Test: test-http command with authentication token."""
        mock_cli_handler.test_http_endpoint.return_value = True

        result = runner.invoke(
            app,
            [
                "test-http",
                "http://api.example.com/mcp",
                "--auth-token",
                "test_token_123",
            ],
        )

        assert result.exit_code == 0
        # Verify the method was called with auth token
        mock_cli_handler.test_http_endpoint.assert_called_once_with(
            "http://api.example.com/mcp",
            ANY,  # TestConfig object
            "test_token_123",
        )

    def test_test_http_command_with_custom_timeout(
        self, runner: CliRunner, mock_cli_handler: Mock
    ) -> None:
        """TDD Test: test-http command with custom timeout."""
        mock_cli_handler.test_http_endpoint.return_value = True

        result = runner.invoke(
            app, ["test-http", "http://localhost:8080/mcp", "--timeout", "300"]
        )

        assert result.exit_code == 0
        mock_cli_handler.test_http_endpoint.assert_called_once()

        # Verify TestConfig was created with custom timeout
        call_args = mock_cli_handler.test_http_endpoint.call_args
        test_config = call_args[0][1]  # Second argument is TestConfig
        assert test_config.timeout == 300

    def test_test_http_command_disable_smart_testing(
        self, runner: CliRunner, mock_cli_handler: Mock
    ) -> None:
        """TDD Test: test-http command with smart testing disabled."""
        mock_cli_handler.test_http_endpoint.return_value = True

        result = runner.invoke(
            app, ["test-http", "http://localhost:8080/mcp", "--no-smart"]
        )

        assert result.exit_code == 0

        # Verify TestConfig has smart testing disabled
        call_args = mock_cli_handler.test_http_endpoint.call_args
        test_config = call_args[0][1]
        assert test_config.smart_test is False

    def test_test_http_command_disable_db_export(
        self, runner: CliRunner, mock_cli_handler: Mock
    ) -> None:
        """TDD Test: test-http command with database export disabled."""
        mock_cli_handler.test_http_endpoint.return_value = True

        result = runner.invoke(
            app, ["test-http", "http://localhost:8080/mcp", "--no-db-export"]
        )

        assert result.exit_code == 0

        # Verify TestConfig has db export disabled
        call_args = mock_cli_handler.test_http_endpoint.call_args
        test_config = call_args[0][1]
        assert test_config.db_export is False

    def test_test_http_command_enable_evaluation_by_default(
        self, runner: CliRunner, mock_cli_handler: Mock
    ) -> None:
        """TDD Test: test-http command has evaluation disabled by default."""
        mock_cli_handler.test_http_endpoint.return_value = True

        result = runner.invoke(app, ["test-http", "http://localhost:8080/mcp"])

        assert result.exit_code == 0

        # Verify TestConfig has evaluation disabled by default for HTTP
        call_args = mock_cli_handler.test_http_endpoint.call_args
        test_config = call_args[0][1]
        assert test_config.evaluate is False

    def test_test_http_command_enable_evaluation_explicitly(
        self, runner: CliRunner, mock_cli_handler: Mock
    ) -> None:
        """TDD Test: test-http command with evaluation explicitly enabled."""
        mock_cli_handler.test_http_endpoint.return_value = True

        result = runner.invoke(
            app, ["test-http", "http://localhost:8080/mcp", "--evaluate"]
        )

        assert result.exit_code == 0

        # Verify TestConfig has evaluation enabled
        call_args = mock_cli_handler.test_http_endpoint.call_args
        test_config = call_args[0][1]
        assert test_config.evaluate is True

    def test_test_http_command_verbose_output(
        self, runner: CliRunner, mock_cli_handler: Mock
    ) -> None:
        """TDD Test: test-http command with verbose output."""
        mock_cli_handler.test_http_endpoint.return_value = True

        result = runner.invoke(
            app, ["test-http", "http://localhost:8080/mcp", "--verbose"]
        )

        assert result.exit_code == 0

        # Verify TestConfig has verbose enabled
        call_args = mock_cli_handler.test_http_endpoint.call_args
        test_config = call_args[0][1]
        assert test_config.verbose is True

    def test_test_http_command_save_report_option(
        self, runner: CliRunner, mock_cli_handler: Mock
    ) -> None:
        """TDD Test: test-http command with save report option."""
        mock_cli_handler.test_http_endpoint.return_value = True

        # Test with --no-save-report
        result = runner.invoke(
            app, ["test-http", "http://localhost:8080/mcp", "--no-save-report"]
        )

        assert result.exit_code == 0

        call_args = mock_cli_handler.test_http_endpoint.call_args
        test_config = call_args[0][1]
        assert test_config.save_report is False

    def test_test_http_command_failure_exit(
        self, runner: CliRunner, mock_cli_handler: Mock
    ) -> None:
        """TDD Test: test-http command exits with error on test failure."""
        # Mock failed test execution
        mock_cli_handler.test_http_endpoint.return_value = False

        result = runner.invoke(app, ["test-http", "http://localhost:8080/mcp"])

        # Should exit with error code 1
        assert result.exit_code == 1

    def test_test_http_command_url_validation(self, runner: CliRunner) -> None:
        """TDD Test: test-http command validates URL format."""
        # Test with invalid URL (missing http scheme)
        result = runner.invoke(
            app,
            [
                "test-http",
                "localhost:8080/mcp",  # Missing http:// or https://
            ],
        )

        # Should fail due to URL validation
        assert result.exit_code != 0

    def test_test_http_command_help_output(self, runner: CliRunner) -> None:
        """TDD Test: test-http command help output contains expected information."""
        result = runner.invoke(app, ["test-http", "--help"])

        assert result.exit_code == 0
        assert "HTTP MCP 端点 URL" in result.stdout
        assert "--auth-token" in result.stdout
        assert "--timeout" in result.stdout
        assert "--verbose" in result.stdout

    def test_test_http_command_all_options_combined(
        self, runner: CliRunner, mock_cli_handler: Mock
    ) -> None:
        """TDD Test: test-http command with all options combined."""
        mock_cli_handler.test_http_endpoint.return_value = True

        result = runner.invoke(
            app,
            [
                "test-http",
                "https://api.example.com/mcp",
                "--timeout",
                "600",
                "--auth-token",
                "bearer_12345",
                "--verbose",
                "--no-save-report",
                "--no-smart",
                "--no-db-export",
                "--evaluate",
            ],
        )

        assert result.exit_code == 0

        # Verify all options were passed correctly
        call_args = mock_cli_handler.test_http_endpoint.call_args
        test_config = call_args[0][1]

        assert test_config.timeout == 600
        assert test_config.verbose is True
        assert test_config.save_report is False
        assert test_config.smart_test is False
        assert test_config.db_export is False
        assert test_config.evaluate is True

        # Verify auth token was passed
        assert call_args[0][2] == "bearer_12345"  # Third argument is auth token

    def test_test_http_command_clean_cleanup_parameter(
        self, runner: CliRunner, mock_cli_handler: Mock
    ) -> None:
        """TDD Test: test-http command cleanup parameter is always True (HTTP doesn't need cleanup)."""
        mock_cli_handler.test_http_endpoint.return_value = True

        result = runner.invoke(app, ["test-http", "http://localhost:8080/mcp"])

        assert result.exit_code == 0

        call_args = mock_cli_handler.test_http_endpoint.call_args
        test_config = call_args[0][1]
        # HTTP tests should always have cleanup=True
        assert test_config.cleanup is True

    def test_test_http_command_https_support(
        self, runner: CliRunner, mock_cli_handler: Mock
    ) -> None:
        """TDD Test: test-http command supports HTTPS URLs."""
        mock_cli_handler.test_http_endpoint.return_value = True

        result = runner.invoke(app, ["test-http", "https://secure.example.com/mcp"])

        assert result.exit_code == 0
        mock_cli_handler.test_http_endpoint.assert_called_once_with(
            "https://secure.example.com/mcp",
            ANY,
            None,  # No auth token
        )
