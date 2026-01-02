"""URL解析器模块.

此模块包含URL到MCP工具的解析和映射函数。
"""

import re
from typing import TYPE_CHECKING

from src.batch_mcp.utils.csv_parser import MCPToolInfo

if TYPE_CHECKING:
    from src.batch_mcp.utils.csv_parser import MCPParser


class URLResolver:
    """URL到MCP工具的解析器."""

    def __init__(self, parser: "MCPParser") -> None:
        self.parser = parser

    def resolve_url_to_tool(self, url: str) -> MCPToolInfo | None:
        """将URL解析为MCP工具信息."""
        # 1. 直接URL匹配
        tool_info = self.parser.find_tool_by_url(url)
        if tool_info and tool_info.package_name:
            return tool_info

        # 如果URL匹配但缺少包名，先尝试构造
        if tool_info and not tool_info.package_name and "github.com" in url:
            constructed_package = self._construct_package_from_github_url(url)
            if constructed_package:
                tool_info.package_name = constructed_package
                return tool_info

        # 2. 从URL提取包名
        package_name = self._extract_package_from_url(url)
        if package_name:
            tool_info = self.parser.find_tool_by_package(package_name)
            if tool_info:
                return tool_info

        # 3. 智能搜索
        search_terms = self._extract_search_terms_from_url(url)
        for term in search_terms:
            tools = self.parser.search_tools(term)
            if tools:
                return tools[0]  # 取第一个匹配的

        # 4. 如果是GitHub URL，尝试构造包名
        if "github.com" in url:
            constructed_package = self._construct_package_from_github_url(url)
            if constructed_package:
                # 创建伪工具信息用于测试
                return MCPToolInfo(
                    name=f"GitHub Tool: {constructed_package}",
                    url=url,
                    author="Unknown",
                    github_url=url,
                    description=f"从GitHub URL {url} 构造的MCP工具",
                    category="GitHub Repository",
                    package_name=constructed_package,
                    requires_api_key=False,
                    api_requirements=[],
                )

        return None

    def _extract_package_from_url(self, url: str) -> str | None:
        """从URL提取NPM包名."""
        # 常见的NPM包URL模式
        patterns = [
            r"npmjs\.com/package/([^/]+(?:/[^/]+)?)",
            r"npm\.im/([^/]+(?:/[^/]+)?)",
            r"@([^/]+/[^/]+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    def extract_package_name(self, url: str) -> str | None:
        """从任意URL中推断可用于 npx 的包名/来源规范.

        优先顺序:
        1) 直接包含的 npm 包名（npmjs 链接或 @scope/name 形式）
        2) GitHub URL -> 返回 npx 可用的 github:owner/repo 规范
        3) 无法推断则返回 None.
        """
        # 直接提取 npm 包名
        pkg = self._extract_package_from_url(url)
        if pkg:
            return pkg

        # GitHub URL 回退
        if "github.com" in url:
            return self._construct_package_from_github_url(url)

        return None

    def _extract_search_terms_from_url(self, url: str) -> list[str]:
        """从URL提取搜索关键词."""
        terms = []

        # 从路径中提取词汇
        path_parts = re.findall(r"/([^/]+)", url)
        for part in path_parts:
            if len(part) > 2 and part not in ["www", "com", "org", "net"]:
                terms.append(part.replace("-", " ").replace("_", " "))

        return terms

    def _construct_package_from_github_url(self, url: str) -> str | None:
        """从GitHub URL构造可能的包名."""
        # 提取 github.com/username/repo 模式
        match = re.search(r"github\.com/([^/]+)/([^/]+)", url)
        if match:
            username, repo = match.groups()

            # 清理repo名称
            repo = repo.rstrip(".git")

            # 优先返回 npx 可直接执行的 GitHub 源规范
            # 参考: npx -y github:owner/repo
            return f"github:{username}/{repo}"

        return None
