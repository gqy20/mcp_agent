#!/usr/bin/env python3
"""AIConfigFactory 单元测试.

测试覆盖：
1. 为不同 agent 类型创建配置（test_generator, validation_agent）
2. OpenAI 配置优先级
3. DashScope 配置回退
4. 环境变量回退
5. 缺失配置的优雅处理
6. 不同的 temperature 和 max_tokens 参数
"""

from src.batch_mcp.utils.ai_config_factory import (
    AIConfigFactory,
    get_ai_config_factory,
)


class TestAIConfigFactory:
    """AIConfigFactory 测试类."""

    def setup_method(self):
        """每个测试前的设置."""
        self.factory = AIConfigFactory()

    def test_create_config_for_test_generator_with_openai(self):
        """测试为 test_generator 创建 OpenAI 配置."""
        # Arrange
        agent_type = "test_generator"
        config_options = {
            "has_openai_config": True,
            "openai_api_key": "sk-test-key",
            "openai_base_url": "https://api.openai.com/v1",
            "openai_model": "gpt-4o",
        }

        # Act
        result = self.factory.create_config(agent_type, config_options)

        # Assert
        assert result["config_name"] == "test_generator_config"
        assert result["model_type"] == "openai_chat"
        assert result["model_name"] == "gpt-4o"
        assert result["api_key"] == "sk-test-key"
        assert result["client_kwargs"]["base_url"] == "https://api.openai.com/v1"
        assert result["client_kwargs"]["timeout"] == 60
        assert result["generate_args"]["temperature"] == 0.7
        assert result["generate_args"]["max_tokens"] == 1000

    def test_create_config_for_validation_agent_with_openai(self):
        """测试为 validation_agent 创建 OpenAI 配置."""
        # Arrange
        agent_type = "validation_agent"
        config_options = {
            "has_openai_config": True,
            "openai_api_key": "sk-test-key",
            "openai_base_url": "https://api.openai.com/v1",
            "openai_model": "gpt-4o",
        }

        # Act
        result = self.factory.create_config(agent_type, config_options)

        # Assert
        assert result["config_name"] == "validation_agent_config"
        assert result["model_type"] == "openai_chat"
        assert result["model_name"] == "gpt-4o"
        assert result["api_key"] == "sk-test-key"
        assert result["client_kwargs"]["base_url"] == "https://api.openai.com/v1"
        assert result["client_kwargs"]["timeout"] == 60
        assert result["generate_args"]["temperature"] == 0.3
        assert result["generate_args"]["max_tokens"] == 800

    def test_create_config_with_dashscope_fallback(self):
        """测试使用 DashScope 配置回退."""
        # Arrange
        agent_type = "test_generator"
        config_options = {
            "has_openai_config": False,
            "has_dashscope_config": True,
            "dashscope_api_key": "dash-test-key",
            "dashscope_base_url": "https://dashscope.aliyuncs.com/api/v1",
            "dashscope_model": "qwen-plus",
        }

        # Act
        result = self.factory.create_config(agent_type, config_options)

        # Assert
        assert result["config_name"] == "test_generator_config"
        assert result["model_type"] == "openai_chat"
        assert result["model_name"] == "qwen-plus"
        assert result["api_key"] == "dash-test-key"
        assert (
            result["client_kwargs"]["base_url"]
            == "https://dashscope.aliyuncs.com/api/v1"
        )
        assert result["generate_args"]["temperature"] == 0.7
        assert result["generate_args"]["max_tokens"] == 1000

    def test_openai_priority_over_dashscope(self):
        """测试 OpenAI 配置优先级高于 DashScope."""
        # Arrange - 两者都可用时，应优先使用 OpenAI
        agent_type = "test_generator"
        config_options = {
            "has_openai_config": True,
            "has_dashscope_config": True,
            "openai_api_key": "sk-openai-key",
            "openai_base_url": "https://api.openai.com/v1",
            "openai_model": "gpt-4o",
            "dashscope_api_key": "dash-key",
            "dashscope_base_url": "https://dashscope.com",
            "dashscope_model": "qwen-plus",
        }

        # Act
        result = self.factory.create_config(agent_type, config_options)

        # Assert - 应该使用 OpenAI 配置
        assert result["model_name"] == "gpt-4o"
        assert result["api_key"] == "sk-openai-key"
        assert result["client_kwargs"]["base_url"] == "https://api.openai.com/v1"

    def test_environment_variable_fallback_when_no_config(self, monkeypatch):
        """测试无配置时回退到环境变量."""
        # Arrange - Mock 环境变量
        monkeypatch.setenv("OPENAI_MODEL", "qwen-plus")
        monkeypatch.setenv("OPENAI_API_KEY", "test-env-key")
        monkeypatch.setenv("OPENAI_BASE_URL", "https://env.example.com")

        agent_type = "test_generator"
        config_options = {
            "has_openai_config": False,
            "has_dashscope_config": False,
        }

        # Act
        result = self.factory.create_config(agent_type, config_options)

        # Assert - 使用环境变量
        assert result["config_name"] == "test_generator_config"
        assert result["model_type"] == "openai_chat"
        assert result["model_name"] == "qwen-plus"
        assert result["api_key"] == "test-env-key"
        assert result["client_kwargs"]["base_url"] == "https://env.example.com"
        assert result["generate_args"]["temperature"] == 0.7
        assert result["generate_args"]["max_tokens"] == 1000

    def test_validation_agent_uses_different_temperature(self):
        """测试 validation_agent 使用不同的 temperature 和 max_tokens."""
        # Arrange
        agent_type = "validation_agent"
        config_options = {
            "has_openai_config": True,
            "openai_api_key": "sk-test-key",
            "openai_base_url": "https://api.openai.com/v1",
            "openai_model": "gpt-4o",
        }

        # Act
        result = self.factory.create_config(agent_type, config_options)

        # Assert - validation_agent 应该有更保守的参数
        assert result["generate_args"]["temperature"] == 0.3
        assert result["generate_args"]["max_tokens"] == 800

    def test_test_generator_uses_creative_parameters(self):
        """测试 test_generator 使用更具创造性的参数."""
        # Arrange
        agent_type = "test_generator"
        config_options = {
            "has_openai_config": True,
            "openai_api_key": "sk-test-key",
            "openai_base_url": "https://api.openai.com/v1",
            "openai_model": "gpt-4o",
        }

        # Act
        result = self.factory.create_config(agent_type, config_options)

        # Assert - test_generator 应该有更创造性的参数
        assert result["generate_args"]["temperature"] == 0.7
        assert result["generate_args"]["max_tokens"] == 1000

    def test_unknown_agent_type_raises_error(self):
        """测试未知的 agent 类型抛出错误."""
        # Arrange
        agent_type = "unknown_agent_type"
        config_options = {"has_openai_config": True}

        # Act & Assert
        try:
            self.factory.create_config(agent_type, config_options)
            assert False, "应该抛出 ValueError"
        except ValueError as e:
            assert "unknown agent type" in str(e).lower()

    def test_config_timeout_always_60(self):
        """测试所有配置的超时时间都是 60 秒."""
        # Arrange
        config_options = {
            "has_openai_config": True,
            "openai_api_key": "sk-test",
            "openai_base_url": "https://api.openai.com/v1",
            "openai_model": "gpt-4o",
        }

        # Act
        test_gen_config = self.factory.create_config("test_generator", config_options)
        validation_config = self.factory.create_config(
            "validation_agent", config_options
        )

        # Assert
        assert test_gen_config["client_kwargs"]["timeout"] == 60
        assert validation_config["client_kwargs"]["timeout"] == 60

    def test_model_type_is_always_openai_chat(self):
        """测试所有配置的 model_type 都是 openai_chat."""
        # Arrange
        config_options = {
            "has_openai_config": True,
            "openai_api_key": "sk-test",
            "openai_base_url": "https://api.openai.com/v1",
            "openai_model": "gpt-4o",
        }

        # Act
        result = self.factory.create_config("test_generator", config_options)

        # Assert
        assert result["model_type"] == "openai_chat"


class TestAIConfigFactoryGlobalInstance:
    """全局实例测试."""

    def test_get_ai_config_factory_returns_instance(self):
        """测试获取全局实例."""
        # Act
        factory = get_ai_config_factory()

        # Assert
        assert factory is not None
        assert isinstance(factory, AIConfigFactory)

    def test_get_ai_config_factory_returns_same_instance(self):
        """测试全局实例单例模式."""
        # Act
        factory1 = get_ai_config_factory()
        factory2 = get_ai_config_factory()

        # Assert
        assert factory1 is factory2
