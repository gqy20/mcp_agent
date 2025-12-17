"""Unit tests for report generator functionality."""
import json
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, mock_open, patch

import pytest

from src.batch_mcp.core.report_generator import (
    MCPReportGenerator,
    MCPTestReport,
    TestResult,
)
from src.batch_mcp.utils.csv_parser import MCPToolInfo


class TestMCPReportGenerator:
    """Test cases for MCPReportGenerator."""

    @pytest.fixture
    def sample_evaluation_data(self):
        """Sample evaluation data for testing."""
        return {
            "tool_name": "test_tool",
            "package": "@test/tool",
            "evaluation_date": "2025-09-15",
            "overall_score": 85.5,
            "criteria_scores": {
                "functionality": 90,
                "documentation": 80,
                "performance": 85,
                "usability": 87,
            },
            "strengths": ["Easy to use", "Well documented"],
            "weaknesses": ["Performance could be improved"],
            "recommendations": ["Add more examples", "Optimize performance"],
        }

    @pytest.fixture
    def sample_tool_info(self):
        """Sample tool info for testing."""
        return MCPToolInfo(
            name="Test MCP Tool",
            author="test_author",
            package_name="@test/tool",
            category="Testing",
            description="A test MCP tool for unit testing",
            url="https://github.com/test/tool",
            github_url="https://github.com/test/tool",
            deployment_method="npx",
        )

    @pytest.fixture
    def sample_test_results(self):
        """Sample test results for testing."""
        return [
            TestResult(
                test_name="Test Communication",
                success=True,
                duration=1.5,
                tool_name="test_tool",
                parameters={"query": "test"},
                actual_response={
                    "success": True,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": "This is a long response text that should be truncated to 100 characters in the concise version to keep the output clean and readable.",
                            }
                        ]
                    },
                },
                ai_analysis="Test passed successfully",
                ai_confidence=0.95,
                test_category="基础功能",
            ),
            TestResult(
                test_name="Test Error Handling",
                success=False,
                duration=0.8,
                error_message="This is a long error message that should be truncated to 100 characters in the concise version to maintain readability.",
                tool_name="test_tool",
                actual_response={"success": False},  # Add this to test "响应失败" case
                test_category="容错能力",
            ),
        ]

    @pytest.fixture
    def sample_test_report(self, sample_tool_info, sample_test_results):
        """Sample test report for testing."""
        return MCPTestReport(
            tool_name="Test MCP Tool",
            test_url="https://github.com/test/tool",
            test_time=datetime.now(),
            deployment_success=True,
            communication_success=True,
            available_tools_count=2,
            test_duration_seconds=10.5,
            tool_info=sample_tool_info,
            test_results=sample_test_results,
            error_messages=[],
            evaluation_result={
                "status": "success",
                "final_comprehensive_score": 88,
                "test_success_rate": {"success_rate": 85.0},
            },
        )

    @pytest.fixture
    def report_generator(self):
        """Create an MCPReportGenerator instance."""
        return MCPReportGenerator()

    def test_test_result_to_concise_dict(self, sample_test_results):
        """Test TestResult.to_concise_dict method."""
        test_result = sample_test_results[0]  # Successful test
        concise_dict = test_result.to_concise_dict()

        # Check that required fields are present
        assert "test_name" in concise_dict
        assert "success" in concise_dict
        assert "duration" in concise_dict
        assert "tool_name" in concise_dict
        assert "test_category" in concise_dict
        assert "response_summary" in concise_dict

        # Check values
        assert concise_dict["test_name"] == "Test Communication"
        assert concise_dict["success"] is True
        assert concise_dict["duration"] == 1.5
        assert concise_dict["tool_name"] == "test_tool"
        assert concise_dict["test_category"] == "基础功能"

        # Check that response summary is truncated to 100 characters
        assert len(concise_dict["response_summary"]) <= 103  # 100 + "..."
        assert "..." in concise_dict["response_summary"]

        # Test error case
        error_result = sample_test_results[1]  # Failed test
        error_concise = error_result.to_concise_dict()
        assert "error_summary" in error_concise
        assert len(error_concise["error_summary"]) <= 103
        assert "..." in error_concise["error_summary"]
        assert error_concise["response_summary"] == "响应失败"

    def test_test_report_to_concise_dict(self, sample_test_report):
        """Test MCPTestReport.to_concise_dict method."""
        concise_dict = sample_test_report.to_concise_dict()

        # Check that required fields are present
        assert "tool_name" in concise_dict
        assert "test_url" in concise_dict
        assert "test_time" in concise_dict
        assert "test_duration_seconds" in concise_dict
        assert "deployment_success" in concise_dict
        assert "communication_success" in concise_dict
        assert "available_tools_count" in concise_dict
        assert "tool_info" in concise_dict
        assert "test_results" in concise_dict
        assert "summary" in concise_dict
        assert "evaluation" in concise_dict

        # Check values
        assert concise_dict["tool_name"] == "Test MCP Tool"
        assert concise_dict["deployment_success"] is True
        assert concise_dict["communication_success"] is True
        assert concise_dict["available_tools_count"] == 2

        # Check summary
        summary = concise_dict["summary"]
        assert "total_tests" in summary
        assert "passed_tests" in summary
        assert "success_rate" in summary
        assert "final_score" in summary
        assert summary["total_tests"] == 2
        assert summary["passed_tests"] == 1
        assert summary["success_rate"] == "50.0%"

        # Check tool info is concise
        tool_info = concise_dict["tool_info"]
        assert len(tool_info["description"]) <= 103  # Truncated description

        # Check evaluation is concise
        evaluation = concise_dict["evaluation"]
        assert "final_score" in evaluation
        assert "test_success_rate" in evaluation
        assert "status" in evaluation

    def test_save_concise_json(self, report_generator, sample_test_report, tmp_path):
        """Test saving concise JSON report."""
        # Temporarily change output directory
        original_output_dir = report_generator.output_dir
        report_generator.output_dir = tmp_path

        try:
            # Save concise JSON
            concise_path = report_generator.save_concise_json(sample_test_report)

            # Check file was created
            assert concise_path.exists()
            assert concise_path.name.endswith("_concise.json")

            # Load and verify content
            with open(concise_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Verify it's concise format
            assert "tool_name" in data
            assert "summary" in data
            assert len(str(data)) < 10000  # Should be much smaller than full report

        finally:
            # Restore original output directory
            report_generator.output_dir = original_output_dir

    def test_print_concise_summary(self, report_generator, sample_test_report, capsys):
        """Test printing concise summary to console."""
        # Print summary
        report_generator.print_concise_summary(sample_test_report)

        # Capture output
        captured = capsys.readouterr()

        # Check that key information is displayed
        assert "Test MCP Tool" in captured.out
        assert "测试完成" in captured.out
        assert "✅" in captured.out
        assert "1/2" in captured.out  # passed/total
        assert "50.0%" in captured.out  # success rate
        assert "⭐" in captured.out or "88" in captured.out  # score

    def test_response_summary_truncation(self):
        """Test response summary truncation logic."""
        # Test short response (no truncation)
        short_response = TestResult(
            test_name="Short Response",
            success=True,
            duration=0.5,
            tool_name="test_tool",
            actual_response={
                "success": True,
                "result": {"content": [{"type": "text", "text": "Short response"}]},
            },
        )

        concise_short = short_response.to_concise_dict()
        assert concise_short["response_summary"] == "Short response"
        assert "..." not in concise_short["response_summary"]

        # Test long response (truncated)
        long_response = TestResult(
            test_name="Long Response",
            success=True,
            duration=0.5,
            tool_name="test_tool",
            actual_response={
                "success": True,
                "result": {
                    "content": [
                        {"type": "text", "text": "A" * 200}  # Very long response
                    ]
                },
            },
        )

        concise_long = long_response.to_concise_dict()
        assert len(concise_long["response_summary"]) <= 103
        assert "..." in concise_long["response_summary"]

    def test_error_summary_truncation(self):
        """Test error message truncation logic."""
        # Test long error message
        long_error = TestResult(
            test_name="Error Test",
            success=False,
            duration=0.5,
            error_message="A" * 200,  # Very long error message
            tool_name="test_tool",
        )

        concise_error = long_error.to_concise_dict()
        assert "error_summary" in concise_error
        assert len(concise_error["error_summary"]) <= 103
        assert "..." in concise_error["error_summary"]

    def test_save_json(self, report_generator, sample_test_report, tmp_path):
        """Test saving full JSON report."""
        # Temporarily change output directory
        original_output_dir = report_generator.output_dir
        report_generator.output_dir = tmp_path

        try:
            # Save JSON
            json_path = report_generator.save_json(sample_test_report)

            # Check file was created
            assert json_path.exists()
            assert json_path.name.endswith(".json")

            # Load and verify content
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Verify it contains full data
            assert "tool_name" in data
            assert "test_results" in data
            assert len(data["test_results"]) == 2

        finally:
            # Restore original output directory
            report_generator.output_dir = original_output_dir

    def test_save_html(self, report_generator, sample_test_report, tmp_path):
        """Test saving HTML report."""
        # Temporarily change output directory
        original_output_dir = report_generator.output_dir
        report_generator.output_dir = tmp_path

        try:
            # Save HTML
            html_path = report_generator.save_html(sample_test_report)

            # Check file was created
            assert html_path.exists()
            assert html_path.name.endswith(".html")

            # Load and verify content
            with open(html_path, "r", encoding="utf-8") as f:
                html_content = f.read()

            # Verify HTML structure
            assert "<html" in html_content.lower()
            assert "Test MCP Tool" in html_content
            assert "测试报告" in html_content

        finally:
            # Restore original output directory
            report_generator.output_dir = original_output_dir

    def test_create_report(self, report_generator, sample_tool_info):
        """Test creating a report object."""
        # Mock server info
        mock_server_info = Mock()
        mock_server_info.available_tools = ["tool1", "tool2"]
        mock_server_info.process.pid = 12345

        # Create report
        report = report_generator.create_report(
            url="https://github.com/test/tool",
            tool_info=sample_tool_info,
            server_info=mock_server_info,
            test_success=True,
            duration=10.5,
            test_results=[],
            error_messages=[],
            evaluation_result={"status": "success"},
        )

        # Verify report structure
        assert report.tool_name == "Test MCP Tool"
        assert report.deployment_success is True
        assert report.communication_success is True
        assert report.available_tools_count == 2
        assert report.test_duration_seconds == 10.5
        assert report.process_pid == 12345

    def test_numpy_type_conversion(self, report_generator):
        """Test NumPy type conversion in JSON serialization."""
        # Create a mock report with numpy-like data
        mock_numpy_obj = Mock()
        mock_numpy_obj.item.return_value = 42

        # Test conversion
        converted = report_generator._convert_numpy_types(mock_numpy_obj)
        assert converted == 42

        # Test with a dictionary containing numpy types
        test_dict = {"value": mock_numpy_obj}
        converted_dict = report_generator._convert_numpy_types(test_dict)
        assert converted_dict["value"] == 42

        # Test with list containing numpy types
        test_list = [mock_numpy_obj]
        converted_list = report_generator._convert_numpy_types(test_list)
        assert converted_list[0] == 42
