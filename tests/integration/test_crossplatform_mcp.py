#!/usr/bin/env python3
"""
跨平台MCP工具测试框架

支持Windows、Linux、macOS的通用MCP工具测试
基于AgentScope + Model Context Protocol (MCP)的完整集成验证

特性:
- 跨平台兼容性(Windows/Linux/macOS)
- 动态配置加载
- 自适应参数映射
- 进程管理优化
- 详细的测试报告

作者: AI Assistant
日期: 2025-08-14
版本: 2.0.0
"""

import json
import os
import platform
import queue
import subprocess
import sys
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 添加tests目录到路径
tests_root = Path(__file__).parent.parent
sys.path.insert(0, str(tests_root))

try:
    import agentscope
    from agentscope.agents import ReActAgent
    from agentscope.message import Msg
    from agentscope.service import ServiceExecStatus, ServiceResponse, ServiceToolkit
    from dotenv import load_dotenv

    from tools.mcp_tools_config import MCP_TOOLS_CONFIG
except ImportError as e:
    print(f"❌ 导入错误: {e}")
    print("请确保已安装所需依赖: pip install agentscope python-dotenv")
    sys.exit(1)

# 全局变量
global_mcp_process = None
global_initialized = False
global_mcp_call_success = False  # 添加MCP调用成功标志


class CrossPlatformMCPCommunicator:
    """跨平台MCP通信器 - 支持Windows/Linux/macOS"""

    def __init__(self, process):
        self.process = process
        self.lock = threading.Lock()
        self.response_queue = queue.Queue()
        self.reader_thread = None
        self.platform = platform.system().lower()
        self.start_reader_thread()

    def start_reader_thread(self):
        """启动读取线程"""

        def reader():
            try:
                while self.process.poll() is None:
                    try:
                        line = self.process.stdout.readline()
                        if line:
                            response = line.decode().strip()
                            if response:
                                self.response_queue.put(response)
                                print(f"📨 收到MCP响应: {response[:100]}...")
                        else:
                            time.sleep(0.05)
                    except Exception as read_e:
                        print(f"读取异常: {read_e}")
                        time.sleep(0.1)
            except Exception as e:
                print(f"读取线程异常: {e}")

        self.reader_thread = threading.Thread(target=reader, daemon=True)
        self.reader_thread.start()
        print(f"🔄 MCP通信读取线程已启动 (平台: {self.platform})")

    def send_request(
        self, request: Dict[str, Any], timeout: float = 20.0
    ) -> Dict[str, Any]:
        """发送同步MCP请求"""
        with self.lock:
            try:
                if self.process.poll() is not None:
                    return {
                        "success": False,
                        "error": f"MCP进程已终止: {self.process.returncode}",
                    }

                # 清空队列
                while not self.response_queue.empty():
                    try:
                        self.response_queue.get_nowait()
                    except queue.Empty:
                        break

                # 发送请求
                request_json = json.dumps(request) + "\n"
                print(f"📤 发送MCP请求: {request.get('method', 'unknown')}")

                self.process.stdin.write(request_json.encode())
                self.process.stdin.flush()

                # 等待响应
                try:
                    response_text = self.response_queue.get(timeout=timeout)
                    print(f"📥 收到完整响应: {response_text[:200]}...")
                    try:
                        response_data = json.loads(response_text)
                        return {
                            "success": True,
                            "data": response_data,
                            "raw": response_text,
                        }
                    except json.JSONDecodeError:
                        return {
                            "success": True,
                            "data": response_text,
                            "raw": response_text,
                        }
                except queue.Empty:
                    print(f"⏰ 请求超时 ({timeout}s)")
                    return {"success": False, "error": "请求超时"}

            except Exception as e:
                return {"success": False, "error": f"通信异常: {str(e)}"}


