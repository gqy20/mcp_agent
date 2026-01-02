"""Processor 模块的数据模型."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from src.batch_mcp.utils.csv_parser import MCPToolInfo


@dataclass
class TestReport:
    """测试报告数据结构."""

    session_id: str
    url: str
    tool_info: MCPToolInfo
    start_time: datetime
    end_time: datetime | None = None
    deployment_success: bool = False
    deployment_time: float = 0.0
    communication_success: bool = False
    available_tools_count: int = 0
    test_results: list[dict[str, Any]] = None
    error_messages: list[str] = None
    performance_metrics: dict[str, float] = None

    def __post_init__(self):
        if self.test_results is None:
            self.test_results = []
        if self.error_messages is None:
            self.error_messages = []
        if self.performance_metrics is None:
            self.performance_metrics = {}
