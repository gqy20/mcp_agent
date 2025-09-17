#!/usr/bin/env python3
"""
测试精简输出功能
"""

import sys
import json
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.report_generator import TestResult, MCPTestReport
from datetime import datetime
from src.utils.csv_parser import MCPToolInfo

def create_sample_test_results():
    """创建示例测试结果"""
    # 模拟工具信息
    tool_info = MCPToolInfo(
        name="Context7 MCP - 最新代码文档适用于任何提示",
        author="upstash",
        package_name="@upstash/context7-mcp",
        category="Documentation",
        description="用于Context7的MCP服务器，提供最新、版本特定的库文档和代码示例，直接嵌入您的提示中。需要Node.js >= v18.0.0运行环境。",
        url="https://lobehub.com/mcp/upstash-context7",
        github_url="https://github.com/upstash/context7",
        deployment_method="npx",
    )
    
    # 模拟测试结果
    test_results = [
        TestResult(
            test_name="基础库名解析测试 - React",
            success=True,
            duration=1.626,
            tool_name="resolve-library-id",
            parameters={"libraryName": "react"},
            actual_response={
                "success": True,
                "result": {
                    "content": [{
                        "type": "text",
                        "text": "Available Libraries (top matches):\n\n- Title: React\n- Context7-compatible library ID: /websites/react_dev\n- Description: React is a JavaScript library for building user interfaces...\n- Code Snippets: 1752\n- Trust Score: 8\n----------\n- Title: React-admin\n- Context7-compatible library ID: /marmelab/react-admin\n- Description: A frontend Framework for building single-page applications..."
                    }]
                }
            },
            ai_analysis="AI分析建议通过测试",
            ai_confidence=0.95,
            test_category="基础功能"
        ),
        TestResult(
            test_name="库文档获取测试 - Next.js",
            success=True,
            duration=1.01,
            tool_name="get-library-docs",
            parameters={"context7CompatibleLibraryID": "/vercel/next.js", "tokens": 2000},
            actual_response={
                "success": True,
                "result": {
                    "content": [{
                        "type": "text",
                        "text": "================\nCODE SNIPPETS\n================\nTITLE: Install Umbraco Headless Blog Sample Data\nDESCRIPTION: Command to install the `Umbraco.Sample.Headless.Blog` NuGet package..."
                    }]
                }
            },
            ai_analysis="AI分析建议通过测试",
            ai_confidence=0.95,
            test_category="基础功能"
        )
    ]
    
    # 创建测试报告
    report = MCPTestReport(
        tool_name="Context7 MCP",
        test_url="https://lobehub.com/mcp/upstash-context7",
        test_time=datetime.now(),
        deployment_success=True,
        communication_success=True,
        available_tools_count=2,
        test_duration_seconds=40.9,
        tool_info=tool_info,
        test_results=test_results,
        error_messages=[],
        evaluation_result={
            "status": "success",
            "final_comprehensive_score": 91,
            "test_success_rate": {"success_rate": 88.0}
        }
    )
    
    return report

def test_concise_output():
    """测试精简输出功能"""
    print("🧪 测试精简输出功能...")
    
    # 创建示例报告
    report = create_sample_test_results()
    
    # 测试精简转换
    print("\n1. 测试 TestResult.to_concise_dict():")
    for result in report.test_results:
        concise = result.to_concise_dict()
        print(json.dumps(concise, indent=2, ensure_ascii=False))
        print("---")
    
    print("\n2. 测试 MCPTestReport.to_concise_dict():")
    concise_report = report.to_concise_dict()
    print(json.dumps(concise_report, indent=2, ensure_ascii=False))
    
    print("\n3. 测试 print_concise_summary():")
    from src.core.report_generator import MCPReportGenerator
    generator = MCPReportGenerator()
    generator.print_concise_summary(report)
    
    print("\n✅ 精简输出功能测试完成！")

if __name__ == "__main__":
    test_concise_output()