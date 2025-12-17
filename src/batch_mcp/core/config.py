#!/usr/bin/env python3
"""
Batch MCP 配置管理

集中管理所有文件路径、环境变量和配置参数
支持环境变量覆盖和配置验证

作者: AI Assistant
日期: 2025-12-17
版本: 0.1.0
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Union


@dataclass
class PathsConfig:
    """文件路径配置"""

    # 基础路径
    project_root: Path = field(default_factory=lambda: Path(__file__).parent.parent.parent.parent)

    # 数据路径
    data_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent.parent.parent / "data")
    mcp_database_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent.parent.parent / "data" / "mcp_database")
    mcp_csv_path: Path = field(default_factory=lambda: Path(__file__).parent.parent.parent.parent / "data" / "mcp_database" / "mcp.csv")

    # 输出路径
    test_results_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent.parent.parent / "data" / "test_results")
    logs_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent.parent.parent / "logs")
    temp_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent.parent.parent / "data" / "temp")

    # 报告路径
    reports_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent.parent.parent / "data" / "test_results" / "reports")
    json_reports_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent.parent.parent / "data" / "test_results" / "reports" / "json")
    html_reports_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent.parent.parent / "data" / "test_results" / "reports" / "html")

    def __post_init__(self):
        """确保所有路径都是绝对路径"""
        for path_field in [
            'project_root', 'data_dir', 'mcp_database_dir', 'mcp_csv_path',
            'test_results_dir', 'logs_dir', 'temp_dir',
            'reports_dir', 'json_reports_dir', 'html_reports_dir'
        ]:
            path_value = getattr(self, path_field)
            if isinstance(path_value, Path) and not path_value.is_absolute():
                absolute_path = self.project_root / path_value
                setattr(self, path_field, absolute_path)


@dataclass
class TimeoutsConfig:
    """超时配置"""

    # 部署相关超时
    deployment_timeout: int = field(default_factory=lambda: int(os.getenv("DEPLOYMENT_TIMEOUT", "120")))
    install_timeout: int = field(default_factory=lambda: int(os.getenv("INSTALL_TIMEOUT", "300")))

    # 测试相关超时
    test_timeout: int = field(default_factory=lambda: int(os.getenv("TEST_TIMEOUT", "60")))
    communication_timeout: int = field(default_factory=lambda: int(os.getenv("COMMUNICATION_TIMEOUT", "30")))

    # AI相关超时
    ai_test_generation_timeout: int = field(default_factory=lambda: int(os.getenv("AI_TEST_GENERATION_TIMEOUT", "180")))
    ai_validation_timeout: int = field(default_factory=lambda: int(os.getenv("AI_VALIDATION_TIMEOUT", "120")))


@dataclass
class AIConfig:
    """AI模型配置"""

    # OpenAI配置
    openai_api_key: Optional[str] = field(default_factory=lambda: os.getenv("OPENAI_API_KEY"))
    openai_base_url: str = field(default_factory=lambda: os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"))
    openai_model: str = field(default_factory=lambda: os.getenv("OPENAI_MODEL", "gpt-4o"))

    # DashScope配置
    dashscope_api_key: Optional[str] = field(default_factory=lambda: os.getenv("DASHSCOPE_API_KEY"))
    dashscope_base_url: str = field(default_factory=lambda: os.getenv("DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/api/v1"))
    dashscope_model: str = field(default_factory=lambda: os.getenv("DASHSCOPE_MODEL", "qwen-plus"))

    @property
    def has_openai_config(self) -> bool:
        """检查是否有有效的OpenAI配置"""
        return bool(self.openai_api_key)

    @property
    def has_dashscope_config(self) -> bool:
        """检查是否有有效的DashScope配置"""
        return bool(self.dashscope_api_key)

    @property
    def has_any_ai_config(self) -> bool:
        """检查是否有任何AI配置"""
        return self.has_openai_config or self.has_dashscope_config


@dataclass
class DatabaseConfig:
    """数据库配置"""

    # Supabase配置
    supabase_url: Optional[str] = field(default_factory=lambda: os.getenv("SUPABASE_URL"))
    supabase_service_role_key: Optional[str] = field(default_factory=lambda: os.getenv("SUPABASE_SERVICE_ROLE_KEY"))
    supabase_table_name: str = "mcp_test_results"

    @property
    def has_supabase_config(self) -> bool:
        """检查是否有有效的Supabase配置"""
        return bool(self.supabase_url and self.supabase_service_role_key)


@dataclass
class TestingConfig:
    """测试配置"""

    # 默认启用功能
    enable_smart_testing: bool = field(default_factory=lambda: os.getenv("ENABLE_SMART_TESTING", "true").lower() == "true")
    enable_database_export: bool = field(default_factory=lambda: os.getenv("ENABLE_DATABASE_EXPORT", "true").lower() == "true")
    enable_evaluation: bool = field(default_factory=lambda: os.getenv("ENABLE_EVALUATION", "true").lower() == "true")

    # 测试限制
    max_test_tools: int = field(default_factory=lambda: int(os.getenv("MAX_TEST_TOOLS", "100")))
    concurrent_tests: int = field(default_factory=lambda: int(os.getenv("CONCURRENT_TESTS", "3")))

    # LobeHub评分权重
    final_score_weights: Dict[str, float] = field(default_factory=lambda: {
        "success_rate": 1.0,
        "evaluator_score": 2.0
    })


@dataclass
class SystemConfig:
    """系统配置"""

    # 节点管理配置
    node_version_required: str = "18.0+"
    python_version_required: str = "3.12+"

    # 支持的部署方法
    supported_deployment_methods: List[str] = field(default_factory=lambda: [
        "npx", "npm", "pip", "uvx", "cargo", "docker"
    ])

    # 平台信息
    platform: str = field(default_factory=lambda: os.uname().sysname)
    architecture: str = field(default_factory=lambda: os.uname().machine)


class AppConfig:
    """应用配置管理器"""

    def __init__(self):
        self.paths = PathsConfig()
        self.timeouts = TimeoutsConfig()
        self.ai = AIConfig()
        self.database = DatabaseConfig()
        self.testing = TestingConfig()
        self.system = SystemConfig()

    def validate_paths(self) -> List[str]:
        """验证路径配置"""
        errors = []

        # 检查关键目录是否存在
        critical_paths = [
            self.paths.project_root,
            self.paths.data_dir,
        ]

        for path in critical_paths:
            if not path.exists():
                errors.append(f"关键路径不存在: {path}")

        # 检查文件是否存在
        if self.paths.mcp_csv_path.exists():
            print(f"✅ MCP数据库文件: {self.paths.mcp_csv_path}")
        else:
            errors.append(f"MCP数据库文件不存在: {self.paths.mcp_csv_path}")

        return errors

    def create_directories(self) -> None:
        """创建必要的目录"""
        directories = [
            self.paths.test_results_dir,
            self.paths.logs_dir,
            self.paths.temp_dir,
            self.paths.reports_dir,
            self.paths.json_reports_dir,
            self.paths.html_reports_dir,
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    def get_summary(self) -> Dict[str, Union[str, bool, int]]:
        """获取配置摘要"""
        return {
            "project_root": str(self.paths.project_root),
            "mcp_csv_path": str(self.paths.mcp_csv_path),
            "has_openai": self.ai.has_openai_config,
            "has_dashscope": self.ai.has_dashscope_config,
            "has_supabase": self.database.has_supabase_config,
            "enable_smart_testing": self.testing.enable_smart_testing,
            "enable_database_export": self.testing.enable_database_export,
            "enable_evaluation": self.testing.enable_evaluation,
            "platform": self.system.platform,
        }


# 全局配置实例
_config = None

def get_config() -> AppConfig:
    """获取全局配置实例"""
    global _config
    if _config is None:
        _config = AppConfig()
        # 自动创建必要的目录
        _config.create_directories()
    return _config

def reset_config() -> None:
    """重置全局配置（主要用于测试）"""
    global _config
    _config = None


# 快速访问常用配置的便捷函数
def get_mcp_csv_path() -> Path:
    """获取MCP CSV文件路径"""
    return get_config().paths.mcp_csv_path

def get_test_results_dir() -> Path:
    """获取测试结果目录"""
    return get_config().paths.test_results_dir

def get_reports_dir() -> Path:
    """获取报告目录"""
    return get_config().paths.reports_dir

def has_ai_config() -> bool:
    """检查是否有AI配置"""
    return get_config().ai.has_any_ai_config

def has_database_config() -> bool:
    """检查是否有数据库配置"""
    return get_config().database.has_supabase_config