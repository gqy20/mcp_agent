"""HTTP MCP评估结果适配器测试

测试HTTP MCP评估函数返回的结果包含数据库导出所需的sustainability和popularity字段
"""

from src.batch_mcp.core.evaluator import evaluate_http_mcp_endpoint


class TestHTTPEvaluationAdapter:
    """测试HTTP MCP评估结果适配器"""

    def test_evaluate_http_mcp_endpoint_contains_required_fields(self):
        """测试HTTP MCP评估结果包含数据库导出所需的字段"""
        # 准备测试数据
        test_results = {
            "deployment_success": True,
            "communication_success": True,
            "test_results": [{"success": True, "test_category": "功能测试"}],
        }

        tools_count = 2
        response_time = 1.5
        tool_info = {
            "name": "test-tool",
            "url": "http://example.com/mcp",
            "description": "Test MCP tool",
            "category": "HTTP MCP",
        }

        # 执行评估
        result = evaluate_http_mcp_endpoint(
            test_results=test_results,
            tools_count=tools_count,
            response_time=response_time,
            tool_info=tool_info,
        )

        # 验证基本字段
        assert result["status"] == "success"
        assert result["evaluation_type"] == "http_mcp_endpoint"
        assert "final_score" in result
        assert isinstance(result["final_score"], (int, float))
        assert "quality_grade" in result
        assert result["quality_grade"] in [
            "A+ (优秀)",
            "A (良好)",
            "B (中等)",
            "C (一般)",
            "D (需要改进)",
        ]

        # 🔥 关键验证：必须包含数据库导出所需的字段
        assert "sustainability" in result, "评估结果必须包含sustainability字段"
        assert "popularity" in result, "评估结果必须包含popularity字段"

        # 验证sustainability字段结构
        sustainability = result["sustainability"]
        assert "total_score" in sustainability, "sustainability必须包含total_score"
        assert "details" in sustainability, "sustainability必须包含details"
        assert isinstance(sustainability["total_score"], (int, float))
        assert 0 <= sustainability["total_score"] <= 100

        # 验证popularity字段结构
        popularity = result["popularity"]
        assert "total_score" in popularity, "popularity必须包含total_score"
        assert "details" in popularity, "popularity必须包含details"
        assert isinstance(popularity["total_score"], (int, float))
        assert 0 <= popularity["total_score"] <= 100

    def test_sustainability_and_popularity_values_are_reasonable(self):
        """测试sustainability和popularity字段的值是合理的"""
        # 测试成功情况
        test_results = {
            "deployment_success": True,
            "communication_success": True,
            "test_results": [
                {"success": True, "test_category": "功能测试"},
                {"success": True, "test_category": "功能测试"},
            ],
        }

        result = evaluate_http_mcp_endpoint(
            test_results=test_results, tools_count=3, response_time=2.0
        )

        sustainability = result["sustainability"]
        popularity = result["popularity"]

        # 对于HTTP端点，sustainability应该基于连通性和功能测试
        # 由于测试成功，sustainability应该比较高
        assert sustainability["total_score"] >= 70, "成功情况下sustainability应该较高"

        # HTTP端点的popularity应该基于工具数量等因素
        assert popularity["total_score"] >= 10, "至少应该有基础分数"

    def test_evaluate_http_mcp_endpoint_with_failure_cases(self):
        """测试失败情况下的评估结果"""
        # 测试部署失败情况
        test_results = {
            "deployment_success": False,
            "communication_success": False,
            "test_results": [{"success": False, "test_category": "功能测试"}],
        }

        result = evaluate_http_mcp_endpoint(
            test_results=test_results, tools_count=0, response_time=10.0
        )

        # 即使失败，也应该包含所需字段
        assert "sustainability" in result
        assert "popularity" in result

        sustainability = result["sustainability"]
        popularity = result["popularity"]

        # 失败情况下分数应该较低
        assert sustainability["total_score"] <= 50, "失败情况下sustainability应该较低"
        assert popularity["total_score"] <= 30, "没有工具时popularity应该较低"

    def test_evaluation_details_contain_explanations(self):
        """测试评估详情包含合理的解释"""
        test_results = {
            "deployment_success": True,
            "communication_success": True,
            "test_results": [{"success": True, "test_category": "功能测试"}],
        }

        result = evaluate_http_mcp_endpoint(
            test_results=test_results, tools_count=2, response_time=1.0
        )

        sustainability = result["sustainability"]
        popularity = result["popularity"]

        # 验证details包含解释性信息
        assert isinstance(sustainability["details"], dict), "details应该是字典"
        assert isinstance(popularity["details"], dict), "details应该是字典"

        # details应该包含一些指标
        sustainability_details = sustainability["details"]
        assert "connectivity_score" in sustainability_details, "应该包含连通性评分"
        assert "functionality_score" in sustainability_details, "应该包含功能性评分"

    def test_final_score_consistency(self):
        """测试最终评分的一致性"""
        test_results = {
            "deployment_success": True,
            "communication_success": True,
            "test_results": [{"success": True, "test_category": "功能测试"}],
        }

        result = evaluate_http_mcp_endpoint(
            test_results=test_results, tools_count=1, response_time=1.0
        )

        # 验证final_score在合理范围内
        final_score = result["final_score"]
        assert 0 <= final_score <= 100, (
            f"final_score应该在0-100之间，实际值: {final_score}"
        )

        # 验证quality_grade与final_score匹配
        quality_grade = result["quality_grade"]
        if final_score >= 90:
            assert quality_grade == "A+ (优秀)"
        elif final_score >= 80:
            assert quality_grade == "A (良好)"
        elif final_score >= 70:
            assert quality_grade == "B (中等)"
        elif final_score >= 60:
            assert quality_grade == "C (一般)"
        else:
            assert quality_grade == "D (需要改进)"
