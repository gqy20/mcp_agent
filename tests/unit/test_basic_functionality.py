"""Basic functionality tests that should pass."""

from src.batch_mcp.core.async_mcp_client import AsyncMCPClient
from src.batch_mcp.core.error_handler import (
    CommunicationError,
    DeploymentError,
    ValidationError,
)
from src.batch_mcp.core.evaluator import (
    evaluate_popularity,
    evaluate_sustainability,
    parse_github_url,
)
from src.batch_mcp.core.simple_mcp_deployer import SimpleMCPDeployer


class TestBasicImports:
    """Test that basic imports work."""

    def test_import_simple_mcp_deployer(self):
        """Test importing SimpleMCPDeployer."""
        assert SimpleMCPDeployer is not None

    def test_import_async_mcp_client(self):
        """Test importing AsyncMCPClient."""
        assert AsyncMCPClient is not None

    def test_import_evaluator(self):
        """Test importing evaluator functions."""
        assert parse_github_url is not None
        assert evaluate_popularity is not None
        assert evaluate_sustainability is not None

    def test_import_error_handler(self):
        """Test importing error handler."""
        assert CommunicationError is not None
        assert DeploymentError is not None
        assert ValidationError is not None


class TestGitHubUrlParser:
    """Test GitHub URL parsing functionality."""

    def test_parse_valid_github_url(self):
        """Test parsing valid GitHub URLs."""
        owner, repo = parse_github_url("https://github.com/test/repo")
        assert owner == "test"
        assert repo == "repo"

    def test_parse_github_url_with_git(self):
        """Test parsing GitHub URL with .git extension."""
        owner, repo = parse_github_url("https://github.com/test/repo.git")
        assert owner == "test"
        assert repo == "repo"

    def test_parse_invalid_github_url(self):
        """Test parsing invalid GitHub URLs."""
        owner, repo = parse_github_url("https://example.com/test/repo")
        assert owner is None
        assert repo is None

    def test_parse_none_url(self):
        """Test parsing None URL."""
        owner, repo = parse_github_url(None)
        assert owner is None
        assert repo is None


class TestErrorHandling:
    """Test error handling functionality."""

    def test_deployment_error_creation(self):
        """Test DeploymentError creation."""
        error = DeploymentError("Test deployment error", {"cmd": "test"})
        assert error.error_code == "DEPLOYMENT_ERROR"
        assert error.message == "Test deployment error"
        assert error.details == {"cmd": "test"}

    def test_communication_error_creation(self):
        """Test CommunicationError creation."""
        error = CommunicationError("Test communication error")
        assert error.error_code == "COMMUNICATION_ERROR"
        assert error.message == "Test communication error"

    def test_validation_error_creation(self):
        """Test ValidationError creation."""
        error = ValidationError("Test validation error")
        assert error.error_code == "VALIDATION_ERROR"
        assert error.message == "Test validation error"


class TestFixtures:
    """Test that fixtures work correctly."""

    def test_sample_mcp_config_fixture(self, sample_mcp_config):
        """Test sample_mcp_config fixture."""
        assert "mcpServers" in sample_mcp_config
        assert "test_server" in sample_mcp_config["mcpServers"]

    def test_mock_openai_client_fixture(self, mock_openai_client):
        """Test mock_openai_client fixture."""
        assert mock_openai_client is not None
        assert hasattr(mock_openai_client, "chat")
        assert hasattr(mock_openai_client.chat, "completions")

    def test_test_data_path_fixture(self, test_data_path):
        """Test test_data_path fixture."""
        assert test_data_path.exists()
        assert test_data_path.name == "fixtures"
