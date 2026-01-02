"""Evaluator 模块.

此模块提供代码质量评估和GitHub仓库分析功能。
拆分为以下子模块：
- github_api: GitHub API 调用
- score_calculator: 评分计算逻辑
- http_scorer: HTTP MCP 评分
- database_queries: 数据库查询

为了保持向后兼容，所有公开函数都从此模块导出。
"""

# 从子模块导出所有公开函数
from .database_queries import (
    calculate_comprehensive_score_from_tests,
    evaluate_full_repository_with_comprehensive_score,
    get_test_success_rate,
)
from .github_api import (
    get_closed_issues_count,
    get_commit_data,
    get_issue_data,
    get_repo_data,
    parse_github_url,
)
from .http_scorer import (
    calculate_functionality_score,
    calculate_http_mcp_score,
    calculate_performance_score,
    evaluate_http_mcp_endpoint,
)
from .score_calculator import (
    FINAL_WEIGHTS,
    POPULARITY_WEIGHTS,
    SUSTAINABILITY_WEIGHTS,
    analyze_forks,
    analyze_frequency,
    analyze_issue_health,
    analyze_issue_responsiveness,
    analyze_recency,
    analyze_stability,
    analyze_stars,
    evaluate_full_repository_profile,
    evaluate_popularity,
    evaluate_sustainability,
)

# 为了向后兼容，导出所有常量
__all__ = [
    # GitHub API 函数
    "parse_github_url",
    "get_repo_data",
    "get_commit_data",
    "get_issue_data",
    "get_closed_issues_count",
    # 评分权重常量
    "FINAL_WEIGHTS",
    "POPULARITY_WEIGHTS",
    "SUSTAINABILITY_WEIGHTS",
    # 可持续性分析函数
    "analyze_recency",
    "analyze_frequency",
    "analyze_stability",
    "analyze_issue_responsiveness",
    "analyze_issue_health",
    # 受欢迎程度分析函数
    "analyze_stars",
    "analyze_forks",
    # 评估编排函数
    "evaluate_sustainability",
    "evaluate_popularity",
    "evaluate_full_repository_profile",
    # 数据库查询函数
    "get_test_success_rate",
    "calculate_comprehensive_score_from_tests",
    "evaluate_full_repository_with_comprehensive_score",
    # HTTP MCP 评分函数
    "calculate_functionality_score",
    "calculate_performance_score",
    "calculate_http_mcp_score",
    "evaluate_http_mcp_endpoint",
]
