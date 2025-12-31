#!/usr/bin/env python3
"""DatabaseExporter - 数据库导出器.

从 cli_handlers.py 提取：
- export_evaluation_to_database() - 导出评估结果到数据库
- export_to_database() - 导出测试结果到数据库
- get_tool_identifier() - 获取工具标识符

遵循 Linus 原则：
- 每个方法只做一件事
- 清晰的职责分离
- 易于测试和维护
"""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from rich import print as rprint

from src.batch_mcp.core.tool_finder import get_tool_finder

try:
    from .config import get_config

    CONFIG_AVAILABLE = True
    config = get_config() if CONFIG_AVAILABLE else None
except ImportError:
    CONFIG_AVAILABLE = False
    config = None


class DatabaseExporter:
    """数据库导出器 - 负责将测试和评估结果导出到数据库."""

    def export_evaluation_to_database(
        self,
        github_url: str,
        evaluation_result: dict[str, Any],
    ) -> None:
        """导出评估结果到数据库 - 包含综合评分.

        Args:
            github_url: GitHub 仓库 URL
            evaluation_result: 评估结果字典

        """
        if not CONFIG_AVAILABLE or not config.database.has_supabase_config:
            rprint("[yellow]⚠️ 数据库配置未设置，跳过数据库导出[/yellow]")
            return

        try:
            from supabase import create_client

            client = create_client(
                config.database.supabase_url,
                config.database.supabase_service_role_key,
            )

            # 获取综合评分数据
            test_success_info = evaluation_result.get("test_success_rate", {})
            comprehensive_info = evaluation_result.get("comprehensive_scoring", {})

            record = {
                "github_url": github_url,
                "final_score": evaluation_result["final_score"],
                "sustainability_score": evaluation_result["sustainability"][
                    "total_score"
                ],
                "popularity_score": evaluation_result["popularity"]["total_score"],
                "sustainability_details": evaluation_result["sustainability"][
                    "details"
                ],
                "popularity_details": evaluation_result["popularity"]["details"],
                "last_evaluated_at": datetime.now(UTC).isoformat(),
                # 新增字段
                "success_rate": test_success_info.get("success_rate"),
                "test_count": test_success_info.get("test_count", 0),
                "total_score": comprehensive_info.get("total_score"),
                "last_calculated_at": datetime.now(UTC).isoformat(),
            }

            client.table("mcp_repository_evaluations").upsert(record).execute()
            rprint(f"[green]✅ 成功导出评估结果到数据库: {github_url}[/green]")

        except ImportError:
            rprint("[yellow]⚠️ Supabase库未安装，跳过数据库导出[/yellow]")
        except Exception as e:
            rprint(f"[yellow]⚠️ 数据库导出异常: {e}[/yellow]")

    def export_to_database(
        self,
        json_report_path: str,
        evaluation_result: dict | None = None,
    ) -> None:
        """导出到数据库 - 使用精简版数据.

        Args:
            json_report_path: JSON 报告文件路径
            evaluation_result: 可选的评估结果

        """
        if not json_report_path:
            rprint("[yellow]⚠️ 没有JSON报告，跳过数据库导出[/yellow]")
            return

        try:
            rprint("[blue]🗄️ 导出精简版结果到数据库...[/blue]")

            if not CONFIG_AVAILABLE or not config.database.has_supabase_config:
                rprint(
                    "[yellow]⚠️ 数据库配置未设置 (SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)，跳过数据库导出[/yellow]",
                )
                return

            from supabase import create_client

            client = create_client(
                config.database.supabase_url,
                config.database.supabase_service_role_key,
            )

            # 检查是否为精简版报告，如果不是则尝试加载精简版
            with open(json_report_path, encoding="utf-8") as f:
                json_data = json.load(f)

            # 如果是完整版报告，尝试查找对应的精简版
            if "actual_response" in str(json_data):  # 简单判断是否为完整版
                concise_path = json_report_path.replace(".json", "_concise.json")
                if Path(concise_path).exists():
                    rprint("[blue]📄 发现精简版报告，使用精简数据导出[/blue]")
                    with open(concise_path, encoding="utf-8") as f:
                        json_data = json.load(f)
                else:
                    rprint("[yellow]⚠️ 未找到精简版报告，使用完整数据导出[/yellow]")

            deployment_ok = json_data.get("deployment_success", False)
            communication_ok = json_data.get("communication_success", False)
            test_results = json_data.get("test_results", [])

            if test_results:
                passed_tests = sum(
                    1 for test in test_results if test.get("success", False)
                )
                success_rate = (passed_tests / len(test_results)) * 100
                tests_successful = success_rate >= 50.0
            else:
                tests_successful = False

            overall_success = deployment_ok and communication_ok and tests_successful

            # 获取工具信息（如果存在）
            tool_info = json_data.get("tool_info", {})

            # 修复tool_identifier计算逻辑，确保不为空
            tool_identifier = self.get_tool_identifier(json_data, tool_info)

            record = {
                "test_timestamp": datetime.now().isoformat(),
                "tool_identifier": tool_identifier,
                "tool_name": (
                    tool_info.get("name", "Unknown")
                    if tool_info
                    else json_data.get("tool_name", "Unknown")
                ),
                "tool_author": tool_info.get("author", "") if tool_info else "",
                "tool_category": tool_info.get("category", "") if tool_info else "",
                "test_success": overall_success,
                "deployment_success": json_data.get("deployment_success", False),
                "communication_success": json_data.get("communication_success", False),
                "available_tools_count": json_data.get("available_tools_count", 0),
                "test_duration_seconds": json_data.get("test_duration_seconds", 0),
                "error_messages": json_data.get("error_messages", []),
                "test_details": json_data.get("test_results", []),
                "environment_info": {
                    "platform": json_data.get("platform_info", "Unknown"),
                },
            }

            # 添加LobeHub评分信息（如果工具信息中有）
            if tool_info:
                record.update(
                    {
                        "lobehub_url": tool_info.get("lobehub_url"),
                        "lobehub_evaluate": tool_info.get("lobehub_evaluate"),
                        "lobehub_score": tool_info.get("lobehub_score"),
                        "lobehub_star_count": tool_info.get("lobehub_star_count"),
                        "lobehub_fork_count": tool_info.get("lobehub_fork_count"),
                    },
                )

            if evaluation_result and evaluation_result.get("status") == "success":
                record["final_score"] = int(evaluation_result["final_score"])
                record["sustainability_score"] = int(
                    evaluation_result["sustainability"]["total_score"]
                )
                record["popularity_score"] = int(
                    evaluation_result["popularity"]["total_score"]
                )
                record["sustainability_details"] = evaluation_result["sustainability"][
                    "details"
                ]
                record["popularity_details"] = evaluation_result["popularity"][
                    "details"
                ]
                record["evaluation_timestamp"] = datetime.now().isoformat()

                # 使用当前测试的成功率计算综合评分
                if evaluation_result and evaluation_result.get("status") == "success":
                    evaluator_score = evaluation_result.get("final_score", 93)

                    # 使用当前测试的成功率，而不是历史数据
                    current_success_rate = success_rate  # 当前测试的成功率
                    current_test_count = len(test_results)  # 当前测试的数量
                    current_passed_tests = passed_tests  # 当前测试的通过数

                    # 计算综合评分 (当前测试成功率 + GitHub评估器评分)
                    comprehensive_score = int(
                        (current_success_rate * 1 + evaluator_score * 2) / 3,
                    )

                    record["comprehensive_score"] = comprehensive_score
                    record["calculation_method"] = "current_test_weighted"

                    rprint(
                        f"[cyan]💾 计算综合评分: (当前测试成功率{current_success_rate:.1f} × 1 + GitHub评估器评分{evaluator_score} × 2) ÷ 3 = {comprehensive_score}[/cyan]",
                    )
                    rprint(
                        f"[cyan]📊 当前测试: {current_passed_tests}/{current_test_count} = {current_success_rate:.1f}%[/cyan]",
                    )

                    # 插入完整记录（包含综合评分）
                    response = client.table("mcp_test_results").insert(record).execute()

                    if response.data:
                        record_id = response.data[0]["test_id"]
                        rprint(
                            f"[green]✅ 完整记录已保存到数据库: {record_id[:8]}...[/green]",
                        )
                        rprint(
                            f"[green]🎉 综合评分 {comprehensive_score} 已包含在记录中! (基于当前测试)[/green]",
                        )
                        return  # 成功，提前返回
                    rprint("[red]❌ 记录保存失败[/red]")
                else:
                    rprint("[yellow]⚠️ 评估结果不可用，跳过综合评分计算[/yellow]")

            rprint(f"[dim]Dumping to database: {record}[/dim]")
            response = client.table("mcp_test_results").insert(record).execute()

            if response.data:
                rprint(
                    "[green]✅ 数据库导出成功 - 记录已保存到 mcp_test_results 表[/green]",
                )
            else:
                rprint(
                    f"[red]❌ 数据库导出失败: {response.error.message if response.error else '未知错误'}[/red]",
                )

        except Exception as e:
            rprint(f"[red]❌ 数据库导出异常: {e}[/red]")
            rprint(
                "[dim]   检查 SUPABASE_URL 和 SUPABASE_SERVICE_ROLE_KEY 环境变量[/dim]",
            )

    def get_tool_identifier(self, json_data: dict, tool_info: dict) -> str:
        """获取工具标识符，确保不为空.

        Args:
            json_data: JSON 报告数据
            tool_info: 工具信息字典

        Returns:
            str: 工具标识符（GitHub URL 或其他标识）

        问题分析：
        1. 在to_concise_dict中，精简的tool_info不包含github_url字段
        2. 在数据库导出时，当tool_info存在但没有github_url时，返回空字符串
        3. 应该在这种情况下尝试从test_url或其他方式获取正确的tool_identifier

        解决方案：
        1. 如果tool_info存在且有github_url，直接使用
        2. 如果tool_info存在但没有github_url，尝试从CSV中查找完整工具信息
        3. 如果无法从CSV中找到，尝试从test_url推断GitHub URL
        4. 如果tool_info不存在，直接使用test_url

        """
        # 首先尝试从tool_info获取github_url
        if tool_info and isinstance(tool_info, dict):
            tool_identifier = tool_info.get("github_url", "")
            if tool_identifier:
                return tool_identifier

        # 如果tool_info中没有github_url，尝试从CSV中查找完整工具信息
        tool_finder = get_tool_finder()
        tool_identifier = tool_finder.lookup_github_url_from_csv(json_data)
        if tool_identifier:
            return tool_identifier

        # 如果无法从CSV中找到，尝试从test_url推断
        test_url = json_data.get("test_url", "")
        tool_identifier = tool_finder.infer_github_url_from_test_url(test_url)
        if tool_identifier:
            return tool_identifier

        # 如果无法推断，回退到test_url
        return test_url


# 全局 DatabaseExporter 实例
_database_exporter_instance = None


def get_database_exporter() -> DatabaseExporter:
    """获取全局 DatabaseExporter 实例.

    Returns:
        DatabaseExporter 单例实例

    """
    global _database_exporter_instance
    if _database_exporter_instance is None:
        _database_exporter_instance = DatabaseExporter()
    return _database_exporter_instance
