#!/usr/bin/env python3
"""MCP 测试报告生成器 (简洁版).

作者: AI Assistant (Linus重构版)
日期: 2025-08-18
版本: 0.1.0 (简洁版)

"""

import json
import platform
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

# 导入工具信息类型
try:
    from src.batch_mcp.utils.csv_parser import MCPToolInfo
except ImportError:

    @dataclass
    class MCPToolInfo:
        name: str
        author: str
        package_name: str
        category: str
        description: str
        requires_api_key: bool = False
        api_requirements: list[str] = None


@dataclass
class TestResult:
    """单个测试结果 - 增强版，包含详细响应和分析."""

    test_name: str
    success: bool
    duration: float
    error_message: str | None = None

    # 新增：详细测试信息
    tool_name: str | None = None
    parameters: dict | None = None
    actual_response: dict | None = None
    ai_analysis: str | None = None
    ai_confidence: float | None = None
    test_category: str | None = (
        None  # "基础功能", "实际使用场景", "容错能力", "边界情况"
    )

    def to_concise_dict(self) -> dict:
        """转换为精简格式 - 保留关键信息."""
        result = {
            "test_name": self.test_name,
            "success": self.success,
            "duration": round(self.duration, 2),
            "tool_name": self.tool_name,
            "test_category": self.test_category or "未知",
        }

        # 添加响应摘要
        if self.actual_response and self.actual_response.get("success"):
            content = self.actual_response.get("result", {}).get("content", [])
            if content and isinstance(content, list) and len(content) > 0:
                text_content = content[0].get("text", "")
                # 截取前100个字符作为摘要
                result["response_summary"] = (
                    text_content[:100] + "..."
                    if len(text_content) > 100
                    else text_content
                )
            else:
                result["response_summary"] = "响应成功但无内容"
        elif self.actual_response:
            result["response_summary"] = "响应失败"
        else:
            result["response_summary"] = "无响应"

        # 添加错误信息
        if self.error_message:
            result["error_summary"] = (
                self.error_message[:100] + "..."
                if len(self.error_message) > 100
                else self.error_message
            )

        return result


@dataclass
class MCPTestReport:
    """MCP测试报告 - 简洁版数据结构."""

    # 核心信息
    tool_name: str
    test_url: str
    test_time: datetime

    # 测试状态 (布尔值，无特殊情况)
    deployment_success: bool
    communication_success: bool

    # 统计数据
    available_tools_count: int
    test_duration_seconds: float

    # 详细信息
    tool_info: MCPToolInfo
    test_results: list[TestResult]
    error_messages: list[str]
    evaluation_result: dict | None = None

    # 环境信息
    platform_info: str = platform.system()
    process_pid: int | None = None

    def to_concise_dict(self) -> dict:
        """转换为精简格式 - 适合控制台输出."""
        passed = sum(1 for t in self.test_results if t.success)
        total = len(self.test_results)
        success_rate = (passed / total * 100) if total > 0 else 0

        # 精简工具信息
        concise_tool_info = None
        if self.tool_info:
            concise_tool_info = {
                "name": self.tool_info.name,
                "author": self.tool_info.author,
                "category": self.tool_info.category,
                "description": (
                    self.tool_info.description[:100] + "..."
                    if len(self.tool_info.description) > 100
                    else self.tool_info.description
                ),
                # 添加LobeHub评分信息
                "lobehub_url": getattr(self.tool_info, "lobehub_url", None),
                "lobehub_evaluate": getattr(self.tool_info, "lobehub_evaluate", None),
                "lobehub_score": getattr(self.tool_info, "lobehub_score", None),
                "lobehub_star_count": getattr(
                    self.tool_info,
                    "lobehub_star_count",
                    None,
                ),
                "lobehub_fork_count": getattr(
                    self.tool_info,
                    "lobehub_fork_count",
                    None,
                ),
            }

        # 精简评估结果
        concise_evaluation = None
        if self.evaluation_result:
            concise_evaluation = {
                "final_score": self.evaluation_result.get(
                    "final_comprehensive_score",
                    0,
                ),
                "test_success_rate": self.evaluation_result.get(
                    "test_success_rate",
                    {},
                ).get("success_rate", 0),
                "status": self.evaluation_result.get("status", "unknown"),
            }

        return {
            "tool_name": self.tool_name,
            "test_url": self.test_url,
            "test_time": self.test_time.strftime("%Y-%m-%d %H:%M:%S"),
            "test_duration_seconds": round(self.test_duration_seconds, 1),
            "deployment_success": self.deployment_success,
            "communication_success": self.communication_success,
            "available_tools_count": self.available_tools_count,
            "tool_info": concise_tool_info,
            "test_results": [result.to_concise_dict() for result in self.test_results],
            "summary": {
                "total_tests": total,
                "passed_tests": passed,
                "success_rate": f"{success_rate:.1f}%",
                "final_score": (
                    concise_evaluation["final_score"] if concise_evaluation else 0
                ),
            },
            "evaluation": concise_evaluation,
        }


