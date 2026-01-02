"""GitHub API 调用函数.

此模块提供与 GitHub API 交互的功能。
"""

import base64
import urllib.parse

import requests


def parse_github_url(url: str) -> tuple[str | None, str | None]:
    """解析GitHub URL获取owner和repo.

    Args:
        url: GitHub仓库URL

    Returns:
        (owner, repo) 元组，解析失败返回 (None, None)

    """
    try:
        # 标准化URL
        url = url.lower().strip()
        if not url.startswith("https://github.com/"):
            return None, None

        # 移除.git后缀
        url = url.replace(".git", "")

        # 解析路径
        parsed = urllib.parse.urlparse(url)
        path_parts = parsed.path.strip("/").split("/")

        if len(path_parts) >= 2:
            return path_parts[0], path_parts[1]

        return None, None

    except Exception:
        return None, None


def get_repo_info(owner: str, repo: str, headers: dict) -> dict | None:
    """获取GitHub仓库信息.

    Args:
        owner: 仓库所有者
        repo: 仓库名称
        headers: HTTP请求头（包含认证信息）

    Returns:
        仓库信息字典，失败返回None

    """
    try:
        url = f"https://api.github.com/repos/{owner}/{repo}"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception:
        return None


def get_readme_content(owner: str, repo: str, headers: dict) -> str | None:
    """获取README内容.

    Args:
        owner: 仓库所有者
        repo: 仓库名称
        headers: HTTP请求头（包含认证信息）

    Returns:
        README内容字符串，失败返回None

    """
    try:
        # 尝试不同的README文件名
        readme_names = ["README.md", "README", "readme.md", "readme"]

        for readme_name in readme_names:
            url = f"https://api.github.com/repos/{owner}/{repo}/contents/{readme_name}"
            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                # 解码base64内容
                return base64.b64decode(response.json()["content"]).decode("utf-8")
            if response.status_code == 404:
                continue
            return None

        return None

    except Exception:
        return None
