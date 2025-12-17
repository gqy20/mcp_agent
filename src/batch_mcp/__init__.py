"""Batch MCP - 批量MCP工具测试框架

一个用于自动部署、测试和评估Model Context Protocol (MCP)工具的综合框架。

作者: AI Assistant <ai@example.com>
版本: 0.1.0
"""

__version__ = "0.1.0"
__author__ = "AI Assistant"
__email__ = "ai@example.com"

# 导出主要接口
__all__ = [
    "app",
    "MCPTester",
    "SimpleMCPDeployer",
    "AsyncMCPClient",
    "URLMCPProcessor",
]

try:
    from .main import app
    from .core.tester import MCPTester
    from .core.simple_mcp_deployer import SimpleMCPDeployer
    from .core.async_mcp_client import AsyncMCPClient
    from .core.url_mcp_processor import URLMCPProcessor
except ImportError as e:
    # 如果导入失败，可能是模块还没有迁移完成
    print(f"警告: 无法导入主要模块: {e}")
