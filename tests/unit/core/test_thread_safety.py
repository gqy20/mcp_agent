"""测试线程安全性.

这些测试确保：
1. 全局单例在多线程环境下安全
2. 没有竞态条件
3. 双重检查锁定正确实现
"""

import threading
from concurrent.futures import ThreadPoolExecutor, as_completed


class TestConfigThreadSafety:
    """测试 config.py 的线程安全性."""

    def test_get_config_has_lock(self):
        """验证 get_config 使用锁来保护全局变量."""
        import inspect  # noqa: PLC0415

        from src.batch_mcp.core.config import get_config  # noqa: PLC0415

        # 检查函数源代码中是否有锁相关的代码
        source = inspect.getsource(get_config)

        # 应该有 threading.Lock 或类似机制
        # 这个测试会失败，因为当前实现没有锁
        has_lock = "Lock" in source or "threading" in source
        assert has_lock, "get_config 应该使用锁来保护全局变量"

    def test_get_config_is_threadsafe(self):
        """验证 get_config 在多线程环境下是安全的."""
        # 使用多个线程同时获取配置
        results = []
        exceptions = []

        def get_config_multiple_times():
            try:
                from src.batch_mcp.core.config import get_config  # noqa: PLC0415

                for _ in range(10):
                    config = get_config()
                    results.append(id(config))
            except Exception as e:  # noqa: BLE001
                exceptions.append(e)

        # 启动 10 个线程
        threads = []
        for _ in range(10):
            t = threading.Thread(target=get_config_multiple_times)
            threads.append(t)
            t.start()

        # 等待所有线程完成
        for t in threads:
            t.join()

        # 检查：没有异常
        assert len(exceptions) == 0, f"发现异常: {exceptions}"

        # 检查：所有获取的配置对象应该是同一个实例
        unique_ids = set(results)
        assert len(unique_ids) == 1, f"预期1个唯一实例，实际发现 {len(unique_ids)} 个"

    def test_concurrent_config_access(self):
        """验证并发访问配置时不会产生竞态条件."""
        from src.batch_mcp.core.config import get_config, reset_config  # noqa: PLC0415

        # 重置配置
        reset_config()

        seen_configs = []
        lock = threading.Lock()

        def access_config():
            config = get_config()
            with lock:
                seen_configs.append(id(config))

        # 使用线程池模拟高并发
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(access_config) for _ in range(50)]
            for future in as_completed(futures):
                future.result()  # 确保没有异常

        # 所有配置应该是同一个实例
        unique_ids = set(seen_configs)
        assert len(unique_ids) == 1, f"预期1个实例，发现 {len(unique_ids)} 个"


class TestCSVParserThreadSafety:
    """测试 csv_parser.py 的线程安全性."""

    def test_get_mcp_parser_has_lock(self):
        """验证 get_mcp_parser 使用锁来保护全局变量."""
        import inspect  # noqa: PLC0415

        from src.batch_mcp.utils.csv_parser import get_mcp_parser  # noqa: PLC0415

        # 检查函数源代码中是否有锁相关的代码
        source = inspect.getsource(get_mcp_parser)

        # 应该有 threading.Lock 或类似机制
        # 这个测试会失败，因为当前实现没有锁
        has_lock = "Lock" in source or "threading" in source
        assert has_lock, "get_mcp_parser 应该使用锁来保护全局变量"

    def test_get_mcp_parser_is_threadsafe(self):
        """验证 get_mcp_parser 在多线程环境下是安全的."""
        results = []
        exceptions = []

        def get_parser_multiple_times():
            try:
                from src.batch_mcp.utils.csv_parser import (  # noqa: PLC0415
                    get_mcp_parser,
                )

                for _ in range(10):
                    parser = get_mcp_parser()
                    results.append(id(parser))
            except Exception as e:  # noqa: BLE001
                exceptions.append(e)

        # 启动 10 个线程
        threads = []
        for _ in range(10):
            t = threading.Thread(target=get_parser_multiple_times)
            threads.append(t)
            t.start()

        # 等待所有线程完成
        for t in threads:
            t.join()

        # 检查：没有异常
        assert len(exceptions) == 0, f"发现异常: {exceptions}"

        # 检查：所有获取的解析器对象应该是同一个实例
        unique_ids = set(results)
        assert len(unique_ids) == 1, f"预期1个唯一实例，实际发现 {len(unique_ids)} 个"

    def test_concurrent_parser_access(self):
        """验证并发访问解析器时不会产生竞态条件."""
        from src.batch_mcp.utils.csv_parser import get_mcp_parser  # noqa: PLC0415

        seen_parsers = []
        lock = threading.Lock()

        def access_parser():
            parser = get_mcp_parser()
            with lock:
                seen_parsers.append(id(parser))

        # 使用线程池模拟高并发
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(access_parser) for _ in range(50)]
            for future in as_completed(futures):
                future.result()  # 确保没有异常

        # 所有解析器应该是同一个实例
        unique_ids = set(seen_parsers)
        assert len(unique_ids) == 1, f"预期1个实例，发现 {len(unique_ids)} 个"

    def test_parser_data_integrity_under_concurrency(self):
        """验证并发访问时解析器数据完整性."""
        from src.batch_mcp.utils.csv_parser import get_mcp_parser  # noqa: PLC0415

        tool_counts = []
        exceptions = []

        def load_and_count():
            try:
                parser = get_mcp_parser()
                tools = parser.get_all_tools()
                tool_counts.append(len(tools))
            except Exception as e:  # noqa: BLE001
                exceptions.append(e)

        # 并发加载数据
        threads = []
        for _ in range(20):
            t = threading.Thread(target=load_and_count)
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # 检查：没有异常
        assert len(exceptions) == 0, f"发现异常: {exceptions}"

        # 检查：所有线程应该获取相同数量的工具
        unique_counts = set(tool_counts)
        assert len(unique_counts) == 1, f"预期一致的工具数量，发现: {unique_counts}"
