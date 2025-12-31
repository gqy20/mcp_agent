"""保护性测试 - 确保 config.py 清理后功能正常.

这些测试确保在移除 AIConfig 后，核心配置功能仍然正常工作。
"""

from src.batch_mcp.core.config import (
    DatabaseConfig,
    PathsConfig,
    SystemConfig,
    TestingConfig,
    TimeoutsConfig,
    get_config,
    has_database_config,
    reset_config,
)


class TestConfigCoreFunctionality:
    """测试核心配置功能（不依赖 AIConfig）."""

    def test_paths_config_works(self):
        """验证 PathsConfig 可以正常工作."""
        config = PathsConfig()

        assert config.project_root.exists(), "项目根路径应该存在"
        assert config.data_dir.exists(), "数据目录应该存在"

    def test_timeouts_config_works(self):
        """验证 TimeoutsConfig 可以正常工作."""
        config = TimeoutsConfig()

        # 基础超时应该有默认值
        assert config.deployment_timeout > 0
        assert config.test_timeout > 0
        assert config.communication_timeout > 0

    def test_database_config_works(self):
        """验证 DatabaseConfig 可以正常工作."""
        config = DatabaseConfig()

        # 应该有表名
        assert config.supabase_table_name == "mcp_test_results"

    def test_testing_config_works(self):
        """验证 TestingConfig 可以正常工作."""
        config = TestingConfig()

        # 基础配置应该存在
        assert config.max_test_tools > 0
        assert config.concurrent_tests > 0
        assert config.enable_database_export is not None
        assert config.enable_evaluation is not None

    def test_system_config_works(self):
        """验证 SystemConfig 可以正常工作."""
        config = SystemConfig()

        # 支持的部署方法应该包含常见方法
        assert "npx" in config.supported_deployment_methods
        assert "npm" in config.supported_deployment_methods

    def test_get_config_returns_valid_config(self):
        """验证 get_config() 返回有效的配置."""
        reset_config()  # 重置全局配置
        config = get_config()

        # 验证核心配置部分存在
        assert hasattr(config, "paths")
        assert hasattr(config, "timeouts")
        assert hasattr(config, "database")
        assert hasattr(config, "testing")
        assert hasattr(config, "system")

    def test_config_summary_works_without_ai(self):
        """验证配置摘要可以在没有 AI 配置的情况下工作."""
        reset_config()
        config = get_config()

        summary = config.get_summary()

        # 核心字段应该存在
        assert "project_root" in summary
        assert "has_supabase" in summary
        assert "platform" in summary

    def test_config_has_database_config(self):
        """验证 has_database_config() 函数工作."""
        # 函数应该可调用（不抛出异常）
        result = has_database_config()
        assert isinstance(result, bool)

    def test_reset_config_works(self):
        """验证 reset_config() 函数工作."""
        # 获取第一个实例
        get_config()

        # 重置
        reset_config()

        # 获取新实例
        config2 = get_config()

        # 应该是同一个全局实例（因为 reset_config 只是设为 None，下次 get 会重新创建）
        # 但我们可以验证函数不会抛出异常
        assert config2 is not None


class TestTimeoutsConfigAfterAIRemoval:
    """测试移除 AI 超时后的 TimeoutsConfig."""

    def test_timeouts_no_ai_fields(self):
        """验证 TimeoutsConfig 移除 AI 字段后仍然有基础超时."""
        config = TimeoutsConfig()

        # 基础超时应该存在
        assert config.deployment_timeout > 0
        assert config.install_timeout > 0
        assert config.test_timeout > 0
        assert config.communication_timeout > 0

        # AI 超时字段将被移除，所以不应该存在
        assert not hasattr(config, "ai_test_generation_timeout")
        assert not hasattr(config, "ai_validation_timeout")
