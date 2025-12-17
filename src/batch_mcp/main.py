#!/usr/bin/env python3
"""MCP 测试框架 - 主入口 (简洁版).

遵循 Linus 的"好品味"原则：
- CLI入口只负责参数解析和委托
- 每个命令<20行
- 无业务逻辑，无深度嵌套

作者: AI Assistant (Linus重构版)
日期: 2025-08-18
版本: 0.1.0 (简洁版)
"""

import sys
from pathlib import Path

import typer
from rich import print as rprint

# 导入配置管理
try:
    from .core.config import get_config

    config = get_config()
    project_root = config.paths.project_root

    # 加载环境变量 - 确保数据库配置可用
    try:
        from dotenv import load_dotenv

        env_file = project_root / ".env"
        if env_file.exists():
            load_dotenv(env_file)
            # rprint(f"[dim]✅ 已加载环境变量: {env_file}[/dim]")
    except ImportError:
        pass  # python-dotenv 不是必须依赖
except ImportError:
    # 如果配置系统不可用，回退到传统方式
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))

from src.batch_mcp.core.cli_handlers import get_cli_handler
from src.batch_mcp.core.tester import TestConfig

app = typer.Typer(
    name="batch-mcp",
    help="动态 MCP 工具部署和测试框架 - 简洁版",
    add_completion=False,
    rich_markup_mode="rich",
)

handler = get_cli_handler()


@app.command("test-url")
def test_single_url(
    url: str = typer.Argument(..., help="要测试的 MCP 工具 URL"),
    timeout: int = typer.Option(
        600,
        "--timeout",
        "-t",
        help="测试超时时间（秒，默认10分钟）",
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="详细输出模式"),
    save_report: bool = typer.Option(
        True,
        "--save-report/--no-save-report",
        help="保存测试报告",
    ),
    cleanup: bool = typer.Option(True, "--cleanup/--no-cleanup", help="自动清理"),
    smart: bool = typer.Option(
        True,
        "--smart/--no-smart",
        help="启用AI智能测试（默认开启）",
    ),
    db_export: bool = typer.Option(
        True,
        "--db-export/--no-db-export",
        help="导出结果到数据库（默认开启）",
    ),
    evaluate: bool = typer.Option(
        True,
        "--evaluate/--no-evaluate",
        help="对工具进行评估（默认开启）",
    ),
) -> None:
    """测试单个 MCP 工具 URL."""
    rprint(f"[bold green]🎯 开始测试 MCP 工具:[/bold green] {url}")

    config = TestConfig(
        timeout,
        verbose,
        smart,
        cleanup,
        save_report,
        db_export,
        evaluate,
    )
    success = handler.test_url(url, config)

    if success:
        rprint(f"\n[bold green]🎉 {url} 测试完成！[/bold green]")
    else:
        raise typer.Exit(1)


@app.command("test-package")
def test_package(
    package: str = typer.Argument(..., help="要测试的 MCP 包名"),
    timeout: int = typer.Option(
        600,
        "--timeout",
        "-t",
        help="测试超时时间（秒，默认10分钟）",
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="详细输出模式"),
    save_report: bool = typer.Option(
        True,
        "--save-report/--no-save-report",
        help="保存测试报告",
    ),
    cleanup: bool = typer.Option(True, "--cleanup/--no-cleanup", help="自动清理"),
    smart: bool = typer.Option(
        True,
        "--smart/--no-smart",
        help="启用AI智能测试（默认开启）",
    ),
    db_export: bool = typer.Option(
        True,
        "--db-export/--no-db-export",
        help="导出结果到数据库（默认开启）",
    ),
    evaluate: bool = typer.Option(
        True,
        "--evaluate/--no-evaluate",
        help="对工具进行评估（默认开启）",
    ),
) -> None:
    """直接测试指定的 MCP 包."""
    rprint(f"[bold green]📦 开始测试 MCP 包:[/bold green] {package}")

    config = TestConfig(
        timeout,
        verbose,
        smart,
        cleanup,
        save_report,
        db_export,
        evaluate,
    )
    success = handler.test_package(package, config)

    if success:
        rprint(f"\n[bold green]🎉 {package} 测试完成！[/bold green]")
    else:
        raise typer.Exit(1)


@app.command("list-tools")
def list_available_tools(
    category: str = typer.Option(None, "--category", "-c", help="按类别筛选"),
    search: str = typer.Option(None, "--search", "-s", help="搜索工具"),
    limit: int = typer.Option(20, "--limit", "-l", help="显示数量限制"),
    show_package: bool = typer.Option(False, "--show-package", help="显示包名"),
) -> None:
    """列出可用的 MCP 工具."""
    rprint("[bold green]📋 加载 MCP 工具列表...[/bold green]")
    handler.list_tools(category, search, limit, show_package)


