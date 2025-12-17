"""Unit tests for evaluator functionality."""

from unittest.mock import Mock, patch

from src.batch_mcp.core.evaluator import (
    analyze_frequency,
    analyze_recency,
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

    @patch("src.core.evaluator.requests.get")
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

    @patch("src.core.evaluator.requests.get")
    def test_get_repo_data_not_found(self, mock_get):
        """Test repository data retrieval with 404 error."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("Not found")
        mock_get.return_value = mock_response

        result = get_repo_data("test", "nonexistent")

        assert result is None

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
        assert level == "N/A"

    def test_analyze_frequency_active_development(self):
        """Test frequency analysis with active development."""
        commit_data = [
            {"date": "2025-09-14T10:00:00Z"},
            {"date": "2025-09-13T10:00:00Z"},
            {"date": "2025-09-12T10:00:00Z"},
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
        assert level == "N/A"

    def test_evaluate_sustainability_complete_data(self):
        """Test sustainability evaluation with complete data."""
        repo_data = {
            "updated_at": "2025-09-14T10:00:00Z",
            "created_at": "2024-01-01T00:00:00Z",
        }
        commit_data = [
            {"date": "2025-09-14T10:00:00Z"},
            {"date": "2025-09-13T10:00:00Z"},
        ]
        closed_issues = [
            {"created_at": "2025-09-10T10:00:00Z", "closed_at": "2025-09-12T10:00:00Z"}
        ]
        closed_issues_count = 5

        result = evaluate_sustainability(
            repo_data, commit_data, closed_issues, closed_issues_count
        )

        assert "score" in result
        assert "level" in result
        assert "details" in result
        assert isinstance(result["score"], int)
        assert 0 <= result["score"] <= 100

    def test_evaluate_popularity_with_data(self):
        """Test popularity evaluation with data."""
        repo_data = {"stargazers_count": 100, "forks_count": 50, "watchers_count": 25}

        result = evaluate_popularity(repo_data)

        assert "score" in result
        assert "level" in result
        assert "details" in result
        assert isinstance(result["score"], int)
        assert 0 <= result["score"] <= 100

    def test_evaluate_popularity_missing_data(self):
        """Test popularity evaluation with missing data."""
        repo_data = {}

        result = evaluate_popularity(repo_data)

        assert result["score"] == 0
        assert result["level"] == "N/A"

    @patch("src.core.evaluator.get_repo_data")
    @patch("src.core.evaluator.get_commit_data")
    @patch("src.core.evaluator.get_issue_data")
    @patch("src.core.evaluator.get_closed_issues_count")
    def test_evaluate_full_repository_profile_success(
        self, mock_closed_count, mock_issues, mock_commits, mock_repo
    ):
        """Test full repository profile evaluation success."""
        mock_repo.return_value = {
            "name": "test-repo",
            "stargazers_count": 100,
            "updated_at": "2025-09-14T10:00:00Z",
        }
        mock_commits.return_value = [{"date": "2025-09-14T10:00:00Z"}]
        mock_issues.return_value = [
            {"created_at": "2025-09-10T10:00:00Z", "closed_at": "2025-09-12T10:00:00Z"}
        ]
        mock_closed_count.return_value = 5

        result = evaluate_full_repository_profile("https://github.com/test/repo")

        assert result["status"] == "success"
        assert "sustainability" in result
        assert "popularity" in result
        assert "overall_score" in result

    def test_evaluate_full_repository_profile_invalid_url(self):
        """Test full repository profile evaluation with invalid URL."""
        result = evaluate_full_repository_profile("https://example.com/test/repo")

        assert result["status"] == "error"
        assert "error" in result

    def test_evaluate_full_repository_profile_none_url(self):
        """Test full repository profile evaluation with None URL."""
        result = evaluate_full_repository_profile(None)

        assert result["status"] == "error"
        assert "error" in result
