#!/usr/bin/env python3
"""
修复数据库中的综合评分数据

这个脚本用于:
1. 为没有综合评分的记录计算综合评分
2. 填充缺失的tool_identifier字段
3. 更新数据库中的记录
"""

import os
from datetime import datetime

from dotenv import load_dotenv
from rich.console import Console
from supabase import create_client

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

    console.print("[blue]🔧 开始修复数据库中的综合评分数据...[/blue]")

    try:
        # 创建Supabase客户端
        client = create_client(supabase_url, supabase_key)

        # 1. 查询没有综合评分的记录
        console.print("[blue]🔍 查找没有综合评分的记录...[/blue]")
        result = (
            client.table("mcp_test_results")
            .select("*")
            .is_("comprehensive_score", "null")
            .execute()
        )

        records_without_score = result.data
        console.print(f"[green]✅ 找到 {len(records_without_score)} 条没有综合评分的记录[/green]")

        # 2. 为每条记录计算综合评分
        updated_count = 0
        failed_count = 0

        for record in records_without_score:
            try:
                test_id = record["test_id"]
                tool_identifier = record.get("tool_identifier")

                if not tool_identifier:
                    console.print(
                        f"[yellow]⚠️ 跳过记录 {test_id}: 缺少tool_identifier[/yellow]"
                    )
                    continue

                console.print(f"[blue]🔄 正在处理: {tool_identifier}[/blue]")

                # 计算综合评分
                score_result = calculate_comprehensive_score_from_tests(
                    tool_identifier, client
                )

                if score_result and score_result.get("comprehensive_score") is not None:
                    comprehensive_score = score_result["comprehensive_score"]
                    github_evaluation_score = score_result.get(
                        "github_evaluation_score"
                    )
                    sustainability_score = score_result.get("sustainability_score")
                    popularity_score = score_result.get("popularity_score")
                    calculation_method = score_result.get("calculation_method")

                    # 更新数据库记录
                    update_data = {
                        "comprehensive_score": comprehensive_score,
                        "evaluation_timestamp": datetime.now().isoformat(),
                    }

                    # 只有当值不为None时才更新
                    if github_evaluation_score is not None:
                        update_data["github_evaluation_score"] = github_evaluation_score
                    if sustainability_score is not None:
                        update_data["sustainability_score"] = sustainability_score
                    if popularity_score is not None:
                        update_data["popularity_score"] = popularity_score
                    if calculation_method:
                        update_data["calculation_method"] = calculation_method

                    # 更新记录
                    update_result = (
                        client.table("mcp_test_results")
                        .update(update_data)
                        .eq("test_id", test_id)
                        .execute()
                    )

                    if update_result.data:
                        console.print(
                            f"[green]✅ 更新成功: {tool_identifier} -> 综合评分: {comprehensive_score}[/green]"
                        )
                        updated_count += 1
                    else:
                        console.print(f"[red]❌ 更新失败: {tool_identifier}[/red]")
                        failed_count += 1
                else:
                    console.print(f"[yellow]⚠️ 无法计算综合评分: {tool_identifier}[/yellow]")
                    failed_count += 1

            except Exception as e:
                console.print(f"[red]❌ 处理记录时出错: {e}[/red]")
                failed_count += 1

        # 3. 显示结果统计
        console.print(f"\n[bold]📊 更新结果统计:[/bold]")
        console.print(f"  成功更新: {updated_count} 条记录")
        console.print(f"  更新失败: {failed_count} 条记录")
        console.print(f"  总计处理: {len(records_without_score)} 条记录")

        # 4. 验证更新结果
        console.print(f"\n[blue]🔍 验证更新结果...[/blue]")
        verification_result = (
            client.table("mcp_test_results")
            .select("count")
            .not_.is_("comprehensive_score", "null")
            .execute()
        )
        new_with_score_count = len(verification_result.data)
        console.print(f"[green]✅ 现在有综合评分的记录数: {new_with_score_count}[/green]")

        console.print(f"\n[green]✅ 数据库修复完成![/green]")

    except Exception as e:
        console.print(f"[red]❌ 修复失败: {e}[/red]")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
