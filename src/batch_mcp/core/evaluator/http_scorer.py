"""HTTP MCP 评分模块.

此模块包含 HTTP MCP 端点的评分计算函数。
"""

from datetime import UTC, datetime
from typing import Any


def calculate_functionality_score(tool_tests: list[dict[str, Any]]) -> float:
    """计算工具功能评分."""
    if not tool_tests:
        return 0.0

    # 计算功能测试成功率
    successful_tests = sum(1 for test in tool_tests if test.get("success", False))
    total_tests = len(tool_tests)

    # 基础成功率评分 (70%)
    success_rate = successful_tests / total_tests if total_tests > 0 else 0
    base_score = success_rate * 70

    # AI置信度加成 (30%) - 添加类型安全检查
    confidence_values = []
    for test in tool_tests:
        confidence = test.get("ai_confidence", 0)
        # 确保confidence是数值类型
        if isinstance(confidence, (int, float)):
            confidence_values.append(float(confidence))
        elif isinstance(confidence, list):
            # 如果是列表，取平均值
            numeric_values = [c for c in confidence if isinstance(c, (int, float))]
            if numeric_values:
                confidence_values.append(sum(numeric_values) / len(numeric_values))
        # 其他类型忽略，使用默认值0

    avg_confidence = sum(confidence_values) / total_tests if confidence_values else 0
    confidence_bonus = avg_confidence * 30

    return base_score + confidence_bonus


def calculate_performance_score(response_time: float) -> float:
    """计算性能评分."""
    if response_time <= 0:
        return 50.0  # 默认中等评分

    # 响应时间评分 (越快越好)
    if response_time <= 1.0:
        return 100.0  # 优秀
    if response_time <= 3.0:
        return 85.0  # 良好
    if response_time <= 5.0:
        return 70.0  # 中等
    if response_time <= 10.0:
        return 50.0  # 一般
    return 30.0  # 较慢


def calculate_http_mcp_score(
    test_results: dict[str, Any], tools_count: int, response_time: float = 0.0
) -> dict[str, Any]:
    """计算HTTP MCP的综合评分.

    Args:
        test_results: 测试结果字典
        tools_count: 可用工具数量
        response_time: 平均响应时间(秒)

    Returns:
        包含各项评分的字典

    """
    # 基础连通性评分 (30%)
    communication_success = test_results.get("communication_success", False)
    deployment_success = test_results.get("deployment_success", False)

    if deployment_success and communication_success:
        connectivity_score = 100.0
    elif deployment_success:
        connectivity_score = 50.0  # 部署成功但通信失败
    else:
        connectivity_score = 0.0  # 部署失败

    # 工具功能评分 (40%)
    all_tests = test_results.get("test_results", [])
    tool_tests = [t for t in all_tests if t.get("test_category") == "功能测试"]

    functionality_score = calculate_functionality_score(tool_tests)

    # 性能评分 (20%)
    performance_score = calculate_performance_score(response_time)

    # 工具数量评分 (10%)
    quantity_score = min(tools_count * 10, 100.0)  # 每个工具10分，最高100分

    # 综合评分
    final_score = (
        connectivity_score * 0.3
        + functionality_score * 0.4
        + performance_score * 0.2
        + quantity_score * 0.1
    )

    return {
        "final_score": round(final_score, 1),
        "connectivity_score": round(connectivity_score, 1),
        "functionality_score": round(functionality_score, 1),
        "performance_score": round(performance_score, 1),
        "quantity_score": round(quantity_score, 1),
        "scoring_method": "http_based_testing",
        "scoring_weights": {
            "connectivity": 0.3,
            "functionality": 0.4,
            "performance": 0.2,
            "quantity": 0.1,
        },
        "details": {
            "deployment_success": deployment_success,
            "communication_success": communication_success,
            "tools_count": tools_count,
            "functional_tests_count": len(tool_tests),
            "functional_tests_success": sum(
                1 for t in tool_tests if t.get("success", False)
            ),
            "response_time_seconds": response_time,
        },
    }


