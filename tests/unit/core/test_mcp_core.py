"""Unit tests for core MCP functionality."""

from unittest.mock import Mock, patch

import pytest

from src.batch_mcp.core.simple_mcp_deployer import SimpleMCPDeployer


class TestSimpleMCPDeployer:
    """Test cases for SimpleMCPDeployer."""

    def test_deployer_initialization(self):
        """Test deployer initialization with valid config."""
        config = {"timeout": 30}
        deployer = SimpleMCPDeployer(config)
        assert deployer.config == config

    def test_deployer_timeout_validation(self):
        """Test deployer timeout validation."""
        config = {"timeout": -1}
        with pytest.raises(ValueError):
            SimpleMCPDeployer(config)


class TestAsyncMCPClient:
    """Test cases for AsyncMCPClient."""

    @pytest.fixture
    def mock_client(self):
        """Create mock MCP client."""
        client = Mock()
        client.list_tools.return_value = {
            "tools": [{"name": "test_tool", "description": "Test tool"}]
        }
        return client

    def test_client_tool_listing(self, mock_client):
        """Test client tool listing functionality."""
        tools = mock_client.list_tools()
        assert "tools" in tools
        assert len(tools["tools"]) == 1
        assert tools["tools"][0]["name"] == "test_tool"

    @patch("src.core.async_mcp_client.logger")
    def test_client_error_handling(self, mock_logger, mock_client):
        """Test client error handling."""
        mock_client.list_tools.side_effect = Exception("Connection failed")

        with pytest.raises(Exception):
            mock_client.list_tools()

        mock_logger.error.assert_called_once()
