"""Processor 模块.

此模块提供URL-MCP处理功能。
拆分为以下子模块：
- models: 数据模型定义
- url_resolver: URL解析器
- report_generator: 报告生成器
- processor: 核心处理器

为了保持向后兼容，所有公开类都从此模块导出。
"""

# 从子模块导出所有公开类
from .models import TestReport
from .processor import URLMCPProcessor, get_url_mcp_processor
from .report_generator import ReportGenerator
from .url_resolver import URLResolver

# 为了向后兼容，导出所有公开接口
__all__ = [
    "ReportGenerator",
    "TestReport",
    "URLMCPProcessor",
    "URLResolver",
    "get_url_mcp_processor",
]
