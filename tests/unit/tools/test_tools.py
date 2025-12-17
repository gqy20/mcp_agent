"""Unit tests for tools functionality."""

from unittest.mock import Mock, mock_open, patch

import pytest

from src.batch_mcp.tools.db_migrate import DatabaseMigrator
from src.batch_mcp.tools.setup_validator import SetupValidator
from src.batch_mcp.tools.verify_database import DatabaseVerifier


class TestDatabaseVerifier:
    """Test cases for DatabaseVerifier."""

    @pytest.fixture
    def db_verifier(self):
        """Create a DatabaseVerifier instance."""
        return DatabaseVerifier()

    def test_verifier_initialization(self, db_verifier):
        """Test verifier initialization."""
        assert db_verifier is not None
        assert hasattr(db_verifier, "verify_connection")
        assert hasattr(db_verifier, "verify_schema")

    @patch("src.tools.verify_database.psycopg2.connect")
    def test_verify_connection_success(self, mock_connect, db_verifier):
        """Test successful database connection verification."""
        mock_conn = Mock()
        mock_connect.return_value = mock_conn

        result = db_verifier.verify_connection(
            host="localhost", database="testdb", user="testuser", password="testpass"
        )

        assert result["status"] == "success"
        assert result["connected"] is True
        mock_connect.assert_called_once()
        mock_conn.close.assert_called_once()

    @patch("src.tools.verify_database.psycopg2.connect")
    def test_verify_connection_failure(self, mock_connect, db_verifier):
        """Test database connection failure."""
        mock_connect.side_effect = Exception("Connection failed")

        result = db_verifier.verify_connection(
            host="localhost", database="testdb", user="testuser", password="testpass"
        )

        assert result["status"] == "error"
        assert "error" in result

    @patch("src.tools.verify_database.psycopg2.connect")
    def test_verify_schema_success(self, mock_connect, db_verifier):
        """Test successful schema verification."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        mock_cursor.fetchall.return_value = [
            ("table1", ["id", "name", "created_at"]),
            ("table2", ["id", "value", "updated_at"]),
        ]

        result = db_verifier.verify_schema(
            host="localhost", database="testdb", user="testuser", password="testpass"
        )

        assert result["status"] == "success"
        assert "tables" in result
        assert len(result["tables"]) == 2

    def test_generate_verification_report(self, db_verifier):
        """Test verification report generation."""
        verification_results = {
            "connection": {"status": "success", "connected": True},
            "schema": {"status": "success", "tables": 2},
            "performance": {"status": "success", "query_time": 0.1},
        }

        report = db_verifier.generate_verification_report(verification_results)

        assert report["overall_status"] == "success"
        assert "checks_performed" in report
        assert "summary" in report


class TestDatabaseMigrator:
    """Test cases for DatabaseMigrator."""

    @pytest.fixture
    def db_migrator(self):
        """Create a DatabaseMigrator instance."""
        return DatabaseMigrator()

    def test_migrator_initialization(self, db_migrator):
        """Test migrator initialization."""
        assert db_migrator is not None
        assert hasattr(db_migrator, "run_migration")
        assert hasattr(db_migrator, "create_backup")

    @patch("src.tools.db_migrate.psycopg2.connect")
    def test_run_migration_success(self, mock_connect, db_migrator):
        """Test successful migration execution."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        migration_script = """
        CREATE TABLE IF NOT EXISTS test_table (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100)
        );
        """

        result = db_migrator.run_migration(
            migration_script=migration_script,
            host="localhost",
            database="testdb",
            user="testuser",
            password="testpass",
        )

        assert result["status"] == "success"
        assert result["migration_applied"] is True
        mock_cursor.execute.assert_called()

    @patch("src.tools.db_migrate.psycopg2.connect")
    def test_run_migration_failure(self, mock_connect, db_migrator):
        """Test migration execution failure."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        mock_cursor.execute.side_effect = Exception("SQL error")

        migration_script = "INVALID SQL STATEMENT"

        result = db_migrator.run_migration(
            migration_script=migration_script,
            host="localhost",
            database="testdb",
            user="testuser",
            password="testpass",
        )

        assert result["status"] == "error"
        assert "error" in result

    @patch("src.tools.db_migrate.subprocess.run")
    def test_create_backup_success(self, mock_run, db_migrator):
        """Test successful backup creation."""
        mock_run.return_value = Mock(
            returncode=0, stdout="Backup created successfully", stderr=""
        )

        result = db_migrator.create_backup(
            host="localhost",
            database="testdb",
            user="testuser",
            backup_file="backup.sql",
        )

        assert result["status"] == "success"
        assert "backup_file" in result
        mock_run.assert_called_once()

    def test_validate_migration_script(self, db_migrator):
        """Test migration script validation."""
        valid_script = """
        CREATE TABLE test_table (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100)
        );
        """

        is_valid = db_migrator.validate_migration_script(valid_script)
        assert is_valid is True

        invalid_script = "DROP TABLE important_table;"
        is_valid = db_migrator.validate_migration_script(invalid_script)
        assert is_valid is False

    def test_generate_migration_report(self, db_migrator):
        """Test migration report generation."""
        migration_result = {
            "status": "success",
            "migration_applied": True,
            "execution_time": 2.5,
            "tables_affected": ["test_table"],
        }

        report = db_migrator.generate_migration_report(migration_result)

        assert report["migration_status"] == "success"
        assert "execution_summary" in report
        assert "changes_made" in report


