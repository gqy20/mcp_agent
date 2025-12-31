"""ToolFinder - 工具查找和列表管理.

从 cli_handlers.py 提取：
- find_tool_info() - 查找工具信息的核心方法
- lookup_github_url_from_csv() - 从 CSV 中查找 GitHub URL
- infer_github_url_from_test_url() - 从测试 URL 推断 GitHub URL
- list_tools() - 列出工具的命令

遵循 Linus 原则：
- 每个方法只做一件事
- 清晰的职责分离
- 易于测试和维护
"""

from rich import print as rprint

from src.batch_mcp.utils.csv_parser import MCPToolInfo, get_mcp_parser


class ToolFinder:
    """工具查找器 - 负责查找和列出 MCP 工具."""

    def __init__(self, tester, input_detector):
        """初始化 ToolFinder.

        Args:
            tester: MCPTester 实例
            input_detector: InputTypeDetector 实例

        """
        self.tester = tester
        self._input_detector = input_detector

    def find_tool_info(self, url: str) -> MCPToolInfo | None:
        """查找工具信息 - 单一职责.

        Args:
            url: 工具 URL 或 HTTP MCP 端点

        Returns:
            MCPToolInfo | None: 工具信息对象

        """
        # 检查是否为 HTTP MCP 端点
        if self._input_detector.is_http_mcp_endpoint(url):
            return self._create_http_tool_info(url)

        rprint("[blue]🔍 在数据库中查找对应的MCP工具...[/blue]")
        tool_info = self.tester.find_tool_by_url(url)

        if not tool_info:
            rprint(f"[yellow]⚠️ 在数据库中未找到URL对应的MCP工具: {url}[/yellow]")
            rprint("[blue]🔍 尝试从GitHub分析项目信息...[/blue]")

            # 使用GitHub项目分析器获取工具信息
            try:
                from src.batch_mcp.core.mcp_table_updater import MCPTableUpdater

                updater = MCPTableUpdater()

                # 分析单个GitHub项目
                result = updater.analyze_github_project(url)
                if result and result.get("success"):
                    rprint(
                        f"[green]✅ 成功分析GitHub项目: {result.get('name', 'Unknown')}[/green]",
                    )

                    # 现在CSV解析器会自动尝试从GitHub获取信息，重新查找
                    tool_info = self.tester.find_tool_by_url(url)
                    if tool_info:
                        self._display_tool_info(tool_info)
                        return tool_info
                    rprint("[red]❌ 分析完成后仍未在数据库中找到工具信息[/red]")
                    return None
                rprint(
                    f"[red]❌ GitHub项目分析失败: {result.get('error', 'Unknown error')}[/red]",
                )
                return None

            except Exception as e:
                rprint(f"[red]❌ GitHub项目分析异常: {e}[/red]")
                rprint(
                    "[yellow]💡 提示: 可以使用 'batch-mcp list-tools --search <关键词>' 搜索可用工具[/yellow]",
                )
                return None

        self._display_tool_info(tool_info)
        return tool_info

    def lookup_github_url_from_csv(self, json_data: dict) -> str:
        """从CSV中查找GitHub URL.

        Args:
            json_data: 包含 tool_name 或 test_url 的字典

        Returns:
            str: GitHub URL 或空字符串

        """
        try:
            # 获取工具名称
            tool_name = json_data.get("tool_name", "")
            test_url = json_data.get("test_url", "")

            if not tool_name and not test_url:
                return ""

            # 使用CSV解析器查找工具
            parser = get_mcp_parser()
            if not parser.load_data():
                return ""

            # 尝试多种方式查找工具
            tool = None

            # 1. 通过工具名称查找
            if tool_name and tool_name != "Unknown":
                tools = parser.search_tools(tool_name)
                if tools:
                    tool = tools[0]

            # 2. 通过包名查找
            if not tool and test_url and test_url.startswith("@"):
                tool = parser.find_tool_by_package(test_url)

            # 3. 通过GitHub URL查找
            if not tool and test_url and test_url.startswith("https://github.com/"):
                tool = parser.find_tool_by_url(test_url)

            if tool and tool.github_url:
                return tool.github_url

        except Exception as e:
            rprint(f"[yellow]⚠️ 从CSV查找GitHub URL时出错: {e}[/yellow]")

        return ""

    def infer_github_url_from_test_url(self, test_url: str) -> str:
        """从test_url推断GitHub URL.

        Args:
            test_url: 测试 URL（可能是包名或 GitHub URL）

        Returns:
            str: 推断的 GitHub URL 或空字符串

        """
        if not test_url:
            return ""

        # 如果test_url已经是GitHub URL，直接返回
        if test_url.startswith("https://github.com/"):
            return test_url

        # 如果test_url是包名，尝试推断GitHub URL
        # 例如: @upstash/context7-mcp -> https://github.com/upstash/context7
        if test_url.startswith("@"):
            # 移除@符号并分割
            parts = test_url[1:].split("/")
            if len(parts) >= 2:
                owner = parts[0]
                repo = parts[1].split("@")[0]  # 移除版本号
                # 特殊处理一些常见的包名映射
                if owner == "upstash" and "context7" in repo:
                    return "https://github.com/upstash/context7"
                if owner == "modelcontextprotocol":
                    if "filesystem" in repo or "sequential-thinking" in repo:
                        return "https://github.com/modelcontextprotocol/servers"
                    return f"https://github.com/modelcontextprotocol/{repo}"
                # 默认映射
                return f"https://github.com/{owner}/{repo}"

        # 对于其他情况，无法推断，返回空字符串
        return ""

    def list_tools(
        self,
        category: str | None,
        search: str | None,
        limit: int,
        show_package: bool,
    ) -> None:
        """列出工具 - 简化实现.

        Args:
            category: 按类别过滤
            search: 搜索关键词
            limit: 结果数量限制
            show_package: 是否显示包名

        """
        try:
            parser, _ = self.tester._get_services()

            # 获取工具列表 - 无特殊情况处理
            if search:
                tools = parser.search_tools(search)
                rprint(f"[blue]🔍 搜索结果 '{search}': 找到 {len(tools)} 个工具[/blue]")
            elif category:
                tools = parser.get_tools_by_category(category)
                rprint(f"[blue]📂 类别 '{category}': 找到 {len(tools)} 个工具[/blue]")
            else:
                tools = parser.get_all_tools()
                rprint(f"[blue]📦 共找到 {len(tools)} 个可部署的 MCP 工具[/blue]")

            if not tools:
                rprint("[yellow]⚠️ 未找到匹配的工具[/yellow]")
                return

            # 限制并显示
            tools = tools[:limit] if len(tools) > limit else tools
            self._display_tools_table(tools, show_package)

        except Exception as e:
            rprint(f"[red]❌ 加载工具列表失败: {e}[/red]")
            raise

    def _display_tool_info(self, tool_info: MCPToolInfo) -> None:
        """显示工具信息 - 统一格式.

        Args:
            tool_info: MCP 工具信息对象

        """
        rprint(f"[green]✅ 找到工具: {tool_info.name}[/green]")
        rprint(f"[blue]👤 作者: {tool_info.author}[/blue]")
        rprint(f"[blue]📦 包名: {tool_info.package_name}[/blue]")
        rprint(f"[blue]📂 类别: {tool_info.category}[/blue]")
        rprint(f"[blue]📝 描述: {tool_info.description[:100]}...[/blue]")

        # 显示 LobeHub 评分信息
        if tool_info.lobehub_evaluate:
            rprint(f"[yellow]⭐ LobeHub 评分: {tool_info.lobehub_evaluate}[/yellow]")
            if tool_info.lobehub_score:
                rprint(f"[yellow]⭐ LobeHub 分数: {tool_info.lobehub_score}[/yellow]")
            if tool_info.lobehub_star_count:
                rprint(
                    f"[yellow]⭐ LobeHub 星标: {tool_info.lobehub_star_count}[/yellow]",
                )
            if tool_info.lobehub_fork_count:
                rprint(
                    f"[yellow]⭐ LobeHub 分支: {tool_info.lobehub_fork_count}[/yellow]",
                )

    def _display_tools_table(
        self,
        tools: list[MCPToolInfo],
        show_package: bool,
    ) -> None:
        """显示工具表格 - 简化实现.

        Args:
            tools: MCP 工具列表
            show_package: 是否显示包名

        """
        from rich.console import Console
        from rich.table import Table

        console = Console()
        table = Table(title="MCP 工具列表")

        table.add_column("名称", style="cyan", width=25)
        table.add_column("作者", style="magenta", width=15)
        table.add_column("类别", style="green", width=12)

        if show_package:
            table.add_column("包名", style="yellow", width=30)

        table.add_column("描述", style="white", width=40)
        table.add_column("API", style="red", width=5)

        for tool in tools:
            api_status = "🔑" if tool.requires_api_key else "🆓"
            name = tool.name[:23] + "..." if len(tool.name) > 25 else tool.name
            desc = (
                tool.description[:38] + "..."
                if len(tool.description) > 40
                else tool.description
            )

            row_data = [name, tool.author, tool.category.split("\n")[0]]

            if show_package:
                package = tool.package_name or "N/A"
                row_data.append(package[:28] + "..." if len(package) > 30 else package)

            row_data.extend([desc, api_status])
            table.add_row(*row_data)

        console.print(table)

    def _create_http_tool_info(self, url: str) -> MCPToolInfo:
        """为 HTTP MCP 端点创建工具信息.

        Args:
            url: HTTP MCP 端点 URL

        Returns:
            MCPToolInfo: HTTP MCP 工具信息对象

        """
        from urllib.parse import parse_qs, urlparse

        parsed = urlparse(url)

        # 生成工具名称 - 将域名中的点号和冒号都替换为连字符
        tool_name = f"http-mcp-{parsed.netloc.replace('.', '-').replace(':', '-')}"

        # 从查询参数提取配置
        headers = {}
        query_params = parse_qs(parsed.query)

        if "api_key" in query_params:
            headers["Authorization"] = f"Bearer {query_params['api_key'][0]}"
        elif "token" in query_params:
            headers["Authorization"] = f"Bearer {query_params['token'][0]}"

        return MCPToolInfo(
            name=tool_name,
            url=url,  # 使用 HTTP URL 作为 URL
            author="HTTP MCP Provider",
            github_url=None,  # HTTP MCP端点没有GitHub URL
            description=f"HTTP MCP endpoint at {parsed.netloc}",
            deployment_method="http",  # HTTP 部署方法
            category="HTTP MCP",
            package_name=tool_name,
            requires_api_key=bool(headers),  # 如果有headers则认为需要API key
            run_command=None,  # 不适用于 HTTP 端点
            install_command=None,
            api_requirements=["httpx"],  # HTTP客户端依赖
        )


# 全局 ToolFinder 实例
_tool_finder_instance = None


def get_tool_finder() -> ToolFinder:
    """获取全局 ToolFinder 实例.

    Returns:
        ToolFinder 单例实例

    """
    global _tool_finder_instance
    if _tool_finder_instance is None:
        from src.batch_mcp.core.input_type_detector import get_input_type_detector
        from src.batch_mcp.core.tester import get_mcp_tester

        _tool_finder_instance = ToolFinder(
            get_mcp_tester(),
            get_input_type_detector(),
        )
    return _tool_finder_instance
