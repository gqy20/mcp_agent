"""DatabaseExporter 单元测试.

测试 DatabaseExporter 类的数据库导出功能：
- export_evaluation_to_database() - 导出评估结果
- export_to_database() - 导出测试结果
- get_tool_identifier() - 获取工具标识符
"""

from unittest.mock import MagicMock, patch

from src.batch_mcp.core.database_exporter import (
    DatabaseExporter,
    get_database_exporter,
)


class TestDatabaseExporter:
    """DatabaseExporter 测试类."""

    def setup_method(self):
        """每个测试方法前的设置."""
        self.exporter = DatabaseExporter()

    @patch("src.batch_mcp.core.database_exporter.rprint")
    @patch("supabase.create_client")
    @patch("src.batch_mcp.core.database_exporter.CONFIG_AVAILABLE", True)
    @patch("src.batch_mcp.core.database_exporter.config")
    def test_export_evaluation_to_database_success(
        self, mock_config, mock_create_client, mock_rprint
    ):
        """测试成功导出评估结果到数据库."""
        # 设置 mock 配置
        mock_config.database.has_supabase_config = True
        mock_config.database.supabase_url = "https://test.supabase.co"
        mock_config.database.supabase_service_role_key = "test-key"

        # 设置 mock 客户端
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client
        mock_client.table.return_value.upsert.return_value.execute.return_value = (
            MagicMock(data=[{"id": "test-id"}])
        )

        # 准备测试数据
        github_url = "https://github.com/example/repo"
        evaluation_result = {
            "status": "success",
            "final_score": 85,
            "sustainability": {
                "total_score": 80,
                "details": {"commits": {"score": 90}},
            },
            "popularity": {
                "total_score": 90,
                "details": {"stars": {"score": 95}},
            },
            "test_success_rate": {"success_rate": 75.0, "test_count": 10},
            "comprehensive_scoring": {"total_score": 87},
        }

        # 执行导出
        self.exporter.export_evaluation_to_database(github_url, evaluation_result)

        # 验证调用
        mock_create_client.assert_called_once_with(
            "https://test.supabase.co",
            "test-key",
        )
        mock_client.table.assert_called_once_with("mcp_repository_evaluations")
        mock_client.table.return_value.upsert.assert_called_once()

        # 验证记录内容
        call_args = mock_client.table.return_value.upsert.call_args
        record = call_args[0][0]
        assert record["github_url"] == github_url
        assert record["final_score"] == 85
        assert record["sustainability_score"] == 80
        assert record["popularity_score"] == 90
        assert record["success_rate"] == 75.0
        assert record["test_count"] == 10
        assert record["total_score"] == 87

    @patch("src.batch_mcp.core.database_exporter.rprint")
    @patch("src.batch_mcp.core.database_exporter.CONFIG_AVAILABLE", False)
    def test_export_evaluation_to_database_no_config(self, mock_rprint):
        """测试数据库配置未设置的情况."""
        github_url = "https://github.com/example/repo"
        evaluation_result = {"status": "success", "final_score": 85}

        self.exporter.export_evaluation_to_database(github_url, evaluation_result)

        # 验证警告消息
        assert mock_rprint.called
        call_args = str(mock_rprint.call_args)
        assert "数据库配置未设置" in call_args or "skip" in call_args.lower()

    @patch("src.batch_mcp.core.database_exporter.rprint")
    @patch("supabase.create_client")
    @patch("builtins.open")
    @patch("src.batch_mcp.core.database_exporter.Path")
    @patch("src.batch_mcp.core.database_exporter.json")
    @patch("src.batch_mcp.core.database_exporter.CONFIG_AVAILABLE", True)
    @patch("src.batch_mcp.core.database_exporter.config")
    def test_export_to_database_success(
        self,
        mock_config,
        mock_json,
        mock_path,
        mock_open,
        mock_create_client,
        mock_rprint,
    ):
        """测试成功导出测试结果到数据库."""
        # 设置 mock 配置
        mock_config.database.has_supabase_config = True
        mock_config.database.supabase_url = "https://test.supabase.co"
        mock_config.database.supabase_service_role_key = "test-key"

        # 设置 mock 客户端
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client
        mock_client.table.return_value.insert.return_value.execute.return_value = (
            MagicMock(data=[{"test_id": "test-id-123"}])
        )

        # 设置 mock 文件读取
        mock_json.load.return_value = {
            "test_url": "https://github.com/example/repo",
            "tool_name": "example-tool",
            "tool_info": {
                "name": "example-tool",
                "author": "test-author",
                "category": "test-category",
                "github_url": "https://github.com/example/repo",
            },
            "deployment_success": True,
            "communication_success": True,
            "available_tools_count": 5,
            "test_duration_seconds": 10.5,
            "error_messages": [],
            "test_results": [
                {"success": True, "test_name": "test1"},
                {"success": True, "test_name": "test2"},
                {"success": False, "test_name": "test3"},
            ],
            "platform_info": "Linux",
        }

        # 执行导出
        self.exporter.export_to_database(
            "/path/to/report.json",
            evaluation_result=None,
        )

        # 验证数据库插入
        mock_client.table.assert_called_once_with("mcp_test_results")
        call_args = mock_client.table.return_value.insert.call_args
        record = call_args[0][0]

        assert record["tool_identifier"] == "https://github.com/example/repo"
        assert record["tool_name"] == "example-tool"
        assert record["tool_author"] == "test-author"
        assert record["tool_category"] == "test-category"
        assert record["test_success"] is True  # 2/3 >= 50%
        assert record["deployment_success"] is True
        assert record["communication_success"] is True
        assert record["available_tools_count"] == 5
        assert record["test_duration_seconds"] == 10.5

    @patch("src.batch_mcp.core.database_exporter.rprint")
    def test_export_to_database_no_report_path(self, mock_rprint):
        """测试没有报告路径的情况."""
        self.exporter.export_to_database("", evaluation_result=None)

        # 验证警告消息
        assert mock_rprint.called
        call_args = str(mock_rprint.call_args)
        assert "没有JSON报告" in call_args or "skip" in call_args.lower()

    @patch("src.batch_mcp.core.database_exporter.get_tool_finder")
    def test_get_tool_identifier_from_tool_info(self, mock_tool_finder):
        """测试从 tool_info 获取工具标识符."""
        json_data = {"test_url": "https://github.com/test/repo"}
        tool_info = {
            "github_url": "https://github.com/example/repo",
        }

        result = self.exporter.get_tool_identifier(json_data, tool_info)

        assert result == "https://github.com/example/repo"
        mock_tool_finder.assert_not_called()

    @patch("src.batch_mcp.core.database_exporter.get_tool_finder")
    def test_get_tool_identifier_from_csv_lookup(self, mock_tool_finder):
        """测试从 CSV 查找获取工具标识符."""
        mock_finder_instance = MagicMock()
        mock_tool_finder.return_value = mock_finder_instance
        mock_finder_instance.lookup_github_url_from_csv.return_value = (
            "https://github.com/csv-found/repo"
        )

        json_data = {"test_url": "test-package"}
        tool_info = {}  # 没有 github_url

        result = self.exporter.get_tool_identifier(json_data, tool_info)

        assert result == "https://github.com/csv-found/repo"
        mock_finder_instance.lookup_github_url_from_csv.assert_called_once_with(
            json_data
        )

    @patch("src.batch_mcp.core.database_exporter.get_tool_finder")
    def test_get_tool_identifier_from_inference(self, mock_tool_finder):
        """测试从推断获取工具标识符."""
        mock_finder_instance = MagicMock()
        mock_tool_finder.return_value = mock_finder_instance
        mock_finder_instance.lookup_github_url_from_csv.return_value = ""
        mock_finder_instance.infer_github_url_from_test_url.return_value = (
            "https://github.com/inferred/repo"
        )

        json_data = {"test_url": "@owner/repo"}
        tool_info = {}

        result = self.exporter.get_tool_identifier(json_data, tool_info)

        assert result == "https://github.com/inferred/repo"
        mock_finder_instance.infer_github_url_from_test_url.assert_called_once_with(
            "@owner/repo"
        )

    @patch("src.batch_mcp.core.database_exporter.get_tool_finder")
    def test_get_tool_identifier_fallback_to_test_url(self, mock_tool_finder):
        """测试回退到 test_url 的情况."""
        mock_finder_instance = MagicMock()
        mock_tool_finder.return_value = mock_finder_instance
        mock_finder_instance.lookup_github_url_from_csv.return_value = ""
        mock_finder_instance.infer_github_url_from_test_url.return_value = ""

        json_data = {"test_url": "https://example.com/tool"}
        tool_info = {}

        result = self.exporter.get_tool_identifier(json_data, tool_info)

        assert result == "https://example.com/tool"

    def test_get_database_exporter_singleton(self):
        """测试 get_database_exporter 返回单例."""
        exporter1 = get_database_exporter()
        exporter2 = get_database_exporter()

        # 应该返回同一个实例
        assert exporter1 is exporter2
        assert isinstance(exporter1, DatabaseExporter)
