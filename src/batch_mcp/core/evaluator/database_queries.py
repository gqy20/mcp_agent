"""数据库查询模块.

此模块包含从 Supabase 数据库查询测试历史数据的函数。
"""

from typing import Any

from src.batch_mcp.utils.database_manager import get_database_manager

from .github_api import parse_github_url


def get_test_success_rate(
    github_url: str,
    supabase_client=None,
) -> dict[str, Any] | None:
    """获取工具的测试成功率.

    Args:
        github_url: GitHub URL
        supabase_client: Supabase客户端，如果为None则尝试创建

    Returns:
        包含成功率、测试数量等信息的字典，失败时返回None

    """
    if not supabase_client:
        db_manager = get_database_manager()
        supabase_client = db_manager.get_client()
        if not supabase_client:
            return None

    try:
        # 查询该工具的测试记录
        # 优先匹配GitHub URL，其次匹配工具名
        owner, repo = parse_github_url(github_url)
        if not owner or not repo:
            return None

        # 构建查询条件 - 支持不同的URL格式
        possible_identifiers = [
            github_url,
            github_url.replace(".git", ""),
            f"https://github.com/{owner}/{repo}",
            f"git+https://github.com/{owner}/{repo}.git",
            f"@{owner}/{repo}",
            repo,
        ]

        # 查询所有匹配的测试记录
        all_tests = []
        for identifier in possible_identifiers:
            result = (
                supabase_client.table("mcp_test_results")
                .select(
                    "test_success, deployment_success, communication_success, test_timestamp",
                )
                .eq("tool_identifier", identifier)
                .execute()
            )
            all_tests.extend(result.data)

        if not all_tests:
            return {
                "success_rate": None,
                "test_count": 0,
                "message": "No test records found",
            }

        # 去重 (根据时间戳)
        unique_tests = {}
        for test in all_tests:
            timestamp = test["test_timestamp"]
            if timestamp not in unique_tests:
                unique_tests[timestamp] = test

        tests = list(unique_tests.values())
        total_tests = len(tests)

        # 计算综合成功率 (部署、通信、测试都成功才算成功)
        successful_tests = sum(
            1
            for test in tests
            if test.get("test_success", False)
            and test.get("deployment_success", False)
            and test.get("communication_success", False)
        )

        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0

        return {
            "success_rate": round(success_rate, 2),
            "test_count": total_tests,
            "successful_tests": successful_tests,
            "message": f"Based on {total_tests} test records",
        }

    except Exception as e:
        return {
            "success_rate": None,
            "test_count": 0,
            "message": f"Error calculating success rate: {e}",
        }


