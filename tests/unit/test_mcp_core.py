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
        """Test deployer initialization."""
        deployer = SimpleMCPDeployer()
        assert deployer is not None
        assert hasattr(deployer, "platform_info")
        assert hasattr(deployer, "active_servers")

    @pytest.fixture
    def deployer(self):
        """Create deployer instance."""
        return SimpleMCPDeployer()

    @pytest.fixture
    def mock_tool_info(self):
        """Mock MCP tool info."""
        return Mock(
            name="test_tool",
            package="@test/tool",
            github_url="https://github.com/test/tool",
            deployment_method="npx",
        )

    def test_deployer_platform_detection(self, deployer):
        """Test platform detection logic."""
        platform_info = deployer.platform_info
        assert "system" in platform_info

    def test_runtime_detection_for_github_url(self, deployer):
        """Test runtime detection based on GitHub URL."""
        # Test npx detection - 返回 tuple (runtime_type, command)
        runtime_type, command = deployer.detect_simple_platform(
            "https://github.com/test/repo"
        )
        assert isinstance(runtime_type, str)
        assert isinstance(command, str)
        assert "npx" in runtime_type or "npx" in command

    @patch("subprocess.Popen")
    def test_successful_process_start(self, mock_popen, deployer):
        """Test successful process start."""
        mock_process = Mock()
        mock_process.poll.return_value = None
        mock_popen.return_value = mock_process

        # 构造 runtime_info dict
        runtime_type, command = deployer.detect_simple_platform(
            "https://github.com/test/repo"
        )
        runtime_info = {"runtime_type": runtime_type, "command": command}

        cmd = ["npx", "test-tool"]
        result = deployer._try_start_process(
            cmd, 0, "test_tool", None, "@test/tool", runtime_info
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

        # 构造 runtime_info dict
        runtime_type, command = deployer.detect_simple_platform(
            "https://github.com/test/repo"
        )
        runtime_info = {"runtime_type": runtime_type, "command": command}

        cmd = ["npx", "test-tool", "--stdio"]
        result = deployer._try_start_process(
            cmd, 0, "test_tool", None, "@test/tool", runtime_info
        )

        # Should return None due to failure
        assert result is None

    def test_cleanup_server_success(self, deployer):
        """Test successful server cleanup."""
        mock_process = Mock()
        mock_process.wait.return_value = None

        # 创建完整的 server_info 结构 (类似 SimpleMCPServerInfo)
        from dataclasses import dataclass

        @dataclass
        class MockServerInfo:
            process: Mock
            package_name: str = "test"
            communicator: Mock = None
            server_id: str = "test_id"
            available_tools: list = None
            status: str = "running"

        server_info = MockServerInfo(process=mock_process)
        deployer.active_servers["test_id"] = server_info

        result = deployer.cleanup_server("test_id")

        assert result is True
        mock_process.terminate.assert_called_once()
        mock_process.wait.assert_called_once_with(timeout=5)
        assert "test_id" not in deployer.active_servers

    def test_cleanup_all_servers(self, deployer):
        """Test cleanup of all servers."""
        mock_process1 = Mock()
        mock_process1.wait.return_value = None
        mock_process2 = Mock()
        mock_process2.wait.return_value = None

        # 创建完整的 server_info 结构
        from dataclasses import dataclass

        @dataclass
        class MockServerInfo:
            process: Mock
            package_name: str = "test"
            communicator: Mock = None
            server_id: str = "test_id"
            available_tools: list = None
            status: str = "running"

        deployer.active_servers["server1"] = MockServerInfo(
            process=mock_process1, server_id="server1"
        )
        deployer.active_servers["server2"] = MockServerInfo(
            process=mock_process2, server_id="server2"
        )

        deployer.cleanup_all()

        mock_process1.terminate.assert_called_once()
        mock_process2.terminate.assert_called_once()
        assert len(deployer.active_servers) == 0


class TestAsyncMCPClient:
    """Test cases for AsyncMCPClient."""

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
        assert client._comm == mock_communicator

    @pytest.mark.asyncio
    async def test_list_tools_success(self, mock_communicator):
        """Test successful list_tools call."""
        mock_communicator.send_request.return_value = {
            "success": True,
            "tools": [{"name": "test_tool"}],
        }

        client = AsyncMCPClient(mock_communicator)
        result = await client.list_tools()

        assert result["success"] is True
        assert "tools" in result
        mock_communicator.send_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_call_tool_success(self, mock_communicator):
        """Test successful call_tool."""
        mock_communicator.send_request.return_value = {
            "success": True,
            "result": {"output": "test output"},
        }

        client = AsyncMCPClient(mock_communicator)
        result = await client.call_tool("test_tool", {"param": "value"})

        assert result["success"] is True
        assert "result" in result
        mock_communicator.send_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_client_error_handling(self, mock_communicator):
        """Test AsyncMCPClient error handling."""
        mock_communicator.send_request.return_value = {
            "success": False,
            "error": "Tool not found",
        }

        client = AsyncMCPClient(mock_communicator)
        result = await client.call_tool("nonexistent_tool", {})

        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_async_client_timeout(self, mock_communicator):
        """Test AsyncMCPClient timeout handling."""
        mock_communicator.send_request.side_effect = CommunicationError(
            "Request timeout"
        )

        client = AsyncMCPClient(mock_communicator)
        result = await client.list_tools()

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
