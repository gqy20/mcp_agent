"""Pytest configuration for MCP Agent project."""

import sys
from pathlib import Path

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