class MCPReportGenerator:
    """简洁的MCP报告生成器 - Linus重构版."""

    def __init__(self, output_dir: str = "data/test_results") -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def create_report(
        self,
        url: str,
        tool_info: MCPToolInfo,
        server_info,
        test_success: bool,
        duration: float,
        test_results: list[TestResult] | None = None,
        error_messages: list[str] | None = None,
        evaluation_result: dict | None = None,
    ) -> MCPTestReport:
        """创建报告对象 - 单一职责."""
        # 处理tool_info为None的情况（用于package测试）
        tool_name = tool_info.name if tool_info else url

        return MCPTestReport(
            tool_name=tool_name,
            test_url=url,
            test_time=datetime.now(),
            deployment_success=server_info is not None,
            communication_success=test_success,
            available_tools_count=(
                len(server_info.available_tools) if server_info else 0
            ),
            test_duration_seconds=duration,
            tool_info=tool_info,
            test_results=test_results or [],
            error_messages=error_messages or [],
            evaluation_result=evaluation_result,
            process_pid=server_info.process.pid if server_info else None,
        )

    def save_json(self, report: MCPTestReport) -> Path:
        """保存JSON报告 - 无条件分支."""
        timestamp = report.test_time.strftime("%Y%m%d_%H%M%S")
        json_path = self.output_dir / f"mcp_test_{timestamp}.json"

        # 直接序列化，无特殊情况处理
        report_dict = asdict(report)
        report_dict["test_time"] = report.test_time.isoformat()

        # 处理JSON序列化问题 - 转换NumPy类型
        report_dict = self._convert_numpy_types(report_dict)

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(report_dict, f, ensure_ascii=False, indent=2)

        return json_path

    def save_concise_json(self, report: MCPTestReport) -> Path:
        """保存精简版JSON报告 - 适合控制台输出和数据库存储."""
        timestamp = report.test_time.strftime("%Y%m%d_%H%M%S")
        concise_path = self.output_dir / f"mcp_test_{timestamp}_concise.json"

        # 生成精简格式
        concise_dict = report.to_concise_dict()

        with open(concise_path, "w", encoding="utf-8") as f:
            json.dump(concise_dict, f, ensure_ascii=False, indent=2)

        return concise_path

    def print_concise_summary(self, report: MCPTestReport) -> None:
        """打印精简摘要到控制台."""
        concise = report.to_concise_dict()

        if concise["evaluation"]:
            pass

        for _i, result in enumerate(concise["test_results"], 1):
            "✅" if result["success"] else "❌"
            if result.get("response_summary"):
                pass

    def _convert_numpy_types(self, obj):
        """递归转换NumPy类型和其他类型为Python原生类型."""
        if isinstance(obj, dict):
            return {key: self._convert_numpy_types(value) for key, value in obj.items()}
        if isinstance(obj, list):
            return [self._convert_numpy_types(item) for item in obj]
        if hasattr(obj, "item"):  # NumPy scalar
            return obj.item()
        if str(type(obj)).startswith("<class 'numpy."):  # NumPy types
            try:
                return obj.item() if hasattr(obj, "item") else obj.tolist()
            except Exception:
                return str(obj)
        else:
            return obj

    def save_html(self, report: MCPTestReport) -> Path:
        """保存HTML报告 - 最简模板."""
        timestamp = report.test_time.strftime("%Y%m%d_%H%M%S")
        html_path = self.output_dir / f"mcp_test_{timestamp}.html"

        # 计算统计数据
        passed = sum(1 for t in report.test_results if t.success)
        total = len(report.test_results)
        success_rate = (passed / total * 100) if total > 0 else 0

        # 生成HTML - 单一模板，无条件分支
        lobehub_section = ""
        if (
            report.tool_info
            and hasattr(report.tool_info, "lobehub_evaluate")
            and report.tool_info.lobehub_evaluate
        ):
            lobehub_section = (
                f"""
<h2>LobeHub 评分</h2>
<div class="stats">
<div class="stat"><div>质量等级</div><div>{report.tool_info.lobehub_evaluate}</div></div>
<div class="stat"><div>评分</div><div>{report.tool_info.lobehub_score or "N/A"}</div></div>
<div class="stat"><div>Stars</div><div>{report.tool_info.lobehub_star_count or 0}</div></div>
<div class="stat"><div>Forks</div><div>{report.tool_info.lobehub_fork_count or 0}</div></div>
</div>
<p>📱 <a href="{report.tool_info.lobehub_url}" target="_blank">LobeHub 页面</a></p>"""
                if report.tool_info.lobehub_url
                else f"""
<h2>LobeHub 评分</h2>
<div class="stats">
<div class="stat"><div>质量等级</div><div>{report.tool_info.lobehub_evaluate}</div></div>
<div class="stat"><div>评分</div><div>{report.tool_info.lobehub_score or "N/A"}</div></div>
<div class="stat"><div>Stars</div><div>{report.tool_info.lobehub_star_count or 0}</div></div>
<div class="stat"><div>Forks</div><div>{report.tool_info.lobehub_fork_count or 0}</div></div>
</div>"""
            )

        # Generate HTML with proper string formatting
        html_content = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>{report.tool_name} 测试报告</title>
