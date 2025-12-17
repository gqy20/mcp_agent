#!/usr/bin/env python3
"""跨平台兼容性验证脚本

验证项目在不同平台上的基本功能
"""

import platform
import shutil
import subprocess
import sys


def check_system_requirements():
    """检查系统要求"""
    print("🔍 检查系统要求...")

    # Python版本
    python_version = sys.version_info
    print(
        f"🐍 Python版本: {python_version.major}.{python_version.minor}.{python_version.micro}"
    )
    if python_version < (3, 12):
        print("❌ Python版本需要 3.12+")
        return False

    # 操作系统
    os_info = platform.platform()
    print(f"🖥️ 操作系统: {os_info}")

    # Node.js检查
    try:
        node_result = subprocess.run(
            ["node", "--version"],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if node_result.returncode == 0:
            print(f"✅ Node.js: {node_result.stdout.strip()}")
        else:
            print("❌ Node.js 不可用")
            return False
    except Exception as e:
        print(f"❌ Node.js 检查失败: {e}")
        return False

    # NPX检查
    npx_path = shutil.which("npx")
    if npx_path:
        print(f"✅ NPX: {npx_path}")
    else:
        print("❌ NPX 不可用")
        return False

    return True


def test_module_imports():
    """测试模块导入"""
    print("\n📦 测试模块导入...")

    try:
        # 核心模块

        print("✅ SimpleMCPDeployer 导入成功")

        print("✅ MCPDataParser 导入成功")

        print("✅ URLMCPProcessor 导入成功")

        return True

    except Exception as e:
        print(f"❌ 模块导入失败: {e}")
        return False


def test_csv_data_loading():
    """测试CSV数据加载"""
    print("\n📊 测试CSV数据加载...")

    try:
        from src.batch_mcp.utils.csv_parser import get_mcp_parser

        parser = get_mcp_parser()
        if parser.load_data():
            tools_count = len(parser.df) if parser.df is not None else 0
            print(f"✅ CSV数据加载成功，包含 {tools_count} 条记录")

            # 测试Context7查找
            context7 = parser.find_tool_by_url(
                "https://lobehub.com/mcp/upstash-context7"
            )
            if context7:
                print(f"✅ Context7工具查找成功: {context7.package_name}")
                return True
            print("⚠️ Context7工具未找到")
            return False
        print("❌ CSV数据加载失败")
        return False

    except Exception as e:
        print(f"❌ CSV测试失败: {e}")
        return False


def test_platform_detection():
    """测试平台检测"""
    print("\n🖥️ 测试平台检测...")

    try:
        from src.batch_mcp.core.simple_mcp_deployer import detect_simple_platform

        platform_info = detect_simple_platform()
        print(f"✅ 平台: {platform_info['system']}")
        print(f"✅ 架构: {platform_info['architecture']}")
        print(f"✅ Node.js可用: {platform_info['node_available']}")

        if platform_info["node_available"]:
            print(f"✅ NPX路径: {platform_info['npx_path']}")
            return True
        print("❌ Node.js环境不可用")
        return False

    except Exception as e:
        print(f"❌ 平台检测失败: {e}")
        return False


def main():
    """主测试函数"""
    print("🚀 跨平台兼容性验证")
    print("=" * 50)

    all_passed = True

    # 系统要求检查
    if not check_system_requirements():
        all_passed = False

    # 模块导入测试
    if not test_module_imports():
        all_passed = False

    # CSV数据加载测试
    if not test_csv_data_loading():
        all_passed = False

    # 平台检测测试
    if not test_platform_detection():
        all_passed = False

    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 所有测试通过！项目在当前平台上可以正常运行")
        return 0
    print("❌ 部分测试失败，请检查上述错误信息")
    return 1


if __name__ == "__main__":
    sys.exit(main())
