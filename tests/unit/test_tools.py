"""Unit tests for tools functionality."""


# 测试可以导入现有的模块
def test_import_db_migrate():
    """Test that db_migrate module can be imported."""
    from src.batch_mcp.tools.db_migrate import app

    assert app is not None


def test_import_setup_validator():
    """Test that setup_validator module can be imported."""
    from src.batch_mcp.tools.setup_validator import app

    assert app is not None


def test_import_verify_database():
    """Test that verify_database module can be imported."""
    from src.batch_mcp.tools.verify_database import app

    assert app is not None


def test_import_test_direct_db():
    """Test that test_direct_db module can be imported."""
    from src.batch_mcp.tools.test_direct_db import app

    assert app is not None
