"""Batch MCP - 批量MCP工具测试框架.

一个用于自动部署、测试和评估Model Context Protocol (MCP)工具的综合框架。

作者: AI Assistant <ai@example.com>
版本: 0.1.0
"""

__version__ = "0.1.0"
__author__ = "AI Assistant"
__email__ = "ai@example.com"

# 导出主要接口
__all__ = [
    "AsyncMCPClient",
    "MCPTester",
    "SimpleMCPDeployer",
    "URLMCPProcessor",
    "app",
]

try:
    from .core.async_mcp_client import AsyncMCPClient
    from .core.deployer import SimpleMCPDeployer
    from .core.tester import MCPTester
    from .core.url_mcp_processor import URLMCPProcessor
    from .main import app
except ImportError:
    # 如果导入失败，可能是模块还没有迁移完成
    pass
