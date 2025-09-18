#!/usr/bin/env python3
"""
MCP GitHub分析器功能测试脚本

测试内容：
1. GitHub分析器的基本功能
2. CSV解析器的GitHub集成
3. MCP表格更新器的功能
4. 完整的端到端流程
"""

import json
import sys
from pathlib import Path

# 添加项目路径到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from src.core.github_mcp_analyzer import GitHubMCPAnalyzer
from src.core.mcp_table_updater import MCPTableUpdater
from src.utils.csv_parser import MCPDataParser


def test_github_analyzer():
    """测试GitHub分析器"""
    print("=" * 60)
    print("测试1: GitHub分析器基本功能")
    print("=" * 60)

    analyzer = GitHubMCPAnalyzer()

    # 测试URLs
    test_urls = [
        "https://github.com/gqy20/article-mcp",  # uvx部署
        "https://github.com/microsoft/playwright-mcp",  # npx部署
        "https://github.com/ahujasid/blender-mcp",  # cargo部署
    ]

    results = []

    for url in test_urls:
        print(f"\n🔍 测试URL: {url}")
        try:
            result = analyzer.analyze_github_repo(url)

            if result and result.get("success"):
                record = result["record"]
                print(f"  ✅ 成功分析: {record.get('name', 'Unknown')}")
                print(f"  📦 包名: {record.get('package_name', '未提取')}")
                print(f"  🚀 部署方法: {record.get('deployment_method', '未提取')}")
                print(f"  ⬇️  安装命令: {record.get('install_command', '未提取')}")
                print(f"  ▶️  运行命令: {record.get('run_command', '未提取')}")
                print(f"  ⭐ 星标数: {record.get('star_count', 0)}")
                print(f"  🍴 分叉数: {record.get('fork_count', 0)}")
                results.append(True)
            else:
                error_msg = result.get("error", "未知错误") if result else "分析返回空结果"
                print(f"  ❌ 分析失败: {error_msg}")
                results.append(False)

        except Exception as e:
            print(f"  ❌ 异常: {e}")
            results.append(False)

    success_rate = sum(results) / len(results) * 100
    print(f"\n📊 GitHub分析器成功率: {success_rate:.1f}% ({sum(results)}/{len(results)})")

    return success_rate >= 66.7  # 至少2/3成功


def test_csv_parser():
    """测试CSV解析器的GitHub集成"""
    print("\n" + "=" * 60)
    print("测试2: CSV解析器GitHub集成")
    print("=" * 60)

    parser = MCPDataParser("data/mcp.csv")

    # 测试URL
    test_url = "https://github.com/gqy20/article-mcp"

    print(f"\n🔍 测试URL: {test_url}")

    # 1. 测试CSV中查找
    tool = parser.find_tool_by_url(test_url)
    if tool:
        print("  ✅ 从CSV中找到工具")
        print(f"  📦 包名: {tool.package_name or '未提取'}")
        print(f"  🚀 部署方法: {tool.deployment_method}")
        print(f"  ⬇️  安装命令: {tool.install_command or '未提取'}")
        print(f"  ▶️  运行命令: {tool.run_command or '未提取'}")
    else:
        print("  ⚠️  CSV中未找到工具")

    # 2. 测试GitHub fallback
    print("\n  🔄 测试GitHub Fallback...")
    github_tool = parser._fetch_from_github(test_url)
    if github_tool:
        print("  ✅ GitHub Fallback成功")
        print(f"  📦 包名: {github_tool.package_name}")
        print(f"  🚀 部署方法: {github_tool.deployment_method}")
        print(f"  ⬇️  安装命令: {github_tool.install_command}")
        print(f"  ▶️  运行命令: {github_tool.run_command}")
        return True
    else:
        print("  ❌ GitHub Fallback失败")
        return False


