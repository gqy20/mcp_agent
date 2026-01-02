"""HTTP MCP CLI 处理模块.

此模块包含 HTTP MCP 端点的 CLI 命令处理逻辑。
"""

import traceback
from typing import Any

from rich import print as rprint

from src.batch_mcp.core.evaluator import evaluate_http_mcp_endpoint
from src.batch_mcp.core.http_mcp_client import HttpMCPClient
from src.batch_mcp.core.report_generator import TestResult, generate_test_report
from src.batch_mcp.core.tester import TestConfig


class HTTPCLIHandler:
    """HTTP MCP CLI 命令处理器."""

    def __init__(self, http_handler, exporter, input_detector, tool_finder) -> None:
        self._http_handler = http_handler
        self._exporter = exporter
        self._input_detector = input_detector
        self._tool_finder = tool_finder

    async def run_http_tests_direct(
        self,
        tool_info: Any,
        http_config: dict[str, Any],
        config: TestConfig,
    ) -> bool:
        """运行 HTTP MCP 测试的专用方法 - 委托给 HTTPMCPHandler."""
        try:
            # 创建 HTTP MCP 客户端
            client = HttpMCPClient(
                url=http_config["url"],
                headers=http_config["headers"],
                timeout=http_config["timeout"],
            )

            # 创建 server_info 对象来包装 client
            server_info = type("ServerInfo", (), {"client": client})()

            # 运行基础测试
            success, test_results = await self._http_handler._run_http_tests(
                tool_info, server_info, config
            )

            # 获取工具列表 - 用于智能测试和评估
            tools_result = await client.list_tools()
            tools_list = tools_result.get("tools", [])
            tools_count = len(tools_list)

            # 如果启用智能测试，运行 AI 测试
            if config.smart_test and success:
                rprint("[blue]🤖 开始 AI 智能测试...[/blue]")

                smart_results = await self._http_handler.run_http_smart_tests(
                    client, tools_list, config
                )

                # 将智能测试结果转换为 TestResult 对象并添加到 basic_tests 中
                for smart_result in smart_results:
                    # 确保 smart_result 是字典类型，防止意外类型混入
                    if not isinstance(smart_result, dict):
                        rprint(
                            f"[yellow]⚠️ 跳过无效的智能测试结果: {type(smart_result)}[/yellow]"
                        )
                        continue

                    smart_test_result = TestResult(
                        test_name=f"AI智能测试: {smart_result.get('tool_name', 'unknown')}",
                        success=smart_result.get("success", False),
                        duration=0.0,  # 智能测试暂不计算耗时
                        test_category="AI智能测试",
                        parameters={"smart_test": True},
                        tool_name=smart_result.get("tool_name"),
                        actual_response=smart_result.get("result"),
                        error_message=smart_result.get("error"),
                        ai_analysis=f"AI智能测试 {smart_result.get('tool_name', 'unknown')} {'成功' if smart_result.get('success') else '失败'}",
                        ai_confidence=0.8 if smart_result.get("success") else 0.2,
                    )
                    # 将智能测试结果添加到 basic_tests 中
                    test_results["basic_tests"].append(smart_test_result)

                # 计算智能测试成功率
                if smart_results:
                    smart_success = all(
                        result.get("success", False) for result in smart_results
                    )
                    success = success and smart_success
                else:
                    smart_success = False

            # 评估和报告生成逻辑保持不变
            evaluation_result = None
            if config.evaluate:
                rprint("[blue]🔍 正在评估HTTP MCP端点...[/blue]")

                # 计算平均响应时间
                basic_tests = test_results.get("basic_tests", [])
                total_duration = sum(
                    getattr(test, "duration", 0) for test in basic_tests
                )
                avg_response_time = (
                    total_duration / len(basic_tests) if basic_tests else 0
                )

                # 将 TestResult 对象转换为字典用于评估
                evaluation_test_results = {
                    "deployment_success": True,
                    "communication_success": success,
                    "test_results": [
                        {
                            "test_name": getattr(test, "test_name", ""),
                            "success": getattr(test, "success", False),
                            "duration": getattr(test, "duration", 0),
                            "test_category": getattr(test, "test_category", ""),
                            "ai_confidence": self._safe_ai_confidence(
                                getattr(test, "ai_confidence", 0.0)
                            ),
                        }
                        for test in basic_tests
                    ],
                }

                # 调用 HTTP MCP 评估
                evaluation_result = evaluate_http_mcp_endpoint(
                    test_results=evaluation_test_results,
                    tools_count=tools_count,
                    response_time=avg_response_time,
                    tool_info=tool_info.__dict__ if tool_info else None,
                )

                # 显示评估结果
                self._display_http_evaluation_result(evaluation_result)

            # 生成报告
            report_files = {}
            if config.save_report:
                # 直接传递 TestResult 对象列表，保持数据格式统一
                basic_tests_list = test_results.get("basic_tests", [])

                report_files = generate_test_report(
                    url=http_config["url"],
                    tool_info=tool_info,
                    server_info=client,
                    test_success=success,
                    duration=0.0,  # 这里可以计算实际持续时间
                    test_results=basic_tests_list,
                    evaluation_result=evaluation_result,
                )

            # 数据库导出
            if config.db_export and success:
                json_report = report_files.get("json")
                if json_report:
                    self._exporter.export_to_database(
                        json_report,
                        evaluation_result=evaluation_result,
                    )

            return success

        except Exception:
            rprint("[red]❌ HTTP 测试执行失败[/red]")
            if config.verbose:
                rprint(f"[red]{traceback.format_exc()}[/red]")
            return False

    def _safe_ai_confidence(self, confidence: Any) -> float:
        """安全处理ai_confidence值，确保返回数值类型."""
        if isinstance(confidence, (int, float)):
            return float(confidence)
        if isinstance(confidence, list):
            # 如果是列表，计算平均值
            numeric_values = [c for c in confidence if isinstance(c, (int, float))]
            if numeric_values:
                return sum(numeric_values) / len(numeric_values)
            return 0.0
        if confidence is None:
            return 0.0
        # 其他类型转换为0.0
        return 0.0

    def _display_http_evaluation_result(self, evaluation_result: dict) -> None:
        """显示 HTTP 评估结果."""
        if evaluation_result.get("status") == "success":
            rprint(
                f"[green]✅ HTTP MCP 评估完成 - "
                f"评分: {evaluation_result.get('final_score', 0)}/100[/green]",
            )
        else:
            rprint("[yellow]⚠️ HTTP MCP 评估失败[/yellow]")
