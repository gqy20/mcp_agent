#!/usr/bin/env python3
"""统一异常处理模块.

提供标准化的异常处理和日志记录功能
"""

import functools
import logging
import traceback
from collections.abc import Callable
from typing import Any

from rich import print as rprint


class MCPError(Exception):
    """MCP基础异常类."""

    def __init__(
        self,
        message: str,
        error_code: str = "MCP_ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}


class DeploymentError(MCPError):
    """部署相关异常."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message, "DEPLOYMENT_ERROR", details)


class CommunicationError(MCPError):
    """通信相关异常."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message, "COMMUNICATION_ERROR", details)


class ValidationError(MCPError):
    """验证相关异常."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message, "VALIDATION_ERROR", details)


class ConfigurationError(MCPError):
    """配置相关异常."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message, "CONFIG_ERROR", details)


def setup_error_logging() -> None:
    """设置错误日志记录."""
    logging.basicConfig(
        level=logging.ERROR,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler("logs/mcp_errors.log"), logging.StreamHandler()],
    )


def log_error(error: Exception, context: str | None = None) -> None:
    """记录错误信息."""
    logger = logging.getLogger(__name__)

    error_info = {
        "error_type": type(error).__name__,
        "error_message": str(error),
        "context": context,
        "traceback": traceback.format_exc(),
    }

    logger.error(f"Error occurred: {error_info}")

    # 用户友好的错误显示
    if isinstance(error, MCPError):
        rprint(f"[red]❌ {error.error_code}: {error.message}[/red]")
        if error.details:
            rprint(f"[yellow]📋 详细信息: {error.details}[/yellow]")
    else:
        rprint(f"[red]❌ 发生错误: {error}[/red]")
        if context:
            rprint(f"[yellow]📍 错误上下文: {context}[/yellow]")


def handle_exceptions(
    *exception_types: type[Exception],
    default_return: Any = None,
    log_error: bool = True,
    reraise: bool = False,
) -> Callable:
    """统一的异常处理装饰器.

    Args:
        exception_types: 要捕获的异常类型
        default_return: 发生异常时的默认返回值
        log_error: 是否记录错误日志
        reraise: 是否重新抛出异常

    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except exception_types as e:
                if log_error:
                    log_error(e, f"Function {func.__name__}")

                if reraise:
                    raise

                return default_return
            except Exception as e:
                # 未预期的异常
                if log_error:
                    log_error(e, f"Unexpected error in {func.__name__}")

                if reraise:
                    raise

                return default_return

        return wrapper

    return decorator


def safe_execute(
    func: Callable,
    *args,
    default_return: Any = None,
    exception_types: tuple[type[Exception], ...] = (Exception,),
    **kwargs,
) -> Any:
    """安全执行函数，捕获并处理异常.

    Args:
        func: 要执行的函数
        *args: 函数参数
        default_return: 发生异常时的默认返回值
        exception_types: 要捕获的异常类型
        **kwargs: 函数关键字参数

    Returns:
        函数执行结果或默认值

    """
    try:
        return func(*args, **kwargs)
    except exception_types as e:
        log_error(e, f"Safe execution of {func.__name__}")
        return default_return


def validate_input(
    value: Any,
    expected_type: type,
    allow_none: bool = False,
    min_value: float | None = None,
    max_value: float | None = None,
    custom_validator: Callable[[Any], bool] | None = None,
) -> Any:
    """输入验证函数.

    Args:
        value: 要验证的值
        expected_type: 期望的类型
        allow_none: 是否允许None值
        min_value: 最小值限制
        max_value: 最大值限制
        custom_validator: 自定义验证函数

    Returns:
        验证通过的值

    Raises:
        ValidationError: 验证失败时抛出

    """
    # None值检查
    if value is None:
        if allow_none:
            return value
        msg = "值不能为None"
        raise ValidationError(msg)

    # 类型检查
    if not isinstance(value, expected_type):
        msg = f"期望类型 {expected_type.__name__}, 实际类型 {type(value).__name__}"
        raise ValidationError(msg)

    # 数值范围检查
    if min_value is not None and value < min_value:
        msg = f"值不能小于 {min_value}"
        raise ValidationError(msg)

    if max_value is not None and value > max_value:
        msg = f"值不能大于 {max_value}"
        raise ValidationError(msg)

    # 自定义验证
    if custom_validator and not custom_validator(value):
        msg = "自定义验证失败"
        raise ValidationError(msg)

    return value


def retry_on_exception(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable:
    """异常重试装饰器.

    Args:
        max_retries: 最大重试次数
        delay: 初始延迟时间（秒）
        backoff: 退避因子
        exceptions: 需要重试的异常类型

    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_retries:
                        raise

                    rprint(
                        f"[yellow]⚠️ 第 {attempt + 1} 次尝试失败: {e}，{current_delay}秒后重试...[/yellow]",
                    )
                    import time

                    time.sleep(current_delay)
                    current_delay *= backoff

            return None

        return wrapper

    return decorator
