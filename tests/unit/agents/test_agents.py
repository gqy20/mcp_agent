"""Unit tests for agent functionality."""
from unittest.mock import Mock, patch

import pytest

from src.batch_mcp.agents.test_agent import TestGeneratorAgent
from src.batch_mcp.agents.validation_agent import ValidationAgent


class TestTestGeneratorAgent:
    """Test cases for TestGeneratorAgent."""

    def test_agent_initialization(self, sample_mcp_config):
        """Test test generator agent initialization."""
        agent = TestGeneratorAgent(config=sample_mcp_config)
        assert agent.config == sample_mcp_config

    def test_agent_name_validation(self):
        """Test agent name validation."""
        with pytest.raises(ValueError):
            TestGeneratorAgent(name="", config={})

    def test_generate_test_cases(self, sample_mcp_config):
        """Test test case generation."""
        agent = TestGeneratorAgent(config=sample_mcp_config)
        test_cases = agent.generate_test_cases(count=3)

        assert len(test_cases) == 3
        for case in test_cases:
            assert "name" in case
            assert "description" in case


class TestValidationAgent:
    """Test cases for ValidationAgent."""

    @pytest.fixture
    def mock_test_result(self):
        """Create mock test result."""
        return {
            "test_id": "test_123",
            "status": "success",
            "duration": 1.5,
            "tools_tested": ["tool1", "tool2"],
        }

    def test_validation_agent_initialization(self):
        """Test validation agent initialization."""
        agent = ValidationAgent()
        assert agent.name == "validation_agent"

    def test_validate_test_result_success(self, mock_test_result):
        """Test successful test result validation."""
        agent = ValidationAgent()
        is_valid = agent.validate_test_result(mock_test_result)
        assert is_valid is True

    def test_validate_test_result_failure(self):
        """Test failed test result validation."""
        agent = ValidationAgent()
        invalid_result = {"test_id": "test_123"}  # Missing required fields

        is_valid = agent.validate_test_result(invalid_result)
        assert is_valid is False
