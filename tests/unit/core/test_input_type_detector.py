"""InputTypeDetector 单元测试.

测试覆盖：
1. 检测各种输入类型（HTTP端点、GitHub URL、包名、搜索查询）
2. HTTP MCP端点检测的各种场景
3. 配置自适应调整
4. 边界情况和特殊情况
"""

from src.batch_mcp.core.input_type_detector import InputType, InputTypeDetector
from src.batch_mcp.core.tester import TestConfig


class TestInputTypeDetector:
    """InputTypeDetector 测试类."""

    def setup_method(self):
        """每个测试前的设置."""
        self.detector = InputTypeDetector()

    # ===== 输入类型检测测试 =====

    def test_detect_http_endpoint_with_standard_path(self):
        """测试检测标准HTTP MCP端点."""
        result = self.detector.detect("https://api.example.com/mcp")
        assert result == InputType.HTTP_ENDPOINT

    def test_detect_http_endpoint_with_api_path(self):
        """测试检测API风格的HTTP MCP端点."""
        result = self.detector.detect("https://api.example.com/api/mcp")
        assert result == InputType.HTTP_ENDPOINT

    def test_detect_http_endpoint_with_port(self):
        """测试检测带端口的HTTP MCP端点."""
        result = self.detector.detect("http://localhost:8080/mcp")
        assert result == InputType.HTTP_ENDPOINT

    def test_detect_http_endpoint_with_query_params(self):
        """测试检测带查询参数的HTTP MCP端点."""
        result = self.detector.detect("https://api.example.com/mcp?token=abc")
        assert result == InputType.HTTP_ENDPOINT

    def test_detect_github_url_https(self):
        """测试检测HTTPS GitHub URL."""
        result = self.detector.detect("https://github.com/user/repo")
        assert result == InputType.GITHUB_URL

    def test_detect_github_url_http(self):
        """测试检测HTTP GitHub URL."""
        result = self.detector.detect("http://github.com/user/repo")
        assert result == InputType.GITHUB_URL

    def test_detect_package_name_with_at(self):
        """测试检测@开头的包名."""
        result = self.detector.detect("@upstash/context7-mcp")
        assert result == InputType.PACKAGE_NAME

    def test_detect_search_query_simple_text(self):
        """测试检测简单搜索查询."""
        result = self.detector.detect("context7")
        assert result == InputType.SEARCH_QUERY

    def test_detect_search_query_with_spaces(self):
        """测试检测带空格的搜索查询."""
        result = self.detector.detect("github search tool")
        assert result == InputType.SEARCH_QUERY

    def test_detect_strips_whitespace(self):
        """测试移除首尾空白字符."""
        result = self.detector.detect("  @upstash/context7-mcp  ")
        assert result == InputType.PACKAGE_NAME

    # ===== HTTP MCP端点检测详细测试 =====

    def test_is_http_mcp_endpoint_with_mcp_path(self):
        """测试/mcp路径检测."""
        result = self.detector.is_http_mcp_endpoint("https://api.example.com/mcp")
        assert result is True

    def test_is_http_mcp_endpoint_with_mcp_query(self):
        """测试/mcp查询参数检测."""
        result = self.detector.is_http_mcp_endpoint(
            "https://api.example.com/mcp?test=1"
        )
        assert result is True

    def test_is_http_mcp_endpoint_with_mcp_slash(self):
        """测试/mcp/路径检测."""
        result = self.detector.is_http_mcp_endpoint("https://api.example.com/mcp/v1")
        assert result is True

    def test_is_http_mcp_endpoint_github_url_excluded(self):
        """测试GitHub URL被排除."""
        result = self.detector.is_http_mcp_endpoint("https://github.com/user/mcp-repo")
        assert result is False

    def test_is_http_mcp_endpoint_api_mcp_path(self):
        """测试/api/mcp路径检测."""
        result = self.detector.is_http_mcp_endpoint("https://api.example.com/api/mcp")
        assert result is True

    def test_is_http_mcp_endpoint_with_dev_port(self):
        """测试开发端口检测."""
        result = self.detector.is_http_mcp_endpoint("http://localhost:3000/mcp")
        assert result is True

    def test_is_http_mcp_endpoint_with_mcp_domain(self):
        """测试MCP域名检测."""
        result = self.detector.is_http_mcp_endpoint(
            "https://mcp-server.example.com/api"
        )
        assert result is True

    def test_is_http_mcp_endpoint_with_api_key_param(self):
        """测试API密钥参数检测."""
        result = self.detector.is_http_mcp_endpoint(
            "https://api.example.com/endpoint?api_key=xxx"
        )
        assert result is True

    def test_is_http_mcp_endpoint_non_http_url(self):
        """测试非HTTP URL返回False."""
        result = self.detector.is_http_mcp_endpoint("ftp://example.com/mcp")
        assert result is False

    def test_is_http_mcp_endpoint_without_mcp_features(self):
        """测试无MCP特征的URL返回False."""
        result = self.detector.is_http_mcp_endpoint("https://example.com/regular/api")
        assert result is False

    # ===== 配置自适应测试 =====

    def test_adapt_config_for_http_endpoint(self):
        """测试HTTP端点配置自适应."""
        original_config = TestConfig(timeout=600, evaluate=False, cleanup=False)
        adapted = self.detector.adapt_config(InputType.HTTP_ENDPOINT, original_config)

        # HTTP端点应缩短超时
        assert adapted.timeout == 300
        # HTTP端点默认启用评估
        assert adapted.evaluate is True
        # HTTP端点默认启用清理
        assert adapted.cleanup is True

    def test_adapt_config_for_github_url(self):
        """测试GitHub URL配置自适应."""
        original_config = TestConfig(timeout=120, evaluate=False)
        adapted = self.detector.adapt_config(InputType.GITHUB_URL, original_config)

        # GitHub URL应延长超时
        assert adapted.timeout == 300
        # 验证enable_fallback属性存在
        assert hasattr(adapted, "enable_fallback")

    def test_adapt_config_for_package_name(self):
        """测试包名配置自适应."""
        original_config = TestConfig(timeout=120, evaluate=False)
        adapted = self.detector.adapt_config(InputType.PACKAGE_NAME, original_config)

        # 包名需要延长超时（安装时间）
        assert adapted.timeout == 180

    def test_adapt_config_does_not_modify_original(self):
        """测试配置自适应不修改原配置."""
        original_config = TestConfig(timeout=600, evaluate=False)
        original_timeout = original_config.timeout

        adapted = self.detector.adapt_config(InputType.HTTP_ENDPOINT, original_config)

        # 原配置不应被修改
        assert original_config.timeout == original_timeout
        # 适配配置应有不同超时
        assert adapted.timeout != original_timeout

    # ===== 边界情况和特殊场景 =====

    def test_detect_empty_string_returns_search_query(self):
        """测试空字符串返回搜索查询类型."""
        result = self.detector.detect("")
        assert result == InputType.SEARCH_QUERY

    def test_detect_only_whitespace(self):
        """测试纯空白字符返回搜索查询类型."""
        result = self.detector.detect("   ")
        assert result == InputType.SEARCH_QUERY

    def test_is_http_mcp_endpoint_empty_string(self):
        """测试空字符串HTTP检测."""
        result = self.detector.is_http_mcp_endpoint("")
        assert result is False

    def test_is_http_mcp_endpoint_none_input(self):
        """测试None输入HTTP检测."""
        result = self.detector.is_http_mcp_endpoint(None)
        assert result is False

    def test_detect_preserves_input_type_priority(self):
        """测试输入类型检测优先级正确."""
        # HTTP端点优先级最高
        assert (
            self.detector.detect("https://api.example.com/mcp")
            == InputType.HTTP_ENDPOINT
        )
        # GitHub URL次之
        assert (
            self.detector.detect("https://github.com/user/repo") == InputType.GITHUB_URL
        )
        # 包名再次
        assert self.detector.detect("@user/package") == InputType.PACKAGE_NAME
        # 其他作为搜索查询
        assert self.detector.detect("search term") == InputType.SEARCH_QUERY

    # ===== 真实世界综合测试 =====

    def test_complex_real_world_urls(self):
        """测试真实世界中的复杂URL案例 - 端到端综合测试."""
        real_world_cases = [
            # HTTP MCP端点
            (
                "https://ai.sitianai.com/api/proxy/mcp?api_key=d4v8kgl26lc8ggculk9g",
                InputType.HTTP_ENDPOINT,
            ),
            ("https://api.openai.com/v1/mcp-server", InputType.HTTP_ENDPOINT),
            ("https://gateway.anthropic.com/mcp-endpoint", InputType.HTTP_ENDPOINT),
            # GitHub URLs
            ("https://github.com/upstash/context7-mcp-server", InputType.GITHUB_URL),
            ("https://github.com/microsoft/autogen", InputType.GITHUB_URL),
            # 包名
            ("@anthropic-ai/claude-mcp", InputType.PACKAGE_NAME),
            ("@openai/gpt-mcp-tools", InputType.PACKAGE_NAME),
            # 搜索查询
            ("claude mcp tools", InputType.SEARCH_QUERY),
            ("autogen multi-agent", InputType.SEARCH_QUERY),
        ]

        for url, expected_type in real_world_cases:
            result = self.detector.detect(url)
            assert result == expected_type, (
                f"真实世界URL检测错误: {url} -> {result} (期望: {expected_type})"
            )
