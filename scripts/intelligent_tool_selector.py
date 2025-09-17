#!/usr/bin/env python3
"""
智能MCP工具选择器
支持多种筛选条件和灵活的测试配置
"""

import json
import os
import sys
from typing import Dict, List, Optional, Set

import pandas as pd


class IntelligentToolSelector:
    """智能MCP工具选择器"""

    def __init__(self) -> None:
        self.csv_path = "data/mcp.csv"
        self.browser_keywords = [
            "playwright",
            "browser",
            "chrome",
            "firefox",
            "selenium",
            "webdriver",
            "screenshot",
            "automation",
            "web",
            "puppeteer",
            "cypress",
            "headless",
            "dom",
            "html",
            "css",
            "javascript",
        ]

    def load_tools_data(self) -> pd.DataFrame:
        """加载工具数据"""
        try:
            df = pd.read_csv(self.csv_path)  # type: ignore
            print(f"📦 总工具数: {len(df)}")
            return df
        except Exception:
            print("❌ 读取CSV文件失败")
            sys.exit(1)

    def parse_deployment_methods(self, extracted_methods: str) -> Set[str]:
        """解析部署方式"""
        if pd.isna(extracted_methods) or not extracted_methods:
            return set()

        methods = set()
        for method in str(extracted_methods).split(","):
            method = method.strip().lower()
            if method:
                methods.add(method)
        return methods

    def parse_tech_stack(self, extracted_stack: str) -> Set[str]:
        """解析技术栈"""
        if pd.isna(extracted_stack) or not extracted_stack:
            return set()

        tech_stack = set()
        # Remove quotes and normalize
        stack_str = str(extracted_stack).strip("\"'")
        for tech in stack_str.split(","):
            tech = tech.strip().lower()
            # Handle special cases like "Node.js (v20+)" -> "node.js"
            if "(" in tech:
                tech = tech.split("(")[0].strip()
            if tech and tech != "":
                tech_stack.add(tech)
        return tech_stack

    def extract_package_name(self, mcp_config: str) -> Optional[str]:
        """从MCP配置中提取包名"""
        try:
            if pd.isna(mcp_config) or not mcp_config:
                return None

            config_data: dict = json.loads(mcp_config)

            # 检查不同的配置结构
            for config_type in [
                "claude_desktop_config",
                "cline_config",
                "cherry_studio_config",
            ]:
                if config_type in config_data:
                    config = config_data[config_type]

                    # 检查 command/args 结构
                    if "command" in config:
                        command: str = config["command"]
                        args = config.get("args", [])

                        # npx packages
                        if command == "npx":
                            # 查找包名在args中
                            for arg in args:
                                if arg.startswith("-y"):
                                    continue
                                if (
                                    arg.startswith("@")
                                    or "/" in arg
                                    or not arg.startswith("-")
                                ):
                                    return arg

                        # uvx packages
                        elif command == "uvx":
                            for arg in args:
                                if not arg.startswith("-"):
                                    return arg

                        # docker packages
                        elif command == "docker":
                            for arg in args:
                                if ":" in arg and "/" in arg:  # image name
                                    return arg

            # 检查 mcpServers 结构
            for config_type in [
                "claude_desktop_config",
                "cline_config",
                "cherry_studio_config",
            ]:
                if (
                    config_type in config_data
                    and "mcpServers" in config_data[config_type]
                ):
                    servers = config_data[config_type]["mcpServers"]
                    for server_name, server_config in servers.items():
                        if "command" in server_config:
                            cmd: str = server_config["command"]
                            args = server_config.get("args", [])

                            if cmd == "npx":
                                for arg in args:
                                    if not arg.startswith("-"):
                                        return arg
                            elif cmd == "uvx":
                                for arg in args:
                                    if not arg.startswith("-"):
                                        return arg

            return None
        except Exception:
            return None

    def extract_deployment_method(self, mcp_config: str) -> Optional[str]:
        """从MCP配置中提取部署方式"""
        try:
            if pd.isna(mcp_config) or not mcp_config:
                return None

            config_data: dict = json.loads(mcp_config)

            # 检查不同的配置结构
            for config_type in [
                "claude_desktop_config",
                "cline_config",
                "cherry_studio_config",
            ]:
                if config_type in config_data:
                    config = config_data[config_type]

                    # 检查 command/args 结构
                    if "command" in config:
                        command: str = config["command"]
                        return command  # 直接返回command作为部署方式

            # 检查 mcpServers 结构
            for config_type in [
                "claude_desktop_config",
                "cline_config",
                "cherry_studio_config",
            ]:
                if (
                    config_type in config_data
                    and "mcpServers" in config_data[config_type]
                ):
                    servers = config_data[config_type]["mcpServers"]
                    for server_name, server_config in servers.items():
                        if "command" in server_config:
                            cmd: str = server_config["command"]
                            return cmd

            return None
        except Exception:
            return None

    def filter_tools(
        self,
        df: pd.DataFrame,
        deployment_method: str = "all",
        tech_stack: str = "all",
        search_keywords: str = "",
        quality_filter: str = "all",
        require_api_key: str = "exclude",
        exclude_browser: bool = True,
        min_stars: int = 0,
        max_count: int = 100,
    ) -> List[Dict]:
        """根据条件筛选工具"""

        filtered_tools = []
        keyword_list = [
            k.strip().lower() for k in search_keywords.split(",") if k.strip()
        ]

        for _, row in df.iterrows():
            try:
                # 提取包名和部署方式
                package_name = self.extract_package_name(
                    row.get("extracted_mcp_config")
                )
                if not package_name:
                    continue

                # 解析实际部署方式和技术栈
                actual_deployment_method = self.extract_deployment_method(
                    row.get("extracted_mcp_config")
                )
                tech_stacks = self.parse_tech_stack(row.get("extracted_tech_stack"))

                # 部署方式筛选
                if deployment_method != "all":
                    if actual_deployment_method != deployment_method:
                        continue

                # 技术栈筛选
                if tech_stack != "all":
                    # Handle common tech stack variations
                    tech_variations = {
                        "nodejs": ["nodejs", "node.js", "node", "nodejs"],
                        "python": ["python", "python3", "py"],
                        "typescript": ["typescript", "ts"],
                        "javascript": ["javascript", "js"],
                        "go": ["go", "golang"],
                        "rust": ["rust", "rs"],
                        "java": ["java"],
                        "docker": ["docker", "container"],
                        "kubernetes": ["kubernetes", "k8s"],
                    }

                    search_terms = tech_variations.get(
                        tech_stack.lower(), [tech_stack.lower()]
                    )
                    if not any(
                        any(term in tech.lower() for tech in tech_stacks)
                        for term in search_terms
                    ):
                        continue

                # 关键词搜索
                if keyword_list:
                    search_text = (
                        str(row.get("name", "")).lower()
                        + " "
                        + str(row.get("description", "")).lower()
                        + " "
                        + str(row.get("author", "")).lower()
                        + " "
                        + package_name.lower()
                    )

                    if not any(keyword in search_text for keyword in keyword_list):
                        continue

                # 质量等级筛选
                quality = str(row.get("evaluate", "N/A"))
                if quality_filter != "all" and quality != quality_filter:
                    continue

                # API key要求筛选
                requires_api = row.get("extracted_requires_api_key", False)
                if require_api_key == "exclude" and requires_api in [
                    True,
                    "True",
                    "true",
                    1,
                    "1",
                ]:
                    continue
                elif require_api_key == "only" and requires_api not in [
                    True,
                    "True",
                    "true",
                    1,
                    "1",
                ]:
                    continue

                # 浏览器工具排除
                if exclude_browser:
                    name = str(row.get("name", "")).lower()
                    description = str(row.get("description", "")).lower()
                    package_lower = package_name.lower()

                    is_browser_related = any(
                        keyword in name
                        or keyword in description
                        or keyword in package_lower
                        for keyword in self.browser_keywords
                    )

                    if is_browser_related:
                        continue

                # 星数要求
                stars = row.get("star_count", 0)
                if isinstance(stars, (int, float)) and stars < min_stars:
                    continue

                # 构建工具信息
                tool_info = {
                    "package": package_name,
                    "name": str(row.get("name", "Unknown"))[:50],
                    "author": str(row.get("author", "Unknown"))[:30],
                    "stars": int(stars) if isinstance(stars, (int, float)) else 0,
                    "quality": quality,
                    "deployment_method": actual_deployment_method or "unknown",
                    "tech_stack": list(tech_stacks),
                    "requires_api_key": bool(requires_api),
                    "description": str(row.get("description", ""))[:100],
                    "github_url": str(row.get("github_url", "")),
                }

                # 计算优先级得分
                priority_score = self._calculate_priority_score(tool_info)
                tool_info["priority_score"] = priority_score

                filtered_tools.append(tool_info)

            except Exception:
                continue

        # 按优先级排序
        filtered_tools.sort(
            key=lambda x: x["priority_score"], reverse=True
        )  # type: ignore

        # 限制数量
        return filtered_tools[:max_count]

    def _calculate_priority_score(self, tool: Dict) -> float:
        """计算工具优先级得分"""
        score: float = 0.0

        # 星数权重 (0-10分)
        stars = tool.get("stars", 0)
        score += min(stars / 100, 10)

        # 质量等级权重
        quality = tool.get("quality")
        if quality == "优质":
            score += 5
        elif quality == "良好":
            score += 3
        elif quality != "N/A":
            score += 1

        # 部署方式权重
        deployment_method = tool.get("deployment_method", "")
        if deployment_method == "npx":
            score += 2
        elif deployment_method == "uvx":
            score += 1.5
        elif deployment_method in ["docker", "pip", "cargo", "python"]:
            score += 1

        # API key权重 (不需要API key的加分)
        if not tool.get("requires_api_key", False):
            score += 1

        # 技术栈权重
        tech_stack = tool.get("tech_stack", [])
        if "nodejs" in tech_stack:
            score += 0.5
        if "python" in tech_stack:
            score += 0.5

        return round(score, 2)

    def get_statistics(self, tools: List[Dict]) -> Dict[str, object]:
        """获取筛选结果的统计信息"""
        if not tools:
            return {}

        stats: Dict[str, object] = {
            "total": len(tools),
            "quality_distribution": {},
            "deployment_method_distribution": {},
            "tech_stack_distribution": {},
            "api_key_distribution": {"requires_key": 0, "no_key": 0},
            "avg_stars": 0,
            "max_stars": 0,
            "min_stars": float("inf"),
        }

        stars: List[float] = []

        for tool in tools:
            # 质量分布
            quality: str = tool.get("quality", "N/A")
            stats["quality_distribution"][quality] = (
                stats["quality_distribution"].get(quality, 0) + 1
            )

            # 部署方式分布
            deployment_method: str = tool.get("deployment_method", "unknown")
            count = stats["deployment_method_distribution"].get(deployment_method, 0)
            stats["deployment_method_distribution"][deployment_method] = count + 1

            # 技术栈分布
            for tech in tool.get("tech_stack", []):
                stats["tech_stack_distribution"][tech] = (
                    stats["tech_stack_distribution"].get(tech, 0) + 1
                )

            # API key分布
            if tool.get("requires_api_key", False):
                stats["api_key_distribution"]["requires_key"] += 1
            else:
                stats["api_key_distribution"]["no_key"] += 1

            # 星数统计
            star_count: int = tool.get("stars", 0)
            stars.append(float(star_count))
            stats["max_stars"] = max(stats["max_stars"], star_count)
            stats["min_stars"] = min(stats["min_stars"], star_count)

        if stars:
            stats["avg_stars"] = round(sum(stars) / len(stars), 1)

        return stats


