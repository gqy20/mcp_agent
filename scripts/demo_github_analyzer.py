#!/usr/bin/env python3
"""
GitHub MCP分析器演示脚本

展示如何使用GitHub MCP项目自动分析功能
"""

import json
import os
from pathlib import Path


def main():
    print("=" * 60)
    print("GitHub MCP项目自动分析器演示")
    print("=" * 60)

    # 示例GitHub URLs（包含已知和未知的项目）
    demo_urls = [
        "https://github.com/microsoft/playwright-mcp",  # 已存在
        "https://github.com/upstash/context7",  # 已存在
        "https://github.com/nonexistent/mcp-project",  # 不存在
        "https://github.com/test/repo",  # 非MCP项目
    ]

    print("\n📋 演示URLs:")
    for i, url in enumerate(demo_urls, 1):
        print(f"   {i}. {url}")

    # 创建演示URL文件
    demo_file = "demo_urls.txt"
    with open(demo_file, "w") as f:
        for url in demo_urls:
            f.write(url + "\n")

    print(f"\n📄 创建演示URL文件: {demo_file}")

    # 执行分析
    print("\n🔍 开始分析GitHub项目...")
    os.system(
        f"python -m src.main analyze-github {demo_file} --output demo_report.json"
    )

    # 读取并展示结果
    if Path("demo_report.json").exists():
        with open("demo_report.json", "r") as f:
            report = json.load(f)

        print("\n📊 分析结果:")
        print(f"   总计处理: {report['total_urls']}")
        print(f"   已存在项目: {report['existing_repos']}")
        print(f"   新增项目: {report['new_repos']}")
        print(f"   MCP项目: {report['mcp_projects']}")
        print(f"   非MCP项目: {report['non_mcp_projects']}")

        if report["added_tools"]:
            print("\n✨ 新增MCP工具:")
            for tool in report["added_tools"]:
                print(
                    f"   • {tool['name']} by {tool['author']} ({tool['stars']} stars)"
                )
        else:
            print("\n💡 本次演示未发现新的MCP工具")

    # 清理临时文件
    cleanup_files = [demo_file, "demo_report.json"]
    for file in cleanup_files:
        if Path(file).exists():
            Path(file).unlink()
            print(f"\n🧹 清理临时文件: {file}")

    print("\n" + "=" * 60)
    print("演示完成！")
    print("=" * 60)
    print("\n📖 使用方法:")
    print("   python -m src.main analyze-github <URLs或文件路径>")
    print("   示例: python -m src.main analyze-github https://github.com/owner/repo")
    print("   示例: python -m src.main analyze-github urls.txt")


if __name__ == "__main__":
    main()
