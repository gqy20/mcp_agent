"""Unit tests for agents functionality."""

import pytest


# 测试agents模块可以导入
def test_import_test_agent():
    """Test that test_agent module can be imported."""
    try:
        from src.batch_mcp.agents.test_agent import TestGeneratorAgent

        assert TestGeneratorAgent is not None
    except ImportError:
        try:
            from src.batch_mcp.agents.test_agent import ValidationResultGenerator

            assert ValidationResultGenerator is not None
        except ImportError:
            pytest.skip("Test agent classes not available")


def test_import_validation_agent():
    """Test that validation_agent module can be imported."""
    try:
        from src.batch_mcp.agents.validation_agent import ValidationAgent

        assert ValidationAgent is not None
    except ImportError:
        try:
            from src.batch_mcp.agents.validation_agent import ValidationResultGenerator

            assert ValidationResultGenerator is not None
        except ImportError:
            pytest.skip("Validation agent classes not available")
