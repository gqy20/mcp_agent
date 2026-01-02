"""GitHub MCP 分析器主类.

此模块提供 GitHub MCP 项目分析的主要逻辑。
"""

import csv


class GitHubMCPAnalyzer:
    """GitHub MCP项目自动分析器."""

    def __init__(self, github_token: str | None = None) -> None:
        """初始化分析器.

        Args:
            github_token: GitHub API token (可选，提高API限制)

        """
        from .patterns import MCP_KEYWORDS

        self.github_token = github_token
        self.headers = {"Accept": "application/vnd.github.v3+json"}
        if github_token:
            self.headers["Authorization"] = f"token {github_token}"

        # MCP相关关键词
        self.mcp_keywords = MCP_KEYWORDS

    def analyze_github_repo(self, github_url: str) -> dict | None:
        """分析GitHub仓库并生成MCP工具记录.

        Args:
            github_url: GitHub仓库URL

        Returns:
            包含MCP工具信息的字典，如果不是MCP项目则返回None

        """
        from .extractors import (
            is_mcp_project,
        )
        from .github_api import (
            get_readme_content,
            get_repo_info,
            parse_github_url,
        )
        from .record import generate_mcp_record

        try:
            # 解析GitHub URL
            owner, repo = parse_github_url(github_url)
            if not owner or not repo:
                return {"success": False, "error": "无法解析GitHub URL"}

            # 获取仓库信息
            repo_info = get_repo_info(owner, repo, self.headers)
            if not repo_info:
                return {"success": False, "error": "无法获取仓库信息"}

            # 获取README内容
            readme_content = get_readme_content(owner, repo, self.headers)
            if not readme_content:
                return {"success": False, "error": "无法获取README内容"}

            # 检查是否为MCP项目
            if not is_mcp_project(readme_content, self.mcp_keywords):
                return {
                    "success": False,
                    "error": "项目不是MCP工具",
                    "is_mcp_project": False,
                }

            # 分析MCP项目
            analysis_result = self._analyze_mcp_content(
                readme_content,
                repo_info,
            )

            # 生成标准化记录
            mcp_record = generate_mcp_record(
                github_url,
                repo_info,
                analysis_result,
            )

            return {"success": True, "record": mcp_record}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _analyze_mcp_content(self, content: str, repo_info: dict) -> dict:
        """分析MCP项目内容.

        Args:
            content: README内容
            repo_info: GitHub仓库信息

        Returns:
            分析结果字典

        """
        from .extractors import (
            check_api_key_requirement,
            extract_deployment_methods,
            extract_description,
            extract_installation_instructions,
            extract_package_info,
            extract_tech_stack,
            extract_tools,
            extract_use_cases,
        )

        deployment_methods = extract_deployment_methods(content)

        analysis = {
            "description": extract_description(content, repo_info),
            "deployment_methods": deployment_methods,
            "requires_api_key": check_api_key_requirement(content),
            "tech_stack": extract_tech_stack(content),
            "tools": extract_tools(content),
            "use_cases": extract_use_cases(content),
            "installation": extract_installation_instructions(content),
        }

        # 提取包名和部署命令信息
        package_info = extract_package_info(
            content,
            deployment_methods,
        )
        analysis.update(package_info)

        return analysis

    def batch_analyze_repos(self, github_urls: list[str]) -> list[dict]:
        """批量分析GitHub仓库.

        Args:
            github_urls: GitHub仓库URL列表

        Returns:
            分析结果列表

        """
        results = []

        for url in github_urls:
            result = self.analyze_github_repo(url)

            if result:
                results.append(result)
            else:
                pass

        return results

    def export_to_csv(self, results: list[dict], output_file: str) -> None:
        """导出结果到CSV文件.

        Args:
            results: 分析结果列表
            output_file: 输出CSV文件路径

        """
        if not results:
            return

        # 获取所有字段
        fieldnames = set()
        for result in results:
            fieldnames.update(result.keys())
        fieldnames = sorted(fieldnames)

        with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for result in results:
                writer.writerow(result)


def main() -> None:
    """测试函数."""
    analyzer = GitHubMCPAnalyzer()

    # 测试分析一个GitHub仓库
    test_url = "https://github.com/microsoft/playwright-mcp"
    result = analyzer.analyze_github_repo(test_url)

    if result:
        pass
    else:
        pass


if __name__ == "__main__":
    main()
