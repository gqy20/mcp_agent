"""Unit tests for tester functionality."""

from unittest.mock import mock_open, patch

import pytest

try:
    from src.batch_mcp.core.tester import MCTester
except ImportError:
    MCTester = None


class TestMCTester:
    """Test cases for MCTester."""

    @pytest.fixture
    def sample_mcp_config(self):
        """Sample MCP configuration for testing."""
        return {
            "mcpServers": {
                "test_server": {
                    "command": "node",
                    "args": ["test_script.js"],
                    "env": {"NODE_ENV": "test"},
                }
            }
        }

    @pytest.fixture
    def tester(self):
        """Create an MCTester instance."""
        return MCTester()

    def test_tester_initialization(self, tester):
        """Test tester initialization."""
        assert tester is not None
        assert hasattr(tester, "test_mcp_server")
        assert hasattr(tester, "test_mcp_tool")

    @pytest.mark.asyncio
    async def test_test_mcp_server_success(self, tester, sample_mcp_config):
        """Test successful MCP server testing."""
        with (
            patch.object(tester, "_start_mcp_server") as mock_start,
            patch.object(tester, "_check_server_health") as mock_health,
            patch.object(tester, "_list_server_tools") as mock_tools,
            patch.object(tester, "_stop_mcp_server"),
        ):
            mock_start.return_value = {"pid": 1234, "port": 8080}
            mock_health.return_value = {"healthy": True, "response_time": 0.5}
            mock_tools.return_value = ["tool1", "tool2", "tool3"]

            result = await tester.test_mcp_server(
                sample_mcp_config["mcpServers"]["test_server"]
            )

            assert result["server_name"] == "test_server"
            assert result["test_status"] == "success"
            assert result["startup_time"] > 0
            assert result["tool_count"] == 3

    @pytest.mark.asyncio
    async def test_test_mcp_server_startup_failure(self, tester, sample_mcp_config):
        """Test MCP server startup failure."""
        with patch.object(tester, "_start_mcp_server") as mock_start:
            mock_start.return_value = {"error": "Failed to start server"}

            result = await tester.test_mcp_server(
                sample_mcp_config["mcpServers"]["test_server"]
            )

            assert result["test_status"] == "failed"
            assert "error" in result

    @pytest.mark.asyncio
    async def test_test_mcp_server_timeout(self, tester, sample_mcp_config):
        """Test MCP server timeout."""
        with patch.object(tester, "_start_mcp_server") as mock_start:
            mock_start.side_effect = TimeoutError("Server startup timeout")

            result = await tester.test_mcp_server(
                sample_mcp_config["mcpServers"]["test_server"]
            )

            assert result["test_status"] == "timeout"
            assert "timeout" in result.get("error", "").lower()

    @pytest.mark.asyncio
    async def test_test_mcp_tool_success(self, tester):
        """Test successful MCP tool testing."""
        tool_config = {"name": "test_tool", "parameters": {"param1": "value1"}}

        with patch.object(tester, "_call_mcp_tool") as mock_call:
            mock_call.return_value = {
                "success": True,
                "result": {"output": "test result"},
                "execution_time": 1.2,
            }

            result = await tester.test_mcp_tool("test_server", tool_config)

            assert result["tool_name"] == "test_tool"
            assert result["test_status"] == "success"
            assert result["execution_time"] == 1.2
            assert "result" in result

    @pytest.mark.asyncio
    async def test_test_mcp_tool_error(self, tester):
        """Test MCP tool error."""
        tool_config = {"name": "test_tool", "parameters": {"param1": "value1"}}

        with patch.object(tester, "_call_mcp_tool") as mock_call:
            mock_call.return_value = {
                "success": False,
                "error": "Tool execution failed",
                "execution_time": 0.5,
            }

            result = await tester.test_mcp_tool("test_server", tool_config)

            assert result["test_status"] == "error"
            assert "error" in result

    def test_validate_test_configuration(self, tester):
        """Test test configuration validation."""
        valid_config = {"command": "node", "args": ["test.js"]}

        is_valid = tester.validate_test_configuration(valid_config)
        assert is_valid is True

        invalid_config = {"command": "node"}
        is_valid = tester.validate_test_configuration(invalid_config)
        assert is_valid is False

    def test_generate_test_report(self, tester):
        """Test test report generation."""
        test_results = [
            {
                "test_name": "server_startup",
                "status": "success",
                "duration": 2.5,
                "details": {"startup_time": 1.2},
            },
            {
                "test_name": "tool_execution",
                "status": "success",
                "duration": 1.8,
                "details": {"tool_count": 5},
            },
        ]

        report = tester.generate_test_report(test_results)

        assert report["total_tests"] == 2
        assert report["passed_tests"] == 2
        assert report["failed_tests"] == 0
        assert report["total_duration"] > 0
        assert "test_results" in report

    @pytest.mark.asyncio
    async def test_run_comprehensive_test_suite(self, tester, sample_mcp_config):
        """Test comprehensive test suite execution."""
        test_suite = {
            "server_tests": True,
            "tool_tests": True,
            "performance_tests": True,
            "stress_tests": False,
        }

        with (
            patch.object(tester, "test_mcp_server") as mock_server_test,
            patch.object(tester, "test_mcp_tool") as mock_tool_test,
        ):
            mock_server_test.return_value = {
                "test_status": "success",
                "startup_time": 1.2,
                "tool_count": 3,
            }

            mock_tool_test.return_value = {
                "test_status": "success",
                "execution_time": 0.8,
            }

            result = await tester.run_comprehensive_test_suite(
                sample_mcp_config["mcpServers"]["test_server"], test_suite
            )

            assert result["overall_status"] == "success"
            assert "server_tests" in result
            assert "tool_tests" in result
            assert "summary" in result

    def test_save_test_results(self, tester):
        """Test saving test results."""
        test_results = {
            "test_name": "comprehensive_test",
            "status": "success",
            "results": [],
            "summary": {"total": 10, "passed": 8, "failed": 2},
        }

        with (
            patch("builtins.open", mock_open()) as mock_file,
            patch("json.dump") as mock_json_dump,
        ):
            tester.save_test_results(test_results, "test_results.json")

            mock_file.assert_called_once_with("test_results.json", "w")
            mock_json_dump.assert_called_once()

    def test_test_result_analysis(self, tester):
        """Test test result analysis."""
        test_results = [
            {"test_name": "test1", "status": "success", "duration": 1.0},
            {
                "test_name": "test2",
                "status": "failed",
                "duration": 2.0,
                "error": "Timeout",
            },
            {"test_name": "test3", "status": "success", "duration": 0.5},
        ]

        analysis = tester.analyze_test_results(test_results)

        assert analysis["total_tests"] == 3
        assert analysis["passed_tests"] == 2
        assert analysis["failed_tests"] == 1
        assert analysis["success_rate"] == pytest.approx(66.67, rel=1e-2)
        assert analysis["average_duration"] == pytest.approx(1.17, rel=1e-2)
        assert "failures" in analysis
        assert len(analysis["failures"]) == 1

    def test_test_configuration_templates(self, tester):
        """Test test configuration templates."""
        templates = tester.get_test_configuration_templates()

        assert isinstance(templates, dict)
        assert "quick_test" in templates
        assert "comprehensive_test" in templates
        assert "performance_test" in templates

        for template_config in templates.values():
            assert isinstance(template_config, dict)
            assert "description" in template_config
            assert "tests" in template_config
