"""SimpleMCPDeployer HTTP 支持单元测试.

TDD 测试：验证 HTTP MCP 部署器功能.

作者: AI Assistant
日期: 2025-12-17
"""

from unittest.mock import MagicMock, patch

import pytest

# 目标模块
from src.batch_mcp.core.simple_mcp_deployer import SimpleMCPDeployer


class TestSimpleMCPDeployerHTTP:
    """SimpleMCPDeployer HTTP 支持测试类."""

    def test_detect_http_url_with_mcp_path(self):
        """测试：检测包含 /mcp 的 HTTP URL."""
        deployer = SimpleMCPDeployer()

        method, config = deployer.detect_deployment_method(
            "https://api.streamoodle.com/mcp"
        )

        assert method == "http"
        assert "url" in config
        assert config["url"] == "https://api.streamoodle.com/mcp"

    def test_detect_http_url_with_api_key_parameter(self):
        """测试：检测包含 API key 参数的 HTTP URL."""
        deployer = SimpleMCPDeployer()

        method, config = deployer.detect_deployment_method(
            "http://ai.sitianai.com/api/proxy/mcp?api_key=d4v8kgl26lc8ggculk9g"
        )

        assert method == "http"
        assert config["url"] == "http://ai.sitianai.com/api/proxy/mcp"
        assert "Authorization" in config.get("headers", {})
        assert config["headers"]["Authorization"] == "Bearer d4v8kgl26lc8ggculk9g"

    def test_detect_stdio_url_fallback(self):
        """测试：非 HTTP URL 回退到 STDIO 检测."""
        deployer = SimpleMCPDeployer()

        # 测试普通 GitHub URL
        method, _config = deployer.detect_deployment_method(
            "https://github.com/streamoodle/mcp-server"
        )

        assert method in ["npx", "uvx", "pip", "cargo"]  # 现有的 STDIO 方法
        assert method != "http"

    def test_parse_http_config_basic_url(self):
        """测试：解析基本 HTTP URL 配置."""
        deployer = SimpleMCPDeployer()

        config = deployer._parse_http_config("https://api.example.com/mcp")

        assert config["url"] == "https://api.example.com/mcp"
        assert config["headers"] == {}
        assert config["timeout"] == 30

    def test_parse_http_config_with_query_params(self):
        """测试：解析带查询参数的 HTTP URL."""
        deployer = SimpleMCPDeployer()

        config = deployer._parse_http_config(
            "https://api.example.com/mcp?api_key=test123&timeout=60"
        )

        assert config["url"] == "https://api.example.com/mcp"
        assert "Authorization" in config["headers"]
        assert config["headers"]["Authorization"] == "Bearer test123"
        assert config["timeout"] == 30  # 默认值，不从查询参数解析

    def test_parse_http_config_with_multiple_params(self):
        """测试：解析带多个查询参数的 HTTP URL."""
        deployer = SimpleMCPDeployer()

        config = deployer._parse_http_config(
            "https://api.example.com/mcp?api_key=test123&custom_header=value"
        )

        assert config["url"] == "https://api.example.com/mcp"
        assert config["headers"]["Authorization"] == "Bearer test123"
        # 其他查询参数应该被忽略或特殊处理

    def test_deploy_http_mcp_creates_client(self):
        """测试：部署 HTTP MCP 创建正确的客户端."""
        deployer = SimpleMCPDeployer()

        config = {
            "url": "https://api.streamoodle.com/mcp",
            "headers": {"Authorization": "Bearer test-token"},
            "timeout": 45,
        }

        with patch(
            "src.batch_mcp.core.http_mcp_client.HttpMCPClient"
        ) as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client

            result = deployer.deploy_http_mcp(config)

            # 验证客户端被正确创建
            mock_client_class.assert_called_once_with(
                url="https://api.streamoodle.com/mcp",
                headers={"Authorization": "Bearer test-token"},
                timeout=45,
            )
            assert result == mock_client

    def test_deploy_http_mcp_with_minimal_config(self):
        """测试：最小配置部署 HTTP MCP."""
        deployer = SimpleMCPDeployer()

        config = {"url": "https://api.example.com/mcp"}

        with patch(
            "src.batch_mcp.core.http_mcp_client.HttpMCPClient"
        ) as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client

            result = deployer.deploy_http_mcp(config)

            # 验证使用默认值
            mock_client_class.assert_called_once_with(
                url="https://api.example.com/mcp", headers={}, timeout=30
            )
            assert result == mock_client

    def test_deploy_http_mcp_missing_url_raises_error(self):
        """测试：缺少 URL 配置时抛出错误."""
        deployer = SimpleMCPDeployer()

        config = {"headers": {"Auth": "token"}}  # 缺少 url

        with pytest.raises(KeyError, match="url"):
            deployer.deploy_http_mcp(config)

    def test_deploy_unified_http_method(self):
        """测试：统一部署方法支持 HTTP."""
        deployer = SimpleMCPDeployer()

        with patch.object(deployer, "deploy_http_mcp") as mock_deploy_http:
            mock_client = MagicMock()
            mock_deploy_http.return_value = mock_client

            result = deployer.deploy("https://api.streamoodle.com/mcp")

            mock_deploy_http.assert_called_once()
            assert result == mock_client

    def test_deploy_unified_stdio_fallback(self):
        """测试：统一部署方法对非 HTTP URL 回退到 STDIO."""
        deployer = SimpleMCPDeployer()

        with patch.object(deployer, "deploy_package") as mock_deploy_package:
            mock_client = MagicMock()
            mock_deploy_package.return_value = mock_client

            result = deployer.deploy("https://github.com/streamoodle/mcp-server")

            # 应该调用现有的 STDIO 部署方法
            mock_deploy_package.assert_called_once_with(
                package_name=None,
                run_command=None,
                github_url="https://github.com/streamoodle/mcp-server",
                timeout=30,
            )
            assert result == mock_client

    def test_http_url_detection_edge_cases(self):
        """测试：HTTP URL 检测的边界情况."""
        deployer = SimpleMCPDeployer()

        # 测试不包含 /mcp 的 HTTP URL
        method, _ = deployer.detect_deployment_method("https://api.example.com/api")
        assert method != "http"

        # 测试包含 mcp 但不是 HTTP 的 URL
        method, _ = deployer.detect_deployment_method("github.com/user/mcp-repo")
        assert method != "http"

        # 测试包含 MCP 的 HTTP URL
        method, _config = deployer.detect_deployment_method(
            "https://api.example.com/mcp-server"
        )
        assert method == "http"
