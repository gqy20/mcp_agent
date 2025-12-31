"""输入类型检测器 - 智能识别用户输入类型.

遵循 Linus 原则：
- 简单直接的检测逻辑
- 清晰的优先级
- 易于扩展

从 cli_handlers.py 提取：
- InputType 枚举
- _detect_input_type()
- _is_http_mcp_endpoint()
- _adapt_config_for_input_type()
"""

import copy
from enum import Enum
from typing import Any

# 常量定义
_MIN_DOMAIN_PARTS = 2
_MAX_DOMAIN_PART_LENGTH = 3


class InputType(Enum):
    """MCP输入类型枚举."""

    HTTP_ENDPOINT = "http_endpoint"
    GITHUB_URL = "github_url"
    PACKAGE_NAME = "package_name"
    SEARCH_QUERY = "search_query"
    UNKNOWN = "unknown"


class InputTypeDetector:
    """输入类型检测器."""

    def detect(self, user_input: str) -> InputType:
        """智能检测用户输入类型.

        Args:
            user_input: 用户输入的字符串

        Returns:
            InputType: 检测到的输入类型.

        """
        if not user_input:
            return InputType.SEARCH_QUERY

        # 移除首尾空白字符
        user_input = user_input.strip()

        # 空白字符串视为搜索查询
        if not user_input:
            return InputType.SEARCH_QUERY

        # 1. HTTP MCP端点检测 (优先级最高)
        if self.is_http_mcp_endpoint(user_input):
            return InputType.HTTP_ENDPOINT

        # 2. GitHub URL检测 (支持http和https)
        if user_input.startswith(("https://github.com/", "http://github.com/")):
            return InputType.GITHUB_URL

        # 3. 包名格式检测 (@开头)
        if user_input.startswith("@"):
            return InputType.PACKAGE_NAME

        # 4. 其他格式视为搜索查询
        return InputType.SEARCH_QUERY

    def is_http_mcp_endpoint(self, url: str) -> bool:  # noqa: PLR0911, PLR0912
        """增强的HTTP MCP端点检测.

        支持多种检测模式：
        1. 路径特征检测 (/mcp, /api/mcp等)
        2. 端口特征检测 (开发环境端口)
        3. 查询参数检测
        4. 域名特征检测

        Args:
            url: 要检测的URL

        Returns:
            bool: 是否为HTTP MCP端点

        """
        if not url:
            return False

        # 基础URL格式检查
        if not url.startswith(("http://", "https://")):
            return False

        # 排除明确的GitHub URL (优先交给GitHub处理)
        if "github.com" in url:
            return False

        url_lower = url.lower()

        # 1. 路径特征检测 (需要精确匹配以避免误报)
        mcp_path_indicators = [
            "/mcp",  # 标准MCP路径
            "/api/mcp",  # API风格的MCP路径
            "/mcp-endpoint",  # 明确的端点路径
            "/mcp-server",  # MCP服务器路径
            "/model-context-protocol",  # 完整协议名
            "/proxy/mcp",  # 代理模式MCP
            "/mcp-v",  # 版本化的MCP路径 (如mcp-v1, mcp-v2)
            "/proxy",  # 单独的代理路径 (在有其他MCP特征时)
        ]

        # 检查是否包含确切的MCP路径指示器
        for indicator in mcp_path_indicators:
            if indicator in url_lower:
                # 确保这是一个真实的路径，而不是URL的一部分
                if indicator == "/mcp":
                    # 对于简单的"/mcp"，需要更严格的验证
                    if (
                        url_lower.endswith("/mcp")
                        or "/mcp?" in url_lower
                        or "/mcp/" in url_lower
                    ):
                        return True
                elif indicator == "/proxy":
                    # 对于"/proxy"路径，需要有查询参数支持
                    if any(
                        param in url_lower
                        for param in ["?key=", "?token=", "?auth=", "?mcp="]
                    ):
                        return True
                else:
                    # 对于其他指示器，直接接受
                    return True

        # 特殊情况：短路径 "/m" 在特定条件下可能表示MCP端点
        # 仅在域名非常短或看起来像测试环境时接受
        if url_lower.endswith("/m") or "/m?" in url_lower or "/m/" in url_lower:
            parsed_url = url.split("//")[-1].split("/")[0]
            domain_lower = parsed_url.lower()
            domain_parts = parsed_url.split(".")
            # 如果域名很短（如a.co, x.y等）或包含localhost等开发环境特征
            if len(domain_parts) == _MIN_DOMAIN_PARTS and all(
                len(part) <= _MAX_DOMAIN_PART_LENGTH for part in domain_parts
            ):
                return True
            if (
                "localhost" in domain_lower
                or "dev" in domain_lower
                or "test" in domain_lower
            ):
                return True

        # 2. 查询参数检测
        mcp_query_indicators = [
            "?mcp=",
            "&mcp=",
            "?api_key=",  # 通常MCP端点需要API密钥
            "?token=",
            "&token=",
            "?auth=",  # 认证参数
            "&auth=",
        ]

        if any(indicator in url_lower for indicator in mcp_query_indicators):
            return True

        # 3. 开发环境端口检测 (常见开发端口)
        dev_ports = [":3000", ":8080", ":8000", ":5000", ":4000", ":9000", ":7000"]
        if any(port in url for port in dev_ports):
            # 对于开发端口，进一步检查是否有API特征
            api_indicators = ["/api", "/v1", "/v2", "/endpoint", "/server"]
            if any(indicator in url_lower for indicator in api_indicators):
                return True

        # 4. 域名特征检测
        mcp_domain_indicators = [
            "mcp-",  # 域名包含mcp前缀
            "-mcp.",  # 域名包含mcp后缀
            "mcp.",  # 域名以mcp开头
        ]

        # API相关的域名，在有其他MCP特征时接受
        api_domain_indicators = [
            "api.",  # API子域名
            "gateway.",  # 网关子域名
            "proxy.",  # 代理子域名
        ]

        parsed_url = url.split("//")[-1].split("/")[0]  # 提取域名部分
        domain_lower = parsed_url.lower()

        # MCP相关域名直接接受
        if any(indicator in domain_lower for indicator in mcp_domain_indicators):
            return True

        # API相关域名需要额外的验证
        if any(indicator in domain_lower for indicator in api_domain_indicators):
            # 如果域名包含API指示器，检查URL中是否有其他MCP特征
            # 如果查询参数包含MCP相关参数，则接受
            if any(indicator in url_lower for indicator in mcp_query_indicators):
                return True
            # 如果路径包含MCP相关内容，则接受
            if any(indicator in url_lower for indicator in mcp_path_indicators):
                return True

        return False

    def adapt_config(self, input_type: InputType, config: Any) -> Any:
        """根据输入类型自适应调整配置.

        Args:
            input_type: 检测到的输入类型
            config: 原始配置对象

        Returns:
            调整后的配置对象

        """
        # 创建配置副本避免修改原配置
        adapted_config = copy.deepcopy(config)

        if input_type == InputType.HTTP_ENDPOINT:
            # HTTP端点特定配置
            adapted_config.timeout = min(config.timeout, 300)  # HTTP通常超时时间较短
            adapted_config.evaluate = True  # HTTP端点默认启用评估
            adapted_config.cleanup = True  # HTTP测试始终启用清理

            # HTTP端点的智能测试通常更快，可以适当减少测试数量
            if hasattr(adapted_config, "max_smart_tests"):
                adapted_config.max_smart_tests = min(
                    getattr(adapted_config, "max_smart_tests", 5), 3
                )

        elif input_type == InputType.GITHUB_URL:
            # GitHub URL特定配置
            adapted_config.timeout = max(config.timeout, 300)  # GitHub可能需要更长时间
            # 动态添加 enable_fallback 属性（如果不存在）
            adapted_config.enable_fallback = True

        elif input_type == InputType.PACKAGE_NAME:
            # 包名特定配置
            adapted_config.timeout = max(config.timeout, 180)  # 包安装需要时间

        return adapted_config


# 全局检测器实例
_detector = InputTypeDetector()


def get_input_type_detector() -> InputTypeDetector:
    """获取输入类型检测器实例.

    Returns:
        InputTypeDetector 单例实例

    """
    return _detector