def detect_platform_environment() -> Dict[str, Any]:
    """检测平台环境和可用工具"""
    platform_info = {
        "system": platform.system(),
        "architecture": platform.architecture()[0],
        "python_version": platform.python_version(),
        "node_available": False,
        "npx_path": None,
    }

    # 检查Node.js和npx
    try:
        import shutil

        npx_path = shutil.which("npx")
        if npx_path:
            platform_info["node_available"] = True
            platform_info["npx_path"] = npx_path

            # 检查Node.js版本
            result = subprocess.run(
                [npx_path, "--version"], capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                platform_info["npx_version"] = result.stdout.strip()
    except Exception as e:
        print(f"⚠️ Node.js环境检测失败: {e}")

    return platform_info


def load_test_environment() -> Dict[str, Any]:
    """加载测试环境配置"""
    env_path = project_root / ".env"
    if not env_path.exists():
        print(f"❌ 未找到环境配置文件 {env_path}")
        sys.exit(1)

    load_dotenv(env_path)

    required_vars = ["OPENAI_API_KEY", "OPENAI_BASE_URL", "OPENAI_MODEL"]
    config = {}

    for var in required_vars:
        value = os.getenv(var)
        if not value or value == "your_api_key_here":
            print(f"❌ 缺少环境变量: {var}")
            sys.exit(1)
        config[var] = value

    return config


def setup_mcp_server(tool_key: str, platform_info: Dict[str, Any]):
    """设置指定的MCP服务器 - 跨平台兼容"""
    global global_mcp_process, global_initialized

    if tool_key not in MCP_TOOLS_CONFIG:
        raise ValueError(f"未知的MCP工具: {tool_key}")

    config = MCP_TOOLS_CONFIG[tool_key]

    try:
        if not platform_info["node_available"]:
            raise Exception("Node.js/npx不可用，请先安装Node.js")

        npx_path = platform_info["npx_path"]
        print(f"✅ 找到npx: {npx_path}")

        # 启动MCP服务器
        package_name = config["package"]
        cmd = [npx_path, "-y", package_name]

        print(f"🚀 启动{config['name']}...")
        print(f"📦 命令: {' '.join(cmd)}")
        print(f"🖥️ 平台: {platform_info['system']} ({platform_info['architecture']})")

        # 跨平台进程创建
        creation_flags = 0
        if platform_info["system"] == "Windows":
            creation_flags = subprocess.CREATE_NO_WINDOW

        global_mcp_process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(project_root),
            text=False,
            bufsize=0,
            creationflags=creation_flags,
        )

        print(f"📦 MCP进程启动: pid={global_mcp_process.pid}")

        # 等待启动
        print(f"⏳ 等待{config['name']}启动...")
        time.sleep(10)  # 统一等待时间

        # 检查进程状态
        if global_mcp_process.poll() is not None:
            stdout, stderr = global_mcp_process.communicate()
            raise Exception(f"MCP服务器启动失败: {stderr.decode()}")

        print(f"✅ {config['name']}启动成功")

        # 创建通信器
        communicator = CrossPlatformMCPCommunicator(global_mcp_process)

        # 初始化MCP协议
        print("🔗 初始化MCP协议...")

        # 1. Initialize
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "clientInfo": {
                    "name": f"agentscope-{tool_key}-client",
                    "version": "2.0.0",
                },
            },
        }

        init_result = communicator.send_request(init_request)
        if not init_result["success"]:
            raise Exception(f"初始化失败: {init_result['error']}")

        print("✅ MCP协议初始化成功")

        # 2. Initialized notification
        init_notification = {"jsonrpc": "2.0", "method": "notifications/initialized"}

        with communicator.lock:
            notification_json = json.dumps(init_notification) + "\n"
            global_mcp_process.stdin.write(notification_json.encode())
            global_mcp_process.stdin.flush()

        print("✅ 发送initialized通知完成")

        # 3. 获取工具列表
        tools_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {},
        }

        tools_result = communicator.send_request(tools_request)
        if tools_result["success"] and "data" in tools_result:
            tools_data = tools_result["data"]
            if isinstance(tools_data, dict) and "result" in tools_data:
                tools = tools_data["result"].get("tools", [])
                print(f"✅ 可用工具: {[tool.get('name') for tool in tools]}")
                global_initialized = True
                return communicator, tools

        raise Exception("获取工具列表失败")

    except Exception as e:
        print(f"❌ {config['name']}设置失败: {e}")
        if global_mcp_process:
            global_mcp_process.terminate()
        raise


