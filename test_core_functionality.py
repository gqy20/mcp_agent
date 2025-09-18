#!/usr/bin/env python3
"""
简化的MCP GitHub分析器功能测试脚本

针对GitHub API限制，测试核心功能
"""

import json
import sys
from pathlib import Path

# 添加项目路径到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from src.core.github_mcp_analyzer import GitHubMCPAnalyzer
from src.utils.csv_parser import MCPDataParser


def test_github_analyzer_with_cache():
    """测试GitHub分析器（使用缓存数据）"""
    print("=" * 60)
    print("测试1: GitHub分析器核心逻辑")
    print("=" * 60)
    
    analyzer = GitHubMCPAnalyzer()
    
    # 模拟README内容进行测试
    test_readme_content = """
    # Article MCP
    
    A literature retrieval MCP server that provides search capabilities for academic articles.
    
    ## Installation
    
    Install using uvx:
    
    ```bash
    uvx article-mcp server
    ```
    
    Or install with pip:
    
    ```bash
    pip install article-mcp
    ```
    
    ## Usage
    
    Run the server:
    
    ```bash
    uvx article-mcp server
    ```
    
    This MCP tool provides the following capabilities:
    - Journal quality assessment
    - Reference retrieval
    - Article details extraction
    - Related literature search
    """
    
    # 测试包名提取逻辑
    deployment_methods = analyzer._extract_deployment_methods(test_readme_content)
    package_info = analyzer._extract_package_info(test_readme_content, deployment_methods)
    
    print(f"🔍 检测到的部署方法: {deployment_methods}")
    print(f"📦 提取的包名: {package_info['package_name']}")
    print(f"🚀 部署方法: {package_info['deployment_method']}")
    print(f"⬇️  安装命令: {package_info['install_command']}")
    print(f"▶️  运行命令: {package_info['run_command']}")
    
    # 验证结果
    expected_results = {
        'package_name': 'article-mcp',
        'deployment_method': 'uvx',
        'install_command': 'pip install article-mcp',
        'run_command': 'uvx article-mcp'
    }
    
    success = True
    for key, expected_value in expected_results.items():
        actual_value = package_info.get(key)
        if actual_value != expected_value:
            print(f"  ❌ {key}: 期望 '{expected_value}', 实际 '{actual_value}'")
            success = False
        else:
            print(f"  ✅ {key}: {actual_value}")
    
    return success


def test_csv_parser_integration():
    """测试CSV解析器集成"""
    print("\n" + "=" * 60)
    print("测试2: CSV解析器功能")
    print("=" * 60)
    
    try:
        parser = MCPDataParser('data/mcp.csv')
        print("✅ CSV解析器初始化成功")
        
        # 测试查找现有工具
        test_url = "https://github.com/microsoft/playwright-mcp"
        tool = parser.find_tool_by_url(test_url)
        
        if tool:
            print(f"✅ 找到工具: {tool.name}")
            print(f"  📦 包名: {tool.package_name or '未提取'}")
            print(f"  🚀 部署方法: {tool.deployment_method}")
            print(f"  ⭐ 星标数: {tool.lobehub_star_count}")
            return True
        else:
            print("❌ 未找到测试工具")
            return False
            
    except Exception as e:
        print(f"❌ CSV解析器测试失败: {e}")
        return False


def test_package_extraction_logic():
    """测试包名提取逻辑的各种情况"""
    print("\n" + "=" * 60)
    print("测试3: 包名提取逻辑")
    print("=" * 60)
    
    analyzer = GitHubMCPAnalyzer()
    
    test_cases = [
        {
            'name': 'NPX scoped package',
            'content': 'Install with npx @myorg/mypackage',
            'expected_deployment': 'npx',
            'expected_package': '@myorg/mypackage'
        },
        {
            'name': 'NPX simple package',
            'content': 'Run with npx simple-package',
            'expected_deployment': 'npx', 
            'expected_package': 'simple-package'
        },
        {
            'name': 'UVX package',
            'content': 'uvx python-package server',
            'expected_deployment': 'uvx',
            'expected_package': 'python-package'
        },
        {
            'name': 'Cargo package',
            'content': 'cargo install my-rust-tool',
            'expected_deployment': 'cargo',
            'expected_package': 'my-rust-tool'
        },
        {
            'name': 'Python module',
            'content': 'python -m my_python_module',
            'expected_deployment': 'python',
            'expected_package': 'my_python_module'
        }
    ]
    
    passed = 0
    total = len(test_cases)
    
    for case in test_cases:
        print(f"\n🔍 测试: {case['name']}")
        
        deployment_methods = analyzer._extract_deployment_methods(case['content'])
        package_info = analyzer._extract_package_info(case['content'], deployment_methods)
        
        print(f"  部署方法: {deployment_methods}")
        print(f"  包名: {package_info['package_name']}")
        
        # 验证部署方法
        if case['expected_deployment'] in deployment_methods:
            print(f"  ✅ 部署方法正确")
            deployment_ok = True
        else:
            print(f"  ❌ 部署方法错误，期望: {case['expected_deployment']}")
            deployment_ok = False
        
        # 验证包名
        if package_info['package_name'] == case['expected_package']:
            print(f"  ✅ 包名正确")
            package_ok = True
        else:
            print(f"  ❌ 包名错误，期望: {case['expected_package']}, 实际: {package_info['package_name']}")
            package_ok = False
        
        if deployment_ok and package_ok:
            passed += 1
            print(f"  🎉 {case['name']} 测试通过")
        else:
            print(f"  💥 {case['name']} 测试失败")
    
    success_rate = passed / total * 100
    print(f"\n📊 包名提取成功率: {success_rate:.1f}% ({passed}/{total})")
    
    return success_rate >= 80  # 80%通过率


def main():
    """主测试函数"""
    print("🧪 MCP GitHub分析器核心功能测试")
    print("=" * 60)
    
    test_results = []
    
    # 运行所有测试
    test_results.append(("GitHub分析器核心逻辑", test_github_analyzer_with_cache()))
    test_results.append(("CSV解析器集成", test_csv_parser_integration()))
    test_results.append(("包名提取逻辑", test_package_extraction_logic()))
    
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
        print("\n🎉 所有核心测试通过! GitHub集成功能正常工作。")
        return 0
    else:
        print(f"\n⚠️  有 {total-passed} 个测试失败，需要修复。")
        return 1


if __name__ == "__main__":
    exit(main())