"""Analyzer 模块.

此模块提供 GitHub MCP 项目分析功能。
拆分为以下子模块：
- patterns: MCP 分析器模式定义
- github_api: GitHub API 调用
- extractors: 内容提取函数
- record: MCP 记录生成
- analyzer: 主要的 GitHubMCPAnalyzer 类

为了保持向后兼容，所有公开类都从此模块导出。
"""

from .analyzer import GitHubMCPAnalyzer
from .extractors import (
    check_api_key_requirement,
    extract_deployment_methods,
    extract_description,
    extract_installation_instructions,
    extract_package_info,
    extract_tech_stack,
    extract_tools,
    extract_use_cases,
    is_mcp_project,
)
from .github_api import (
    get_readme_content,
    get_repo_info,
    parse_github_url,
)
from .patterns import (
    API_KEY_PATTERNS,
    CARGO_PATTERNS,
    DEPLOYMENT_PATTERNS,
    DEPLOYMENT_PRIORITY,
    MCP_KEYWORDS,
    NPX_PATTERNS,
    PYTHON_PATTERNS,
    TECH_STACK_PATTERNS,
    TITLE_PATTERNS,
    TOOL_PATTERNS,
    USE_CASE_PATTERNS,
    UVX_PATTERNS,
)
from .record import (
    calculate_evaluate_score,
    generate_mcp_record,
)

__all__ = [
    # 主类
    "GitHubMCPAnalyzer",
    # GitHub API
    "parse_github_url",
    "get_repo_info",
    "get_readme_content",
    # 内容提取
    "is_mcp_project",
    "extract_description",
    "extract_deployment_methods",
    "check_api_key_requirement",
    "extract_tech_stack",
    "extract_tools",
    "extract_use_cases",
    "extract_installation_instructions",
    "extract_package_info",
    # 记录生成
    "generate_mcp_record",
    "calculate_evaluate_score",
    # 模式常量（按字母顺序）
    "API_KEY_PATTERNS",
    "CARGO_PATTERNS",
    "DEPLOYMENT_PATTERNS",
    "DEPLOYMENT_PRIORITY",
    "MCP_KEYWORDS",
    "NPX_PATTERNS",
    "PYTHON_PATTERNS",
    "TECH_STACK_PATTERNS",
    "TITLE_PATTERNS",
    "TOOL_PATTERNS",
    "USE_CASE_PATTERNS",
    "UVX_PATTERNS",
]
