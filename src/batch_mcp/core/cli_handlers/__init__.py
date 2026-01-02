"""Handlers 模块.

此模块提供 CLI 命令处理功能。
拆分为以下子模块：
- utils: 辅助函数
- http_cli: HTTP MCP CLI 处理
- stdio_cli: STDIO MCP CLI 处理
- handler: 核心处理器

为了保持向后兼容，所有公开类都从此模块导出。
"""

# 从子模块导出所有公开类和函数
from .handler import CLIHandler, get_cli_handler
from .http_cli import HTTPCLIHandler
from .stdio_cli import STDIOCLIHandler
from .utils import convert_test_results_to_dict

# 为了向后兼容，导出所有公开接口
__all__ = [
    "CLIHandler",
    "HTTPCLIHandler",
    "STDIOCLIHandler",
    "convert_test_results_to_dict",
    "get_cli_handler",
]
