"""测试 CLI handlers 导入规范.

这些测试确保：
1. 所有导入在文件顶部（不在函数内部）
2. 没有重复的导入语句
3. 可选依赖有适当的处理
"""

import ast
import re
from collections import Counter
from pathlib import Path


class TestCLIHandlersImports:
    """测试 CLI handlers 导入规范."""

    def test_all_imports_at_top_level(self):
        """验证所有导入都在文件顶部."""
        file_path = Path("src/batch_mcp/core/cli_handlers.py")
        content = file_path.read_text()

        # 解析 Python 文件
        tree = ast.parse(content)

        # 找到所有 Import 和 ImportFrom 节点
        imports = [
            {
                "type": node.__class__.__name__,
                "line": node.lineno,
                "module": getattr(node, "module", None),
                "names": [alias.name for alias in node.names],
            }
            for node in ast.walk(tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
        ]

        # 检查是否有导入在函数内部（行号 > 100 通常表示在函数内）
        function_level_imports = [imp for imp in imports if imp["line"] >= 100]

        # 断言：不应该有函数级别的导入
        assert len(function_level_imports) == 0, (
            f"发现 {len(function_level_imports)} 个函数内导入，应移到文件顶部:\n"
            + "\n".join(
                f"  行 {imp['line']}: {imp['module']}" for imp in function_level_imports
            )
        )

    def test_no_duplicate_imports(self):
        """验证没有重复的导入."""
        file_path = Path("src/batch_mcp/core/cli_handlers.py")
        content = file_path.read_text()

        # 查找所有导入语句（完整的导入行，而不仅仅是前缀）
        import_pattern = r"^(from [^\s]+ import [^\n]+|import [^\n]+)"
        imports = re.findall(import_pattern, content, re.MULTILINE)

        # 统计每个导入的出现次数
        import_counts = Counter(imports)

        # 找出重复的导入
        duplicates = {imp: count for imp, count in import_counts.items() if count > 1}

        assert len(duplicates) == 0, "发现重复导入:\n" + "\n".join(
            f"  {imp}: {count} 次" for imp, count in duplicates.items()
        )

    def test_supabase_import_at_top(self):
        """验证 supabase 导入在文件顶部."""
        file_path = Path("src/batch_mcp/core/cli_handlers.py")
        content = file_path.read_text()

        # supabase 应该在顶部导入
        # 检查是否有 "from supabase import" 在文件的前 100 行
        first_100_lines = "\n".join(content.split("\n")[:100])

        # 验证 supabase 在顶部导入
        has_top_level_supabase = "from supabase import" in first_100_lines
        assert has_top_level_supabase, "supabase 应该在文件顶部导入"

    def test_module_can_be_imported(self):
        """验证模块可以被正常导入."""
        # 这确保即使有动态导入，模块也能正常工作
        try:
            from src.batch_mcp.core import cli_handlers  # noqa: PLC0415

            assert hasattr(cli_handlers, "CLIHandler")
        except ImportError as e:
            raise AssertionError(f"模块导入失败: {e}") from e
