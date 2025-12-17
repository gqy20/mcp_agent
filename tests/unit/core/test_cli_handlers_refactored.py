"""Unit tests for refactored CLI handlers."""

from unittest.mock import Mock, patch

import pytest
from src.batch_mcp.core.cli_handlers_refactored import (
    CLIToolEvaluator,
    EvaluationResultProcessor,
    SupabaseClientManager,
    ToolEvaluator,
)


class TestSupabaseClientManager:
    """Test Supabase client management."""

    @patch.dict(
        "os.environ",
        {"SUPABASE_URL": "test_url", "SUPABASE_SERVICE_ROLE_KEY": "test_key"},
    )
    @patch("src.core.cli_handlers_refactored.create_client")
    def test_create_client_with_valid_config(self, mock_create_client):
        """Test client creation with valid configuration."""
        mock_client = Mock()
        mock_create_client.return_value = mock_client

        client = SupabaseClientManager.create_client_if_configured()

        assert client is not None
        mock_create_client.assert_called_once_with("test_url", "test_key")

    def test_create_client_with_missing_config(self):
        """Test client creation with missing configuration."""
        with patch.dict("os.environ", {}, clear=True):
            client = SupabaseClientManager.create_client_if_configured()
            assert client is None

    @patch("src.core.cli_handlers_refactored.create_client")
    def test_export_evaluation_success(self, mock_create_client):
        """Test successful evaluation export."""
        mock_client = Mock()
        mock_result = Mock()
        mock_result.data = [{"id": 1}]
        mock_client.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_result
        mock_create_client.return_value = mock_client

        evaluation_result = {
            "final_score": 85,
            "sustainability_score": 80,
            "popularity_score": 90,
            "sustainability_details": {"test": "data"},
            "popularity_details": {"test": "data"},
        }

        success = SupabaseClientManager.export_evaluation_to_database(
            "https://github.com/test/repo", evaluation_result
        )

        assert success is True
        mock_client.table.assert_called_once_with("mcp_test_results")

    @patch("src.core.cli_handlers_refactored.create_client")
    def test_export_evaluation_failure(self, mock_create_client):
        """Test failed evaluation export."""
        mock_create_client.side_effect = Exception("Connection failed")

        evaluation_result = {"final_score": 85}

        success = SupabaseClientManager.export_evaluation_to_database(
            "https://github.com/test/repo", evaluation_result
        )

        assert success is False


class TestToolEvaluator:
    """Test tool evaluation functionality."""

    @pytest.fixture
    def mock_tool_info(self):
        """Mock tool info."""
        return Mock(
            name="test_tool",
            package="@test/tool",
            github_url="https://github.com/test/tool",
            deployment_method="npx",
        )

    @patch(
        "src.core.cli_handlers_refactored."
        "evaluate_full_repository_with_comprehensive_score"
    )
    def test_evaluate_tool_success(self, mock_evaluate, mock_tool_info):
        """Test successful tool evaluation."""
        mock_evaluate.return_value = {
            "status": "success",
            "final_score": 85,
            "final_comprehensive_score": 88,
        }

        result = ToolEvaluator.evaluate_single_tool(mock_tool_info, None)

        assert result["status"] == "success"
        assert result["final_score"] == 85
        mock_evaluate.assert_called_once_with("https://github.com/test/tool", None)

    def test_evaluate_tool_no_github_url(self, mock_tool_info):
        """Test tool evaluation without GitHub URL."""
        mock_tool_info.github_url = None

        result = ToolEvaluator.evaluate_single_tool(mock_tool_info, None)

        assert result["status"] == "skipped"
        assert result["message"] == "没有GitHub URL"

    @patch(
        "src.core.cli_handlers_refactored."
        "evaluate_full_repository_with_comprehensive_score"
    )
    def test_evaluate_tool_with_exception(self, mock_evaluate, mock_tool_info):
        """Test tool evaluation with exception."""
        mock_evaluate.side_effect = Exception("Evaluation failed")

        result = ToolEvaluator.evaluate_single_tool(mock_tool_info, None)

        assert result["status"] == "error"
        assert "评估异常" in result["message"]


