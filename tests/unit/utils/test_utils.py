"""Unit tests for utility functions."""
from unittest.mock import Mock, mock_open, patch

import pytest

from src.utils.config_loader import ConfigLoader
from src.utils.csv_parser import CSVParser


class TestCSVParser:
    """Test cases for CSVParser."""

    @pytest.fixture
    def sample_csv_data(self):
        """Sample CSV data for testing."""
        return """name,package,description,author
tool1,@test/tool1,Test tool 1,Author1
tool2,@test/tool2,Test tool 2,Author2"""

    def test_parse_csv_file(self, sample_csv_data):
        """Test CSV file parsing."""
        with patch("builtins.open", mock_open(read_data=sample_csv_data)):
            parser = CSVParser()
            result = parser.parse_file("test.csv")

            assert len(result) == 2
            assert result[0]["name"] == "tool1"
            assert result[0]["package"] == "@test/tool1"

    def test_parse_csv_string(self, sample_csv_data):
        """Test CSV string parsing."""
        parser = CSVParser()
        result = parser.parse_string(sample_csv_data)

        assert len(result) == 2
        assert result[1]["name"] == "tool2"
        assert result[1]["description"] == "Test tool 2"

    def test_parse_empty_csv(self):
        """Test empty CSV parsing."""
        parser = CSVParser()
        result = parser.parse_string("name,package\n")

        assert len(result) == 0

    def test_parse_invalid_csv(self):
        """Test invalid CSV parsing."""
        parser = CSVParser()
        with pytest.raises(ValueError):
            parser.parse_string("invalid,data,without,headers")


class TestConfigLoader:
    """Test cases for ConfigLoader."""

    @pytest.fixture
    def sample_config(self):
        """Sample configuration for testing."""
        return {"timeout": 30, "max_retries": 3, "log_level": "INFO"}

    def test_load_valid_config(self, sample_config):
        """Test loading valid configuration."""
        with patch(
            "builtins.open",
            mock_open(
                read_data='{"timeout": 30, "max_retries": 3, "log_level": "INFO"}'
            ),
        ):
            loader = ConfigLoader()
            config = loader.load_config("config.json")

            assert config["timeout"] == 30
            assert config["max_retries"] == 3
            assert config["log_level"] == "INFO"

    def test_load_config_file_not_found(self):
        """Test loading non-existent config file."""
        loader = ConfigLoader()
        with pytest.raises(FileNotFoundError):
            loader.load_config("nonexistent.json")

    def test_load_invalid_json(self):
        """Test loading invalid JSON config."""
        with patch("builtins.open", mock_open(read_data="invalid json")):
            loader = ConfigLoader()
            with pytest.raises(ValueError):
                loader.load_config("invalid.json")

    def test_validate_config(self, sample_config):
        """Test configuration validation."""
        loader = ConfigLoader()
        is_valid = loader.validate_config(sample_config)
        assert is_valid is True

    def test_validate_invalid_config(self):
        """Test invalid configuration validation."""
        loader = ConfigLoader()
        invalid_config = {"timeout": "invalid"}  # timeout should be int

        is_valid = loader.validate_config(invalid_config)
        assert is_valid is False
