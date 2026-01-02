"""MCP 记录生成函数.

此模块提供生成标准化 MCP 工具记录的功能。
"""

import json
from datetime import datetime


def generate_mcp_record(
    github_url: str,
    repo_info: dict,
    analysis: dict,
) -> dict:
    """生成标准化的MCP记录.

    Args:
        github_url: GitHub仓库URL
        repo_info: GitHub仓库信息
        analysis: 分析结果

    Returns:
        MCP工具记录字典

    """
    owner = repo_info.get("owner", {}).get("login", "")
    repo_name = repo_info.get("name", "")

    # 生成评分
    stars = repo_info.get("stargazers_count", 0)
    forks = repo_info.get("forks_count", 0)

    # 生成MCP配置JSON
    mcp_config = {
        "package_name": analysis.get("package_name", ""),
        "deployment_method": analysis.get("deployment_method", ""),
        "install_command": analysis.get("install_command", ""),
        "run_command": analysis.get("run_command", ""),
    }

    return {
        "name": f"{repo_name} MCP",
        "url": "",
        "author": owner,
        "github_url": github_url,
        "evaluate": calculate_evaluate_score(stars, forks),
        "score": "",
        "description": analysis["description"],
        "date": datetime.now().strftime("%Y-%m-%d"),
        "type": "开发工具",
        "usage": "推荐",
        "star_count": stars,
        "fork_count": forks,
        "readme_path": "",
        "extraction_status": "success",
        "extraction_error": "",
        "extraction_timestamp": datetime.now().isoformat(),
        "extracted_function_description": analysis["description"],
        "extracted_tools": ", ".join(analysis["tools"]),
        "extracted_deployment_methods": ", ".join(analysis["deployment_methods"]),
        "extracted_tech_stack": ", ".join(analysis["tech_stack"]),
        "extracted_requires_api_key": analysis["requires_api_key"],
        "extracted_mcp_config": json.dumps(mcp_config, ensure_ascii=False),
        "extracted_api_requirements": "",
        "extracted_use_cases": ", ".join(analysis["use_cases"]),
        # 添加直接字段以便其他组件使用
        "package_name": analysis.get("package_name", ""),
        "deployment_method": analysis.get("deployment_method", ""),
        "install_command": analysis.get("install_command", ""),
        "run_command": analysis.get("run_command", ""),
    }


def calculate_evaluate_score(stars: int, forks: int) -> str:
    """计算评估分数.

    Args:
        stars: Star数量
        forks: Fork数量

    Returns:
        评估等级字符串

    """
    score = (stars / 100) + (forks / 10)

    if score >= 80:
        return "优质"
    if score >= 50:
        return "中等"
    return "一般"
