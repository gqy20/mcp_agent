"""数据库管理器 - 统一 Supabase 客户端创建.

遵循 Linus 原则：
- 简单的单例模式
- 无嵌套
- 易于使用

解决 evaluator.py 和其他文件中重复的数据库连接创建代码。
"""

import os
from typing import Any


class DatabaseManager:
    """数据库管理器 - Supabase 客户端单例."""

    _instance = None
    _client = None

    def __new__(cls) -> "DatabaseManager":
        """实现单例模式."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get_client(self) -> Any:
        """获取 Supabase 客户端.

        Returns:
            Supabase 客户端实例，如果配置无效则返回 None

        """
        # 如果已有客户端，直接返回
        if self._client is not None:
            return self._client

        # 检查环境变量
        if not self.has_env_vars():
            return None

        try:
            from supabase import create_client

            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

            if not supabase_url or not supabase_key:
                return None

            self._client = create_client(supabase_url, supabase_key)
            return self._client
        except Exception:  # noqa: BLE001 - 捕获所有异常以优雅处理
            return None

    def has_env_vars(self) -> bool:
        """检查数据库环境变量是否配置.

        Returns:
            如果两个环境变量都存在则返回 True

        """
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        return bool(supabase_url and supabase_key)

    def is_available(self) -> bool:
        """检查数据库客户端是否可用.

        Returns:
            如果客户端存在则返回 True

        """
        return self._client is not None


# 全局实例（保持项目风格）
_manager = DatabaseManager()


def get_database_manager() -> DatabaseManager:
    """获取数据库管理器实例.

    Returns:
        DatabaseManager 单例实例

    """
    return _manager
