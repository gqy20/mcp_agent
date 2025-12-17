"""Unit tests for evaluator functionality."""
import json
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.batch_mcp.core.evaluator import ToolEvaluator


class TestToolEvaluator:
    """Test cases for ToolEvaluator."""

    @pytest.fixture
    def sample_tool_info(self):
        """Sample tool information for testing."""
        return {
            "name": "test_tool",
            "package": "@test/tool",
            "description": "A test tool for evaluation",
            "author": "Test Author",
            "github_url": "https://github.com/test/tool",
            "homepage": "https://test-tool.example.com",
        }

    @pytest.fixture
    def evaluator(self):
        """Create a ToolEvaluator instance."""
        return ToolEvaluator()

    def test_evaluator_initialization(self, evaluator):
        """Test evaluator initialization."""
        assert evaluator is not None
        assert hasattr(evaluator, "evaluate_tool")

    def test_evaluate_tool_with_valid_info(self, evaluator, sample_tool_info):
        """Test tool evaluation with valid information."""
        with patch.object(evaluator, "_check_github_repo") as mock_github, patch.object(
            evaluator, "_analyze_documentation"
        ) as mock_docs, patch.object(
            evaluator, "_check_package_installation"
        ) as mock_install:
            mock_github.return_value = {"exists": True, "stars": 100}
            mock_docs.return_value = {"has_readme": True, "quality": 0.8}
            mock_install.return_value = {"installable": True, "dependencies": 5}

            result = evaluator.evaluate_tool(sample_tool_info)

            assert result["tool_name"] == "test_tool"
            assert result["evaluation_status"] == "completed"
            assert "overall_score" in result
            assert "criteria_scores" in result

    def test_evaluate_tool_with_missing_github(self, evaluator, sample_tool_info):
        """Test tool evaluation without GitHub URL."""
        sample_tool_info.pop("github_url")

        with patch.object(
            evaluator, "_analyze_documentation"
        ) as mock_docs, patch.object(
            evaluator, "_check_package_installation"
        ) as mock_install:
            mock_docs.return_value = {"has_readme": True, "quality": 0.8}
            mock_install.return_value = {"installable": True, "dependencies": 5}

            result = evaluator.evaluate_tool(sample_tool_info)

            assert result["tool_name"] == "test_tool"
            assert result["evaluation_status"] == "completed"
            assert "github_analysis" not in result

    def test_evaluate_tool_with_invalid_package(self, evaluator, sample_tool_info):
        """Test tool evaluation with invalid package name."""
        sample_tool_info["package"] = "invalid-package-name"

        with patch.object(evaluator, "_check_package_installation") as mock_install:
            mock_install.return_value = {
                "installable": False,
                "error": "Invalid package name",
            }

            result = evaluator.evaluate_tool(sample_tool_info)

            assert result["evaluation_status"] == "failed"
            assert "error" in result

    def test_calculate_overall_score(self, evaluator):
        """Test overall score calculation."""
        criteria_scores = {
            "functionality": 90,
            "documentation": 80,
            "performance": 85,
            "usability": 87,
        }

        overall_score = evaluator._calculate_overall_score(criteria_scores)

        assert isinstance(overall_score, (int, float))
        assert 0 <= overall_score <= 100

    def test_generate_recommendations(self, evaluator):
        """Test recommendation generation."""
        evaluation_result = {
            "criteria_scores": {
                "documentation": 60,
                "performance": 85,
                "usability": 90,
            },
            "issues_found": ["Missing API documentation"],
        }

        recommendations = evaluator._generate_recommendations(evaluation_result)

        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        assert any("documentation" in rec.lower() for rec in recommendations)

    def test_batch_evaluation(self, evaluator):
        """Test batch tool evaluation."""
        tools_to_evaluate = [
            {
                "name": "tool1",
                "package": "@test/tool1",
                "github_url": "https://github.com/test/tool1",
            },
            {
                "name": "tool2",
                "package": "@test/tool2",
                "github_url": "https://github.com/test/tool2",
            },
        ]

        with patch.object(evaluator, "evaluate_tool") as mock_evaluate:
            mock_evaluate.return_value = {
                "tool_name": "test_tool",
                "overall_score": 85.0,
                "evaluation_status": "completed",
            }

            results = evaluator.batch_evaluate(tools_to_evaluate)

            assert len(results) == 2
            assert mock_evaluate.call_count == 2

    def test_evaluation_timeout_handling(self, evaluator, sample_tool_info):
        """Test evaluation timeout handling."""
        with patch.object(evaluator, "_check_github_repo") as mock_github:
            mock_github.side_effect = TimeoutError("GitHub API timeout")

            result = evaluator.evaluate_tool(sample_tool_info)

            assert result["evaluation_status"] == "timeout"
            assert "timeout" in result.get("error", "").lower()

    def test_evaluation_error_handling(self, evaluator, sample_tool_info):
        """Test evaluation error handling."""
        with patch.object(evaluator, "_check_github_repo") as mock_github:
            mock_github.side_effect = Exception("Unexpected error")

            result = evaluator.evaluate_tool(sample_tool_info)

            assert result["evaluation_status"] == "error"
            assert "error" in result

    def test_save_evaluation_result(self, evaluator, sample_tool_info):
        """Test saving evaluation result."""
        evaluation_result = {
            "tool_name": "test_tool",
            "overall_score": 85.0,
            "evaluation_status": "completed",
        }

        with patch("builtins.open", mock_open()) as mock_file, patch(
            "json.dump"
        ) as mock_json_dump:
            evaluator.save_evaluation_result(evaluation_result, "test_result.json")

            mock_file.assert_called_once_with("test_result.json", "w")
            mock_json_dump.assert_called_once()

    def test_load_evaluation_criteria(self, evaluator):
        """Test loading evaluation criteria."""
        criteria = evaluator.get_evaluation_criteria()

        assert isinstance(criteria, dict)
        assert "functionality" in criteria
        assert "documentation" in criteria
        assert "performance" in criteria
        assert "usability" in criteria

        for criterion_name, criterion_info in criteria.items():
            assert "weight" in criterion_info
            assert "max_score" in criterion_info
            assert isinstance(criterion_info["weight"], (int, float))
            assert isinstance(criterion_info["max_score"], (int, float))