def calculate_comprehensive_score_from_tests(
    github_url: str,
    supabase_client=None,
) -> dict[str, Any]:
    """从mcp_test_results表计算工具的综合评分
    使用现有的final_score作为github_evaluation_score.

    Args:
        github_url: GitHub URL
        supabase_client: Supabase客户端，如果为None则尝试创建

    Returns:
        包含综合评分和详细信息的字典

    """
    if not supabase_client:
        db_manager = get_database_manager()
        supabase_client = db_manager.get_client()
        if not supabase_client:
            return None

    try:
        # 查询该工具的所有测试记录
        owner, repo = parse_github_url(github_url)
        if not owner or not repo:
            return None

        # 构建查询条件 - 支持不同的URL格式
        possible_identifiers = [
            github_url,
            github_url.replace(".git", ""),
            f"https://github.com/{owner}/{repo}",
            f"git+https://github.com/{owner}/{repo}.git",
        ]

        # 查询所有匹配的测试记录 - 使用现有列名
        all_tests = []
        for identifier in possible_identifiers:
            result = (
                supabase_client.table("mcp_test_results")
                .select(
                    "test_success, deployment_success, communication_success, test_timestamp, final_score, sustainability_score, popularity_score",
                )
                .eq("tool_identifier", identifier)
                .execute()
            )
            all_tests.extend(result.data)

        if not all_tests:
            return {
                "success_rate": None,
                "test_count": 0,
                "github_evaluation_score": None,
                "comprehensive_score": None,
                "message": "No test records found for this repository",
            }

        # 去重和统计
        unique_tests = {}
        github_score = None
        sustainability_score = None
        popularity_score = None

        for test in all_tests:
            timestamp = test["test_timestamp"]
            if timestamp not in unique_tests:
                unique_tests[timestamp] = test

                # 获取GitHub评估分数（使用final_score，取最新的非空值）
                if test.get("final_score") is not None:
                    github_score = test["final_score"]
                    sustainability_score = test.get("sustainability_score")
                    popularity_score = test.get("popularity_score")

        tests = list(unique_tests.values())
        total_tests = len(tests)

        # 计算测试成功率
        successful_tests = sum(
            1
            for test in tests
            if test.get("test_success", False)
            and test.get("deployment_success", False)
            and test.get("communication_success", False)
        )

        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0

        # 计算综合评分
        if github_score is not None:
            # 按1:2权重计算综合评分
            comprehensive_score = int((success_rate * 1 + github_score * 2) / 3)
            calculation_method = "weighted_average"
            message = f"Comprehensive score: (success_rate({success_rate:.1f})*1 + github_score({github_score})*2)/3 = {comprehensive_score}"
        else:
            # 仅使用测试成功率
            comprehensive_score = int(success_rate)
            calculation_method = "success_rate_only"
            message = f"No GitHub evaluation found, using test success rate only: {comprehensive_score}"

        return {
            "success_rate": round(success_rate, 2),
            "test_count": total_tests,
            "successful_tests": successful_tests,
            "github_evaluation_score": github_score,
            "sustainability_score": sustainability_score,
            "popularity_score": popularity_score,
            "comprehensive_score": comprehensive_score,
            "calculation_method": calculation_method,
            "message": message,
        }

    except Exception as e:
        return {
            "success_rate": None,
            "test_count": 0,
            "successful_tests": 0,
            "github_evaluation_score": None,
            "comprehensive_score": None,
            "message": f"Error calculating comprehensive score: {e}",
        }


def evaluate_full_repository_with_comprehensive_score(
    github_url: str,
    supabase_client=None,
) -> dict[str, Any]:
    """完整的仓库评估 + 测试成功率 + 综合评分.

    Args:
        github_url: GitHub URL
        supabase_client: 可选的Supabase客户端

    Returns:
        完整的评估结果，包含综合评分

    """
    from .score_calculator import evaluate_full_repository_profile

    # 1. 执行基本的GitHub仓库评估
    basic_evaluation = evaluate_full_repository_profile(github_url)

    if basic_evaluation["status"] != "success":
        return basic_evaluation

    # 2. 获取测试成功率
    success_rate_result = get_test_success_rate(github_url, supabase_client)

    # 3. 计算综合评分
    evaluator_score = basic_evaluation["final_score"]
    success_rate = (
        success_rate_result.get("success_rate") if success_rate_result else None
    )
    test_count = success_rate_result.get("test_count", 0) if success_rate_result else 0
    successful_tests = (
        success_rate_result.get("successful_tests", 0) if success_rate_result else 0
    )

    # 按1:2权重计算综合评分
    if success_rate is not None:
        comprehensive_score = int((success_rate * 1 + evaluator_score * 2) / 3)
        calculation_method = "weighted_average"
        message = f"Comprehensive score: (success_rate({success_rate})*1 + evaluator_score({evaluator_score})*2)/3 = {comprehensive_score}"
    else:
        comprehensive_score = evaluator_score
        calculation_method = "evaluator_only"
        message = "No test data available, using evaluator score only"

    comprehensive_result = {
        "total_score": comprehensive_score,
        "evaluator_score": evaluator_score,
        "success_rate": success_rate,
        "test_count": test_count,
        "successful_tests": successful_tests,
        "calculation_method": calculation_method,
        "weights": {"success_rate": 1, "evaluator_score": 2},
        "message": message,
    }

    # 4. 合并所有结果
    result = basic_evaluation.copy()
    result.update(
        {
            "test_success_rate": success_rate_result,
            "comprehensive_scoring": comprehensive_result,
            "final_comprehensive_score": comprehensive_result["total_score"],
        },
    )

    return result
