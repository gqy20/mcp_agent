"""ResultPresenter 单元测试.

测试 ResultPresenter 类的各种显示方法。
由于这些方法主要使用 rich.print 输出，我们需要 mock 输出进行验证。
"""

from unittest.mock import MagicMock, patch

from src.batch_mcp.core.input_type_detector import InputType
from src.batch_mcp.core.result_presenter import ResultPresenter, get_result_presenter


class TestResultPresenter:
    """ResultPresenter 测试类."""

    def setup_method(self):
        """每个测试方法前的设置."""
        self.presenter = ResultPresenter()

    @patch("src.batch_mcp.core.result_presenter.rprint")
    def test_display_input_type_detection_github_url(self, mock_rprint):
        """测试显示 GitHub URL 输入类型检测结果."""
        input_str = "https://github.com/example/repo"
        input_type = InputType.GITHUB_URL

        self.presenter.display_input_type_detection(input_str, input_type)

        # 验证 rprint 被调用
        assert mock_rprint.called
        # 验证输出包含预期的内容
        call_args = str(mock_rprint.call_args)
        assert "GitHub仓库" in call_args or "GitHub" in call_args
        assert input_str in call_args

    @patch("src.batch_mcp.core.result_presenter.rprint")
    def test_display_input_type_detection_http_endpoint(self, mock_rprint):
        """测试显示 HTTP 端点输入类型检测结果."""
        input_str = "https://api.example.com/mcp"
        input_type = InputType.HTTP_ENDPOINT

        self.presenter.display_input_type_detection(input_str, input_type)

        assert mock_rprint.called
        call_args = str(mock_rprint.call_args)
        assert "HTTP" in call_args
        assert input_str in call_args

    @patch("src.batch_mcp.core.result_presenter.rprint")
    def test_display_input_type_detection_package_name(self, mock_rprint):
        """测试显示包名输入类型检测结果."""
        input_str = "@upstash/context7-mcp"
        input_type = InputType.PACKAGE_NAME

        self.presenter.display_input_type_detection(input_str, input_type)

        assert mock_rprint.called
        call_args = str(mock_rprint.call_args)
        assert "MCP包名" in call_args or "包名" in call_args
        assert input_str in call_args

    @patch("src.batch_mcp.core.result_presenter.rprint")
    def test_display_input_type_detection_search_query(self, mock_rprint):
        """测试显示搜索查询输入类型检测结果."""
        input_str = "context7"
        input_type = InputType.SEARCH_QUERY

        self.presenter.display_input_type_detection(input_str, input_type)

        assert mock_rprint.called
        call_args = str(mock_rprint.call_args)
        assert "搜索" in call_args
        assert input_str in call_args

    @patch("src.batch_mcp.core.result_presenter.rprint")
    def test_display_input_type_detection_unknown(self, mock_rprint):
        """测试显示未知类型输入检测结果."""
        input_str = "some_unknown_input"
        input_type = InputType.UNKNOWN

        self.presenter.display_input_type_detection(input_str, input_type)

        assert mock_rprint.called
        call_args = str(mock_rprint.call_args)
        assert "未知" in call_args
        assert input_str in call_args

    @patch("src.batch_mcp.core.result_presenter.Console")
    def test_display_evaluation_result_full(self, mock_console_class):
        """测试显示完整评估结果."""
        # 设置 mock
        mock_console = MagicMock()
        mock_console_class.return_value = mock_console

        evaluation_result = {
            "status": "success",
            "final_score": 85,
            "final_comprehensive_score": 87,
            "sustainability": {
                "total_score": 80,
                "details": {
                    "commits": {"score": 90, "reason": "活跃开发"},
                    "contributors": {"score": 70, "reason": "较少贡献者"},
                },
            },
            "popularity": {
                "total_score": 90,
                "details": {
                    "stars": {"score": 95, "reason": "高star数"},
                    "forks": {"score": 85, "reason": "较多fork"},
                },
            },
            "test_success_rate": {
                "success_rate": 75.0,
                "test_count": 10,
            },
        }

        self.presenter.display_evaluation_result(evaluation_result)

        # 验证 Console 被创建
        assert mock_console_class.called
        # 验证 table 被打印
        assert mock_console.print.called

    @patch("src.batch_mcp.core.result_presenter.rprint")
    def test_display_deployment_success_with_package(self, mock_rprint):
        """测试显示部署成功信息（带包名）."""
        # 创建 mock server_info
        server_info = MagicMock()
        server_info.server_id = "test-server-123"
        server_info.available_tools = [
            {"name": "tool1", "description": "First tool"},
            {"name": "tool2", "description": "Second tool"},
        ]

        self.presenter.display_deployment_success(server_info, "test-package")

        # 验证 rprint 被调用多次（服务器ID、包名、工具列表）
        assert mock_rprint.call_count >= 3
        call_args_list = [str(call) for call in mock_rprint.call_args_list]
        all_args = " ".join(call_args_list)
        assert "test-server-123" in all_args
        assert "test-package" in all_args
        assert "tool1" in all_args
        assert "tool2" in all_args

    @patch("src.batch_mcp.core.result_presenter.rprint")
    def test_display_deployment_success_without_package(self, mock_rprint):
        """测试显示部署成功信息（不带包名）."""
        server_info = MagicMock()
        server_info.server_id = "test-server-456"
        server_info.available_tools = []

        self.presenter.display_deployment_success(server_info)

        assert mock_rprint.called
        call_args = str(mock_rprint.call_args)
        assert "test-server-456" in call_args

    @patch("src.batch_mcp.core.result_presenter.Console")
    def test_display_http_evaluation_result(self, mock_console_class):
        """测试显示 HTTP MCP 端点评估结果."""
        mock_console = MagicMock()
        mock_console_class.return_value = mock_console

        evaluation_result = {
            "status": "success",
            "quality_grade": "A",
            "scoring_breakdown": {
                "final_score": 88,
                "connectivity_score": 100,
                "functionality_score": 85,
                "performance_score": 90,
                "quantity_score": 80,
            },
            "details": {
                "tools_count": 5,
                "functional_tests_count": 3,
                "functional_tests_success": 3,
                "response_time_seconds": 0.5,
            },
            "recommendations": [
                "建议1: 改进文档",
                "建议2: 增加测试覆盖",
            ],
        }

        self.presenter.display_http_evaluation_result(evaluation_result)

        # 验证 Console 被创建
        assert mock_console_class.called
        # 验证 print 被调用
        assert mock_console.print.called

    def test_get_result_presenter_singleton(self):
        """测试 get_result_presenter 返回单例."""
        presenter1 = get_result_presenter()
        presenter2 = get_result_presenter()

        # 应该返回同一个实例
        assert presenter1 is presenter2
        assert isinstance(presenter1, ResultPresenter)
