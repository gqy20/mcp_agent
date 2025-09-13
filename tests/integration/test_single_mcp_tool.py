#!/usr/bin/env python3
"""
单个MCP工具快速测试脚本

用于快速验证单个MCP工具的功能
基于通用跨平台框架的轻量化版本

使用方法:
  python test_single_mcp_tool.py context7
  python test_single_mcp_tool.py youtube
  python test_single_mcp_tool.py think

作者: AI Assistant
日期: 2025-08-14
版本: 1.0.0
"""

import argparse
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 导入跨平台测试框架
try:
    from tests.tools.test_crossplatform_mcp import (
        MCP_TOOLS_CONFIG,
        test_single_mcp_tool,
    )
except ImportError as e:
    print(f"❌ 导入错误: {e}")
    print("请确保test_crossplatform_mcp.py存在且可用")
    sys.exit(1)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="单个MCP工具快速测试",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
可用的MCP工具:
  context7  - Context7库文档查询工具
  youtube   - YouTube视频信息获取工具
  think     - 最小化思考分析工具
  svelte    - Svelte框架文档工具
  openalex  - 学术文献检索工具
  12306     - 12306火车票查询工具

示例:
  python test_single_mcp_tool.py context7
  python test_single_mcp_tool.py youtube --verbose
        """,
    )

    parser.add_argument(
        "tool", choices=list(MCP_TOOLS_CONFIG.keys()), help="要测试的MCP工具名称"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="显示详细输出")

    args = parser.parse_args()

    if args.verbose:
        print(f"🎯 开始测试MCP工具: {args.tool}")
        print(f"📋 工具配置: {MCP_TOOLS_CONFIG[args.tool]['name']}")
        print(f"📦 包名: {MCP_TOOLS_CONFIG[args.tool]['package']}")
        print("-" * 50)

    # 执行测试
    try:
        success = test_single_mcp_tool(args.tool)

        if success:
            print(f"\n🎉 {args.tool} 测试成功！")
            sys.exit(0)
        else:
            print(f"\n❌ {args.tool} 测试失败！")
            sys.exit(1)

    except KeyboardInterrupt:
        print(f"\n⚠️ 用户中断测试")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 测试过程中发生异常: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
