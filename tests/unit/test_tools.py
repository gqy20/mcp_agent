"""Unit tests for tools functionality."""

import pytest


def test_import_db_migrate():
    """Test that db_migrate module can be imported."""
    from src.batch_mcp.tools.db_migrate import init_database, test_connection

    assert init_database is not None
    assert callable(init_database)
    assert test_connection is not None
    assert callable(test_connection)


def test_import_setup_validator():
    """Test that setup_validator module can be imported."""
    # setup_validator 提供环境验证功能
    from src.batch_mcp.tools.setup_validator import validate_environment

    assert validate_environment is not None
    assert callable(validate_environment)


def test_setup_validator_config_check():
    """Test that setup_validator can check configuration."""
    from src.batch_mcp.tools.setup_validator import CONFIG_AVAILABLE

    # CONFIG_AVAILABLE 表示配置是否可用
    assert isinstance(CONFIG_AVAILABLE, bool)


def test_import_report_generator_module():
    """Test that report_generator module can be imported."""
    from src.batch_mcp.core import report_generator

    assert report_generator is not None
    # 检查是否有生成报告的函数
    assert hasattr(report_generator, "generate_test_report")
    assert callable(report_generator.generate_test_report)


def test_import_database_manager():
    """Test that database_manager module can be imported."""
    from src.batch_mcp.utils.database_manager import DatabaseManager

    assert DatabaseManager is not None


def test_database_manager_class():
    """Test that DatabaseManager has expected methods."""
    from src.batch_mcp.utils.database_manager import DatabaseManager

    # 检查 DatabaseManager 是否有预期的方法
    expected_methods = ["get_client", "has_env_vars", "is_available"]
    for method in expected_methods:
        assert hasattr(DatabaseManager, method), (
            f"DatabaseManager should have {method} method"
        )


@pytest.mark.skip(
    reason="verify_database 和 test_direct_db 依赖已移除的 supabase_connector 模块"
)
def test_import_verify_database():
    """Test that verify_database module can be imported.

    注意: 此测试被跳过，因为 verify_database 依赖旧的 supabase_connector 模块，
    该模块已被 database_manager 替代。
    """
    from src.batch_mcp.tools.verify_database import app

    assert app is not None


@pytest.mark.skip(reason="test_direct_db 依赖已移除的 supabase_connector 模块")
def test_import_test_direct_db():
    """Test that test_direct_db module can be imported.

    注意: 此测试被跳过，因为 test_direct_db 依赖旧的 supabase_connector 模块，
    该模块已被 database_manager 替代。
    """
    from src.batch_mcp.tools.test_direct_db import app

    assert app is not None
