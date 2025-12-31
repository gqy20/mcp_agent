#!/usr/bin/env python3
"""输入类型检测器的单元测试

遵循TDD方法，先编写测试用例，然后实现对应的功能
测试覆盖各种输入类型的准确检测和边界情况
"""

from src.batch_mcp.core.input_type_detector import InputType, get_input_type_detector


class TestInputTypeDetection:
    """测试输入类型检测功能"""

    def setup_method(self):
        """每个测试方法前的设置"""
        self.detector = get_input_type_detector()

    def test_detect_github_url(self):
        """测试GitHub URL的正确识别"""
        github_urls = [
            "https://github.com/upstash/context7",
            "https://github.com/microsoft/autogen",
            "https://github.com/anthropics/claude-desk",
            "https://github.com/example-user/example-repo",
        ]

        for url in github_urls:
            result = self.detector.detect(url)
            assert result == InputType.GITHUB_URL, f"应该识别为GitHub URL: {url}"

    def test_detect_http_mcp_endpoint(self):
        """测试HTTP MCP端点的正确识别"""
        http_endpoints = [
            "https://api.example.com/mcp",
            "https://api.example.com/api/mcp",
            "https://mcp.example.com/endpoint",
            "https://gateway.example.com/proxy/mcp",
            "https://localhost:8080/mcp",
            "https://localhost:3000/api/mcp",
            "https://api.example.com/mcp?api_key=test123",
            "https://mcp.example.com/model-context-protocol",
            "https://api.example.com/mcp-server",
            "https://proxy.example.com/mcp?token=abc123",
        ]

        for endpoint in http_endpoints:
            result = self.detector.detect(endpoint)
            assert result == InputType.HTTP_ENDPOINT, (
                f"应该识别为HTTP MCP端点: {endpoint}"
            )

    def test_detect_package_name(self):
        """测试包名格式的正确识别"""
        package_names = [
            "@upstash/context7-mcp",
            "@microsoft/autogen",
            "@anthropics/claude-mcp",
            "@example/tool-name",
            "@scoped/package-with-dashes",
        ]

        for package in package_names:
            result = self.detector.detect(package)
            assert result == InputType.PACKAGE_NAME, f"应该识别为包名: {package}"

    def test_detect_search_query(self):
        """测试搜索查询的正确识别"""
        search_queries = [
            "context7",
            "autogen",
            "claude-mcp",
            "excel-mcp-server",
            "tool name with spaces",
            "just-a-random-string",
        ]

        for query in search_queries:
            result = self.detector.detect(query)
            assert result == InputType.SEARCH_QUERY, f"应该识别为搜索查询: {query}"

    def test_priority_github_over_http(self):
        """测试GitHub URL优先于HTTP端点检测"""
        # GitHub URL即使包含mcp字样也应该优先识别为GitHub URL
        github_mcp_urls = [
            "https://github.com/user/mcp-server",
            "https://github.com/project/mcp-tool",
            "https://github.com/example/model-context-protocol",
        ]

        for url in github_mcp_urls:
            result = self.detector.detect(url)
            assert result == InputType.GITHUB_URL, (
                f"GitHub URL应该优先于HTTP检测: {url}"
            )

    def test_case_insensitive_http_detection(self):
        """测试HTTP检测的大小写不敏感性"""
        case_variations = [
            "https://API.EXAMPLE.COM/MCP",
            "https://api.example.com/API/MCP",
            "https://api.example.com/Model-Context-Protocol",
            "https://MCP.example.com/endpoint",
        ]

        for url in case_variations:
            result = self.detector.detect(url)
            assert result == InputType.HTTP_ENDPOINT, f"HTTP检测应该大小写不敏感: {url}"

    def test_input_sanitization(self):
        """测试输入的清理和规范化"""
        inputs_with_whitespace = [
            "  https://github.com/upstash/context7  ",
            "\thttps://api.example.com/mcp\n",
            "  @upstash/context7-mcp  ",
            "  context7  ",
        ]

        expected_types = [
            InputType.GITHUB_URL,
            InputType.HTTP_ENDPOINT,
            InputType.PACKAGE_NAME,
            InputType.SEARCH_QUERY,
        ]

        for input_str, expected_type in zip(inputs_with_whitespace, expected_types):
            result = self.detector.detect(input_str)
            assert result == expected_type, f"应该正确处理空白字符: {input_str!r}"

    def test_edge_cases(self):
        """测试边界情况和异常输入"""
        edge_cases = [
            ("", InputType.SEARCH_QUERY),  # 空字符串
            ("   ", InputType.SEARCH_QUERY),  # 只有空白字符
            ("not-a-url", InputType.SEARCH_QUERY),  # 不是URL
            ("ftp://example.com/mcp", InputType.SEARCH_QUERY),  # 非HTTP协议
            ("http://github.com/user/repo", InputType.GITHUB_URL),  # HTTP GitHub URL
        ]

        for input_str, expected_type in edge_cases:
            result = self.detector.detect(input_str)
            assert result == expected_type, (
                f"边界情况处理错误: {input_str!r} -> {result} (期望: {expected_type})"
            )

    def test_port_based_detection(self):
        """测试基于端口的HTTP MCP端点检测"""
        port_based_endpoints = [
            "https://localhost:3000/api",  # 开发端口+API路径
            "https://localhost:8080/mcp",  # 开发端口+MCP路径
            "https://dev.example.com:9000/server",  # 非标准端口+服务路径
            "https://api.example.com:7000/v1",  # 非标准端口+版本路径
        ]

        for endpoint in port_based_endpoints:
            result = self.detector.detect(endpoint)
            assert result == InputType.HTTP_ENDPOINT, (
                f"应该通过端口识别HTTP MCP: {endpoint}"
            )

    def test_query_parameter_detection(self):
        """测试基于查询参数的HTTP MCP端点检测"""
        query_param_endpoints = [
            "https://api.example.com/endpoint?mcp=true",
            "https://service.example.com/api?key=abc123&mcp=1",
            "https://gateway.example.com/proxy?api_key=xyz789",
            "https://auth.example.com/token?auth=bearer123",
        ]

        for endpoint in query_param_endpoints:
            result = self.detector.detect(endpoint)
            assert result == InputType.HTTP_ENDPOINT, (
                f"应该通过查询参数识别HTTP MCP: {endpoint}"
            )

    def test_complex_real_world_urls(self):
        """测试真实世界中的复杂URL案例"""
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