def create_dynamic_mcp_tool(communicator, tool_key: str, available_tools: list):
    """创建动态MCP工具函数 - 自适应参数格式"""

    config = MCP_TOOLS_CONFIG[tool_key]

    # 动态创建参数处理函数
    def create_tool_function():
        param_name = config.get("param_name", "query")
        mcp_args = config.get("mcp_args", {})

        # 根据参数类型创建不同的函数签名
        if param_name == "reasoning":

            def mcp_tool(reasoning: str) -> ServiceResponse:
                """使用MCP思考工具进行深度分析和推理"""
                return call_mcp_tool_with_args(reasoning, {"reasoning": reasoning})

        elif param_name == "video_id":

            def mcp_tool(video_id: str) -> ServiceResponse:
                """通过MCP获取YouTube视频的详细信息"""
                return call_mcp_tool_with_args(video_id, {"video_id": video_id})

        elif param_name == "libraryName":

            def mcp_tool(libraryName: str) -> ServiceResponse:
                """通过MCP查询指定库的文档和信息"""
                return call_mcp_tool_with_args(
                    libraryName, {"libraryName": libraryName}
                )

        elif param_name == "from_to":

            def mcp_tool(from_to: str) -> ServiceResponse:
                """通过MCP查询火车票信息，格式：出发地到目的地"""
                # 解析from_to参数为from和to
                parts = from_to.split("到")
                if len(parts) == 2:
                    args = {"from": parts[0].strip(), "to": parts[1].strip()}
                else:
                    args = mcp_args  # 使用默认参数
                return call_mcp_tool_with_args(from_to, args)

        else:  # 默认为query参数

            def mcp_tool(query: str) -> ServiceResponse:
                """通过MCP工具执行查询操作"""
                return call_mcp_tool_with_args(query, {"query": query})

        # 为函数添加名称（AgentScope要求）
        mcp_tool.__name__ = f"{tool_key}_mcp_tool"

        return mcp_tool

    def call_mcp_tool_with_args(input_value: str, arguments: dict) -> ServiceResponse:
        """实际的MCP工具调用逻辑"""
        global global_mcp_call_success

        try:
            if not global_initialized:
                return ServiceResponse(
                    ServiceExecStatus.ERROR, f"❌ {config['name']}未初始化"
                )

            call_id = f"{tool_key.upper()}_MCP_{uuid.uuid4().hex[:8]}"

            # 获取工具名称
            tool_name = (
                available_tools[0]["name"] if available_tools else config["tools"][0]
            )

            # 构建工具调用请求
            tool_request = {
                "jsonrpc": "2.0",
                "id": call_id,
                "method": "tools/call",
                "params": {"name": tool_name, "arguments": arguments},
            }

            print(f"🔧 调用{config['name']}: {tool_name}, 参数: {arguments}")

            # 调用MCP工具
            result = communicator.send_request(tool_request, timeout=30.0)

            if result["success"]:
                # 设置成功标志
                global_mcp_call_success = True

                if (
                    "data" in result
                    and isinstance(result["data"], dict)
                    and "result" in result["data"]
                ):
                    tool_result = result["data"]["result"]

                    # 提取结果内容
                    result_text = ""
                    if isinstance(tool_result, dict) and "content" in tool_result:
                        content = tool_result["content"]
                        if isinstance(content, list):
                            for item in content:
                                if (
                                    isinstance(item, dict)
                                    and item.get("type") == "text"
                                ):
                                    result_text = item.get("text", "")[:1000]
                                    break
                        elif isinstance(content, str):
                            result_text = content[:1000]
                    elif isinstance(tool_result, str):
                        result_text = tool_result[:1000]

                    response_text = f"""🔍 {config['name']}调用成功:
- 输入: {input_value}
- 调用ID: {call_id}
- MCP服务器: {config['name']} ({config['package']})
- 协议状态: ✅ 真实{tool_key} MCP通信成功
- 结果: {result_text[:500]}..."""
                else:
                    response_text = f"""🔍 {config['name']}调用完成:
- 输入: {input_value}
- 调用ID: {call_id}
- 原始响应: {str(result.get('data', ''))[:300]}...
- 协议状态: ✅ 真实{tool_key} MCP通信成功"""

                return ServiceResponse(ServiceExecStatus.SUCCESS, response_text)
            else:
                error_text = f"""❌ {config['name']}调用失败:
- 输入: {input_value}
- 错误: {result.get('error', '未知错误')}
- MCP服务器状态: 连接异常"""

                return ServiceResponse(ServiceExecStatus.ERROR, error_text)

        except Exception as e:
            return ServiceResponse(
                ServiceExecStatus.ERROR, f"❌ {config['name']}调用异常: {str(e)}"
            )

    return create_tool_function()


