"""GitHub API 调用模块.

此模块包含所有与 GitHub API 交互的函数，用于获取仓库、提交、issue等数据。
"""

import os
import re
from typing import Any

import requests

# --- API 和头部信息 ---
API_URL = "https://api.github.com"
HUB_TOKEN = os.environ.get("HUB_TOKEN")
HEADERS = {"Accept": "application/vnd.github.v3+json"}
if HUB_TOKEN:
    HEADERS["Authorization"] = f"token {HUB_TOKEN}"


def parse_github_url(url: str) -> tuple[str | None, str | None]:
    """解析GitHub URL获取owner和repo."""
    if not isinstance(url, str):
        return None, None
    match = re.search(r"github\.com/([^/]+)/([^/]+)", url)
    if match:
        owner, repo = match.groups()
        return owner, repo.replace(".git", "")
    return None, None


def get_repo_data(owner: str, repo: str) -> dict[str, Any]:
    """获取仓库数据."""
    url = f"{API_URL}/repos/{owner}/{repo}"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json()


def get_commit_data(owner: str, repo: str, limit: int = 100) -> list[dict[str, Any]]:
    """获取提交数据."""
    url = f"{API_URL}/repos/{owner}/{repo}/commits"
    params = {"per_page": limit}
    response = requests.get(url, headers=HEADERS, params=params)
    response.raise_for_status()
    return response.json()


def get_issue_data(
    owner: str,
    repo: str,
    state: str = "closed",
    limit: int = 100,
) -> list[dict[str, Any]]:
    """获取issue数据."""
    url = f"{API_URL}/repos/{owner}/{repo}/issues"
    params = {"per_page": limit, "state": state}
    response = requests.get(url, headers=HEADERS, params=params)
    response.raise_for_status()
    return response.json()


def get_closed_issues_count(owner: str, repo: str) -> int:
    """获取已关闭issue数量."""
    url = f"{API_URL}/search/issues"
    params = {"q": f"repo:{owner}/{repo} is:issue is:closed"}
    response = requests.get(url, headers=HEADERS, params=params)
    response.raise_for_status()
    return response.json().get("total_count", 0)
