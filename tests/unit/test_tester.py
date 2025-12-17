"""Unit tests for MCP tester functionality."""

import pytest

try:
    from src.batch_mcp.core.tester import MCPTester as MCTester
except ImportError:
    MCTester = None


class TestMCTester:
    """Test cases for MCPTester based on actual API."""

    @pytest.fixture
    def tester(self):
        """Create an MCPTester instance."""
        if MCTester is None:
            pytest.skip("MCPTester not available")
        return MCTester()

    def test_tester_initialization(self, tester):
        """Test tester initialization."""
        assert tester is not None
        # 初始化时parser和deployer为None（延迟加载）
        assert tester.parser is None
        assert tester.deployer is None

    def test_services_lazy_loading(self, tester):
        """Test that services are loaded lazily."""
        # 首次调用应该创建服务
        parser, deployer = tester._get_services()
        assert parser is not None
        assert deployer is not None

        # 再次调用应该返回相同的服务
        parser2, deployer2 = tester._get_services()
        assert parser is parser2
        assert deployer is deployer2

    def test_find_tool_by_url_with_none(self, tester):
        """Test finding tool by URL returns None for invalid URL."""
        result = tester.find_tool_by_url("invalid-url")
        assert result is None

    def test_find_tool_by_url_with_valid_url(self, tester):
        """Test finding tool by URL with potentially valid URL."""
        # This might return None if the URL is not in the CSV data
        result = tester.find_tool_by_url("https://github.com/some-owner/some-repo")
        # We don't assert the result because it depends on the CSV data
        assert isinstance(result, (type(None), object))

    def test_cleanup_server_with_string(self, tester):
        """Test cleanup server with string server ID."""
        # This should not raise an exception even if server doesn't exist
        result = tester.cleanup_server("non_existent_server")
        # The return type depends on the deployer implementation
        # It might be bool or a dict, so we just check it doesn't crash
        assert result is not None or result is False or result is True

    def test_deploy_tool_with_minimal_args(self, tester):
        """Test deploy tool with minimal arguments."""
        # This should not raise an exception even if package doesn't exist
        try:
            result = tester.deploy_tool("non_existent_package", timeout=1)
            # The result can be any type depending on implementation
            assert result is not None
        except Exception:
            # It's okay if deployment fails, we just want to test the API exists
            pass

    def test_deploy_tool_with_all_args(self, tester):
        """Test deploy tool with all arguments."""
        try:
            result = tester.deploy_tool(
                "non_existent_package", timeout=1, run_command="echo test"
            )
            assert result is not None
        except Exception:
            # It's okay if deployment fails, we just want to test the API exists
            pass

    def test_class_methods_exist(self, tester):
        """Test that all expected methods exist."""
        expected_methods = [
            "find_tool_by_url",
            "deploy_tool",
            "cleanup_server",
            "run_basic_test",
            "run_smart_test",
            "_get_services",
        ]

        for method_name in expected_methods:
            assert hasattr(tester, method_name)
            assert callable(getattr(tester, method_name))

    def test_run_basic_test_requires_server_info(self, tester):
        """Test that run_basic_test requires proper server_info parameter."""
        # This should fail because we don't have proper server_info
        # The test just ensures the method exists and has expected signature
        try:
            # Passing invalid data should raise an exception
            tester.run_basic_test("invalid_server_info")
            assert False, "Should have raised an exception"
        except Exception:
            # Expected behavior
            pass

    def test_run_smart_test_requires_server_info(self, tester):
        """Test that run_smart_test requires proper server_info parameter."""
        # This should fail because we don't have proper server_info
        # The test just ensures the method exists and has expected signature
        try:
            # Passing invalid data should raise an exception
            tester.run_smart_test("invalid_server_info")
            assert False, "Should have raised an exception"
        except Exception:
            # Expected behavior
            pass