def test_mcp_table_updater():
    """测试MCP表格更新器"""
    print("\n" + "=" * 60)
    print("测试3: MCP表格更新器")
    print("=" * 60)

    updater = MCPTableUpdater()

    # 测试URL
    test_url = "https://github.com/gqy20/article-mcp"

    print(f"\n🔍 测试URL: {test_url}")

    # 检查现有记录
    existing_record = updater.get_existing_record(test_url)
    if existing_record:
        print("  📋 找到现有记录")
        print(f"  📦 包名: {existing_record.get('package_name', '未提取')}")
        print(f"  🚀 部署方法: {existing_record.get('deployment_method', '未提取')}")
        print(f"  ⬇️  安装命令: {existing_record.get('install_command', '未提取')}")
        print(f"  ▶️  运行命令: {existing_record.get('run_command', '未提取')}")
        print(f"  🔍 需要更新: {updater._needs_update(existing_record)}")

    # 测试更新
    print("\n  🔄 测试更新功能...")
    result = updater.analyze_github_project(test_url)

    if result and result.get("success"):
        print("  ✅ 更新成功!")
        record = result.get("record", {})
        print(f"  📦 包名: {record.get('package_name', '未提取')}")
        print(f"  🚀 部署方法: {record.get('deployment_method', '未提取')}")
        print(f"  ⬇️  安装命令: {record.get('install_command', '未提取')}")
        print(f"  ▶️  运行命令: {record.get('run_command', '未提取')}")
        return True
    else:
        error_msg = result.get("error", "未知错误") if result else "更新返回空结果"
        print(f"  ❌ 更新失败: {error_msg}")
        return False


def test_end_to_end():
    """测试完整的端到端流程"""
    print("\n" + "=" * 60)
    print("测试4: 端到端流程")
    print("=" * 60)

    test_url = "https://github.com/gqy20/article-mcp"

    print(f"\n🔄 测试完整流程: {test_url}")

    # 1. 使用CSV解析器查找
    parser = MCPDataParser("data/mcp.csv")
    tool = parser.find_tool_by_url(test_url)

    if tool:
        print("  ✅ 步骤1: CSV查找成功")
        print(f"  📦 当前包名: {tool.package_name or '未提取'}")

        # 检查是否有完整的部署信息
        if tool.package_name and tool.install_command and tool.run_command:
            print("  ✅ 步骤2: 部署信息完整")
            print("  ✅ 端到端流程成功!")
            return True
        else:
            print("  ⚠️  步骤2: 部署信息不完整")

            # 2. 使用MCP表格更新器更新
            updater = MCPTableUpdater()
            result = updater.analyze_github_project(test_url)

            if result and result.get("success"):
                print("  ✅ 步骤3: 表格更新成功")

                # 3. 再次使用CSV解析器查找
                updated_tool = parser.find_tool_by_url(test_url)
                if updated_tool and updated_tool.package_name:
                    print("  ✅ 步骤4: 更新后查找成功")
                    print(f"  📦 更新后包名: {updated_tool.package_name}")
                    print("  ✅ 端到端流程成功!")
                    return True
                else:
                    print("  ❌ 步骤4: 更新后查找失败")
                    return False
            else:
                print("  ❌ 步骤3: 表格更新失败")
                return False
    else:
        print("  ❌ 步骤1: CSV查找失败")
        return False


def main():
    """主测试函数"""
    print("🧪 MCP GitHub分析器功能测试")
    print("=" * 60)

    test_results = []

    # 运行所有测试
    test_results.append(("GitHub分析器", test_github_analyzer()))
    test_results.append(("CSV解析器GitHub集成", test_csv_parser()))
    test_results.append(("MCP表格更新器", test_mcp_table_updater()))
    test_results.append(("端到端流程", test_end_to_end()))

    # 输出测试结果摘要
    print("\n" + "=" * 60)
    print("📊 测试结果摘要")
    print("=" * 60)

    passed = 0
    total = len(test_results)

    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name:.<30} {status}")
        if result:
            passed += 1

    print(f"\n总计: {passed}/{total} 测试通过")
    print(f"成功率: {passed/total*100:.1f}%")

    if passed == total:
        print("\n🎉 所有测试通过! 功能正常工作。")
        return 0
    else:
        print(f"\n⚠️  有 {total-passed} 个测试失败，需要修复。")
        return 1


if __name__ == "__main__":
    exit(main())
