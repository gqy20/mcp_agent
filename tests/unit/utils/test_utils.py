"""Unit tests for utility functions."""
from unittest.mock import Mock, mock_open, patch

import pytest

from src.utils.csv_parser import MCPDataParser


class TestMCPDataParser:
    """Test cases for MCPDataParser."""

    @pytest.fixture
    def sample_csv_data(self):
        """Sample CSV data for testing."""
        return """name,package,description,author
tool1,@test/tool1,Test tool 1,Author1
tool2,@test/tool2,Test tool 2,Author2"""

    def test_parse_csv_file(self, sample_csv_data):
        """Test CSV file parsing."""
        with patch("builtins.open", mock_open(read_data=sample_csv_data)):
            parser = MCPDataParser()
            result = parser.parse_file("test.csv")

            assert len(result) == 2
            assert result[0]["name"] == "tool1"
            assert result[0]["package"] == "@test/tool1"

    def test_parse_csv_string(self, sample_csv_data):
        """Test CSV string parsing."""
        parser = MCPDataParser()
        result = parser.parse_string(sample_csv_data)

        assert len(result) == 2
        assert result[1]["name"] == "tool2"
        assert result[1]["description"] == "Test tool 2"

    def test_parse_empty_csv(self):
        """Test empty CSV parsing."""
        parser = MCPDataParser()
        result = parser.parse_string("name,package\n")

        assert len(result) == 0

    def test_parse_invalid_csv(self):
        """Test invalid CSV parsing."""
        parser = MCPDataParser()
        with pytest.raises(ValueError):
            parser.parse_string("invalid,data,without,headers")
