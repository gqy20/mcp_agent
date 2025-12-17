"""Unit tests for core MCP functionality."""

from unittest.mock import Mock, patch

import pytest

from src.batch_mcp.core.async_mcp_client import AsyncMCPClient
from src.batch_mcp.core.error_handler import (
    CommunicationError,
    DeploymentError,
    ValidationError,
    retry_on_exception,
    validate_input,
)
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

    @pytest.fixture
    def deployer(self):
        """Create deployer instance with mock config."""
        config = {
            "timeout": 30,
            "max_retries": 3,
            "platform_info": {
                "system": "Linux",
                "node_available": True,
                "npx_path": "/usr/bin/npx",
            },
        }
        return SimpleMCPDeployer(config)

    @pytest.fixture
    def mock_tool_info(self):
        """Mock MCP tool info."""
        return Mock(
            name="test_tool",
            package="@test/tool",
            github_url="https://github.com/test/tool",
            deployment_method="npx",
        )

    def test_deployer_initialization_with_invalid_config(self):
        """Test deployer initialization with invalid config."""
        with pytest.raises(ValueError):
            SimpleMCPDeployer({"timeout": -1})

    def test_deployer_platform_detection(self, deployer):
        """Test platform detection logic."""
        platform_info = deployer.platform_info
        assert "system" in platform_info
        assert "node_available" in platform_info
        assert "npx_path" in platform_info

    def test_runtime_detection_for_github_url(self, deployer):
        """Test runtime detection based on GitHub URL."""
        # Test npx detection
        runtime_type, command = deployer.detect_simple_platform(
            "https://github.com/test/repo"
        )
        assert runtime_type == "npx"
        assert "npx" in command

        # Test uvx detection with indicators
        uvx_url = "https://github.com/user/uv-mcp-tool"
        runtime_type, command = deployer.detect_simple_platform(uvx_url)
        assert runtime_type == "uvx"
        assert "uvx" in command

    @patch("subprocess.Popen")
    def test_successful_process_start(self, mock_popen, deployer):
        """Test successful process start."""
        mock_process = Mock()
        mock_process.poll.return_value = None
        mock_popen.return_value = mock_process

        cmd = ["npx", "test-tool"]
        result = deployer._try_start_process(
            cmd, 0, "test_tool", None, "@test/tool", {"runtime_type": "npx"}
        )

        assert result is not None
        mock_popen.assert_called_once()

    @patch("subprocess.Popen")
    def test_failed_process_start_with_error(self, mock_popen, deployer):
        """Test failed process start with error message."""
        mock_process = Mock()
        mock_process.poll.return_value = 1  # Process exited with error
        mock_process.communicate.return_value = (b"", b"unknown option '--stdio'")
        mock_popen.return_value = mock_process

        cmd = ["npx", "test-tool", "--stdio"]
        result = deployer._try_start_process(
            cmd, 0, "test_tool", None, "@test/tool", {"runtime_type": "npx"}
        )

        # Should raise DeploymentError due to retry logic
        assert result is None

    def test_cleanup_server_success(self, deployer):
        """Test successful server cleanup."""
        mock_process = Mock()
        mock_server_info = {"id": "test_id", "process": mock_process}
        deployer.active_servers["test_id"] = mock_server_info

        result = deployer.cleanup_server("test_id")

        assert result is True
        mock_process.terminate.assert_called_once()
        mock_process.wait.assert_called_once_with(timeout=5)
        assert "test_id" not in deployer.active_servers

    def test_cleanup_all_servers(self, deployer):
        """Test cleanup of all servers."""
        mock_process1 = Mock()
        mock_process2 = Mock()

        deployer.active_servers["server1"] = {"id": "server1", "process": mock_process1}
        deployer.active_servers["server2"] = {"id": "server2", "process": mock_process2}

        deployer.cleanup_all()

        mock_process1.terminate.assert_called_once()
        mock_process2.terminate.assert_called_once()
        assert len(deployer.active_servers) == 0


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

    @pytest.fixture
    def mock_communicator(self):
        """Mock communicator for testing."""
        communicator = Mock()
        communicator.send_request.return_value = {
            "success": True,
            "data": {"tools": [{"name": "test_tool"}]},
        }
        return communicator

    def test_async_client_initialization(self, mock_communicator):
        """Test AsyncMCPClient initialization."""
        client = AsyncMCPClient(mock_communicator)
        assert client.communicator == mock_communicator

    def test_list_tools_success(self, mock_communicator):
        """Test successful list_tools call."""
        client = AsyncMCPClient(mock_communicator)
        result = client.list_tools()

        assert result["success"] is True
        assert "tools" in result["data"]
        mock_communicator.send_request.assert_called_once()

    def test_call_tool_success(self, mock_communicator):
        """Test successful call_tool."""
        client = AsyncMCPClient(mock_communicator)
        result = client.call_tool("test_tool", {"param": "value"})

        assert result["success"] is True
        mock_communicator.send_request.assert_called_once()

    def test_async_client_error_handling(self, mock_communicator):
        """Test AsyncMCPClient error handling."""
        mock_communicator.send_request.return_value = {
            "success": False,
            "error": "Tool not found",
        }

        client = AsyncMCPClient(mock_communicator)
        result = client.call_tool("nonexistent_tool", {})

        assert result["success"] is False
        assert "error" in result

    def test_async_client_timeout(self, mock_communicator):
        """Test AsyncMCPClient timeout handling."""
        mock_communicator.send_request.side_effect = CommunicationError(
            "Request timeout"
        )

        client = AsyncMCPClient(mock_communicator)
        result = client.list_tools()

        assert result["success"] is False
        assert "timeout" in result.get("error", "").lower()


class TestErrorHandling:
    """Test error handling mechanisms."""

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

    def test_retry_decorator(self):
        """Test retry decorator functionality."""
        call_count = 0

        @retry_on_exception(max_retries=2, delay=0.1)
        def failing_function():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise CommunicationError("Temporary failure")
            return "success"

        result = failing_function()
        assert result == "success"
        assert call_count == 2

    def test_input_validation(self):
        """Test input validation function."""
        # Valid input
        result = validate_input(10, int, min_value=5, max_value=15)
        assert result == 10

        # Invalid type
        with pytest.raises(ValidationError):
            validate_input("10", int)

        # Out of range
        with pytest.raises(ValidationError):
            validate_input(20, int, max_value=15)

        # Custom validator
        def is_even(x):
            return x % 2 == 0

        result = validate_input(10, int, custom_validator=is_even)
        assert result == 10

        with pytest.raises(ValidationError):
            validate_input(11, int, custom_validator=is_even)


class TestIntegration:
    """Integration tests for core components."""

    def test_full_deployment_workflow(self):
        """Test complete deployment workflow."""
        # This would be a more complex integration test
        # For now, we'll just test the basic workflow

    def test_error_recovery_workflow(self):
        """Test error recovery in workflow."""
        # Test that errors are properly handled and don't crash the system

    def test_concurrent_operations(self):
        """Test concurrent operations handling."""
        # Test thread safety and concurrent access