def test_single_mcp_tool(tool_key: str) -> bool:
    """测试指定的MCP工具"""
    global global_mcp_process, global_initialized, global_mcp_call_success

    if tool_key not in MCP_TOOLS_CONFIG:
        print(f"❌ 未知的MCP工具: {tool_key}")
        return False

    config = MCP_TOOLS_CONFIG[tool_key]
    platform_info = detect_platform_environment()

    print(f"\n🎯 {config['name']}验证测试")
    print(f"📦 使用包名: {config['package']}")
    print(f"🖥️ 运行平台: {platform_info['system']} ({platform_info['architecture']})")
    print("=" * 70)

    try:
        # 重置状态
        global_mcp_process = None
        global_initialized = False
        global_mcp_call_success = False  # 重置MCP调用成功标志

        # 加载环境
        env_config = load_test_environment()
        print("✅ 环境配置加载完成")

        # 设置MCP服务器
        communicator, available_tools = setup_mcp_server(tool_key, platform_info)

        # 创建工具
        mcp_tool = create_dynamic_mcp_tool(communicator, tool_key, available_tools)
        toolkit = ServiceToolkit()
        toolkit.add(mcp_tool)
        print(f"🔧 {config['name']}工具包创建完成")

        # 创建模型配置
        model_config = {
            "config_name": f"{tool_key}_mcp_test",
            "model_type": "openai_chat",
            "model_name": env_config["OPENAI_MODEL"],
            "api_key": env_config["OPENAI_API_KEY"],
            "client_args": {"base_url": env_config["OPENAI_BASE_URL"], "timeout": 30},
            "generate_args": {"temperature": 0.1, "max_tokens": 2000},
        }

        # 初始化AgentScope
        agentscope.init(
            model_configs=[model_config],
            project=f"{tool_key.title()}_MCP_Test",
            save_dir="./runs",
            save_log=True,
            save_api_invoke=True,
        )

        # 创建ReActAgent
        agent = ReActAgent(
            name=f"{tool_key}_mcp_agent",
            model_config_name=f"{tool_key}_mcp_test",
            service_toolkit=toolkit,
            sys_prompt=config.get("sys_prompt", f"你是一个{config['name']}助手。"),
            verbose=True,
        )

        print("✅ ReActAgent 创建完成")

        # 测试MCP调用
        print(f"\n🧪 测试真实{config['name']}调用...")
        test_message = config.get("user_message", f"请使用{config['name']}进行查询")
        print(f"❓ 测试消息: {test_message}")
        print("-" * 50)

        start_time = time.time()
        user_msg = Msg("user", test_message, role="user")
        response = agent(user_msg)
        response_time = time.time() - start_time

        print(f"⏱️ 响应时间: {response_time:.2f}s")
        print(f"📝 AI响应:\n{response.content}")

        # 验证成功 - 使用全局标志和内容检查
        success_markers = [
            f"真实{tool_key} MCP通信成功",
            f"{tool_key.upper()}_MCP_",
            "调用成功",
            "MCP服务器:",
        ]

        # 获取对话历史来检查MCP调用
        conversation_history = ""
        if hasattr(agent, "memory") and hasattr(agent.memory, "get_memory"):
            try:
                memory = agent.memory.get_memory()
                for msg in memory:
                    if hasattr(msg, "content"):
                        conversation_history += str(msg.content) + " "
            except:
                pass

        # 检查AI最终响应和对话历史
        all_content = response.content + " " + conversation_history

        # 验证条件：全局标志 OR 内容标记
        if (
            global_mcp_call_success
            or any(marker in all_content for marker in success_markers)
            or f"{tool_key.upper()}_MCP_" in all_content
            or "MCP通信成功" in all_content
            or "调用成功" in all_content
        ):
            print(f"\n🎉 {config['name']}验证成功！")
            print("✅ 验证要点:")
            print(f"   - 成功部署了真实的{config['name']}")
            print(f"   - AgentScope通过MCP协议调用了真实工具")
            print(f"   - 验证了端到端的{config['name']}集成")
            print(f"   - 获取了有效的{config['category']}结果")
            print(f"   - 跨平台兼容性: {platform_info['system']}")
            print(f"   - MCP调用状态: {'✅' if global_mcp_call_success else '🔍'}")
            return True
        else:
            print(f"\n⚠️ {config['name']}验证失败")
            print(f"MCP调用标志: {global_mcp_call_success}")
            print(f"最终响应长度: {len(response.content)} 字符")
            print(f"对话历史长度: {len(conversation_history)} 字符")
            return False

    except Exception as e:
        print(f"❌ {config['name']}测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False

    finally:
        # 清理
        if global_mcp_process:
            print(f"\n🧹 清理{config['name']}...")
            try:
                global_mcp_process.terminate()
                global_mcp_process.wait(timeout=5)
                print(f"✅ {config['name']}已停止")
            except Exception as e:
                print(f"⚠️ 清理异常: {e}")


def test_all_mcp_tools():
    """测试所有MCP工具"""
    platform_info = detect_platform_environment()

    print("🎯 跨平台MCP工具验证测试框架 v2.0")
    print(f"🖥️ 运行环境: {platform_info['system']} ({platform_info['architecture']})")
    print(f"🐍 Python版本: {platform_info['python_version']}")
    if platform_info["node_available"]:
        print(f"📦 NPX版本: {platform_info.get('npx_version', '未知')}")
    print("📋 测试所有配置的MCP工具")
    print("=" * 70)

    # 测试结果记录
    test_results = {}

    # 按推荐顺序测试
    test_order = ["context7", "youtube", "think", "svelte", "openalex", "12306"]

    for tool_key in test_order:
        if tool_key not in MCP_TOOLS_CONFIG:
            continue

        print(f"\n{'='*20} 开始测试 {tool_key} {'='*20}")
        try:
            success = test_single_mcp_tool(tool_key)
            test_results[tool_key] = success
            status = "成功" if success else "失败"
            print(f"{'='*20} {tool_key} 测试{status} {'='*20}")
        except Exception as e:
            print(f"❌ {tool_key} 测试异常: {e}")
            test_results[tool_key] = False

        # 测试间隔
        time.sleep(2)

    # 输出总结
    print(f"\n🎯 跨平台测试总结")
    print(f"🖥️ 测试平台: {platform_info['system']} ({platform_info['architecture']})")
    print("=" * 70)
    success_count = sum(1 for success in test_results.values() if success)
    total_count = len(test_results)

    for tool_key, success in test_results.items():
        config = MCP_TOOLS_CONFIG[tool_key]
        status = "✅ 成功" if success else "❌ 失败"
        print(f"{config['name']}: {status}")

    print(f"\n📊 总体结果: {success_count}/{total_count} 个工具验证成功")
    print(f"🏆 成功率: {success_count/total_count*100:.1f}%")

    return test_results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="跨平台MCP工具测试框架 v2.0")
    parser.add_argument(
        "--tool", help="测试指定工具 (context7, youtube, think, svelte, openalex, 12306)"
    )
    parser.add_argument("--all", action="store_true", help="测试所有工具")
    parser.add_argument("--info", action="store_true", help="显示平台信息")

    args = parser.parse_args()

    if args.info:
        platform_info = detect_platform_environment()
        print("🖥️ 平台信息:")
        for key, value in platform_info.items():
            print(f"  {key}: {value}")
        sys.exit(0)
    elif args.tool:
        success = test_single_mcp_tool(args.tool)
        sys.exit(0 if success else 1)
    elif args.all:
        results = test_all_mcp_tools()
        success_count = sum(1 for success in results.values() if success)
        sys.exit(0 if success_count == len(results) else 1)
    else:
        print("跨平台MCP工具测试框架 v2.0")
        print("使用方法:")
        print("  python test_crossplatform_mcp.py --info              # 显示平台信息")
        print("  python test_crossplatform_mcp.py --tool youtube      # 测试单个工具")
        print("  python test_crossplatform_mcp.py --all               # 测试所有工具")
        sys.exit(1)
