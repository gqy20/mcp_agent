"""Unit tests for evaluator functionality."""

from unittest.mock import Mock, patch

import pytest

from src.batch_mcp.core.evaluator import (
    analyze_frequency,
    analyze_recency,
    calculate_functionality_score,
    evaluate_full_repository_profile,
    evaluate_popularity,
    evaluate_sustainability,
    get_repo_data,
    parse_github_url,
)


class TestEvaluatorFunctions:
    """Test cases for evaluator functions."""

    def test_parse_github_url_valid(self):
        """Test parsing valid GitHub URLs."""
        owner, repo = parse_github_url("https://github.com/test/repo")
        assert owner == "test"
        assert repo == "repo"

    def test_parse_github_url_with_git(self):
        """Test parsing GitHub URL with .git extension."""
        owner, repo = parse_github_url("https://github.com/test/repo.git")
        assert owner == "test"
        assert repo == "repo"

    def test_parse_github_url_invalid(self):
        """Test parsing invalid GitHub URLs."""
        owner, repo = parse_github_url("https://example.com/test/repo")
        assert owner is None
        assert repo is None

    def test_parse_github_url_none(self):
        """Test parsing None URL."""
        owner, repo = parse_github_url(None)
        assert owner is None
        assert repo is None

    @patch("src.batch_mcp.core.evaluator.github_api.requests.get")
    def test_get_repo_data_success(self, mock_get):
        """Test successful repository data retrieval."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "name": "test-repo",
            "stargazers_count": 100,
            "forks_count": 50,
            "updated_at": "2025-09-15T10:00:00Z",
            "created_at": "2024-01-01T00:00:00Z",
            "open_issues_count": 10,
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = get_repo_data("test", "repo")

        assert result["name"] == "test-repo"
        assert result["stargazers_count"] == 100
        assert result["forks_count"] == 50

    @patch("src.batch_mcp.core.evaluator.github_api.requests.get")
    def test_get_repo_data_not_found(self, mock_get):
        """Test repository data retrieval with 404 error."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("Not found")
        mock_get.return_value = mock_response

        # get_repo_data 会抛出异常，因为 raise_for_status() 会抛出异常
        with pytest.raises(Exception, match="Not found"):
            get_repo_data("test", "nonexistent")

    def test_analyze_recency_recent_activity(self):
        """Test recency analysis with recent activity."""
        repo_data = {"updated_at": "2025-09-14T10:00:00Z"}

        score, level = analyze_recency(repo_data)

        assert isinstance(score, int)
        assert isinstance(level, str)
        assert 0 <= score <= 100

    def test_analyze_recency_old_activity(self):
        """Test recency analysis with old activity."""
        repo_data = {"updated_at": "2020-01-01T00:00:00Z"}

        score, level = analyze_recency(repo_data)

        assert isinstance(score, int)
        assert isinstance(level, str)
        assert 0 <= score <= 100

    def test_analyze_recency_missing_data(self):
        """Test recency analysis with missing data."""
        repo_data = {}

        score, level = analyze_recency(repo_data)

        assert score == 0
        assert level == "无法获取最后更新时间"

    def test_analyze_frequency_active_development(self):
        """Test frequency analysis with active development."""
        # 正确的 GitHub API commit 数据结构
        commit_data = [
            {"commit": {"author": {"date": "2025-09-14T10:00:00Z"}}},
            {"commit": {"author": {"date": "2025-09-13T10:00:00Z"}}},
            {"commit": {"author": {"date": "2025-09-12T10:00:00Z"}}},
        ]

        score, level = analyze_frequency(commit_data)

        assert isinstance(score, int)
        assert isinstance(level, str)
        assert 0 <= score <= 100

    def test_analyze_frequency_no_commits(self):
        """Test frequency analysis with no commits."""
        commit_data = []

        score, level = analyze_frequency(commit_data)

        assert score == 0
        assert level == "没有提交记录"

    def test_evaluate_sustainability_complete_data(self):
        """Test sustainability evaluation with complete data."""
        repo_data = {
            "updated_at": "2025-09-14T10:00:00Z",
            "created_at": "2024-01-01T00:00:00Z",
            "open_issues_count": 2,
        }
        # 正确的 commit 数据结构
        commit_data = [
            {"commit": {"author": {"date": "2025-09-14T10:00:00Z"}}},
            {"commit": {"author": {"date": "2025-09-13T10:00:00Z"}}},
        ]
        closed_issues = [
            {"created_at": "2025-09-10T10:00:00Z", "closed_at": "2025-09-12T10:00:00Z"}
        ]
        closed_issues_count = 5

        result = evaluate_sustainability(
            repo_data, commit_data, closed_issues, closed_issues_count
        )

        assert "total_score" in result
        assert "details" in result
        assert isinstance(result["total_score"], int)
        assert 0 <= result["total_score"] <= 100

    def test_evaluate_popularity_with_data(self):
        """Test popularity evaluation with data."""
        repo_data = {"stargazers_count": 100, "forks_count": 50, "watchers_count": 25}

        result = evaluate_popularity(repo_data)

        assert "total_score" in result
        assert "details" in result
        assert isinstance(result["total_score"], int)
        assert 0 <= result["total_score"] <= 100

    def test_evaluate_popularity_missing_data(self):
        """Test popularity evaluation with missing data."""
        repo_data = {}

        result = evaluate_popularity(repo_data)

        # 小众项目的分数是 stars(70 * 0.1) + forks(30 * 0.2) = 7 + 6 = 13
        assert result["total_score"] == 13
        assert "details" in result

    @patch("src.batch_mcp.core.evaluator.score_calculator.get_repo_data")
    @patch("src.batch_mcp.core.evaluator.score_calculator.get_commit_data")
    @patch("src.batch_mcp.core.evaluator.score_calculator.get_issue_data")
    @patch("src.batch_mcp.core.evaluator.score_calculator.get_closed_issues_count")
    def test_evaluate_full_repository_profile_success(
        self, mock_closed_count, mock_issues, mock_commits, mock_repo
    ):
        """Test full repository profile evaluation success."""
        mock_repo.return_value = {
            "name": "test-repo",
            "stargazers_count": 100,
            "updated_at": "2025-09-14T10:00:00Z",
            "open_issues_count": 2,
        }
        # 正确的 commit 数据结构
        mock_commits.return_value = [
            {"commit": {"author": {"date": "2025-09-14T10:00:00Z"}}}
        ]
        mock_issues.return_value = [
            {"created_at": "2025-09-10T10:00:00Z", "closed_at": "2025-09-12T10:00:00Z"}
        ]
        mock_closed_count.return_value = 5

        result = evaluate_full_repository_profile("https://github.com/test/repo")

        assert result["status"] == "success"
        assert "sustainability" in result
        assert "popularity" in result
        assert "final_score" in result

    def test_evaluate_full_repository_profile_invalid_url(self):
        """Test full repository profile evaluation with invalid URL."""
        result = evaluate_full_repository_profile("https://example.com/test/repo")

        assert result["status"] == "error"
        assert "message" in result

    def test_evaluate_full_repository_profile_none_url(self):
        """Test full repository profile evaluation with None URL."""
        result = evaluate_full_repository_profile(None)

        assert result["status"] == "error"
        assert "message" in result


