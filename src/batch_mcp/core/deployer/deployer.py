"""MCP部署器模块.

此模块包含MCP工具的部署逻辑。
"""

import contextlib
import platform
import shutil
import subprocess
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from .communicator import SimpleMCPCommunicator


def detect_simple_platform() -> dict[str, Any]:
    """简化的平台检测."""
    platform_info = {
        "system": platform.system(),
        "architecture": platform.architecture()[0],
        "python_version": platform.python_version(),
        "node_available": False,
        "npx_path": None,
        "uv_available": False,
        "uvx_path": None,
    }

    # 检查Node.js和npx
    try:
        npx_path = shutil.which("npx")
        if npx_path:
            platform_info["node_available"] = True
            platform_info["npx_path"] = npx_path

            # 检查Node.js版本
            result = subprocess.run(
                [npx_path, "--version"],
                check=False,
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                platform_info["npx_version"] = result.stdout.strip()
    except Exception:
        pass

    # 检查uv和uvx
    try:
        uvx_path = shutil.which("uvx")
        if uvx_path:
            platform_info["uv_available"] = True
            platform_info["uvx_path"] = uvx_path

            # 检查uvx版本
            result = subprocess.run(
                [uvx_path, "--version"],
                check=False,
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                platform_info["uvx_version"] = result.stdout.strip()
    except Exception:
        pass

    return platform_info


@dataclass
class SimpleMCPServerInfo:
    """简化的MCP服务器信息."""

    package_name: str
    process: subprocess.Popen
    communicator: SimpleMCPCommunicator
    server_id: str
    available_tools: list[dict[str, Any]]
    status: str = "running"
    start_time: float = 0.0


class SimpleMCPDeployer:
    """简化的MCP工具部署器."""

    def __init__(self) -> None:
        self.active_servers = {}  # server_id -> SimpleMCPServerInfo
        self.platform_info = detect_simple_platform()

    def detect_deployment_method(self, url: str) -> tuple[str, dict[str, Any]]:
        """检测部署方法和配置.

        Args:
            url: GitHub URL 或 HTTP MCP 端点 URL

        Returns:
            (method, config): 部署方法和配置字典

        """
        # 检查是否为 HTTP MCP 端点（更精确的检测）
        if url.startswith(("http://", "https://")):
            # 排除 GitHub URLs
            if "github.com" not in url:
                # 检查是否包含 MCP 相关路径模式
                if "/mcp" in url or "/api/mcp" in url or url.endswith("/mcp"):
                    return "http", self._parse_http_config(url)

        # 回退到现有的 STDIO 检测逻辑
        runtime_type, runtime_cmd = self.detect_simple_platform(url)
        return runtime_type, {
            "url": url,
            "runtime": runtime_type,
            "command": runtime_cmd,
        }

    def detect_simple_platform(self, github_url: str) -> tuple[str, str]:
        """根据GitHub URL检测简单平台类型（运行时）.

        Args:
            github_url: GitHub仓库URL

        Returns:
            (runtime_type, runtime_command): 运行时类型和对应的命令路径

        """
        # 检查URL中是否包含uvx的指示信息
        uvx_indicators = [
            "/uv-",  # 包含uv-前缀
            "uvx://",  # uvx协议
            "uv-mcp",  # uv-mcp字样
            "-uv-",  # 中间包含-uv-
            "uv_mcp",  # uv_mcp字样（下划线）
        ]

        if any(indicator in github_url for indicator in uvx_indicators):
            return "uvx", self._get_uvx_command()

        # 默认使用npx
        return "npx", self._get_npx_command()

    def _get_npx_command(self) -> str:
        """获取npx命令路径."""
        if self.platform_info["node_available"] and self.platform_info["npx_path"]:
            return self.platform_info["npx_path"]
        return "npx"

    def _get_uvx_command(self) -> str:
        """获取uvx命令路径."""
        if self.platform_info["uv_available"] and self.platform_info["uvx_path"]:
            return self.platform_info["uvx_path"]
        return "uvx"

    def _parse_http_config(self, url: str) -> dict[str, Any]:
        """解析 HTTP MCP 端点配置.

        Args:
            url: HTTP MCP 端点 URL

        Returns:
            HTTP 配置字典

        """
        parsed = urlparse(url)
        config = {
            "url": url,  # 使用完整的 URL，包括查询参数
            "headers": {},
            "timeout": 30,
        }

        # 从查询参数提取配置
        query_params = parse_qs(parsed.query)

        # 支持 api_key 参数
        if "api_key" in query_params:
            api_key = query_params["api_key"][0]
            config["headers"]["Authorization"] = f"Bearer {api_key}"

        # 支持 token 参数
        if "token" in query_params:
            token = query_params["token"][0]
            config["headers"]["Authorization"] = f"Bearer {token}"

        return config

    def deploy_http_mcp(self, config: dict[str, Any]):
        """部署 HTTP MCP 服务器.

        Args:
            config: HTTP 配置字典

        Returns:
            HttpMCPClient 实例

        """
        from ..http_mcp_client import HttpMCPClient

        if "url" not in config:
            msg = "HTTP MCP 配置必须包含 'url' 字段"
            raise KeyError(msg)

        return HttpMCPClient(
            url=config["url"],
            headers=config.get("headers", {}),
            timeout=config.get("timeout", 30),
        )

    def deploy(self, url: str, **kwargs: Any):
        """统一部署方法 - 支持 STDIO 和 HTTP.

        Args:
            url: GitHub URL 或 HTTP MCP 端点 URL
            **kwargs: 额外的部署参数

        Returns:
            客户端实例 (SimpleMCPServerInfo 或 HttpMCPClient)

        """
        method, config = self.detect_deployment_method(url)

        if method == "http":
            return self.deploy_http_mcp(config)

        # 对于 STDIO，使用现有的 deploy_package 方法
        if method in ["npx", "uvx"]:
            return self.deploy_package(
                package_name=kwargs.get("package_name"),
                run_command=kwargs.get("run_command"),
                github_url=url,
                timeout=kwargs.get("timeout", 30),
            )

        raise ValueError(f"不支持的部署方法: {method}")

    def _get_runtime_info(
        self,
        run_command: str | None = None,
        package_name: str | None = None,
    ) -> dict[str, Any]:
        """获取运行时信息（npx或uvx）.

        Args:
            run_command: 完整的运行命令，如 "uvx excel-mcp-server stdio"
            package_name: 包名（当没有run_command时使用）

        Returns:
            包含runtime_type, runtime_path, display_name等的字典

        """
        runtime_info = {
            "runtime_type": "npx",  # 默认使用npx
            "runtime_path": None,
            "display_name": package_name or "unknown",
            "available": False,
        }

        # 从run_command推断运行时类型
        if run_command:
            cmd_parts = run_command.split()
            if cmd_parts and cmd_parts[0] in ["uvx", "npx"]:
                runtime_info["runtime_type"] = cmd_parts[0]
                runtime_info["display_name"] = (
                    cmd_parts[-1] if len(cmd_parts) > 1 else cmd_parts[0]
                )
            else:
                # 如果不是以uvx或npx开头，假设是包名，默认使用npx
                runtime_info["display_name"] = run_command.split()[-1]

        # 检查对应的运行时是否可用
        if runtime_info["runtime_type"] == "uvx":
            if self.platform_info["uv_available"]:
                runtime_info["runtime_path"] = self.platform_info["uvx_path"]
                runtime_info["available"] = True
            else:
                runtime_info["runtime_type"] = "npx"

        if runtime_info["runtime_type"] == "npx":
            if self.platform_info["node_available"]:
                runtime_info["runtime_path"] = self.platform_info["npx_path"]
                runtime_info["available"] = True

        return runtime_info

    def _build_runtime_command(
        self,
        runtime_info: dict[str, Any],
        run_command: str | None = None,
        package_name: str | None = None,
    ) -> list[str]:
        """构建运行时命令.

        Args:
            runtime_info: 运行时信息
            run_command: 完整的运行命令
            package_name: 包名

        Returns:
            命令列表

        """
        runtime_path = runtime_info["runtime_path"]
        runtime_type = runtime_info["runtime_type"]

        if run_command:
            # 处理占位符
            processed_command = run_command.replace("[transport]", "stdio")

            # 解析完整的run_command
            cmd_parts = processed_command.split()
            if cmd_parts[0] in ["npx", "uvx"]:
                # 替换第一个词为实际的运行时路径
                if runtime_type == "npx":
                    return [runtime_path, *cmd_parts[1:]]
                # uvx
                return [runtime_path, *cmd_parts[1:]]
            # 不是标准格式，添加运行时前缀
            if runtime_type == "npx":
                return [runtime_path, "-y", *cmd_parts]
            # uvx
            return [runtime_path, *cmd_parts]
        # 使用包名构建命令
        if runtime_type == "npx":
            return [runtime_path, "-y", package_name]
        # uvx
        return [runtime_path, package_name]

    def _try_start_process(
        self,
        cmd,
        creation_flags,
        display_name,
        run_command,
        package_name,
        runtime_info,
    ):
        """尝试启动进程，带--stdio回退机制."""
        try:
            # 构建进程参数（跨平台兼容）
            popen_kwargs = {
                "stdin": subprocess.PIPE,
                "stdout": subprocess.PIPE,
                "stderr": subprocess.PIPE,
                "cwd": str(Path.cwd()),
                "text": False,
                "bufsize": 0,
            }

            # Windows特定的creation flags
            if self.platform_info["system"] == "Windows":
                popen_kwargs["creationflags"] = creation_flags

            # 首次尝试
            process = subprocess.Popen(cmd, **popen_kwargs)

            # 等待一小段时间检查是否立即失败
            time.sleep(2)

            if process.poll() is not None:
                # 进程已退出，检查错误
                _stdout, stderr = process.communicate()
                error_msg = stderr.decode() if stderr else ""

                # 如果是参数错误且有备用方案，则重试
                error_indicators = [
                    "unknown option '--stdio'",
                    "too many arguments",
                    "Expected 0 arguments but got",
                    "unexpected argument",
                ]

                if (
                    any(indicator in error_msg for indicator in error_indicators)
                    and not run_command
                ):
                    # 重新构建命令（仅包含包名）
                    runtime_type = runtime_info["runtime_type"]
                    runtime_path = runtime_info["runtime_path"]
                    if runtime_type == "npx":
                        fallback_cmd = [runtime_path, "-y", package_name]
                    else:  # uvx
                        fallback_cmd = [runtime_path, package_name]

                    process = subprocess.Popen(fallback_cmd, **popen_kwargs)
                    time.sleep(2)
                else:
                    msg = f"MCP服务器启动失败: {error_msg}"
                    raise Exception(msg)

            return process

        except Exception:
            return None

    def deploy_package(
        self,
        package_name: str,
        timeout: int = 30,
        run_command: str | None = None,
        github_url: str | None = None,
    ) -> SimpleMCPServerInfo | None:
        """部署MCP包.

        Args:
            package_name: 包名（仅在run_command为空时使用）
            timeout: 超时时间
            run_command: 完整的运行命令（优先使用，来自CSV数据）
            github_url: GitHub URL（用于智能运行时检测）

        """
        if not package_name and not run_command:
            return None

        # 如果提供了GitHub URL，尝试智能检测运行时
        if github_url and not run_command:
            runtime_type, runtime_cmd = self.detect_simple_platform(github_url)

            # 构建基于GitHub URL的运行命令
            if runtime_type == "uvx" and "/uv-" in github_url:
                # 从GitHub URL中提取包名或使用--from参数
                if package_name:
                    run_command = f"uvx {package_name}"
                else:
                    run_command = f"uvx --from git+{github_url} mcp-server"
            elif runtime_type == "npx":
                run_command = f"npx -y {package_name}" if package_name else None

        # 获取运行时信息
        runtime_info = self._get_runtime_info(run_command, package_name)
        display_name = runtime_info["display_name"]
        runtime_type = runtime_info["runtime_type"]

        server_id = f"mcp_{uuid.uuid4().hex[:8]}"

        try:
            # 检查运行时环境
            if not runtime_info["available"]:
                if runtime_type == "uvx":
                    msg = "uvx不可用，请先安装uv: curl -LsSf https://astral.sh/uv/install.sh | sh"
                    raise Exception(msg)
                msg = "npx不可用，请先安装Node.js"
                raise Exception(msg)

            runtime_path = runtime_info["runtime_path"]

            # 构建启动命令
            cmd = self._build_runtime_command(runtime_info, run_command, package_name)

            # 启动MCP服务器进程
            creation_flags = 0
            if self.platform_info["system"] == "Windows":
                creation_flags = subprocess.CREATE_NO_WINDOW

            process = self._try_start_process(
                cmd,
                creation_flags,
                display_name,
                run_command,
                package_name,
                runtime_info,
            )
            if not process:
                return None

            # 创建通信器
            communicator = SimpleMCPCommunicator(process)
            time.sleep(1)

            # 初始化MCP协议
            available_tools = self._initialize_mcp_protocol(
                communicator,
                package_name,
                timeout,
            )

            # 创建服务器信息
            server_info = SimpleMCPServerInfo(
                package_name=package_name,
                process=process,
                communicator=communicator,
                server_id=server_id,
                available_tools=available_tools,
                status="running",
                start_time=time.time(),
            )

            # 保存到活动服务器列表
            self.active_servers[server_id] = server_info

            return server_info

        except Exception:
            if "process" in locals():
                with contextlib.suppress(Exception):
                    process.terminate()
            return None

    def _initialize_mcp_protocol(
        self,
        communicator: SimpleMCPCommunicator,
        package_name: str,
        timeout: int,
    ) -> list[dict[str, Any]]:
        """初始化MCP协议并获取工具列表."""
        # 1. Initialize请求 (移除可选字段以增强兼容性)
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "simple-mcp-client", "version": "0.1.0"},
            },
        }

        init_result = communicator.send_request(init_request, timeout=timeout)
        if not init_result["success"]:
            # 尝试更简化的初始化

            simple_init_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {"protocolVersion": "2024-11-05"},
            }

            init_result = communicator.send_request(
                simple_init_request,
                timeout=timeout,
            )
            if not init_result["success"]:
                msg = f"MCP初始化失败: {init_result['error']}"
                raise Exception(msg)

        # 2. Initialized通知 (MCP协议要求此通知不能有params字段)
        init_notification = {"jsonrpc": "2.0", "method": "notifications/initialized"}
        communicator.send_notification(init_notification)

        # 3. 获取工具列表 (某些MCP工具不需要params字段)
        tools_request = {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}
        tools_result = communicator.send_request(tools_request, timeout=timeout)
        if tools_result["success"] and "data" in tools_result:
            tools_data = tools_result["data"]
            if isinstance(tools_data, dict) and "result" in tools_data:
                return tools_data["result"].get("tools", [])

        msg = "获取工具列表失败"
        raise Exception(msg)

    def cleanup_server(self, server_id: str) -> bool:
        """清理指定的服务器."""
        if server_id not in self.active_servers:
            return False

        server_info = self.active_servers[server_id]

        try:
            server_info.process.terminate()
            server_info.process.wait(timeout=5)
        except Exception:
            pass

        # 从活动列表中移除
        del self.active_servers[server_id]
        return True

    def cleanup_all(self) -> None:
        """清理所有服务器."""
        server_ids = list(self.active_servers.keys())
        for server_id in server_ids:
            self.cleanup_server(server_id)


# 全局部署器实例
_simple_deployer_instance = None


def get_simple_mcp_deployer() -> SimpleMCPDeployer:
    """获取全局简化MCP部署器实例."""
    global _simple_deployer_instance
    if _simple_deployer_instance is None:
        _simple_deployer_instance = SimpleMCPDeployer()
    return _simple_deployer_instance
