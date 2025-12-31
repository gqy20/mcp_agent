"""DatabaseManager 单元测试.

测试覆盖：
1. 从环境变量获取客户端（成功场景）
2. 缺少环境变量时返回 None
3. Supabase 不可用时优雅处理
4. 单例模式（返回同一实例）
5. 多次调用不会重复创建客户端
"""

from unittest.mock import MagicMock, patch

from src.batch_mcp.utils import database_manager
from src.batch_mcp.utils.database_manager import (
    DatabaseManager,
    get_database_manager,
)


class TestDatabaseManager:
    """DatabaseManager 测试类."""

    def setup_method(self):
        """每个测试前的设置."""
        # 重置单例和模块状态
        DatabaseManager._instance = None
        DatabaseManager._client = None
        # 重置模块级单例
        database_manager._manager = DatabaseManager()

    def test_get_client_with_valid_env_vars(self, monkeypatch):
        """测试环境变量有效时返回客户端."""
        # Arrange
        monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
        monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "test-key")

        mock_client = MagicMock()
        with patch("supabase.create_client", return_value=mock_client):
            manager = get_database_manager()

            # Act
            result = manager.get_client()

            # Assert
            assert result is mock_client

    def test_get_client_missing_url_returns_none(self, monkeypatch):
        """测试缺少 SUPABASE_URL 时返回 None."""
        # Arrange
        monkeypatch.delenv("SUPABASE_URL", raising=False)
        monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "test-key")

        # Act
        manager = get_database_manager()
        result = manager.get_client()

        # Assert
        assert result is None

    def test_get_client_missing_key_returns_none(self, monkeypatch):
        """测试缺少 SUPABASE_SERVICE_ROLE_KEY 时返回 None."""
        # Arrange
        monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
        monkeypatch.delenv("SUPABASE_SERVICE_ROLE_KEY", raising=False)

        # Act
        manager = get_database_manager()
        result = manager.get_client()

        # Assert
        assert result is None

    def test_get_client_import_error_returns_none(self, monkeypatch):
        """测试 Supabase 不可用时返回 None."""
        # Arrange
        monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
        monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "test-key")

        with patch("supabase.create_client", side_effect=ImportError):
            # Act
            manager = get_database_manager()
            result = manager.get_client()

            # Assert
            assert result is None

    def test_get_client_generic_exception_returns_none(self, monkeypatch):
        """测试其他异常时返回 None."""
        # Arrange
        monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
        monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "test-key")

        with patch("supabase.create_client", side_effect=Exception("test error")):
            # Act
            manager = get_database_manager()
            result = manager.get_client()

            # Assert
            assert result is None

    def test_singleton_pattern_returns_same_instance(self):
        """测试单例模式返回同一实例."""
        # Act
        manager1 = get_database_manager()
        manager2 = get_database_manager()

        # Assert
        assert manager1 is manager2

    def test_get_client_caches_result(self, monkeypatch):
        """测试客户端结果被缓存."""
        # Arrange
        monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
        monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "test-key")

        mock_client = MagicMock()
        create_client_mock = MagicMock(return_value=mock_client)

        with patch("supabase.create_client", create_client_mock):
            manager = get_database_manager()

            # Act - 调用两次
            result1 = manager.get_client()
            result2 = manager.get_client()

            # Assert - create_client 只被调用一次
            assert result1 is mock_client
            assert result2 is mock_client
            create_client_mock.assert_called_once()

    def test_is_available_with_valid_client(self, monkeypatch):
        """测试有客户端时 is_available 返回 True."""
        # Arrange
        monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
        monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "test-key")

        mock_client = MagicMock()
        with patch("supabase.create_client", return_value=mock_client):
            manager = get_database_manager()
            # 先调用 get_client 创建客户端
            manager.get_client()

            # Act
            result = manager.is_available()

            # Assert
            assert result is True

    def test_is_available_without_client(self):
        """测试无客户端时 is_available 返回 False."""
        # Arrange - 确保没有环境变量
        manager = get_database_manager()
        manager._client = None

        # Act
        result = manager.is_available()

        # Assert
        assert result is False

    def test_has_both_env_vars(self, monkeypatch):
        """测试两个环境变量都存在时返回 True."""
        # Arrange
        monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
        monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "test-key")

        # Act
        manager = get_database_manager()
        result = manager.has_env_vars()

        # Assert
        assert result is True

    def test_has_only_url_env_var(self, monkeypatch):
        """测试只有 URL 时返回 False."""
        # Arrange
        monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
        monkeypatch.delenv("SUPABASE_SERVICE_ROLE_KEY", raising=False)

        # Act
        manager = get_database_manager()
        result = manager.has_env_vars()

        # Assert
        assert result is False

    def test_has_only_key_env_var(self, monkeypatch):
        """测试只有 Key 时返回 False."""
        # Arrange
        monkeypatch.delenv("SUPABASE_URL", raising=False)
        monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "test-key")

        # Act
        manager = get_database_manager()
        result = manager.has_env_vars()

        # Assert
        assert result is False
