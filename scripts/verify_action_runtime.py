#!/usr/bin/env python3
"""GitHub Action 运行时验证脚本

验证npm/npx和uvx环境是否正确配置，确保Action能够正常运行

作者: AI Assistant
日期: 2025-08-24
"""

import os
import shutil
import subprocess
import sys


def check_command(cmd, name):
    """检查命令是否可用"""
    try:
        result = subprocess.run(
            [cmd, "--help"], check=False, capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            print(f"✅ {name} 命令可用: {shutil.which(cmd)}")
            return True
        print(f"❌ {name} 命令异常: 返回码 {result.returncode}")
        return False
    except subprocess.TimeoutExpired:
        print(f"❌ {name} 命令超时")
        return False
    except FileNotFoundError:
        print(f"❌ {name} 命令未找到")
        return False
    except Exception as e:
        print(f"❌ {name} 命令检查失败: {e}")
        return False


def check_version(cmd, name):
    """检查命令版本"""
    try:
        result = subprocess.run(
            [cmd, "--version"], check=False, capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"📦 {name} 版本: {version}")
            return version
        print(f"⚠️ 无法获取 {name} 版本信息")
        return None
    except Exception as e:
        print(f"⚠️ 获取 {name} 版本失败: {e}")
        return None


def test_runtime_functionality():
    """测试运行时功能"""
    print("\n🧪 测试运行时功能...")

    # 测试npx功能
    print("\n📦 测试npx功能...")
    try:
        # 使用简单的npx命令测试
        result = subprocess.run(
            ["npx", "--yes", "cowsay", "npx works!"],
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            print("✅ npx 功能测试通过")
        else:
            print(f"⚠️ npx 功能测试失败: {result.stderr}")
    except Exception as e:
        print(f"⚠️ npx 功能测试异常: {e}")

    # 测试uvx功能
    print("\n📦 测试uvx功能...")
    try:
        # 使用简单的uvx命令测试
        result = subprocess.run(
            ["uvx", "--help"], check=False, capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            print("✅ uvx 功能测试通过")
        else:
            print(f"⚠️ uvx 功能测试失败: {result.stderr}")
    except Exception as e:
        print(f"⚠️ uvx 功能测试异常: {e}")


def main():
    """主函数"""
    print("🔍 GitHub Action 运行时环境验证")
    print("=" * 50)

    # 检查Python环境
    print(f"🐍 Python 版本: {sys.version}")
    print(f"🐍 Python 路径: {sys.executable}")

    # 检查环境变量
    print(f"\n🌍 PATH: {os.environ.get('PATH', 'Not set')}")

    # 检查基本命令
    commands_to_check = [
        ("node", "Node.js"),
        ("npm", "npm"),
        ("npx", "npx"),
        ("uv", "UV"),
        ("uvx", "uvx"),
        ("python", "Python"),
        ("python3", "Python3"),
    ]

    print("\n🔧 检查命令可用性...")
    available_commands = []
    for cmd, name in commands_to_check:
        if check_command(cmd, name):
            available_commands.append(cmd)
            check_version(cmd, name)

    # 运行功能测试
    if "npx" in available_commands or "uvx" in available_commands:
        test_runtime_functionality()

    # 综合评估
    print("\n📊 评估结果:")
    print(f"   可用命令数: {len(available_commands)}/{len(commands_to_check)}")

    critical_commands = ["node", "npm", "npx", "uv", "uvx"]
    available_critical = [cmd for cmd in critical_commands if cmd in available_commands]

    print(f"   关键命令: {len(available_critical)}/{len(critical_commands)}")
    print(f"   关键命令列表: {', '.join(available_critical)}")

    if len(available_critical) >= 4:  # node, npm, npx 和 (uv 或 uvx)
        print("🎉 运行时环境配置良好，Action应该能正常工作!")
        return 0
    if len(available_critical) >= 2:
        print("⚠️ 运行时环境部分可用，某些功能可能受限")
        return 0
    print("❌ 运行时环境严重不足，Action可能无法正常工作")
    return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
