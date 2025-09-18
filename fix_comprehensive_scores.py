#!/usr/bin/env python3
"""
综合评分修复工具
修复数据库中缺少comprehensive_score的记录
"""

import os
import sys
from datetime import datetime
from pathlib import Path

from rich.console import Console

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from supabase import create_client

console = Console()


def fix_missing_comprehensive_scores():
    """修复缺少综合评分的记录"""
    console.print("[bold blue]🔧 修复缺少综合评分的记录...[/bold blue]")

    # 检查环境变量
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not supabase_url or not supabase_key:
        console.print("[red]❌ 数据库配置未设置[/red]")
        return False

    client = create_client(supabase_url, supabase_key)

    try:
        from src.core.evaluator import calculate_comprehensive_score_from_tests

        # 查询所有缺少综合评分的记录
        console.print("[cyan]🔍 查询缺少综合评分的记录...[/cyan]")

        response = (
            client.table("mcp_test_results")
            .select("*")
            .is_("comprehensive_score", "null")
            .execute()
        )

        if not response.data:
            console.print("[green]✅ 没有缺少综合评分的记录[/green]")
            return True

        records = response.data
        console.print(f"[yellow]📋 找到 {len(records)} 条需要修复的记录[/yellow]")

        fixed_count = 0
        failed_count = 0

        for record in records:
            tool_identifier = record.get("tool_identifier", "")
            record_id = record["test_id"]

            if not tool_identifier:
                console.print(
                    f"[yellow]⚠️ 跳过记录 {record_id[:8]}...: 缺少tool_identifier[/yellow]"
                )
                continue

            console.print(f"[cyan]🔄 处理: {tool_identifier}[/cyan]")

            try:
                # 计算综合评分
                result = calculate_comprehensive_score_from_tests(
                    tool_identifier, client
                )

                if result and result.get("comprehensive_score") is not None:
                    # 更新记录
                    update_data = {
                        "comprehensive_score": result["comprehensive_score"],
                        "calculation_method": result["calculation_method"],
                    }

                    update_response = (
                        client.table("mcp_test_results")
                        .update(update_data)
                        .eq("test_id", record_id)
                        .execute()
                    )

                    if update_response.data:
                        console.print(
                            f"[green]✅ 修复成功: {result['comprehensive_score']} ({result['calculation_method']})[/green]"
                        )
                        fixed_count += 1
                    else:
                        console.print(f"[red]❌ 更新失败[/red]")
                        failed_count += 1
                else:
                    console.print(f"[yellow]⚠️ 无法计算综合评分[/yellow]")
                    failed_count += 1

            except Exception as e:
                console.print(f"[red]❌ 处理异常: {e}[/red]")
                failed_count += 1

        console.print(f"\n[bold green]🎉 修复完成![/bold green]")
        console.print(f"[green]✅ 成功修复: {fixed_count} 条记录[/green]")
        console.print(f"[red]❌ 修复失败: {failed_count} 条记录[/red]")

        return True

    except Exception as e:
        console.print(f"[red]❌ 修复异常: {e}[/red]")
        import traceback

        console.print(f"[red]{traceback.format_exc()}[/red]")
        return False


def verify_article_mcp_score():
    """验证article-mcp的综合评分"""
    console.print("\n[bold blue]🔍 验证article-mcp综合评分...[/bold blue]")

    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not supabase_url or not supabase_key:
        console.print("[red]❌ 数据库配置未设置[/red]")
        return False

    client = create_client(supabase_url, supabase_key)

    # 查询article-mcp的记录
    response = (
        client.table("mcp_test_results")
        .select("*")
        .eq("tool_identifier", "https://github.com/gqy20/article-mcp")
        .order("test_timestamp", desc=True)
        .limit(1)
        .execute()
    )

    if response.data:
        record = response.data[0]
        console.print(f"[green]✅ 找到记录:[/green]")
        console.print(f"  ID: {record['test_id'][:8]}...")
        console.print(f"  工具名: {record['tool_name']}")
        console.print(f"  综合评分: {record.get('comprehensive_score', 'NULL')}")
        console.print(f"  计算方法: {record.get('calculation_method', 'NULL')}")
        console.print(f"  GitHub评分: {record.get('final_score', 'NULL')}")
        console.print(f"  测试成功: {record.get('test_success', 'NULL')}")
        console.print(f"  时间: {record['test_timestamp'][:19]}")

        return True
    else:
        console.print("[red]❌ 未找到记录[/red]")
        return False


def main():
    """主函数"""
    console.print("[bold magenta]🔧 综合评分修复工具[/bold magenta]")

    # 修复缺少综合评分的记录
    if not fix_missing_comprehensive_scores():
        console.print("[red]❌ 修复失败[/red]")
        return

    # 验证article-mcp
    if not verify_article_mcp_score():
        console.print("[red]❌ 验证失败[/red]")
        return

    console.print("\n[bold green]🎉 所有操作成功完成![/bold green]")


if __name__ == "__main__":
    main()
