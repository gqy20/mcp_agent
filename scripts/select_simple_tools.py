#!/usr/bin/env python3
"""
筛选不需要API key的MCP工具脚本
按照MVP原则，专注于基础功能工具
"""

import json
import os
import sys

sys.path.insert(0, ".")

from src.batch_mcp.utils.csv_parser import get_mcp_parser


def main():
    """选择简单可靠、不需要API key的MCP工具"""
    parser = get_mcp_parser()
    tools = parser.get_all_tools()

    test_count = int(os.getenv("TEST_COUNT", 20))
    print(f"📦 总工具数: {len(tools)}")

    # 第一轮：筛选明确不需要API key的工具
    no_api_tools = []
    for tool in tools:
        # 检查是否明确标记不需要API key
        requires_api = getattr(tool, "extracted_requires_api_key", None)
        if requires_api in [False, "False", "false", None, ""]:
            # 必须有包名才能测试
            if tool.package_name and tool.package_name.strip():
                no_api_tools.append(tool)

    print(f"🔓 明确不需要API key的工具: {len(no_api_tools)}")

    # 第二轮：如果第一轮工具不足，添加基础开发工具
    if len(no_api_tools) < test_count:
        # 基础开发工具关键词（通常不需要API key）
        basic_keywords = [
            "filesystem",
            "file",
            "directory",
            "git",
            "sqlite",
            "memory",
            "time",
            "date",
            "calculator",
            "math",
            "text",
            "json",
            "csv",
            "log",
            "terminal",
            "shell",
            "docker",
            "kubernetes",
            "server",
            "http",
            "rest",
        ]

        for tool in tools:
            if len(no_api_tools) >= test_count:
                break

            if tool in no_api_tools:
                continue

            if not tool.package_name or not tool.package_name.strip():
                continue

            # 检查工具名称和描述中的基础关键词
            tool_text = (
                (tool.name or "").lower() + " " + (tool.description or "").lower()
            )

            if any(keyword in tool_text for keyword in basic_keywords):
                # 排除明确需要API key的工具
                requires_api = getattr(tool, "extracted_requires_api_key", None)
                if requires_api not in [True, "True", "true"]:
                    no_api_tools.append(tool)

    print(f"🎯 筛选后工具数: {len(no_api_tools)}")

    # 第三轮：按可靠性排序
    def reliability_score(tool):
        """计算工具可靠性评分"""
        score = 0

        # 星数权重
        stars = tool.lobehub_star_count or 0
        score += min(stars, 1000) * 0.001  # 最多1分

        # 质量评级权重
        if tool.lobehub_evaluate == "优质":
            score += 3
        elif tool.lobehub_evaluate == "良好":
            score += 2
        elif tool.lobehub_evaluate:
            score += 1

        # NPX部署方式更可靠
        if hasattr(tool, "deployment_method") and tool.deployment_method == "npx":
            score += 1

        # 有作者信息更可靠
        if tool.author and tool.author.strip():
            score += 0.5

        return score

    # 排序并限制数量
    no_api_tools.sort(key=reliability_score, reverse=True)
    test_tools = no_api_tools[:test_count]

    print(f"📋 最终测试工具数: {len(test_tools)}")

    # 统计信息
    quality_dist = {}
    for tool in test_tools:
        quality = tool.lobehub_evaluate or "未知"
        quality_dist[quality] = quality_dist.get(quality, 0) + 1

    print(f"📊 质量分布: {quality_dist}")

    # 生成测试目标列表
    targets = []
    for i, tool in enumerate(test_tools):
        targets.append(
            {
                "package": tool.package_name,
                "name": tool.name or f"Tool_{i+1}",
                "stars": tool.lobehub_star_count or 0,
                "author": tool.author or "Unknown",
                "quality": tool.lobehub_evaluate or "N/A",
                "reliability_score": reliability_score(tool),
            }
        )

    # 输出为GitHub Actions格式
    print(f"targets={json.dumps(targets)}")
    print(f"total={len(targets)}")

    # 显示前5个工具
    print("\n🔧 选定的前5个工具:")
    for i, tool in enumerate(test_tools[:5]):
        print(
            f"{i+1}. {tool.name} ({tool.package_name}) - {tool.lobehub_evaluate or 'N/A'}"
        )

    return len(targets)


if __name__ == "__main__":
    count = main()
    sys.exit(0)
