"""AI 配置工厂 - 统一 AI 配置生成逻辑.

遵循 Linus 原则：
- 简单的 if-elif 链
- 无嵌套
- 易于扩展

解决 test_agent.py 和 validation_agent.py 中的配置加载重复代码。
"""

import os
from pathlib import Path
from typing import Any, ClassVar

from dotenv import load_dotenv


class AIConfigFactory:
    """AI 配置工厂.

    负责为不同的 AI agent 类型生成合理的模型配置。
    """

    # 不同 agent 类型的生成参数配置
    AGENT_GENERATE_ARGS: ClassVar[dict[str, dict[str, Any]]] = {
        "test_generator": {
            "temperature": 0.7,
            "max_tokens": 1000,
        },
        "validation_agent": {
            "temperature": 0.3,
            "max_tokens": 800,
        },
    }

    # 支持的 agent 类型
    SUPPORTED_AGENT_TYPES: ClassVar[frozenset[str]] = frozenset(
        ["test_generator", "validation_agent"]
    )

    @classmethod
    def create_config(
        cls, agent_type: str, config_options: dict[str, Any]
    ) -> dict[str, Any]:
        """创建 AI 模型配置.

        Args:
            agent_type: Agent 类型（test_generator 或 validation_agent）
            config_options: 配置选项字典

        Returns:
            模型配置字典

        Raises:
            ValueError: 当 agent_type 不支持时

        """
        # 1. 验证 agent 类型
        if agent_type not in cls.SUPPORTED_AGENT_TYPES:
            raise ValueError(f"Unknown agent type: {agent_type}")

        # 2. 获取生成参数
        generate_args = cls.AGENT_GENERATE_ARGS[agent_type].copy()

        # 3. 尝试从配置系统获取
        # 注意：检查是否提供了具体的 AI 配置（优先使用传入的配置）
        if (
            config_options.get("has_any_ai_config")
            or config_options.get("has_openai_config")
            or config_options.get("has_dashscope_config")
        ):
            config = cls._try_config_system(config_options, agent_type)
            if config:
                return config

        # 4. 回退到环境变量
        return cls._get_env_config(agent_type, generate_args)

    @classmethod
    def _try_config_system(
        cls, config_options: dict[str, Any], agent_type: str
    ) -> dict[str, Any] | None:
        """尝试从配置系统获取配置.

        Args:
            config_options: 配置选项
            agent_type: Agent 类型

        Returns:
            配置字典，如果无法获取则返回 None

        """
        # OpenAI 配置优先
        if config_options.get("has_openai_config"):
            return {
                "config_name": f"{agent_type}_config",
                "model_type": "openai_chat",
                "model_name": config_options.get("openai_model", "gpt-4o"),
                "api_key": config_options.get("openai_api_key"),
                "client_kwargs": {
                    "base_url": config_options.get(
                        "openai_base_url", "https://api.openai.com/v1"
                    ),
                    "timeout": 60,
                },
                "generate_args": cls.AGENT_GENERATE_ARGS[agent_type].copy(),
            }

        # DashScope 配置回退
        if config_options.get("has_dashscope_config"):
            return {
                "config_name": f"{agent_type}_config",
                "model_type": "openai_chat",
                "model_name": config_options.get("dashscope_model", "qwen-plus"),
                "api_key": config_options.get("dashscope_api_key"),
                "client_kwargs": {
                    "base_url": config_options.get(
                        "dashscope_base_url",
                        "https://dashscope.aliyuncs.com/api/v1",
                    ),
                    "timeout": 60,
                },
                "generate_args": cls.AGENT_GENERATE_ARGS[agent_type].copy(),
            }

        return None

    @classmethod
    def _get_env_config(
        cls, agent_type: str, generate_args: dict[str, Any]
    ) -> dict[str, Any]:
        """从环境变量获取配置.

        Args:
            agent_type: Agent 类型
            generate_args: 生成参数

        Returns:
            配置字典

        """
        # 加载 .env 文件
        env_path = Path(__file__).parent.parent.parent / ".env"
        load_dotenv(env_path)

        return {
            "config_name": f"{agent_type}_config",
            "model_type": "openai_chat",
            "model_name": os.getenv("OPENAI_MODEL", "qwen-plus"),
            "api_key": os.getenv("OPENAI_API_KEY"),
            "client_kwargs": {
                "base_url": os.getenv("OPENAI_BASE_URL"),
                "timeout": 60,
            },
            "generate_args": generate_args,
        }


# 全局实例（保持项目风格）
_factory = AIConfigFactory()


def get_ai_config_factory() -> AIConfigFactory:
    """获取 AI 配置工厂实例.

    Returns:
        AIConfigFactory 实例

    """
    return _factory