<style>body{{font-family:sans-serif;margin:40px;}}
.header{{background:#667eea;color:white;padding:20px;border-radius:8px;}}
.stats{{display:flex;gap:20px;margin:20px 0;}}
.stat{{background:#f5f5f5;padding:15px;border-radius:8px;text-align:center;}}
.success{{color:#28a745;}} .failure{{color:#dc3545;}}
a{{color:#667eea;text-decoration:none;}} a:hover{{text-decoration:underline;}}
</style></head>
<body>
<div class="header">
<h1>🧪 {report.tool_name}</h1>
<p>{report.test_time.strftime("%Y-%m-%d %H:%M:%S")} | 耗时: {report.test_duration_seconds:.1f}秒</p>
</div>

<div class="stats">
<div class="stat"><div>部署</div><div class="{"success" if report.deployment_success else "failure"}">{"✅" if report.deployment_success else "❌"}</div></div>
<div class="stat"><div>通信</div><div class="{"success" if report.communication_success else "failure"}">{"✅" if report.communication_success else "❌"}</div></div>
<div class="stat"><div>工具数</div><div>{report.available_tools_count}</div></div>
<div class="stat"><div>成功率</div><div>{success_rate:.1f}%</div></div>
</div>

{lobehub_section}

<h2>测试结果</h2>
<table style="width:100%;border-collapse:collapse;">
<tr style="background:#f5f5f5;"><th>测试名</th><th>状态</th><th>耗时</th><th>错误</th></tr>"""

        # 生成测试结果表格 - 统一处理
        for test in report.test_results:
            html_content += f"""<tr>
<td>{test.test_name}</td>
<td class="{"success" if test.success else "failure"}">{"✅" if test.success else "❌"}</td>
<td>{test.duration:.2f}s</td>
<td>{test.error_message or "-"}</td>
</tr>"""

        html_content += "</table></body></html>"

        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        return html_path


# 全局实例和便捷函数
_generator = MCPReportGenerator()


def generate_test_report(
    url: str,
    tool_info,
    server_info,
    test_success: bool,
    duration: float,
    test_results: list | None = None,
    evaluation_result: dict | None = None,
    formats: list[str] | None = None,
) -> dict[str, str]:
    """便捷的报告生成函数 - 保持向后兼容."""
    formats = formats or ["json", "html"]

    # 创建报告
    report = _generator.create_report(
        url,
        tool_info,
        server_info,
        test_success,
        duration,
        test_results,
        evaluation_result=evaluation_result,
    )

    # 生成文件
    files = {}
    if "json" in formats:
        files["json"] = str(_generator.save_json(report))
        # 自动生成精简版本
        files["concise"] = str(_generator.save_concise_json(report))

        # 显示精简摘要
        _generator.print_concise_summary(report)

    if "html" in formats:
        files["html"] = str(_generator.save_html(report))

    return files
