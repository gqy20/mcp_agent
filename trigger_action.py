#!/usr/bin/env python3
"""手动触发GitHub Action的脚本"""

import subprocess
import json
import sys

def trigger_workflow():
    """触发GitHub Action工作流"""

    # 测试用例列表
    test_cases = [
        {
            "name": "HTTP MCP端点智能检测",
            "input": "http://ai.sitianai.com/api/proxy/mcp?api_key=d4v8kgl26lc8ggculk9g",
            "type_hint": "auto-detect"
        },
        {
            "name": "GitHub URL智能检测",
            "input": "https://github.com/upstash/context7",
            "type_hint": "auto-detect"
        },
        {
            "name": "包名格式测试",
            "input": "@upstash/context7-mcp",
            "type_hint": "package_name"
        },
        {
            "name": "搜索查询测试",
            "input": "context7 documentation",
            "type_hint": "search_query"
        }
    ]

    print("🚀 准备触发GitHub Action工作流测试...")
    print("=" * 60)

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 测试用例 {i}: {test_case['name']}")
        print(f"   输入: {test_case['input']}")
        print(f"   类型提示: {test_case['type_hint']}")

        # 构建gh命令
        cmd = [
            'gh', 'workflow', 'run', '183636118',
            '--field', f'mcp_input={test_case["input"]}',
            '--field', f'input_type_hint={test_case["type_hint"]}'
        ]

        try:
            print(f"   🔧 执行命令: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                print(f"   ✅ 触发成功")
                if result.stdout.strip():
                    print(f"   📤 输出: {result.stdout.strip()}")
            else:
                print(f"   ❌ 触发失败")
                print(f"   📤 错误: {result.stderr.strip()}")

        except subprocess.TimeoutExpired:
            print(f"   ⏰ 超时")
        except Exception as e:
            print(f"   💥 异常: {e}")

    print("\n" + "=" * 60)
    print("🎯 请在GitHub Actions页面查看执行结果:")
    print("   https://github.com/gqy20/mcp_agent/actions")

if __name__ == "__main__":
    trigger_workflow()