def main() -> int:
    """主函数"""
    selector = IntelligentToolSelector()

    # 从环境变量获取筛选条件
    deployment_method = os.getenv("DEPLOYMENT_METHOD", "all")
    tech_stack = os.getenv("TECH_STACK", "all")
    search_keywords = os.getenv("SEARCH_KEYWORDS", "")
    quality_filter = os.getenv("QUALITY_FILTER", "all")
    require_api_key = os.getenv("REQUIRE_API_KEY", "exclude")
    exclude_browser = os.getenv("EXCLUDE_BROWSER", "true").lower() == "true"
    min_stars = int(os.getenv("MIN_STARS", "0"))
    test_count = int(os.getenv("TEST_COUNT", "20"))

    print("🔍 智能MCP工具选择器")
    print("📋 筛选条件:")
    print(f"  - 部署方式: {deployment_method}")
    print(f"  - 技术栈: {tech_stack}")
    print(f"  - 搜索关键词: {search_keywords or '无'}")
    print(f"  - 质量等级: {quality_filter}")
    print(f"  - API Key要求: {require_api_key}")
    print(f"  - 排除浏览器工具: {exclude_browser}")
    print(f"  - 最小星数: {min_stars}")
    print(f"  - 目标数量: {test_count}")

    # 加载数据
    df = selector.load_tools_data()

    # 筛选工具
    filtered_tools = selector.filter_tools(
        df=df,
        deployment_method=deployment_method,
        tech_stack=tech_stack,
        search_keywords=search_keywords,
        quality_filter=quality_filter,
        require_api_key=require_api_key,
        exclude_browser=exclude_browser,
        min_stars=min_stars,
        max_count=test_count,
    )

    print(f"✅ 筛选出 {len(filtered_tools)} 个工具")

    # 获取统计信息
    stats = selector.get_statistics(filtered_tools)

    if stats:
        print("📊 统计信息:")
        print(f"  - 质量分布: {stats['quality_distribution']}")
        print(f"  - 部署方式分布: {stats['deployment_method_distribution']}")
        print(f"  - 技术栈分布: {stats['tech_stack_distribution']}")
        print(f"  - API Key分布: {stats['api_key_distribution']}")
        print(f"  - 平均星数: {stats['avg_stars']}")
        print(f"  - 星数范围: {stats['min_stars']} - {stats['max_stars']}")

    # 输出结果
    print(f"targets={json.dumps(filtered_tools)}")
    print(f"total={len(filtered_tools)}")

    # 显示前5个工具
    if filtered_tools:
        print("选定的前5个工具:")
        for i, tool in enumerate(filtered_tools[:5]):
            print(f"{i+1}. {tool['name']} ({tool['package']})")
            print(
                f"   质量: {tool['quality']} | 星数: {tool['stars']} | "
                f"优先级: {tool['priority_score']}"
            )
            print(
                f"   部署: {tool['deployment_method']} | "
                f"技术栈: {', '.join(tool['tech_stack'])}"
            )

    return len(filtered_tools)


if __name__ == "__main__":
    try:
        count = main()
        sys.exit(0)
    except Exception:
        print("❌ 执行失败")
        sys.exit(1)
