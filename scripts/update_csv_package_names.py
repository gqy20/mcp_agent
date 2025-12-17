#!/usr/bin/env python3
"""
更新CSV数据库中缺少包名信息的记录

使用GitHub分析器更新缺少package_name、deployment_method、
install_command和run_command的记录
"""

import csv
import sys
from pathlib import Path

import pandas as pd
from rich.console import Console

from src.core.github_mcp_analyzer import GitHubMCPAnalyzer
from src.utils.csv_parser import MCPDataParser

console = Console()


def update_missing_package_names():
    """更新缺少包名信息的记录"""
    console.print("[bold blue]🔧 开始更新CSV数据库中的包名信息...[/bold blue]")

    # 初始化解析器和分析器
    parser = MCPDataParser("data/mcp_database/mcp.csv")
    analyzer = GitHubMCPAnalyzer()

    # 加载数据
    if not parser.load_data():
        console.print("[red]❌ 无法加载CSV数据[/red]")
        return False

    df = parser.df.copy()
    console.print(f"[blue]📊 总记录数: {len(df)}[/blue]")

    # 检查字段是否存在，不存在则创建
    if "package_name" not in df.columns:
        df["package_name"] = ""
    if "deployment_method" not in df.columns:
        df["deployment_method"] = ""
    if "install_command" not in df.columns:
        df["install_command"] = ""
    if "run_command" not in df.columns:
        df["run_command"] = ""

    # 统计需要更新的记录
    missing_package = (
        df["package_name"].isna()
        | (df["package_name"] == "")
        | (df["package_name"] == "None")
    )
    missing_deployment = df["deployment_method"].isna() | (
        df["deployment_method"] == ""
    )
    missing_install = df["install_command"].isna() | (df["install_command"] == "")
    missing_run = df["run_command"].isna() | (df["run_command"] == "")

    needs_update = missing_package | missing_deployment | missing_install | missing_run
    update_count = needs_update.sum()

    console.print(f"[yellow]📋 需要更新的记录数: {update_count}[/yellow]")

    if update_count == 0:
        console.print("[green]✅ 所有记录都已包含完整信息，无需更新[/green]")
        return True

    # 备份原文件
    backup_path = Path("data/mcp_database/mcp.csv.backup")
    if backup_path.exists():
        backup_path.unlink()

    Path("data/mcp_database/mcp.csv").rename(backup_path)
    console.print(f"[blue]💾 原文件已备份到: {backup_path}[/blue]")

    # 更新记录
    updated_count = 0
    failed_count = 0

    for index, row in df.iterrows():
        if not needs_update.iloc[index]:
            continue

        github_url = row.get("github_url", "")
        if not github_url or pd.isna(github_url):
            continue

        console.print(
            f"\n[cyan]🔄 正在处理 ({index + 1}/{len(df)}): {row.get('name', 'Unknown')}[/cyan]"
        )

        try:
            # 使用GitHub分析器重新分析
            result = analyzer.analyze_github_repo(github_url)

            if result and result.get("success"):
                record = result.get("record", {})

                # 更新字段
                df.at[index, "package_name"] = record.get("package_name", "")
                df.at[index, "deployment_method"] = record.get("deployment_method", "")
                df.at[index, "install_command"] = record.get("install_command", "")
                df.at[index, "run_command"] = record.get("run_command", "")

                console.print(
                    f"[green]✅ 已更新包名: {record.get('package_name', 'N/A')}[/green]"
                )
                updated_count += 1
            else:
                console.print(
                    f"[red]❌ 分析失败: {result.get('error', 'Unknown') if result else 'Unknown'}[/red]"
                )
                failed_count += 1

        except Exception as e:
            console.print(f"[red]❌ 处理异常: {e}[/red]")
            failed_count += 1

    # 保存更新后的文件
    df.to_csv("data/mcp_database/mcp.csv", index=False, encoding="utf-8")

    console.print(f"\n[bold green]🎉 更新完成！[/bold green]")
    console.print(f"[green]✅ 成功更新: {updated_count} 条记录[/green]")
    console.print(f"[red]❌ 更新失败: {failed_count} 条记录[/red]")

    # 验证更新结果
    console.print("\n[blue]🔍 验证更新结果...[/blue]")

    # 检查article-mcp是否已更新
    article_mcp = df[df["github_url"] == "https://github.com/gqy20/article-mcp"]
    if not article_mcp.empty:
        package_name = article_mcp.iloc[0].get("package_name", "")
        console.print(f"[green]✅ article-mcp包名已更新为: {package_name}[/green]")
    else:
        console.print("[yellow]⚠️ 未找到article-mcp记录[/yellow]")

    return True


def test_article_mcp():
    """测试article-mcp的信息是否正确"""
    console.print("\n[bold blue]🧪 测试article-mcp信息...[/bold blue]")

    parser = MCPDataParser("data/mcp_database/mcp.csv")
    tool = parser.find_tool_by_url("https://github.com/gqy20/article-mcp")

    if tool:
        console.print(f"[green]✅ 找到工具: {tool.name}[/green]")
        console.print(f"[green]✅ 包名: {tool.package_name}[/green]")
        console.print(f"[green]✅ 部署方法: {tool.deployment_method}[/green]")
        console.print(f"[green]✅ 安装命令: {tool.install_command}[/green]")
        console.print(f"[green]✅ 运行命令: {tool.run_command}[/green]")

        # 检查是否还有缺失信息
        if not tool.package_name:
            console.print("[red]❌ 包名仍为空[/red]")
            return False
        if not tool.install_command:
            console.print("[red]❌ 安装命令为空[/red]")
            return False
        if not tool.run_command:
            console.print("[red]❌ 运行命令为空[/red]")
            return False

        console.print("[green]✅ 所有信息都已完整！[/green]")
        return True
    else:
        console.print("[red]❌ 未找到article-mcp[/red]")
        return False


def main():
    """主函数"""
    console.print("[bold magenta]🔧 MCP数据库包名信息更新工具[/bold magenta]")

    # 更新数据库
    if not update_missing_package_names():
        console.print("[red]❌ 更新失败[/red]")
        sys.exit(1)

    # 测试结果
    if not test_article_mcp():
        console.print("[red]❌ 测试失败[/red]")
        sys.exit(1)

    console.print("\n[bold green]🎉 所有操作成功完成！[/bold green]")


if __name__ == "__main__":
    main()
