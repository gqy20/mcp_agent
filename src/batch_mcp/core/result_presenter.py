"""ResultPresenter - 结果展示模块.

负责统一处理 CLI 命令的各种结果展示。
从 CLIHandler 中提取所有 _display_* 方法，遵循单一职责原则。

作者: AI Assistant
日期: 2025-08-18
版本: 0.1.0
"""

from typing import Any

from rich import print as rprint
from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, TextColumn
from rich.table import Table

from src.batch_mcp.core.input_type_detector import InputType


class ResultPresenter:
    """结果展示器 - 统一处理所有结果显示."""

    def display_input_type_detection(
        self, input_str: str, input_type: InputType
    ) -> None:
        """显示输入类型检测结果."""
        type_descriptions = {
            InputType.HTTP_ENDPOINT: "HTTP MCP端点",
            InputType.GITHUB_URL: "GitHub仓库",
            InputType.PACKAGE_NAME: "MCP包名",
            InputType.SEARCH_QUERY: "搜索查询",
            InputType.UNKNOWN: "未知格式",
        }

        type_icons = {
            InputType.HTTP_ENDPOINT: "🌐",
            InputType.GITHUB_URL: "📦",
            InputType.PACKAGE_NAME: "📋",
            InputType.SEARCH_QUERY: "🔍",
            InputType.UNKNOWN: "❓",
        }

        description = type_descriptions.get(input_type, "未知格式")
        icon = type_icons.get(input_type, "❓")

        rprint(f"[blue]{icon} 检测到{description}: {input_str}[/blue]")

    def display_evaluation_result(self, evaluation_result: dict) -> None:
        """显示评估结果 - 包含综合评分."""
        console = Console()
        table = Table(title="MCP 工具评估结果")

        table.add_column("类别", style="cyan", width=20)
        table.add_column("指标", style="magenta", width=25)
        table.add_column("分数", style="green", width=10)
        table.add_column("原因", style="white", width=50)

        sustainability = evaluation_result.get("sustainability", {})
        popularity = evaluation_result.get("popularity", {})
        test_success_info = evaluation_result.get("test_success_rate", {})
        evaluation_result.get("comprehensive_scoring", {})

        # 显示综合评分
        final_comprehensive_score = evaluation_result.get(
            "final_comprehensive_score",
            evaluation_result.get("final_score"),
        )
        table.add_row(
            "[bold red]综合评分[/bold red]",
            "",
            f"[bold red]{final_comprehensive_score}[/bold red]",
            "GitHub评估 + 测试成功率综合",
        )

        # 显示GitHub评估分数
        table.add_row(
            "GitHub评分",
            "",
            f"[bold]{evaluation_result.get('final_score')}[/bold]",
            "仓库可持续性和受欢迎程度",
        )

        # 显示测试成功率
        if test_success_info.get("success_rate") is not None:
            success_rate = test_success_info["success_rate"]
            test_count = test_success_info.get("test_count", 0)
            table.add_row(
                "测试成功率",
                "",
                f"[bold]{success_rate}%[/bold]",
                f"基于 {test_count} 次测试记录",
            )
        else:
            table.add_row("测试成功率", "", "[dim]暂无数据[/dim]", "无测试记录")

        table.add_section()
        table.add_row(
            "[bold]可持续性[/bold]",
            "",
            f"[bold]{sustainability.get('total_score')}[/bold]",
            "",
        )
        for metric, data in sustainability.get("details", {}).items():
            table.add_row("", metric, str(data.get("score")), data.get("reason"))

        table.add_section()
        table.add_row(
            "[bold]受欢迎程度[/bold]",
            "",
            f"[bold]{popularity.get('total_score')}[/bold]",
            "",
        )
        for metric, data in popularity.get("details", {}).items():
            table.add_row("", metric, str(data.get("score")), data.get("reason"))

        console.print(table)

    def display_deployment_success(
        self, server_info: Any, package_name: str | None = None
    ) -> None:
        """显示部署成功信息 - 统一格式."""
        rprint(f"[green]✅ 部署成功！服务器ID: {server_info.server_id}[/green]")

        if package_name:
            rprint(f"[blue]📦 包名: {package_name}[/blue]")

        if server_info.available_tools:
            rprint(
                f"[green]🛠️ 可用工具 ({len(server_info.available_tools)} 个):[/green]",
            )
            for i, tool in enumerate(server_info.available_tools, 1):
                tool_name = tool.get("name", "unknown")
                tool_desc = tool.get("description", "无描述")
                rprint(f"  {i}. [cyan]{tool_name}[/cyan] - {tool_desc[:60]}...")

    def display_http_evaluation_result(self, evaluation_result: dict) -> None:
        """显示HTTP MCP端点评估结果."""
        console = Console()

        # 显示总体评分
        scoring_breakdown = evaluation_result.get("scoring_breakdown", {})
        final_score = scoring_breakdown.get("final_score", 0)
        quality_grade = evaluation_result.get("quality_grade", "N/A")

        # 创建评分面板
        score_text = "[bold green]HTTP MCP 端点评估结果[/bold green]\n\n"
        score_text += f"🎯 综合评分: [bold cyan]{final_score}[/bold cyan]/100\n"
        score_text += f"🏆 质量等级: [bold yellow]{quality_grade}[/bold yellow]\n\n"

        score_text += "[bold]详细评分:[/bold]\n"
        score_text += f"🔗 连通性: {scoring_breakdown.get('connectivity_score', 0)}/100 (权重30%)\n"
        score_text += f"⚙️  功能性: {scoring_breakdown.get('functionality_score', 0)}/100 (权重40%)\n"
        score_text += (
            f"⚡ 性能: {scoring_breakdown.get('performance_score', 0)}/100 (权重20%)\n"
        )
        score_text += (
            f"📊 工具数量: {scoring_breakdown.get('quantity_score', 0)}/100 (权重10%)"
        )

        console.print(Panel(score_text, title="🔍 评估报告", border_style="green"))

        # 创建详细评分表格
        table = Table(title="评分明细")
        table.add_column("评估维度", style="cyan", width=15)
        table.add_column("得分", style="green", width=10)
        table.add_column("权重", style="yellow", width=10)
        table.add_column("说明", style="white", width=50)

        # 连通性评分
        connectivity_score = scoring_breakdown.get("connectivity_score", 0)
        connectivity_desc = (
            "服务连通性和稳定性" if connectivity_score == 100 else "服务连接存在问题"
        )
        table.add_row("连通性", f"{connectivity_score}/100", "30%", connectivity_desc)

        # 功能性评分
        functionality_score = scoring_breakdown.get("functionality_score", 0)
        functionality_desc = (
            "工具功能完整性" if functionality_score >= 80 else "工具功能需要改进"
        )
        table.add_row("功能性", f"{functionality_score}/100", "40%", functionality_desc)

        # 性能评分
        performance_score = scoring_breakdown.get("performance_score", 0)
        if performance_score >= 85:
            performance_desc = "响应速度优秀"
        elif performance_score >= 70:
            performance_desc = "响应速度良好"
        elif performance_score >= 50:
            performance_desc = "响应速度一般"
        else:
            performance_desc = "响应速度需要优化"
        table.add_row("性能", f"{performance_score}/100", "20%", performance_desc)

        # 工具数量评分
        quantity_score = scoring_breakdown.get("quantity_score", 0)
        details = scoring_breakdown.get("details", {})
        tools_count = details.get("tools_count", 0)
        quantity_desc = f"提供{tools_count}个工具" if tools_count > 0 else "未提供工具"
        table.add_row("工具数量", f"{quantity_score}/100", "10%", quantity_desc)

        console.print(table)

        # 显示改进建议
        recommendations = evaluation_result.get("recommendations", [])
        if recommendations:
            console.print("\n[bold yellow]💡 改进建议:[/bold yellow]")
            for i, rec in enumerate(recommendations, 1):
                console.print(f"  {i}. {rec}")

        # 显示详细信息
        if details:
            console.print("\n[bold]📈 统计信息:[/bold]")
            console.print(
                f"  • 功能测试数量: {details.get('functional_tests_count', 0)}"
            )
            console.print(
                f"  • 功能测试成功: {details.get('functional_tests_success', 0)}"
            )
            console.print(
                f"  • 平均响应时间: {details.get('response_time_seconds', 0):.2f}秒"
            )

        # 显示评分进度条
        console.print("\n[bold]📊 综合评分构成:[/bold]")
        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        ) as progress:
            # 连通性进度条
            connectivity_task = progress.add_task("连通性", total=100)
            progress.update(connectivity_task, completed=connectivity_score)

            # 功能性进度条
            functionality_task = progress.add_task("功能性", total=100)
            progress.update(functionality_task, completed=functionality_score)

            # 性能进度条
            performance_task = progress.add_task("性能", total=100)
            progress.update(performance_task, completed=performance_score)

            # 工具数量进度条
            quantity_task = progress.add_task("工具数量", total=100)
            progress.update(quantity_task, completed=quantity_score)


# 全局单例实例
_presenter = None


def get_result_presenter() -> ResultPresenter:
    """获取全局 ResultPresenter 实例（单例模式）."""
    global _presenter
    if _presenter is None:
        _presenter = ResultPresenter()
    return _presenter
