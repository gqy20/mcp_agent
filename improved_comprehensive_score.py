#!/usr/bin/env python3
"""
改进的综合评分计算和更新功能
用于修复主流程中的综合评分计算问题
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


def improved_comprehensive_score_update(github_url: str, record_id: str, client=None):
    """
    改进的综合评分更新函数
    解决主流程中综合评分计算失败的问题
    """
    console.print(f"[cyan]🔄 改进的综合评分更新: {github_url}[/cyan]")

    # 如果没有提供客户端，创建一个
    if not client:
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        if not supabase_url or not supabase_key:
            console.print("[red]❌ 数据库配置未设置[/red]")
            return False
        client = create_client(supabase_url, supabase_key)

    try:
        from src.core.evaluator import calculate_comprehensive_score_from_tests

        # 步骤1: 计算综合评分
        console.print("[dim]📊 步骤1: 计算综合评分...[/dim]")
        comp_result = calculate_comprehensive_score_from_tests(github_url, client)

        if not comp_result:
            console.print("[red]❌ 综合评分计算返回None[/red]")
            return False

        comprehensive_score = comp_result.get("comprehensive_score")
        if comprehensive_score is None:
            console.print("[red]❌ 综合评分为None[/red]")
            console.print(f"[dim]调试信息: {comp_result}[/dim]")
            return False

        console.print(f"[green]✅ 综合评分计算成功: {comprehensive_score}[/green]")

        # 步骤2: 验证数据库记录存在
        console.print("[dim]🔍 步骤2: 验证数据库记录...[/dim]")
        record_check = (
            client.table("mcp_test_results")
            .select("test_id")
            .eq("test_id", record_id)
            .execute()
        )

        if not record_check.data:
            console.print(f"[red]❌ 记录不存在: {record_id}[/red]")
            return False

        console.print(f"[green]✅ 记录验证成功: {record_id[:8]}...[/green]")

        # 步骤3: 准备更新数据
        console.print("[dim]💾 步骤3: 准备更新数据...[/dim]")
        update_data = {
            "comprehensive_score": comprehensive_score,
            "calculation_method": comp_result.get("calculation_method", "unknown"),
        }

        console.print(f"[dim]更新数据: {update_data}[/dim]")

        # 步骤4: 执行更新
        console.print("[dim]📤 步骤4: 执行数据库更新...[/dim]")
        update_response = (
            client.table("mcp_test_results")
            .update(update_data)
            .eq("test_id", record_id)
            .execute()
        )

        if update_response.data:
            console.print(f"[green]✅ 数据库更新成功![/green]")
            console.print(
                f"[green]✅ 综合评分: {comprehensive_score} ({comp_result.get('calculation_method')})[/green]"
            )
            return True
        else:
            console.print(f"[red]❌ 数据库更新失败[/red]")
            if hasattr(update_response, "error") and update_response.error:
                console.print(f"[red]错误信息: {update_response.error}[/red]")
            return False

    except Exception as e:
        console.print(f"[red]❌ 更新异常: {e}[/red]")
        import traceback

        console.print(f"[red]{traceback.format_exc()}[/red]")
        return False


def test_with_article_mcp():
    """使用article-mcp测试改进的综合评分更新"""
    console.print("[bold blue]🧪 测试改进的综合评分更新功能...[/bold blue]")

    github_url = "https://github.com/gqy20/article-mcp"

    # 获取最新的记录ID
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not supabase_url or not supabase_key:
        console.print("[red]❌ 数据库配置未设置[/red]")
        return False

    client = create_client(supabase_url, supabase_key)

    # 查询最新的记录
    response = (
        client.table("mcp_test_results")
        .select("test_id, test_timestamp")
        .eq("tool_identifier", github_url)
        .order("test_timestamp", desc=True)
        .limit(1)
        .execute()
    )

    if not response.data:
        console.print("[red]❌ 未找到记录[/red]")
        return False

    record_id = response.data[0]["test_id"]
    console.print(f"[cyan]📋 使用记录: {record_id[:8]}...[/cyan]")

    # 先检查当前的综合评分
    current_record = (
        client.table("mcp_test_results")
        .select("comprehensive_score, calculation_method")
        .eq("test_id", record_id)
        .execute()
    )
    if current_record.data:
        current_score = current_record.data[0].get("comprehensive_score", "NULL")
        current_method = current_record.data[0].get("calculation_method", "NULL")
        console.print(f"[yellow]当前综合评分: {current_score} ({current_method})[/yellow]")

    # 执行改进的更新
    success = improved_comprehensive_score_update(github_url, record_id, client)

    if success:
        # 验证更新结果
        updated_record = (
            client.table("mcp_test_results")
            .select("comprehensive_score, calculation_method")
            .eq("test_id", record_id)
            .execute()
        )
        if updated_record.data:
            new_score = updated_record.data[0].get("comprehensive_score", "NULL")
            new_method = updated_record.data[0].get("calculation_method", "NULL")
            console.print(f"[green]✅ 更新后综合评分: {new_score} ({new_method})[/green]")

            if new_score != current_score:
                console.print("[bold green]🎉 综合评分更新成功![/bold green]")
            else:
                console.print("[yellow]⚠️ 综合评分未变化[/yellow]")

    return success


def main():
    """主函数"""
    console.print("[bold magenta]🔧 改进的综合评分更新工具[/bold magenta]")

    # 测试article-mcp
    if not test_with_article_mcp():
        console.print("[red]❌ 测试失败[/red]")
        return

    console.print("\n[bold green]🎉 测试完成![/bold green]")


if __name__ == "__main__":
    main()
