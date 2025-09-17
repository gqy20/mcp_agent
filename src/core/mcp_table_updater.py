"""
MCP表格更新器

功能：
1. 检查GitHub项目是否存在于现有表格中
2. 添加新发现的MCP工具到表格
3. 更新现有工具的信息
4. 维护数据一致性
"""

import csv
import json
from pathlib import Path
from typing import Dict, List, Optional, Set

from .github_mcp_analyzer import GitHubMCPAnalyzer


class MCPTableUpdater:
    """MCP表格更新器"""

    def __init__(self, mcp_csv_path: str = None, tashan_csv_path: str = None):
        """
        初始化表格更新器

        Args:
            mcp_csv_path: mcp.csv文件路径
            tashan_csv_path: tashan_verified_mcp.csv文件路径
        """
        self.mcp_csv_path = (
            mcp_csv_path or "/home/qy113/workspace/project/mcp/mcp_agent/data/mcp.csv"
        )
        self.tashan_csv_path = (
            tashan_csv_path
            or "/home/qy113/workspace/project/mcp/mcp_agent/data/tashan_verified_mcp.csv"
        )

        self.analyzer = GitHubMCPAnalyzer()

        # 加载现有数据
        self.existing_mcp_data = self._load_mcp_data()
        self.existing_tashan_data = self._load_tashan_data()

        # 提取现有GitHub URLs
        self.existing_urls = self._extract_existing_urls()

    def _load_mcp_data(self) -> List[Dict]:
        """加载mcp.csv数据"""
        try:
            data = []
            with open(self.mcp_csv_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    data.append(row)
            return data
        except Exception as e:
            print(f"加载mcp.csv失败: {e}")
            return []

    def _load_tashan_data(self) -> List[Dict]:
        """加载tashan_verified_mcp.csv数据"""
        try:
            data = []
            with open(self.tashan_csv_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    data.append(row)
            return data
        except Exception as e:
            print(f"加载tashan_verified_mcp.csv失败: {e}")
            return []

    def _extract_existing_urls(self) -> Set[str]:
        """提取现有的GitHub URLs"""
        urls = set()

        # 从mcp.csv提取
        for row in self.existing_mcp_data:
            if row.get("github_url"):
                urls.add(row["github_url"].lower().strip())

        # 从tashan_verified_mcp.csv提取
        for row in self.existing_tashan_data:
            if row.get("github_url"):
                urls.add(row["github_url"].lower().strip())

        return urls

    def is_repo_exists(self, github_url: str) -> bool:
        """检查GitHub项目是否已存在"""
        normalized_url = github_url.lower().strip()

        # 移除.git后缀进行标准化
        normalized_url = normalized_url.replace(".git", "")

        # 检查现有URLs
        for existing_url in self.existing_urls:
            normalized_existing = existing_url.replace(".git", "")
            if normalized_url == normalized_existing:
                return True

        return False

    def analyze_github_project(self, github_url: str) -> Dict:
        """
        分析单个GitHub项目并添加到表格

        Args:
            github_url: GitHub项目URL

        Returns:
            分析结果
        """
        # 检查是否已存在
        if self.is_repo_exists(github_url):
            return {"success": False, "error": "项目已存在于数据库中", "url": github_url}

        # 分析GitHub项目
        try:
            analysis_result = self.analyzer.analyze_github_repo(github_url)

            if not analysis_result or not analysis_result.get("success", False):
                error_msg = (
                    analysis_result.get("error", "分析失败")
                    if analysis_result
                    else "分析返回空结果"
                )
                return {"success": False, "error": error_msg, "url": github_url}
        except Exception as e:
            return {"success": False, "error": f"分析异常: {str(e)}", "url": github_url}

        record = analysis_result["record"]

        # 如果成功到达这里，说明已经是MCP项目
        # (因为 analyze_github_repo 只在成功分析MCP项目时才返回 success=True)

        # 添加到mcp.csv
        self._add_to_mcp_table(record)

        # 添加到tashan_verified_mcp.csv
        tashan_record = self._convert_to_tashan_format(record)
        self._add_to_tashan_table(tashan_record)

        # 更新内存中的数据
        self.existing_mcp_data.append(record)
        self.existing_tashan_data.append(tashan_record)
        self.existing_urls.add(github_url.lower().strip())

        return {
            "success": True,
            "name": record.get("name", "Unknown"),
            "url": github_url,
            "is_mcp_project": True,
            "record": record,
        }

    def update_with_new_repos(self, github_urls: List[str]) -> Dict:
        """
        用新的GitHub URLs更新表格

        Args:
            github_urls: GitHub URL列表

        Returns:
            更新结果统计
        """
        results = {
            "total_urls": len(github_urls),
            "existing_repos": 0,
            "new_repos": 0,
            "mcp_projects": 0,
            "non_mcp_projects": 0,
            "failed_analysis": 0,
            "added_tools": [],
        }

        for url in github_urls:
            print(f"\n处理: {url}")

            # 检查是否已存在
            if self.is_repo_exists(url):
                results["existing_repos"] += 1
                print(f"⚠️ 项目已存在，跳过")
                continue

            # 分析GitHub项目
            mcp_record = self.analyzer.analyze_github_repo(url)

            if mcp_record:
                results["mcp_projects"] += 1
                results["new_repos"] += 1

                # 添加到表格
                self._add_to_mcp_table(mcp_record)
                self._add_to_tashan_table(mcp_record)

                results["added_tools"].append(
                    {
                        "name": mcp_record["name"],
                        "url": url,
                        "author": mcp_record["author"],
                        "stars": mcp_record["star_count"],
                    }
                )

                print(f"✅ 添加MCP工具: {mcp_record['name']}")
            else:
                results["non_mcp_projects"] += 1
                results["new_repos"] += 1
                print(f"❌ 非MCP项目或分析失败")

        return results

    def _add_to_mcp_table(self, record: Dict):
        """添加记录到mcp.csv"""
        try:
            # 确保字段顺序一致
            fieldnames = [
                "name",
                "url",
                "author",
                "github_url",
                "evaluate",
                "score",
                "description",
                "date",
                "type",
                "usage",
                "star_count",
                "fork_count",
                "readme_path",
                "extraction_status",
                "extraction_error",
                "extraction_timestamp",
                "extracted_function_description",
                "extracted_tools",
                "extracted_deployment_methods",
                "extracted_tech_stack",
                "extracted_requires_api_key",
                "extracted_mcp_config",
                "extracted_api_requirements",
                "extracted_use_cases",
            ]

            # 检查文件是否存在
            file_exists = Path(self.mcp_csv_path).exists()

            with open(self.mcp_csv_path, "a", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)

                # 如果文件不存在，写入标题
                if not file_exists:
                    writer.writeheader()

                # 写入记录
                writer.writerow(record)

        except Exception as e:
            print(f"添加到mcp.csv失败: {e}")

    def _add_to_tashan_table(self, record: Dict):
        """添加记录到tashan_verified_mcp.csv"""
        try:
            # 计算他山评分
            tashan_record = self._convert_to_tashan_format(record)

            # 定义标准字段名
            fieldnames = [
                "工具名称",
                "工具作者",
                "他山评分",
                "实用性评分",
                "可持续性评分",
                "受欢迎度评分",
                "可用工具数量",
                "github_url",
            ]

            # 检查文件是否存在
            file_exists = Path(self.tashan_csv_path).exists()

            with open(self.tashan_csv_path, "a", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)

                # 如果文件不存在，写入标题
                if not file_exists:
                    writer.writeheader()

                # 写入记录
                writer.writerow(tashan_record)

        except Exception as e:
            print(f"添加到tashan_verified_mcp.csv失败: {e}")

    def _convert_to_tashan_format(self, record: Dict) -> Dict:
        """转换记录为tashan_verified_mcp.csv格式"""
        # 简单的评分计算
        stars = int(record.get("star_count", 0))
        forks = int(record.get("fork_count", 0))

        # 计算各项评分
        usability_score = min(100, stars / 50 + 20)
        sustainability_score = min(100, stars / 100 + 30)
        popularity_score = min(100, stars / 100 + forks / 10 + 10)

        total_score = (usability_score + sustainability_score + popularity_score) / 3

        # 计算工具数量
        tools_count = (
            len(record.get("extracted_tools", "").split(","))
            if record.get("extracted_tools")
            else 0
        )

        return {
            "工具名称": record["name"],
            "工具作者": record["author"],
            "他山评分": f"{total_score:.2f}",
            "实用性评分": f"{usability_score:.2f}",
            "可持续性评分": f"{sustainability_score:.2f}",
            "受欢迎度评分": f"{popularity_score:.2f}",
            "可用工具数量": tools_count,
            "github_url": record["github_url"],
        }

    def batch_update_from_file(self, urls_file: str) -> Dict:
        """
        从文件批量更新

        Args:
            urls_file: 包含GitHub URLs的文件路径
        """
        try:
            with open(urls_file, "r", encoding="utf-8") as f:
                urls = [line.strip() for line in f if line.strip()]

            return self.update_with_new_repos(urls)

        except Exception as e:
            print(f"读取文件失败: {e}")
            return {"error": str(e)}

    def generate_report(self, results: Dict):
        """生成更新报告"""
        print("\n" + "=" * 50)
        print("MCP表格更新报告")
        print("=" * 50)
        print(f"总计处理URLs: {results['total_urls']}")
        print(f"已存在项目: {results['existing_repos']}")
        print(f"新增项目: {results['new_repos']}")
        print(f"MCP项目: {results['mcp_projects']}")
        print(f"非MCP项目: {results['non_mcp_projects']}")
        print(f"分析失败: {results['failed_analysis']}")

        if results["added_tools"]:
            print(f"\n新增MCP工具 ({len(results['added_tools'])}):")
            for tool in results["added_tools"]:
                print(f"  • {tool['name']} by {tool['author']} ({tool['stars']} stars)")

        print("=" * 50)


def main():
    """测试函数"""
    updater = MCPTableUpdater()

    # 测试URLs
    test_urls = [
        "https://github.com/microsoft/playwright-mcp",
        "https://github.com/upstash/context7",
        "https://github.com/ahujasid/blender-mcp",
        "https://github.com/nonexistent/project",  # 不存在的项目
    ]

    results = updater.update_with_new_repos(test_urls)
    updater.generate_report(results)


if __name__ == "__main__":
    main()
