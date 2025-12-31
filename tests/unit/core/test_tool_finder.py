"""ToolFinder 单元测试.

测试覆盖：
1. find_tool_info() - HTTP MCP 端点检测
2. find_tool_info() - 从数据库查找工具
3. find_tool_info() - 使用 GitHub 分析器（需要 mock）
4. lookup_github_url_from_csv() - 通过工具名称查找
5. lookup_github_url_from_csv() - 通过包名查找
6. lookup_github_url_from_csv() - 通过 GitHub URL 查找
7. infer_github_url_from_test_url() - 包名到 GitHub URL 映射
8. infer_github_url_from_test_url() - 特殊包名处理
9. list_tools() - 搜索功能
10. list_tools() - 分类过滤
"""

from unittest.mock import MagicMock, patch

from src.batch_mcp.utils.csv_parser import MCPToolInfo


class TestToolFinder:
    """ToolFinder 测试类."""

    def setup_method(self):
        """每个测试前的设置."""
        # 使用单例模式获取 ToolFinder
        from src.batch_mcp.core.tool_finder import ToolFinder

        # 创建 mock tester
        self.mock_tester = MagicMock()
        self.mock_input_detector = MagicMock()

        # 创建独立的 ToolFinder 实例用于测试
        self.finder = ToolFinder(self.mock_tester, self.mock_input_detector)

    # ===== find_tool_info() 测试 =====

    def test_find_tool_info_with_http_endpoint(self):
        """测试查找 HTTP MCP 端点工具信息."""
        # 设置 mock: HTTP MCP 端点检测
        self.mock_input_detector.is_http_mcp_endpoint.return_value = True

        url = "http://localhost:8080/mcp"
        result = self.finder.find_tool_info(url)

        # 应该返回 HTTP MCP 工具信息
        assert result is not None
        assert result.deployment_method == "http"
        assert result.name == "http-mcp-localhost-8080"
        assert "localhost" in result.description

    def test_find_tool_info_from_database(self):
        """测试从数据库查找工具信息."""
        # 设置 mock: 不是 HTTP MCP 端点
        self.mock_input_detector.is_http_mcp_endpoint.return_value = False

        # 设置 mock: 从 tester 找到工具
        mock_tool = MCPToolInfo(
            name="context7",
            url="https://github.com/upstash/context7",
            author="upstash",
            github_url="https://github.com/upstash/context7",
            description="Context7 MCP server",
            deployment_method="npx",
            package_name="@upstash/context7-mcp",
        )
        self.mock_tester.find_tool_by_url.return_value = mock_tool

        url = "https://github.com/upstash/context7"
        result = self.finder.find_tool_info(url)

        assert result is not None
        assert result.name == "context7"
        assert result.github_url == url

    def test_find_tool_info_not_found(self):
        """测试工具信息未找到."""
        # 设置 mock: 不是 HTTP MCP 端点
        self.mock_input_detector.is_http_mcp_endpoint.return_value = False

        # 设置 mock: 从 tester 找不到工具
        self.mock_tester.find_tool_by_url.return_value = None

        # Mock MCPTableUpdater 返回失败 - 在导入位置 patch
        with patch(
            "src.batch_mcp.core.mcp_table_updater.MCPTableUpdater"
        ) as mock_updater_class:
            mock_updater_instance = MagicMock()
            mock_updater_instance.analyze_github_project.return_value = {
                "success": False,
                "error": "Test error",
            }
            mock_updater_class.return_value = mock_updater_instance

            url = "https://github.com/unknown/repo"
            result = self.finder.find_tool_info(url)

            assert result is None

    # ===== lookup_github_url_from_csv() 测试 =====

    def test_lookup_github_url_by_tool_name(self):
        """测试通过工具名称查找 GitHub URL."""
        # Mock CSV parser
        mock_tool = MCPToolInfo(
            name="context7",
            url="https://github.com/upstash/context7",
            author="upstash",
            github_url="https://github.com/upstash/context7",
            description="Context7 MCP server",
            deployment_method="npx",
        )

        with patch("src.batch_mcp.core.tool_finder.get_mcp_parser") as mock_get_parser:
            mock_parser = MagicMock()
            mock_parser.load_data.return_value = True
            mock_parser.search_tools.return_value = [mock_tool]
            mock_get_parser.return_value = mock_parser

            json_data = {"tool_name": "context7"}
            result = self.finder.lookup_github_url_from_csv(json_data)

            assert result == "https://github.com/upstash/context7"

    def test_lookup_github_url_by_package_name(self):
        """测试通过包名查找 GitHub URL."""
        mock_tool = MCPToolInfo(
            name="context7",
            url="https://github.com/upstash/context7",
            author="upstash",
            github_url="https://github.com/upstash/context7",
            description="Context7 MCP server",
            deployment_method="npx",
        )

        with patch("src.batch_mcp.core.tool_finder.get_mcp_parser") as mock_get_parser:
            mock_parser = MagicMock()
            mock_parser.load_data.return_value = True
            # search_tools 返回空列表
            mock_parser.search_tools.return_value = []
            # find_tool_by_package 返回工具
            mock_parser.find_tool_by_package.return_value = mock_tool
            mock_get_parser.return_value = mock_parser

            json_data = {"test_url": "@upstash/context7-mcp"}
            result = self.finder.lookup_github_url_from_csv(json_data)

            assert result == "https://github.com/upstash/context7"

    def test_lookup_github_url_by_github_url(self):
        """测试通过 GitHub URL 查找."""
        mock_tool = MCPToolInfo(
            name="context7",
            url="https://github.com/upstash/context7",
            author="upstash",
            github_url="https://github.com/upstash/context7",
            description="Context7 MCP server",
            deployment_method="npx",
        )

        with patch("src.batch_mcp.core.tool_finder.get_mcp_parser") as mock_get_parser:
            mock_parser = MagicMock()
            mock_parser.load_data.return_value = True
            mock_parser.search_tools.return_value = []
            mock_parser.find_tool_by_package.return_value = None
            mock_parser.find_tool_by_url.return_value = mock_tool
            mock_get_parser.return_value = mock_parser

            json_data = {"test_url": "https://github.com/upstash/context7"}
            result = self.finder.lookup_github_url_from_csv(json_data)

            assert result == "https://github.com/upstash/context7"

    def test_lookup_github_url_not_found(self):
        """测试未找到 GitHub URL."""
        with patch("src.batch_mcp.core.tool_finder.get_mcp_parser") as mock_get_parser:
            mock_parser = MagicMock()
            mock_parser.load_data.return_value = True
            mock_parser.search_tools.return_value = []
            mock_parser.find_tool_by_package.return_value = None
            mock_parser.find_tool_by_url.return_value = None
            mock_get_parser.return_value = mock_parser

            json_data = {"tool_name": "unknown"}
            result = self.finder.lookup_github_url_from_csv(json_data)

            assert result == ""

    # ===== infer_github_url_from_test_url() 测试 =====

    def test_infer_github_url_already_github_url(self):
        """测试已经是 GitHub URL 的情况."""
        url = "https://github.com/upstash/context7"
        result = self.finder.infer_github_url_from_test_url(url)

        assert result == url

    def test_infer_github_url_from_package_name(self):
        """测试从包名推断 GitHub URL."""
        url = "@upstash/context7-mcp"
        result = self.finder.infer_github_url_from_test_url(url)

        assert result == "https://github.com/upstash/context7"

    def test_infer_github_url_special_context7(self):
        """测试 context7 特殊处理."""
        url = "@upstash/context7-mcp-server@1.0.0"
        result = self.finder.infer_github_url_from_test_url(url)

        assert result == "https://github.com/upstash/context7"

    def test_infer_github_url_modelcontextprotocol(self):
        """测试 modelcontextprotocol 包名."""
        url = "@modelcontextprotocol/server-filesystem"
        result = self.finder.infer_github_url_from_test_url(url)

        assert result == "https://github.com/modelcontextprotocol/servers"

    def test_infer_github_url_default_mapping(self):
        """测试默认包名映射."""
        url = "@owner/repo-name"
        result = self.finder.infer_github_url_from_test_url(url)

        assert result == "https://github.com/owner/repo-name"

    def test_infer_github_url_empty_input(self):
        """测试空输入."""
        result = self.finder.infer_github_url_from_test_url("")
        assert result == ""

    def test_infer_github_url_unsupported_format(self):
        """测试不支持的格式."""
        result = self.finder.infer_github_url_from_test_url(
            "https://example.com/not-github"
        )
        assert result == ""

    # ===== list_tools() 测试 =====

    def test_list_tools_with_search(self):
        """测试搜索工具."""
        mock_tool = MCPToolInfo(
            name="context7",
            url="https://github.com/upstash/context7",
            author="upstash",
            github_url="https://github.com/upstash/context7",
            description="Context7 MCP server",
            deployment_method="npx",
        )

        # Mock parser
        mock_parser = MagicMock()
        mock_parser.search_tools.return_value = [mock_tool]

        # Mock tester._get_services()
        self.mock_tester._get_services.return_value = (mock_parser, MagicMock())

        # list_tools 调用搜索
        self.finder.list_tools(
            category=None, search="context7", limit=10, show_package=False
        )

        # 验证调用
        mock_parser.search_tools.assert_called_once_with("context7")

    def test_list_tools_with_category(self):
        """测试按类别过滤工具."""
        mock_tool = MCPToolInfo(
            name="context7",
            url="https://github.com/upstash/context7",
            author="upstash",
            github_url="https://github.com/upstash/context7",
            description="Context7 MCP server",
            deployment_method="npx",
            category="Developer Tools",
        )

        # Mock parser
        mock_parser = MagicMock()
        mock_parser.get_tools_by_category.return_value = [mock_tool]

        # Mock tester._get_services()
        self.mock_tester._get_services.return_value = (mock_parser, MagicMock())

        self.finder.list_tools(
            category="Developer Tools", search=None, limit=10, show_package=False
        )

        mock_parser.get_tools_by_category.assert_called_once_with("Developer Tools")

    def test_list_tools_all(self):
        """测试列出所有工具."""
        # Mock parser
        mock_parser = MagicMock()
        mock_parser.get_all_tools.return_value = []

        # Mock tester._get_services()
        self.mock_tester._get_services.return_value = (mock_parser, MagicMock())

        self.finder.list_tools(category=None, search=None, limit=10, show_package=False)

        mock_parser.get_all_tools.assert_called_once()

    # ===== get_tool_finder() 单例测试 =====

    def test_get_tool_finder_singleton(self):
        """测试 get_tool_finder 返回单例."""
        from src.batch_mcp.core.tool_finder import get_tool_finder

        finder1 = get_tool_finder()
        finder2 = get_tool_finder()

        # 应该是同一个实例
        assert finder1 is finder2
