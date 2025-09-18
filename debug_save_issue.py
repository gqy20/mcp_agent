#!/usr/bin/env python3
"""
调试综合评分保存失败的详细原因
"""

import os
import sys
from datetime import datetime
from pathlib import Path

from rich.console import Console

console = Console()


def debug_main_flow_issues():
    """调试主流程中的综合评分保存问题"""
    console.print("[bold blue]🔍 调试主流程综合评分保存问题...[/bold blue]")

    # 获取最新的测试记录
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not supabase_url or not supabase_key:
        console.print("[red]❌ 数据库配置未设置[/red]")
        return False

    from supabase import create_client

    client = create_client(supabase_url, supabase_key)

    # 获取最新记录
    response = (
        client.table("mcp_test_results")
        .select("*")
        .eq("tool_identifier", "https://github.com/gqy20/article-mcp")
        .order("test_timestamp", desc=True)
        .limit(1)
        .execute()
    )

    if not response.data:
        console.print("[red]❌ 未找到测试记录[/red]")
        return False

    record = response.data[0]
    record_id = record["test_id"]
    github_url = record["tool_identifier"]

    console.print(f"[cyan]📋 调试记录: {record_id[:8]}...[/cyan]")
    console.print(f"  GitHub URL: {github_url}")
    console.print(f"  当前综合评分: {record.get('comprehensive_score', 'NULL')}")
    console.print(f"  当前GitHub评分: {record.get('final_score', 'NULL')}")

    # 步骤1: 测试综合评分计算函数
    console.print("\n[dim]🧮 步骤1: 测试综合评分计算函数...[/dim]")
    try:
        from src.core.evaluator import calculate_comprehensive_score_from_tests

        comp_result = calculate_comprehensive_score_from_tests(github_url, client)

        if comp_result:
            console.print(f"[green]✅ 计算函数返回结果:[/green]")
            for key, value in comp_result.items():
                console.print(f"  {key}: {value}")
        else:
            console.print("[red]❌ 计算函数返回None[/red]")
            return False

    except Exception as e:
        console.print(f"[red]❌ 计算函数异常: {e}[/red]")
        import traceback

        console.print(f"[red]{traceback.format_exc()}[/red]")
        return False

    # 步骤2: 测试数据库更新操作
    console.print("\n[dim]💾 步骤2: 测试数据库更新操作...[/dim]")
    try:
        if comp_result and comp_result.get("comprehensive_score") is not None:
            update_data = {
                "comprehensive_score": comp_result["comprehensive_score"],
                "calculation_method": comp_result["calculation_method"],
            }

            console.print(f"[dim]更新数据: {update_data}[/dim]")

            # 尝试更新
            update_response = (
                client.table("mcp_test_results")
                .update(update_data)
                .eq("test_id", record_id)
                .execute()
            )

            if update_response.data:
                console.print(f"[green]✅ 数据库更新成功[/green]")

                # 验证更新
                verify_response = (
                    client.table("mcp_test_results")
                    .select("comprehensive_score, calculation_method")
                    .eq("test_id", record_id)
                    .execute()
                )
                if verify_response.data:
                    updated_score = verify_response.data[0].get("comprehensive_score")
                    updated_method = verify_response.data[0].get("calculation_method")
                    console.print(
                        f"[green]✅ 验证成功: {updated_score} ({updated_method})[/green]"
                    )
                    return True
                else:
                    console.print("[red]❌ 更新后验证失败[/red]")
                    return False
            else:
                console.print("[red]❌ 数据库更新失败[/red]")
                if hasattr(update_response, "error") and update_response.error:
                    console.print(f"[red]错误: {update_response.error}[/red]")
                return False
        else:
            console.print("[red]❌ 综合评分为None，无法更新[/red]")
            return False

    except Exception as e:
        console.print(f"[red]❌ 数据库更新异常: {e}[/red]")
        import traceback

        console.print(f"[red]{traceback.format_exc()}[/red]")
        return False


def simulate_main_flow_logic():
    """模拟主流程逻辑，找出问题所在"""
    console.print("\n[bold blue]🔄 模拟主流程逻辑...[/bold blue]")

    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not supabase_url or not supabase_key:
        console.print("[red]❌ 数据库配置未设置[/red]")
        return False

    from supabase import create_client

    client = create_client(supabase_url, supabase_key)

    # 模拟主流程的评估结果
    evaluation_result = {
        "status": "success",
        "final_score": 45,
        "sustainability": {"total_score": 78},
        "popularity": {"total_score": 13},
    }

    github_url = "https://github.com/gqy20/article-mcp"

    console.print("[cyan]📊 模拟主流程步骤:[/cyan]")

    # 步骤1: 检查评估结果
    if evaluation_result and evaluation_result.get("status") == "success":
        console.print("[dim]✅ 评估结果成功[/dim]")

        # 步骤2: 计算综合评分
        try:
            from src.core.evaluator import calculate_comprehensive_score_from_tests

            console.print("[dim]🔄 计算综合评分...[/dim]")
            comp_result = calculate_comprehensive_score_from_tests(github_url, client)

            if comp_result and comp_result.get("comprehensive_score") is not None:
                console.print(
                    f"[dim]✅ 综合评分计算成功: {comp_result['comprehensive_score']}[/dim]"
                )

                # 步骤3: 模拟更新操作
                try:
                    # 这里我们测试更新一个已存在的记录
                    record_response = (
                        client.table("mcp_test_results")
                        .select("test_id")
                        .eq("tool_identifier", github_url)
                        .order("test_timestamp", desc=True)
                        .limit(1)
                        .execute()
                    )

                    if record_response.data:
                        record_id = record_response.data[0]["test_id"]
                        console.print(f"[dim]📋 找到记录: {record_id[:8]}...[/dim]")

                        update_data = {
                            "comprehensive_score": comp_result["comprehensive_score"],
                            "calculation_method": comp_result["calculation_method"],
                        }

                        update_response = (
                            client.table("mcp_test_results")
                            .update(update_data)
                            .eq("test_id", record_id)
                            .execute()
                        )

                        if update_response.data:
                            console.print(f"[green]✅ 主流程逻辑模拟成功[/green]")
                            console.print(
                                f"[green]✅ 综合评分: {comp_result['comprehensive_score']} ({comp_result['calculation_method']})[/green]"
                            )
                            return True
                        else:
                            console.print("[red]❌ 主流程更新失败[/red]")
                            return False
                    else:
                        console.print("[red]❌ 未找到记录[/red]")
                        return False

                except Exception as update_error:
                    console.print(f"[red]❌ 更新异常: {update_error}[/red]")
                    return False
            else:
                console.print("[red]❌ 综合评分计算失败[/red]")
                console.print(f"[red]计算结果: {comp_result}[/red]")
                return False

        except Exception as e:
            console.print(f"[red]❌ 综合评分处理异常: {e}[/red]")
            return False
    else:
        console.print("[red]❌ 评估结果失败[/red]")
        return False


def main():
    """主函数"""
    console.print("[bold magenta]🔧 综合评分保存问题调试工具[/bold magenta]")

    # 调试现有问题
    if not debug_main_flow_issues():
        console.print("[red]❌ 调试失败[/red]")
        return

    # 模拟主流程
    if not simulate_main_flow_logic():
        console.print("[red]❌ 模拟失败[/red]")
        return

    console.print("\n[bold green]🎉 调试完成![/bold green]")


if __name__ == "__main__":
    main()
