#!/usr/bin/env python3
"""
导出MCP工具综合评分数据到CSV文件
包含测试结果和GitHub评估的完整数据

遵循Linus原则：数据就是一切，好的数据结构胜过花哨的代码
"""

import csv
import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
from rich.progress import track

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core.evaluator import calculate_comprehensive_score_from_tests


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

    console.print("[blue]🗄️ 开始导出MCP工具综合评分数据...[/blue]")

    try:
        from supabase import create_client

        client = create_client(supabase_url, supabase_key)

        # 查询所有有评分的不同工具
        result = (
            client.table("mcp_test_results")
            .select("tool_identifier, tool_name, final_score")
            .not_.is_("final_score", "null")
            .execute()
        )

        if not result.data:
            console.print("[red]❌ 数据库中没有找到测试数据[/red]")
            return

        # 去重获取唯一工具
        tools = {}
        for record in result.data:
            identifier = record["tool_identifier"]
            if identifier not in tools:
                tools[identifier] = record["tool_name"]

        # 创建输出文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"mcp_comprehensive_scores_{timestamp}.csv"

        console.print(f"[green]✅ 找到 {len(tools)} 个工具，正在计算综合评分...[/green]")

        # CSV列定义
        fieldnames = [
            "tool_name",
            "github_url",
            "test_success_rate",
            "test_count",
            "successful_tests",
            "github_evaluation_score",
            "sustainability_score",
            "popularity_score",
            "comprehensive_score",
            "calculation_method",
            "quality_level",
            "export_timestamp",
        ]

        exported_count = 0

        with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for github_url in track(tools.keys(), description="计算评分..."):
                tool_name = tools[github_url]

                # 计算综合评分
                result = calculate_comprehensive_score_from_tests(github_url)

                if result and result.get("test_count", 0) > 0:
                    # 确定质量级别
                    comprehensive_score = result.get("comprehensive_score", 0)
                    if comprehensive_score >= 80:
                        quality_level = "优秀"
                    elif comprehensive_score >= 60:
                        quality_level = "良好"
                    else:
                        quality_level = "需改进"

                    # 写入CSV
                    row = {
                        "tool_name": tool_name,
                        "github_url": github_url,
                        "test_success_rate": result.get("success_rate"),
                        "test_count": result.get("test_count"),
                        "successful_tests": result.get("successful_tests"),
                        "github_evaluation_score": result.get(
                            "github_evaluation_score"
                        ),
                        "sustainability_score": result.get("sustainability_score"),
                        "popularity_score": result.get("popularity_score"),
                        "comprehensive_score": comprehensive_score,
                        "calculation_method": result.get("calculation_method"),
                        "quality_level": quality_level,
                        "export_timestamp": datetime.now().isoformat(),
                    }

                    writer.writerow(row)
                    exported_count += 1
                else:
                    console.print(
                        f"[dim yellow]⚠️ 跳过无测试数据的工具: {tool_name}[/dim yellow]"
                    )

        console.print(f"[green]✅ 成功导出 {exported_count} 个工具的综合评分数据[/green]")
        console.print(f"[blue]📄 输出文件: {output_file}[/blue]")

        # 显示统计信息
        console.print(f"\n[bold]📊 导出统计[/bold]")
        console.print(f"  总工具数: {len(tools)}")
        console.print(f"  有效数据: {exported_count}")
        console.print(f"  数据时间: {timestamp}")

        # 显示文件大小
        file_size = os.path.getsize(output_file)
        console.print(f"  文件大小: {file_size:,} 字节")

        console.print(f"\n[dim]💡 使用Excel或其他工具打开 {output_file} 进行进一步分析[/dim]")

    except Exception as e:
        console.print(f"[red]❌ 导出失败: {e}[/red]")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
