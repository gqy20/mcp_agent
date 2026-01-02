"""Deployer 模块.

此模块提供MCP工具的部署功能。
拆分为以下子模块：
- communicator: MCP通信器类
- deployer: MCP部署器类

为了保持向后兼容，所有公开类和函数都从此模块导出。
"""

# 从子模块导出所有公开类和函数
from .communicator import SimpleMCPCommunicator
from .deployer import (
    SimpleMCPDeployer,
    SimpleMCPServerInfo,
    detect_simple_platform,
    get_simple_mcp_deployer,
)

# 为了向后兼容，导出所有公开接口
__all__ = [
    "SimpleMCPCommunicator",
    "SimpleMCPDeployer",
    "SimpleMCPServerInfo",
    "detect_simple_platform",
    "get_simple_mcp_deployer",
]
