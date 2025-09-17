#!/usr/bin/env python3
"""
检查数据库完整性并导出完整数据

这个脚本用于:
1. 检查数据库中的数据完整性
2. 导出包含tool_identifier和comprehensive_score的完整数据
3. 分析缺失数据的原因
"""

import csv
import os
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from supabase import create_client


def main():
    # 加载环境变量
    load_dotenv()

    console = Console()

    # 检查环境变量
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not supabase_url or not supabase_key:
        console.print("[red]❌ 缺少Supabase数据库配置[/red]")
        return

    console.print("[blue]🔍 开始检查数据库完整性...[/blue]")

    try:
        # 创建Supabase客户端
        client = create_client(supabase_url, supabase_key)

        # 1. 获取总记录数
        total_result = (
            client.table("mcp_test_results").select("count", count="exact").execute()
        )
        total_count = total_result.count
        console.print(f"[green]📊 总记录数: {total_count}[/green]")

        # 2. 检查有comprehensive_score的记录数
        with_score_result = (
            client.table("mcp_test_results")
            .select("count")
            .not_.is_("comprehensive_score", "null")
            .execute()
        )
        with_score_count = len(with_score_result.data)
        console.print(f"[green]✅ 有综合评分的记录数: {with_score_count}[/green]")

        # 3. 检查没有comprehensive_score的记录数
        without_score_result = (
            client.table("mcp_test_results")
            .select("count")
            .is_("comprehensive_score", "null")
            .execute()
        )
        without_score_count = len(without_score_result.data)
        console.print(f"[yellow]⚠️ 没有综合评分的记录数: {without_score_count}[/yellow]")

        # 4. 检查tool_identifier是否存在
        with_identifier_result = (
            client.table("mcp_test_results")
            .select("count")
            .not_.is_("tool_identifier", "null")
            .execute()
        )
        with_identifier_count = len(with_identifier_result.data)
        console.print(f"[green]✅ 有工具标识符的记录数: {with_identifier_count}[/green]")

        without_identifier_result = (
            client.table("mcp_test_results")
            .select("count")
            .is_("tool_identifier", "null")
            .execute()
        )
        without_identifier_count = len(without_identifier_result.data)
        console.print(f"[red]❌ 没有工具标识符的记录数: {without_identifier_count}[/red]")

        # 5. 显示详细统计信息
        console.print(f"\n[bold]📈 详细统计:[/bold]")
        console.print(f"  总记录数: {total_count}")
        console.print(
            f"  有综合评分: {with_score_count} ({with_score_count/total_count*100:.1f}%)"
        )
        console.print(
            f"  无综合评分: {without_score_count} ({without_score_count/total_count*100:.1f}%)"
        )
        console.print(
            f"  有标识符: {with_identifier_count} ({with_identifier_count/total_count*100:.1f}%)"
        )
        console.print(
            f"  无标识符: {without_identifier_count} ({without_identifier_count/total_count*100:.1f}%)"
        )

        # 6. 导出完整数据到CSV
        console.print(f"\n[blue]💾 正在导出完整数据...[/blue]")

        # 查询所有数据
        all_data_result = client.table("mcp_test_results").select("*").execute()

        # 创建输出文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"mcp_complete_data_{timestamp}.csv"

        # 定义CSV字段
        fieldnames = [
            "test_id",
            "test_timestamp",
            "tool_identifier",
            "tool_name",
            "tool_author",
            "tool_category",
            "test_success",
            "deployment_success",
            "communication_success",
            "available_tools_count",
            "test_duration_seconds",
            "comprehensive_score",
            "github_evaluation_score",
            "sustainability_score",
            "popularity_score",
            "calculation_method",
        ]

        # 写入CSV文件
        with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for record in all_data_result.data:
                # 只导出需要的字段
                row = {field: record.get(field) for field in fieldnames}
                writer.writerow(row)

        console.print(f"[green]✅ 数据已导出到: {output_file}[/green]")
        console.print(f"[green]📄 记录数: {len(all_data_result.data)}[/green]")

        # 7. 分析问题原因
        console.print(f"\n[bold]🔍 问题分析:[/bold]")

        # 检查没有综合评分的记录是否都有GitHub评估分数
        try:
            # 先检查表结构是否存在github_evaluation_score字段
            github_score_exists = any(
                record.get("github_evaluation_score") is not None
                for record in all_data_result.data[:10]  # 检查前10条记录
            )

            if github_score_exists:
                no_comprehensive_with_github = [
                    record
                    for record in all_data_result.data
                    if record.get("comprehensive_score") is None
                    and record.get("github_evaluation_score") is not None
                ]
                console.print(
                    f"  有GitHub评分但无综合评分: {len(no_comprehensive_with_github)} 条记录"
                )

                no_comprehensive_no_github = [
                    record
                    for record in all_data_result.data
                    if record.get("comprehensive_score") is None
                    and record.get("github_evaluation_score") is None
                ]
                console.print(
                    f"  既无GitHub评分又无综合评分: {len(no_comprehensive_no_github)} 条记录"
                )
            else:
                console.print("  [yellow]⚠️ 表中不存在github_evaluation_score字段[/yellow]")
        except Exception as e:
            console.print(f"  [yellow]⚠️ 检查GitHub评分时出错: {e}[/yellow]")

        # 8. 按工具分组统计
        tool_stats = defaultdict(
            lambda: {"total": 0, "with_score": 0, "without_score": 0}
        )

        for record in all_data_result.data:
            tool_id = record.get("tool_identifier", "unknown")
            tool_stats[tool_id]["total"] += 1

            if record.get("comprehensive_score") is not None:
                tool_stats[tool_id]["with_score"] += 1
            else:
                tool_stats[tool_id]["without_score"] += 1

        # 显示工具统计
        console.print(f"\n[bold]🛠️ 工具统计 (前10个):[/bold]")
        sorted_tools = sorted(
            tool_stats.items(), key=lambda x: x[1]["total"], reverse=True
        )[:10]

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("工具标识符", style="dim")
        table.add_column("总记录数")
        table.add_column("有评分")
        table.add_column("无评分")
        table.add_column("完整性")

        for tool_id, stats in sorted_tools:
            completeness = (
                stats["with_score"] / stats["total"] * 100 if stats["total"] > 0 else 0
            )
            table.add_row(
                tool_id[:50] + "..." if len(tool_id) > 50 else tool_id,
                str(stats["total"]),
                str(stats["with_score"]),
                str(stats["without_score"]),
                f"{completeness:.1f}%",
            )

        console.print(table)

        console.print(f"\n[green]✅ 数据库完整性检查完成![/green]")

    except Exception as e:
        console.print(f"[red]❌ 检查失败: {e}[/red]")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
