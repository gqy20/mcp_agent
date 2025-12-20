#!/usr/bin/env python3
"""GitHub Actions输入类型检测脚本"""

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, project_root)

from src.batch_mcp.core.cli_handlers import CLIHandler, InputType


def detect_input_type(user_input: str) -> str:
    """检测输入类型并返回字符串值"""
    handler = CLIHandler()
    try:
        input_type = handler._detect_input_type(user_input)
        return input_type.value
    except Exception as e:
        print(f"检测失败: {e}", file=sys.stderr)
        return "unknown"


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("用法: detect_input_type.py '<输入内容>'", file=sys.stderr)
        sys.exit(1)

    user_input = sys.argv[1]
    result = detect_input_type(user_input)
    print(result)