class TestSetupValidator:
    """Test cases for SetupValidator."""

    @pytest.fixture
    def setup_validator(self):
        """Create a SetupValidator instance."""
        return SetupValidator()

    def test_validator_initialization(self, setup_validator):
        """Test validator initialization."""
        assert setup_validator is not None
        assert hasattr(setup_validator, "validate_environment")
        assert hasattr(setup_validator, "validate_dependencies")

    @patch("src.tools.setup_validator.subprocess.run")
    def test_validate_environment_success(self, mock_run, setup_validator):
        """Test successful environment validation."""
        mock_run.return_value = Mock(returncode=0, stdout="Python 3.12.0", stderr="")

        result = setup_validator.validate_environment()

        assert result["status"] == "success"
        assert "python_version" in result
        mock_run.assert_called()

    @patch("src.tools.setup_validator.subprocess.run")
    def test_validate_environment_failure(self, mock_run, setup_validator):
        """Test environment validation failure."""
        mock_run.return_value = Mock(returncode=1, stdout="", stderr="Python not found")

        result = setup_validator.validate_environment()

        assert result["status"] == "error"
        assert "error" in result

    @patch("src.tools.setup_validator.importlib.import_module")
    def test_validate_dependencies_success(self, mock_import, setup_validator):
        """Test successful dependencies validation."""
        mock_import.return_value = Mock()

        dependencies = ["psycopg2", "requests", "typer"]
        result = setup_validator.validate_dependencies(dependencies)

        assert result["status"] == "success"
        assert "checked_dependencies" in result
        assert result["missing_dependencies"] == []
        assert mock_import.call_count == len(dependencies)

    @patch("src.tools.setup_validator.importlib.import_module")
    def test_validate_dependencies_with_missing(self, mock_import, setup_validator):
        """Test dependencies validation with missing packages."""
        mock_import.side_effect = [
            Mock(),
            ImportError("No module named 'missing_package'"),
        ]

        dependencies = ["psycopg2", "missing_package"]
        result = setup_validator.validate_dependencies(dependencies)

        assert result["status"] == "partial_success"
        assert "missing_dependencies" in result
        assert len(result["missing_dependencies"]) == 1

    def test_validate_configuration_file(self, setup_validator):
        """Test configuration file validation."""
        with patch("builtins.open", mock_open(read_data='{"key": "value"}')):
            result = setup_validator.validate_configuration_file("config.json")

            assert result["status"] == "success"
            assert "config_valid" in result

    def test_validate_configuration_file_not_found(self, setup_validator):
        """Test configuration file validation with missing file."""
        result = setup_validator.validate_configuration_file("nonexistent.json")

        assert result["status"] == "error"
        assert "error" in result

    @patch("src.tools.setup_validator.os.path.exists")
    @patch("src.tools.setup_validator.os.access")
    def test_validate_file_permissions(self, mock_access, mock_exists, setup_validator):
        """Test file permissions validation."""
        mock_exists.return_value = True
        mock_access.return_value = True

        result = setup_validator.validate_file_permissions("/tmp/test_file")

        assert result["status"] == "success"
        assert "permissions_ok" in result

    def test_generate_setup_report(self, setup_validator):
        """Test setup report generation."""
        validation_results = {
            "environment": {"status": "success", "python_version": "3.12.0"},
            "dependencies": {"status": "success", "missing_dependencies": []},
            "configuration": {"status": "success", "config_valid": True},
            "permissions": {"status": "success", "permissions_ok": True},
        }

        report = setup_validator.generate_setup_report(validation_results)

        assert report["overall_status"] == "success"
        assert "validation_checks" in report
        assert "recommendations" in report

    def test_check_system_requirements(self, setup_validator):
        """Test system requirements checking."""
        with (
            patch("psutil.virtual_memory") as mock_memory,
            patch("psutil.disk_usage") as mock_disk,
        ):
            mock_memory.return_value = Mock(
                total=8589934592, available=4294967296
            )  # 8GB total, 4GB available
            mock_disk.return_value = Mock(
                total=107374182400, free=53687091200
            )  # 100GB total, 50GB free

            result = setup_validator.check_system_requirements()

            assert result["status"] == "success"
            assert "memory" in result
            assert "disk_space" in result
            assert result["meets_requirements"] is True
