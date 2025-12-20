#!/usr/bin/env python3
"""HTTP MCP端点检测器的单元测试

测试HTTP MCP端点的各种检测规则，包括路径特征、端口特征、
查询参数特征和域名特征等
"""

import pytest

from src.batch_mcp.core.cli_handlers import CLIHandler


class TestHTTPEndpointDetection:
    """测试HTTP MCP端点检测功能"""

    def setup_method(self):
        """每个测试方法前的设置"""
        self.handler = CLIHandler()

    def test_basic_path_indicators(self):
        """测试基础路径指示器的检测"""
        path_indicator_cases = [
            "https://api.example.com/mcp",
            "https://api.example.com/api/mcp",
            "https://api.example.com/mcp-endpoint",
            "https://api.example.com/mcp-server",
            "https://api.example.com/model-context-protocol",
            "https://api.example.com/proxy/mcp",
        ]

        for url in path_indicator_cases:
            result = self.handler._is_http_mcp_endpoint(url)
            assert result, f"应该通过路径指示器检测为HTTP MCP: {url}"

    def test_case_insensitive_path_detection(self):
        """测试路径检测的大小写不敏感性"""
        case_variations = [
            "https://API.EXAMPLE.COM/MCP",
            "https://api.example.com/API/MCP",
            "https://api.example.com/MCP-SERVER",
            "https://api.example.com/Model-Context-Protocol",
            "https://api.example.com/PROXY/mcp",
        ]

        for url in case_variations:
            result = self.handler._is_http_mcp_endpoint(url)
            assert result, f"路径检测应该大小写不敏感: {url}"

    def test_query_parameter_indicators(self):
        """测试查询参数指示器的检测"""
        query_param_cases = [
            "https://api.example.com/endpoint?mcp=true",
            "https://service.example.com/api?key=abc123&mcp=1",
            "https://api.example.com/mcp?api_key=test123",
            "https://service.example.com/auth?token=xyz789&mcp=enabled",
            "https://api.example.com/proxy?key=abc123",
            "https://auth.example.com/token?auth=bearer123",
        ]

        for url in query_param_cases:
            result = self.handler._is_http_mcp_endpoint(url)
            assert result, f"应该通过查询参数检测为HTTP MCP: {url}"

    def test_development_port_detection(self):
        """测试开发端口检测"""
        dev_port_cases = [
            "https://localhost:3000/api/mcp",
            "https://localhost:8080/mcp",
            "https://localhost:8000/api",
            "https://localhost:5000/server",
            "https://localhost:4000/v1",
            "https://localhost:9000/endpoint",
            "https://localhost:7000/api",
            "https://dev.example.com:3000/mcp",
            "https://staging.example.com:8080/api",
        ]

        for url in dev_port_cases:
            result = self.handler._is_http_mcp_endpoint(url)
            assert result, f"应该通过开发端口检测为HTTP MCP: {url}"

    def test_domain_feature_detection(self):
        """测试域名特征检测"""
        domain_feature_cases = [
            "https://mcp.example.com/api",
            "https://mcp-server.example.com/endpoint",
            "https://api.example.com/mcp",
            "https://gateway.example.com/mcp",
            "https://proxy.example.com/api/mcp",
            "https://mcp.example.com",
            "https://api-mcp.example.com",
            "https://gateway-mcp.example.com",
        ]

        for url in domain_feature_cases:
            result = self.handler._is_http_mcp_endpoint(url)
            assert result, f"应该通过域名特征检测为HTTP MCP: {url}"

    def test_github_url_exclusion(self):
        """测试GitHub URL的排除"""
        github_urls = [
            "https://github.com/upstash/context7",
            "https://github.com/user/mcp-server",
            "https://github.com/project/mcp-tool",
            "https://github.com/example/model-context-protocol",
        ]

        for url in github_urls:
            result = self.handler._is_http_mcp_endpoint(url)
            assert not result, f"GitHub URL应该被排除: {url}"

    def test_protocol_validation(self):
        """测试协议验证"""
        invalid_protocols = [
            "ftp://example.com/mcp",
            "ssh://example.com/mcp",
            "ws://example.com/mcp",
            "file://example.com/mcp",
            "just-a-string",
            "not-a-url-at-all",
            "/local/path/mcp",
        ]

        for invalid_url in invalid_protocols:
            result = self.handler._is_http_mcp_endpoint(invalid_url)
            assert not result, f"无效协议应该被排除: {invalid_url}"

    def test_edge_cases_and_boundary_conditions(self):
        """测试边界条件和特殊情况"""
        edge_cases = [
            # 最小有效URL
            ("https://a.co/m", True),
            # 包含mcp但不是MCP端点
            ("https://example.com/document/ampc123", False),
            ("https://example.com/category/competing", False),
            # 域名中包含mcp子串但不是MCP相关
            ("https://example.com/path?param=amcp", False),
            # 端口号边界
            ("https://localhost:65535/mcp", True),  # 最大有效端口
            ("https://localhost:80/mcp", True),  # 标准HTTP端口
        ]

        for url, expected in edge_cases:
            result = self.handler._is_http_mcp_endpoint(url)
            assert result == expected, (
                f"边界条件处理错误: {url} -> {result} (期望: {expected})"
            )

    def test_combination_detection(self):
        """测试多种特征的组合检测"""
        combination_cases = [
            # 路径 + 查询参数
            "https://api.example.com/mcp?api_key=test123",
            "https://service.example.com/api/mcp?token=xyz789",
            # 端口 + 路径
            "https://localhost:3000/api/mcp",
            "https://dev.example.com:8080/mcp-server",
            # 域名 + 查询参数
            "https://mcp.example.com/api?key=abc123",
            "https://api.example.com/mcp?auth=bearer456",
            # 多种特征组合
            "https://mcp.example.com:8080/api/mcp?api_key=test123",
            "https://gateway-mcp.example.com:3000/proxy/mcp?token=xyz789",
        ]

        for url in combination_cases:
            result = self.handler._is_http_mcp_endpoint(url)
            assert result, f"组合特征检测失败: {url}"

    def test_real_world_http_mcp_endpoints(self):
        """测试真实世界的HTTP MCP端点案例"""
        real_world_cases = [
            # 实际的HTTP MCP端点
            "https://ai.sitianai.com/api/proxy/mcp?api_key=d4v8kgl26lc8ggculk9g",
            "https://api.example.com/v1/mcp-server",
            "https://mcp.example.com:8080/endpoint",
            "https://gateway.anthropic.com/mcp-v2",
            # 可能的开发环境端点
            "https://localhost:3000/api/mcp",
            "https://dev.example.com:8080/mcp",
            "https://staging.mcp.example.com/api",
        ]

        for url in real_world_cases:
            result = self.handler._is_http_mcp_endpoint(url)
            assert result, f"真实世界HTTP MCP端点检测失败: {url}"

    def test_negative_cases_and_false_positives(self):
        """测试负例和误报情况"""
        negative_cases = [
            # 普通API端点
            "https://api.example.com/users",
            "https://api.example.com/posts/123",
            "https://api.example.com/v1/data",
            # 普通网站
            "https://example.com",
            "https://www.google.com",
            "https://stackoverflow.com",
            # 不相关的查询参数
            "https://example.com/api?param=value",
            "https://example.com/search?q=test",
            # 不相关的端口
            "https://example.com:3000",
            "https://localhost:8080",
            "https://dev.example.com:9000",
        ]

        for url in negative_cases:
            result = self.handler._is_http_mcp_endpoint(url)
            assert not result, f"不应该检测为HTTP MCP端点: {url}"

    def test_url_parsing_robustness(self):
        """测试URL解析的健壮性"""
        robustness_cases = [
            # 复杂的查询参数
            "https://api.example.com/mcp?key=value&param=extra&mcp=true",
            "https://example.com/api?complex[filter][field]=value&mcp=1",
            # 带认证信息的URL
            "https://user:pass@example.com/mcp",
            # 特殊字符编码
            "https://example.com/mcp%20server",
            "https://example.com/api/mcp?key=test%20value",
            # 长路径
            "https://example.com/very/deep/nested/path/structure/that/contains/mcp/endpoint",
        ]

        for url in robustness_cases:
            try:
                result = self.handler._is_http_mcp_endpoint(url)
                # 如果URL解析失败，不应该抛出异常
                assert isinstance(result, bool), f"应该返回布尔值: {url}"
            except Exception as e:
                pytest.fail(f"URL解析不应该抛出异常: {url} -> {e}")

    def test_performance_considerations(self):
        """测试性能考虑的边界情况"""
        large_urls = [
            # 非常长的URL
            "https://example.com/" + "a" * 1000 + "/mcp",
            "https://example.com/mcp?" + "param=value&" * 100,
            # 包含大量字符的URL
            "https://example.com/api/" + "path" * 200 + "/mcp",
        ]

        for url in large_urls:
            # 即使对于很长的URL，检测也应该快速完成
            # 这里我们只验证不会因为长度而崩溃
            try:
                result = self.handler._is_http_mcp_endpoint(url)
                assert isinstance(result, bool)
            except Exception as e:
                pytest.fail(f"长URL处理不应该失败: {len(url)}字符 -> {e}")