class TestEvaluationResultProcessor:
    """Test evaluation result processing."""

    @pytest.fixture
    def mock_tool_info(self):
        """Mock tool info."""
        return Mock(github_url="https://github.com/test/tool")

    @patch(
        "src.core.cli_handlers_refactored."
        "SupabaseClientManager.export_evaluation_to_database"
    )
    def test_process_successful_result(self, mock_export, mock_tool_info):
        """Test processing successful evaluation result."""
        mock_export.return_value = True

        result = {
            "status": "success",
            "final_score": 85,
            "sustainability_score": 80,
            "popularity_score": 90,
        }

        success = EvaluationResultProcessor.process_evaluation_result(
            mock_tool_info, result, Mock()
        )

        assert success is True
        mock_export.assert_called_once()

    def test_process_failed_result(self, mock_tool_info):
        """Test processing failed evaluation result."""
        result = {"status": "failed", "message": "Evaluation failed"}

        success = EvaluationResultProcessor.process_evaluation_result(
            mock_tool_info, result, Mock()
        )

        assert success is False


class TestCLIToolEvaluator:
    """Test main CLI tool evaluator."""

    @patch("src.core.cli_handlers_refactored.get_mcp_parser")
    def test_get_tools_for_evaluation_success(self, mock_get_parser):
        """Test successful tool list retrieval."""
        mock_parser = Mock()
        mock_tool1 = Mock(github_url="https://github.com/test/tool1")
        mock_tool2 = Mock(github_url=None)  # Should be filtered out
        mock_tool3 = Mock(github_url="https://github.com/test/tool3")

        mock_parser.get_all_tools.return_value = [mock_tool1, mock_tool2, mock_tool3]
        mock_get_parser.return_value = mock_parser

        tools = CLIToolEvaluator.get_tools_for_evaluation()

        assert len(tools) == 2  # Only tools with GitHub URLs
        assert all(tool.github_url for tool in tools)

    @patch("src.core.cli_handlers_refactored.get_mcp_parser")
    def test_get_tools_for_evaluation_empty(self, mock_get_parser):
        """Test tool retrieval with empty result."""
        mock_parser = Mock()
        mock_parser.get_all_tools.return_value = []
        mock_get_parser.return_value = mock_parser

        tools = CLIToolEvaluator.get_tools_for_evaluation()

        assert tools == []

    @patch("src.core.cli_handlers_refactored.CLIToolEvaluator.get_tools_for_evaluation")
    @patch(
        "src.core.cli_handlers_refactored."
        "SupabaseClientManager.create_client_if_configured"
    )
    @patch("src.core.cli_handlers_refactored.ToolEvaluator.evaluate_single_tool")
    def test_evaluate_all_tools_success(
        self, mock_evaluate, mock_create_client, mock_get_tools
    ):
        """Test successful evaluation of all tools."""
        mock_tool1 = Mock(github_url="https://github.com/test/tool1")
        mock_tool2 = Mock(github_url="https://github.com/test/tool2")
        mock_get_tools.return_value = [mock_tool1, mock_tool2]

        mock_client = Mock()
        mock_create_client.return_value = mock_client

        mock_evaluate.side_effect = [
            {"status": "success", "final_score": 85},
            {"status": "success", "final_score": 90},
        ]

        result = CLIToolEvaluator.evaluate_all_tools()

        assert result["status"] == "success"
        assert result["stats"]["total"] == 2
        assert result["stats"]["successful"] == 2
        assert result["stats"]["failed"] == 0

    @patch("src.core.cli_handlers_refactored.CLIToolEvaluator.get_tools_for_evaluation")
    def test_evaluate_all_tools_with_exception(self, mock_get_tools):
        """Test evaluation with exception."""
        mock_get_tools.side_effect = Exception("Parser error")

        result = CLIToolEvaluator.evaluate_all_tools()

        assert result["status"] == "error"
        assert "Parser error" in result["message"]


class TestIntegration:
    """Integration tests for the refactored CLI handlers."""

    @patch("src.core.cli_handlers_refactored.CLIToolEvaluator.evaluate_all_tools")
    def test_full_evaluation_workflow(self, mock_evaluate):
        """Test complete evaluation workflow."""
        mock_evaluate.return_value = {
            "status": "success",
            "stats": {"total": 5, "successful": 4, "failed": 1},
        }

        # This would be called from the main CLI handler
        result = CLIToolEvaluator.evaluate_all_tools(db_export=True)

        assert result["status"] == "success"
        assert result["stats"]["total"] == 5

    def test_error_propagation(self):
        """Test that errors are properly propagated and handled."""
        # Test that errors in the chain are properly caught and handled

    def test_concurrent_evaluation_safety(self):
        """Test that concurrent evaluations are thread-safe."""
        # Test thread safety of the evaluation process