@app.command("analyze-github")
def analyze_github_repos(
    urls: str = typer.Argument(..., help="GitHub URLs，用逗号分隔或提供文件路径"),
    output: str = typer.Option(
        "auto_update_report.json",
        "--output",
        "-o",
        help="输出报告文件",
    ),
    update_tables: bool = typer.Option(
        True,
        "--update-tables/--no-update-tables",
        help="是否更新MCP表格",
    ),
) -> None:
    """分析GitHub项目并自动添加MCP工具到表格."""
    rprint("[bold green]🔍 开始分析GitHub项目...[/bold green]")

    try:
        from src.batch_mcp.core.mcp_table_updater import MCPTableUpdater

        # 检查输入是文件还是直接URLs
        if urls.endswith((".txt", ".csv")):
            # 从文件读取URLs
            with open(urls, encoding="utf-8") as f:
                github_urls = [line.strip() for line in f if line.strip()]
            rprint(f"[dim]📄 从文件读取 {len(github_urls)} 个URLs[/dim]")
        else:
            # 直接解析URLs
            github_urls = [url.strip() for url in urls.split(",") if url.strip()]
            rprint(f"[dim]📋 解析到 {len(github_urls)} 个URLs[/dim]")

        if not github_urls:
            rprint("[red]❌ 没有找到有效的GitHub URLs[/red]")
            raise typer.Exit(1)

        # 初始化更新器
        updater = MCPTableUpdater()

        # 执行更新
        results = updater.update_with_new_repos(github_urls)

        # 生成报告
        updater.generate_report(results)

        # 保存结果到文件
        import json

        with open(output, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        rprint(f"[green]📄 报告已保存到: {output}[/green]")

        # 如果没有新增MCP工具，输出提示
        if not results["added_tools"]:
            rprint("[yellow]💡 没有发现新的MCP工具。可能的原因：[/yellow]")
            rprint("[yellow]   • 这些项目已经在表格中[/yellow]")
            rprint("[yellow]   • 这些项目不是MCP工具[/yellow]")
            rprint("[yellow]   • GitHub API访问限制[/yellow]")

    except Exception as e:
        rprint(f"[red]❌ 分析失败: {e}[/red]")
        raise typer.Exit(1)


@app.command("test-http")
def test_http_endpoint(
    url: str = typer.Argument(..., help="HTTP MCP 端点 URL"),
    timeout: int = typer.Option(
        300,
        "--timeout",
        "-t",
        help="测试超时时间（秒，默认5分钟）",
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="详细输出模式"),
    save_report: bool = typer.Option(
        True,
        "--save-report/--no-save-report",
        help="保存测试报告",
    ),
    cleanup: bool = typer.Option(True, "--cleanup/--no-cleanup", help="自动清理"),
    smart: bool = typer.Option(
        True,
        "--smart/--no-smart",
        help="启用AI智能测试（默认开启）",
    ),
    db_export: bool = typer.Option(
        True,
        "--db-export/--no-db-export",
        help="导出结果到数据库（默认开启）",
    ),
    evaluate: bool = typer.Option(
        False,  # HTTP端点通常没有GitHub仓库，默认禁用
        "--evaluate/--no-evaluate",
        help="对工具进行评估（默认禁用）",
    ),
    auth_token: str = typer.Option(
        None,
        "--auth-token",
        help="API认证令牌（Bearer Token）",
    ),
) -> None:
    """测试 HTTP MCP 端点."""
    # URL验证
    if not (url.startswith(("http://", "https://"))):
        rprint("[red]❌ URL 必须以 http:// 或 https:// 开头[/red]")
        raise typer.Exit(1)

    rprint(f"[bold green]🌐 开始测试 HTTP MCP 端点:[/bold green] {url}")

    config = TestConfig(
        timeout=timeout,
        verbose=verbose,
        smart_test=smart,  # 注意字段名是smart_test
        cleanup=cleanup,  # HTTP测试始终启用cleanup
        save_report=save_report,
        db_export=db_export,
        evaluate=evaluate,
    )

    success = handler.test_http_endpoint(url, config, auth_token)

    if success:
        rprint("\n[bold green]🎉 HTTP MCP 端点测试完成！[/bold green]")
    else:
        raise typer.Exit(1)


@app.command("init-env")
def init_environment() -> None:
    """初始化测试环境."""
    rprint("[bold green]🔧 初始化测试环境...[/bold green]")
    # 简化的环境检查
    try:
        from src.batch_mcp.core.simple_mcp_deployer import get_simple_mcp_deployer
        from src.batch_mcp.utils.csv_parser import get_mcp_parser

        parser = get_mcp_parser()
        tools = parser.get_all_tools()
        rprint(f"[green]✅ 找到 {len(tools)} 个可用工具[/green]")

        get_simple_mcp_deployer()
        rprint("[green]✅ 部署器已就绪[/green]")
        rprint("[green]✅ 环境检查完成[/green]")

    except Exception as e:
        rprint(f"[red]❌ 环境检查失败: {e}[/red]")
        raise typer.Exit(1)


@app.callback()
def main(version: bool = typer.Option(False, "--version", help="显示版本信息")) -> None:
    """MCP 测试框架 - 简洁版."""
    if version:
        rprint("[bold green]Batch MCP Testing Framework v0.1.0 (简洁版)[/bold green]")
        raise typer.Exit


if __name__ == "__main__":
    app()
