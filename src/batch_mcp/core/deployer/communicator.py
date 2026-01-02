"""MCP通信器模块.

此模块包含MCP STDIO协议的通信处理类。
"""

import json
import platform
import queue
import threading
import time
from typing import Any


class SimpleMCPCommunicator:
    """简化的MCP通信器."""

    def __init__(self, process) -> None:
        self.process = process
        self.lock = threading.Lock()
        self.response_queue = queue.Queue()
        self.reader_thread = None
        self.stderr_thread = None
        self.platform = platform.system().lower()
        # 流式缓冲区（二进制）
        self._buffer = bytearray()
        self.start_reader_thread()
        self.start_stderr_thread()

    def start_reader_thread(self) -> None:
        """启动读取线程."""

        def reader() -> None:
            try:
                stdout = self.process.stdout  # binary
                while self.process.poll() is None:
                    try:
                        chunk = stdout.read(1)
                        if not chunk:
                            time.sleep(0.01)
                            continue
                        self._buffer.extend(chunk)
                        # 解析可能到达的完整帧（Content-Length 格式）
                        while True:
                            msg = self._try_extract_message()
                            if msg is None:
                                break
                            self.response_queue.put(msg)
                            (msg[:100] + "...") if len(msg) > 100 else msg
                    except Exception:
                        time.sleep(0.02)
            except Exception:
                pass

        self.reader_thread = threading.Thread(target=reader, daemon=True)
        self.reader_thread.start()

    def start_stderr_thread(self) -> None:
        """读取并打印 stderr，辅助诊断."""

        def err_reader() -> None:
            try:
                stderr = self.process.stderr
                while self.process.poll() is None:
                    try:
                        line = stderr.readline()
                        if line:
                            try:
                                text = line.decode(errors="ignore").rstrip()
                            except Exception:
                                text = str(line)
                            if text:
                                # 限制单行长度，避免刷屏
                                pass
                        else:
                            time.sleep(0.02)
                    except Exception:
                        time.sleep(0.05)
            except Exception:
                pass

        self.stderr_thread = threading.Thread(target=err_reader, daemon=True)
        self.stderr_thread.start()

    def _try_extract_message(self) -> str | None:
        """从缓冲区解析一条换行符分隔的消息，返回解码后的 JSON 文本；无完整行返回 None."""
        try:
            buffer_str = self._buffer.decode("utf-8", errors="ignore")

            # 查找第一个换行符
            newline_pos = buffer_str.find("\n")
            if newline_pos == -1:
                return None

            # 提取消息内容（去除回车符）
            message_line = buffer_str[:newline_pos].rstrip("\r")

            # 更新缓冲区（移除已处理的消息）
            remaining = buffer_str[newline_pos + 1 :]
            self._buffer = bytearray(remaining.encode("utf-8"))

            # 返回非空行
            if message_line.strip():
                return message_line
            # 跳过空行，继续尝试解析下一行
            return self._try_extract_message() if remaining else None

        except Exception:
            return None

    def _write_json_frame(self, payload: dict[str, Any]) -> None:
        """发送JSON消息（MCP STDIO 协议：JSON + 换行符）."""
        json_str = json.dumps(payload, ensure_ascii=False)
        # MCP STDIO 协议使用简单的换行符分隔
        message = json_str + "\n"
        self.process.stdin.write(message.encode("utf-8"))
        self.process.stdin.flush()

    def send_notification(self, payload: dict[str, Any]) -> None:
        """发送 JSON-RPC 通知（换行符分隔）."""
        with self.lock:
            self._write_json_frame(payload)

    def send_request(
        self,
        request: dict[str, Any],
        timeout: float = 20.0,
    ) -> dict[str, Any]:
        """发送同步MCP请求."""
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

                # 发送请求（换行符分隔）
                self._write_json_frame(request)

                # 等待响应
                try:
                    response_text = self.response_queue.get(timeout=timeout)
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
                    return {"success": False, "error": "请求超时"}

            except Exception as e:
                return {"success": False, "error": f"通信异常: {e!s}"}
