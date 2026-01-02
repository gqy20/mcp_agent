"""报告生成器模块.

此模块包含测试报告的生成函数。
"""

import json
from pathlib import Path

from rich.panel import Panel

try:
    from rich import print as rprint
    from rich.console import Console
except ImportError:

    def rprint(text) -> None:
        pass

    Console = None

from .models import TestReport


class ReportGenerator:
    """测试报告生成器."""

    def __init__(self, reports_dir: Path) -> None:
        self.reports_dir = reports_dir
        self.console = Console() if Console else None

    async def generate_reports(self, report: TestReport) -> None:
        """生成多格式测试报告."""
        # 1. JSON报告
        await self._generate_json_report(report)

        # 2. HTML报告
        await self._generate_html_report(report)

        # 3. 控制台摘要
        self._print_console_summary(report)

    async def _generate_json_report(self, report: TestReport) -> None:
        """生成JSON格式报告."""
        try:
            from dataclasses import asdict

            timestamp = report.start_time.strftime("%Y%m%d_%H%M%S")
            filename = f"mcp_test_{timestamp}_{report.session_id}.json"
            filepath = self.reports_dir / filename

            # 转换为可序列化的格式
            report_data = asdict(report)
            report_data["start_time"] = report.start_time.isoformat()
            report_data["end_time"] = (
                report.end_time.isoformat() if report.end_time else None
            )

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)

            rprint(f"[green]✅ JSON报告: {filepath}[/green]")

        except Exception as e:
            rprint(f"[red]❌ JSON报告生成失败: {e}[/red]")

    async def _generate_html_report(self, report: TestReport) -> None:
        """生成HTML格式报告."""
        try:
            timestamp = report.start_time.strftime("%Y%m%d_%H%M%S")
            filename = f"mcp_test_{timestamp}_{report.session_id}.html"
            filepath = self.reports_dir / filename

            html_content = self._create_html_template(report)

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(html_content)

            rprint(f"[green]✅ HTML报告: {filepath}[/green]")

        except Exception as e:
            rprint(f"[red]❌ HTML报告生成失败: {e}[/red]")

    def _create_html_template(self, report: TestReport) -> str:
        """创建HTML报告模板."""
        duration = (
            (report.end_time - report.start_time).total_seconds()
            if report.end_time
            else 0
        )

        success_count = sum(
            1 for test in report.test_results if test.get("success", False)
        )
        total_tests = len(report.test_results)
        success_rate = (success_count / total_tests * 100) if total_tests > 0 else 0

        html = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MCP测试报告 - {report.session_id}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .header {{ background: #2563eb; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
        .status-success {{ color: #16a34a; font-weight: bold; }}
        .status-failed {{ color: #dc2626; font-weight: bold; }}
        .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }}
        .metric {{ background: #f8fafc; padding: 15px; border-radius: 6px; border-left: 4px solid #3b82f6; }}
        .test-results {{ margin-top: 20px; }}
        .test-item {{ background: #f9fafb; margin: 10px 0; padding: 15px; border-radius: 6px; border-left: 4px solid #10b981; }}
        .test-failed {{ border-left-color: #ef4444; }}
        .timestamp {{ color: #6b7280; font-size: 0.9em; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>MCP工具测试报告</h1>
            <p>会话ID: {report.session_id}</p>
            <p class="timestamp">生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>

        <h2>基本信息</h2>
        <div class="metrics">
            <div class="metric">
                <strong>测试URL</strong><br>
                <code>{report.url}</code>
            </div>
            <div class="metric">
                <strong>工具名称</strong><br>
                {report.tool_info.name if report.tool_info else '未知'}
            </div>
            <div class="metric">
                <strong>包名</strong><br>
                <code>{report.tool_info.package_name if report.tool_info else '未知'}</code>
            </div>
            <div class="metric">
                <strong>测试时长</strong><br>
                {duration:.2f} 秒
            </div>
        </div>

        <h2>测试状态</h2>
        <div class="metrics">
            <div class="metric">
                <strong>部署状态</strong><br>
                <span class="{'status-success' if report.deployment_success else 'status-failed'}">
                    {'✅ 成功' if report.deployment_success else '❌ 失败'}
                </span>
            </div>
            <div class="metric">
                <strong>通信状态</strong><br>
                <span class="{'status-success' if report.communication_success else 'status-failed'}">
                    {'✅ 正常' if report.communication_success else '❌ 异常'}
                </span>
            </div>
            <div class="metric">
                <strong>可用工具数</strong><br>
                {report.available_tools_count} 个
            </div>
            <div class="metric">
                <strong>测试成功率</strong><br>
                {success_count}/{total_tests} ({success_rate:.1f}%)
            </div>
        </div>

        <h2>性能指标</h2>
        <div class="metrics">
            <div class="metric">
                <strong>部署时间</strong><br>
                {report.deployment_time:.2f} 秒
            </div>
            <div class="metric">
                <strong>平均响应时间</strong><br>
                {report.performance_metrics.get('avg_response_time', -1):.3f} 秒
            </div>
            <div class="metric">
                <strong>启动时间</strong><br>
                {report.performance_metrics.get('startup_time', -1):.2f} 秒
            </div>
        </div>

        <h2>测试结果详情</h2>
        <div class="test-results">
"""

        for test in report.test_results:
            success_class = "" if test.get("success", False) else "test-failed"
            status_icon = "✅" if test.get("success", False) else "❌"

            html += """
            <div class="test-item {success_class}">
                <strong>{status_icon} {test.get('name', '未命名测试')}</strong><br>
                <span class="timestamp">响应时间: {test.get('response_time', 0):.3f}s</span>
                {f"<br><span style='color: #dc2626;'>错误: {test.get('error', '')}</span>" if test.get('error') else ""}
            </div>
"""

        if report.error_messages:
            html += """
        <h2>错误信息</h2>
        <div style="background: #fef2f2; padding: 15px; border-radius: 6px; border-left: 4px solid #ef4444;">
"""
            for error in report.error_messages:
                html += f"<p style='color: #dc2626;'>❌ {error}</p>"

            html += "</div>"

        html += """
        </div>
    </div>
</body>
</html>
"""
        return html

    def _print_console_summary(self, report: TestReport) -> None:
        """打印控制台摘要."""
        if not self.console:
            return

        try:
            duration = (
                (report.end_time - report.start_time).total_seconds()
                if report.end_time
                else 0
            )
            success_count = sum(
                1 for test in report.test_results if test.get("success", False)
            )
            total_tests = len(report.test_results)
            success_rate = (success_count / total_tests * 100) if total_tests > 0 else 0

            # 创建摘要面板
            summary_text = f"""
🎯 URL: {report.url}
📦 工具: {report.tool_info.name if report.tool_info else '未知'}
⏱️ 耗时: {duration:.2f}秒
🚀 部署: {'✅ 成功' if report.deployment_success else '❌ 失败'}
📡 通信: {'✅ 正常' if report.communication_success else '❌ 异常'}
🛠️ 工具数: {report.available_tools_count}
🧪 测试: {success_count}/{total_tests} 通过 ({success_rate:.1f}%)
"""

            panel = Panel(
                summary_text.strip(),
                title=f"📊 测试摘要 [{report.session_id}]",
                border_style=(
                    "green"
                    if report.deployment_success and report.communication_success
                    else "red"
                ),
            )

            self.console.print(panel)

        except Exception as e:
            rprint(f"[yellow]⚠️ 控制台摘要生成失败: {e}[/yellow]")