class TestCalculateFunctionalityScoreFix:
    """Test calculate_functionality_score function type safety and edge cases."""

    def test_normal_confidence_values(self):
        """Test normal confidence values."""
        tool_tests = [
            {
                "test_name": "测试1",
                "success": True,
                "ai_confidence": 0.85,
                "test_category": "功能测试",
            },
            {
                "test_name": "测试2",
                "success": False,
                "ai_confidence": 0.75,
                "test_category": "功能测试",
            },
            {
                "test_name": "测试3",
                "success": True,
                "ai_confidence": 0.90,
                "test_category": "功能测试",
            },
        ]

        score = calculate_functionality_score(tool_tests)

        assert isinstance(score, (int, float))
        assert 70 <= score <= 75

    def test_missing_confidence_values(self):
        """Test missing confidence field."""
        tool_tests = [
            {
                "test_name": "测试1",
                "success": True,
                "test_category": "功能测试",
            },
            {
                "test_name": "测试2",
                "success": False,
                "test_category": "功能测试",
            },
        ]

        score = calculate_functionality_score(tool_tests)

        assert isinstance(score, (int, float))
        assert score == 35.0

    def test_none_confidence_values(self):
        """Test confidence is None."""
        tool_tests = [
            {
                "test_name": "测试1",
                "success": True,
                "ai_confidence": None,
                "test_category": "功能测试",
            },
            {
                "test_name": "测试2",
                "success": True,
                "ai_confidence": None,
                "test_category": "功能测试",
            },
        ]

        score = calculate_functionality_score(tool_tests)

        assert isinstance(score, (int, float))
        assert score == 70.0

    def test_list_confidence_values(self):
        """Test confidence as list type."""
        tool_tests = [
            {
                "test_name": "测试1",
                "success": True,
                "ai_confidence": [0.8, 0.9, 0.7],
                "test_category": "功能测试",
            },
            {
                "test_name": "测试2",
                "success": False,
                "ai_confidence": [0.6, 0.7],
                "test_category": "功能测试",
            },
        ]

        score = calculate_functionality_score(tool_tests)

        assert isinstance(score, (int, float))
        assert abs(score - 56.75) < 1e-10

    def test_mixed_confidence_types(self):
        """Test mixed confidence types."""
        tool_tests = [
            {
                "test_name": "正常数值",
                "success": True,
                "ai_confidence": 0.85,
                "test_category": "功能测试",
            },
            {
                "test_name": "整数类型",
                "success": True,
                "ai_confidence": 1,
                "test_category": "功能测试",
            },
            {
                "test_name": "列表类型",
                "success": False,
                "ai_confidence": [0.7, 0.8, 0.6],
                "test_category": "功能测试",
            },
            {
                "test_name": "缺失字段",
                "success": True,
                "test_category": "功能测试",
            },
            {
                "test_name": "None值",
                "success": False,
                "ai_confidence": None,
                "test_category": "功能测试",
            },
        ]

        score = calculate_functionality_score(tool_tests)

        assert isinstance(score, (int, float))
        assert 57 <= score <= 58

    def test_empty_list_with_numeric_elements(self):
        """Test list with mixed elements."""
        tool_tests = [
            {
                "test_name": "混合列表测试",
                "success": True,
                "ai_confidence": [0.8, "invalid", 0.9, None, 0.7],
                "test_category": "功能测试",
            },
        ]

        score = calculate_functionality_score(tool_tests)

        assert isinstance(score, (int, float))
        assert score == 94.0

    def test_empty_list_confidence(self):
        """Test empty list confidence."""
        tool_tests = [
            {
                "test_name": "空列表测试",
                "success": True,
                "ai_confidence": [],
                "test_category": "功能测试",
            },
        ]

        score = calculate_functionality_score(tool_tests)

        assert isinstance(score, (int, float))
        assert score == 70.0

    def test_empty_tool_tests(self):
        """Test empty tool tests list."""
        tool_tests = []

        score = calculate_functionality_score(tool_tests)

        assert score == 0.0

    def test_all_failed_tests(self):
        """Test all tests failed."""
        tool_tests = [
            {
                "test_name": "失败测试1",
                "success": False,
                "ai_confidence": 0.8,
                "test_category": "功能测试",
            },
            {
                "test_name": "失败测试2",
                "success": False,
                "ai_confidence": 0.9,
                "test_category": "功能测试",
            },
        ]

        score = calculate_functionality_score(tool_tests)

        assert isinstance(score, (int, float))
        assert abs(score - 25.5) < 1e-10
