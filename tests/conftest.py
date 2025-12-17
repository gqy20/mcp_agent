"""pytest configuration for MCP Agent project."""

import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def test_data_path():
    """Provide path to test data directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_mcp_config():
    """Provide sample MCP configuration for testing."""
    return {
        "mcpServers": {"test_server": {"command": "node", "args": ["test_script.js"]}}
    }


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Mock environment variables for testing."""
    monkeypatch.setenv("OPENAI_API_KEY", "test_key")
    monkeypatch.setenv("SUPABASE_URL", "test_url")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "test_key")
    return monkeypatch


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing."""
    client = Mock()
    client.chat.completions.create.return_value = Mock(
        choices=[Mock(message=Mock(content="Test response"))]
    )
    return client


# 简单的测试标记
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "slow: marks tests as slow")
    config.addinivalue_line("markers", "integration: marks tests as integration")
