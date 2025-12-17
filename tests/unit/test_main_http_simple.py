"""简化的test-http命令测试 - 验证基本功能"""

from unittest.mock import patch

from typer.testing import CliRunner

from src.batch_mcp.main import app


def test_http_command_with_full_mock():
    """使用完整mock测试test-http命令"""
    runner = CliRunner()

    with patch("src.batch_mcp.main.get_cli_handler") as mock_get_handler:
        mock_handler = mock_get_handler.return_value
        mock_handler.test_http_endpoint.return_value = True

        result = runner.invoke(
            app, ["test-http", "http://localhost:8080/mcp", "--no-save-report"]
        )

        assert result.exit_code == 0
        assert "HTTP MCP 端点" in result.stdout


def test_http_command_invalid_url():
    """测试无效URL"""
    runner = CliRunner()

    result = runner.invoke(app, ["test-http", "invalid-url"])

    assert result.exit_code == 1
    assert "必须以 http:// 或 https:// 开头" in result.stdout


def test_http_command_help():
    """测试帮助信息"""
    runner = CliRunner()

    result = runner.invoke(app, ["test-http", "--help"])

    assert result.exit_code == 0
    assert "HTTP MCP 端点 URL" in result.stdout
    assert "--auth-token" in result.stdout