def evaluate_http_mcp_endpoint(
    test_results: dict[str, Any],
    tools_count: int,
    response_time: float = 0.0,
    tool_info: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """评估HTTP MCP端点的综合质量.

    Args:
        test_results: 测试结果
        tools_count: 工具数量
        response_time: 响应时间
        tool_info: 工具信息(可选)

    Returns:
        评估结果字典

    """
    # 计算基础评分
    scoring_result = calculate_http_mcp_score(test_results, tools_count, response_time)

    # 添加质量等级
    final_score = scoring_result["final_score"]
    if final_score >= 90:
        quality_grade = "A+ (优秀)"
    elif final_score >= 80:
        quality_grade = "A (良好)"
    elif final_score >= 70:
        quality_grade = "B (中等)"
    elif final_score >= 60:
        quality_grade = "C (一般)"
    else:
        quality_grade = "D (需要改进)"

    # 添加改进建议
    suggestions = []
    if scoring_result["connectivity_score"] < 100:
        suggestions.append("改善服务连通性稳定性")
    if scoring_result["functionality_score"] < 80:
        suggestions.append("提高工具功能完整性和稳定性")
    if scoring_result["performance_score"] < 70:
        suggestions.append("优化响应时间和服务性能")
    if scoring_result["quantity_score"] < 50:
        suggestions.append("增加更多实用工具")

    # 构建最终结果
    result = {
        "status": "success",
        "evaluation_type": "http_mcp_endpoint",
        "quality_grade": quality_grade,
        "final_score": final_score,
        "scoring_breakdown": scoring_result,
        "recommendations": suggestions,
        "evaluation_timestamp": datetime.now(UTC).isoformat(),
    }

    # 添加数据库导出所需的虚拟字段
    # HTTP端点没有GitHub仓库的sustainability和popularity数据，所以基于测试结果生成合理值
    result["sustainability"] = _generate_http_sustainability_data(
        scoring_result, test_results
    )
    result["popularity"] = _generate_http_popularity_data(scoring_result, tools_count)

    # 添加工具信息(如果提供)
    if tool_info:
        result["tool_info"] = {
            "name": tool_info.get("name"),
            "url": tool_info.get("url"),
            "description": tool_info.get("description"),
            "category": tool_info.get("category", "HTTP MCP"),
        }

    return result


def _generate_http_sustainability_data(
    scoring_result: dict[str, Any], test_results: dict[str, Any]
) -> dict[str, Any]:
    """为HTTP MCP生成sustainability数据.

    HTTP端点没有GitHub仓库的sustainability数据，基于测试结果生成合理值

    Args:
        scoring_result: HTTP MCP评分结果
        test_results: 测试结果

    Returns:
        包含sustainability数据的字典

    """
    # 基于连通性和功能测试成功率计算sustainability分数
    connectivity_score = scoring_result.get("connectivity_score", 0)
    functionality_score = scoring_result.get("functionality_score", 0)
    performance_score = scoring_result.get("performance_score", 0)

    # 计算综合sustainability分数
    sustainability_total = (
        connectivity_score * 0.5 + functionality_score * 0.3 + performance_score * 0.2
    )

    return {
        "total_score": round(sustainability_total, 1),
        "details": {
            "connectivity_score": round(connectivity_score, 1),
            "functionality_score": round(functionality_score, 1),
            "performance_score": round(performance_score, 1),
            "deployment_success": test_results.get("deployment_success", False),
            "communication_success": test_results.get("communication_success", False),
            "note": "HTTP端点sustainability基于测试结果生成",
        },
    }


def _generate_http_popularity_data(
    scoring_result: dict[str, Any], tools_count: int
) -> dict[str, Any]:
    """为HTTP MCP生成popularity数据.

    HTTP端点没有GitHub仓库的popularity数据，基于工具数量和功能评分生成合理值

    Args:
        scoring_result: HTTP MCP评分结果
        tools_count: 工具数量

    Returns:
        包含popularity数据的字典

    """
    # 基于工具数量和功能评分计算popularity分数
    quantity_score = scoring_result.get("quantity_score", 0)
    functionality_score = scoring_result.get("functionality_score", 0)

    # HTTP端点的popularity基于工具数量和功能质量
    popularity_total = quantity_score * 0.6 + functionality_score * 0.4

    return {
        "total_score": round(popularity_total, 1),
        "details": {
            "tools_count": tools_count,
            "quantity_score": round(quantity_score, 1),
            "functionality_score": round(functionality_score, 1),
            "stars": 0,  # HTTP端点没有GitHub stars
            "forks": 0,  # HTTP端点没有GitHub forks
            "note": "HTTP端点popularity基于工具数量和功能质量生成",
        },
    }
