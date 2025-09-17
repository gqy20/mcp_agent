#!/usr/bin/env python3
"""
CLI 命令处理器重构 - 模块化版本

将长函数拆分为更小的、可测试的模块
"""

import os
from datetime import datetime

from rich import print as rprint
from supabase import create_client

from src.core.evaluator import evaluate_full_repository_with_comprehensive_score
from src.core.report_generator import generate_test_report
from src.core.tester import TestConfig, get_mcp_tester
from src.utils.csv_parser import MCPToolInfo, get_mcp_parser


class SupabaseClientManager:
    """Supabase客户端管理器"""

    @staticmethod
    def create_client_if_configured() -> Optional[Any]:
        """如果配置了环境变量，则创建Supabase客户端"""
        try:
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
            if supabase_url and supabase_key:
                return create_client(supabase_url, supabase_key)
        except Exception:
            pass
        return None

    @staticmethod
    def export_evaluation_to_database(
        github_url: str, evaluation_result: Dict[str, Any]
    ) -> bool:
        """导出评估结果到数据库"""
        try:
            supabase_client = SupabaseClientManager.create_client_if_configured()
            if not supabase_client:
                return False

            # 准备评估数据
            evaluation_data = {
                "evaluation_timestamp": datetime.now(),
                "github_url": github_url,
                "final_score": evaluation_result["final_score"],
                "sustainability_score": evaluation_result["sustainability_score"],
                "popularity_score": evaluation_result["popularity_score"],
                "sustainability_details": evaluation_result["sustainability_details"],
                "popularity_details": evaluation_result["popularity_details"],
            }

            # 更新数据库
            result = (
                supabase_client.table("mcp_test_results")
                .update(evaluation_data)
                .eq("github_url", github_url)
                .execute()
            )

            return len(result.data) > 0

        except Exception as e:
            rprint(f"[yellow]⚠️ 数据库导出失败: {e}[/yellow]")
            return False


class ToolEvaluator:
    """工具评估器 - 负责单个工具的评估"""

    @staticmethod
    def evaluate_single_tool(
        tool: MCPToolInfo, supabase_client: Optional[Any]
    ) -> Dict[str, Any]:
        """评估单个工具"""
        if not tool.github_url:
            return {"status": "skipped", "message": "没有GitHub URL"}

        try:
            rprint(f"[blue]🔍 正在评估: {tool.name}[/blue]")
            evaluation_result = evaluate_full_repository_with_comprehensive_score(
                tool.github_url, supabase_client
            )

            if evaluation_result["status"] == "success":
                final_score = evaluation_result["final_score"]
                comprehensive_score = evaluation_result.get(
                    "final_comprehensive_score", final_score
                )
                rprint(
                    f"[green]✅ 评估完成: {tool.name} - "
                    f"GitHub评分: {final_score}/100, "
                    f"综合评分: {comprehensive_score}/100[/green]"
                )
                return evaluation_result
            else:
                rprint(
                    f"[red]❌ 评估失败: {tool.name} - {evaluation_result['message']}[/red]"
                )
                return evaluation_result

        except Exception as e:
            error_result = {"status": "error", "message": f"评估异常: {str(e)}"}
            rprint(f"[red]❌ 评估异常: {tool.name} - {e}[/red]")
            return error_result


class EvaluationResultProcessor:
    """评估结果处理器"""

    @staticmethod
    def process_evaluation_result(
        tool: MCPToolInfo, result: Dict[str, Any], supabase_client: Optional[Any]
    ) -> bool:
        """处理评估结果并导出到数据库"""
        if result["status"] == "success":
            if supabase_client:
                return SupabaseClientManager.export_evaluation_to_database(
                    tool.github_url, result
                )
            return True
        return False


class CLIToolEvaluator:
    """CLI工具评估器 - 主评估逻辑"""

    @staticmethod
    def get_tools_for_evaluation() -> List[MCPToolInfo]:
        """获取需要评估的工具列表"""
        try:
            parser = get_mcp_parser()
            tools = parser.get_all_tools()
            if not tools:
                rprint("[red]❌ 没有找到可评估的工具。[/red]")
                return []
            return [tool for tool in tools if tool.github_url]
        except Exception as e:
            rprint(f"[red]❌ 获取工具列表失败: {e}[/red]")
            return []

    @staticmethod
    def evaluate_all_tools(db_export: bool = False) -> Dict[str, Any]:
        """评估所有工具 - 主入口函数"""
        try:
            # 获取工具列表
            tools = CLIToolEvaluator.get_tools_for_evaluation()
            if not tools:
                return {"status": "error", "message": "没有找到可评估的工具"}

            # 创建Supabase客户端
            supabase_client = SupabaseClientManager.create_client_if_configured()

            # 评估统计
            stats = {"total": len(tools), "successful": 0, "failed": 0, "skipped": 0}

            # 评估每个工具
            for tool in tools:
                result = ToolEvaluator.evaluate_single_tool(tool, supabase_client)

                # 处理结果
                if result["status"] == "success":
                    stats["successful"] += 1
                    EvaluationResultProcessor.process_evaluation_result(
                        tool, result, supabase_client
                    )
                elif result["status"] == "skipped":
                    stats["skipped"] += 1
                else:
                    stats["failed"] += 1

            # 输出统计结果
            rprint(f"[green]📊 评估完成: {stats['successful']}/{stats['total']} 成功[/green]")
            return {"status": "success", "stats": stats}

        except Exception as e:
            rprint(f"[red]❌ 评估过程发生错误: {e}[/red]")
            return {"status": "error", "message": str(e)}
