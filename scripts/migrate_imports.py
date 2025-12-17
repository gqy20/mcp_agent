#!/usr/bin/env python3
"""自动化路径更新脚本 - src layout迁移专用

用于将 src/ 下的文件移动到 src/batch_mcp/ 后，批量更新所有导入路径。
"""

import re
import sys
from pathlib import Path


class ImportMigrator:
    """导入路径迁移器"""

    def __init__(self):
        self.updated_files = []
        self.failed_files = []
        self.total_updates = 0

        # 需要处理的导入模式
        self.patterns = [
            # from batch_mcp.core.xxx import Yyy -> from batch_mcp.core.xxx import Yyy
            (r"from\s+(core|agents|utils|tools)\.", r"from batch_mcp.\1."),
            # import batch_mcp.core.xxx -> import batch_mcp.core.xxx
            (r"import\s+(core|agents|utils|tools)\.", r"import batch_mcp.\1."),
            # from src.batch_mcp.core.xxx -> from src.batch_mcp.core.xxx
            (r"from\s+src\.(core|agents|utils|tools)", r"from src.batch_mcp.\1"),
            # relative imports inside the package
            (r"^from\s+\.\.?\s*(core|agents|utils|tools)\.", r"from batch_mcp.\1."),
        ]

    def update_file(self, file_path: Path) -> tuple[bool, int]:
        """更新单个文件中的导入路径

        Returns:
            (是否更新, 更新的数量)

        """
        if not file_path.exists() or not file_path.is_file():
            return (False, 0)

        if not file_path.suffix == ".py":
            return (False, 0)

        try:
            with open(file_path, encoding="utf-8") as f:
                original_content = f.read()

            content = original_content
            update_count = 0

            # 应用所有模式
            for pattern, replacement in self.patterns:
                new_content, count = re.subn(pattern, replacement, content)
                content = new_content
                update_count += count

            # 如果有更新，写回文件
            if content != original_content:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                return (True, update_count)

            return (False, 0)

        except Exception as e:
            print(f"❌ 处理文件失败 {file_path}: {e}")
            self.failed_files.append((str(file_path), str(e)))
            return (False, 0)

    def update_directory(self, directory: Path, recursive: bool = True) -> None:
        """更新目录中的所有Python文件"""
        if recursive:
            pattern = "**/*.py"
        else:
            pattern = "*.py"

        for file_path in directory.glob(pattern):
            # 跳过__pycache__目录
            if "__pycache__" in file_path.parts:
                continue

            updated, count = self.update_file(file_path)
            if updated:
                self.updated_files.append(file_path)
                self.total_updates += count
                print(f"✅ 更新: {file_path} ({count}个变更)")

    def update_external_files(self, root_dir: Path) -> None:
        """更新外部文件（scripts/, tests/, tools/）中的src导入"""
        external_dirs = ["scripts", "tests", "tools"]

        for dir_name in external_dirs:
            dir_path = root_dir / dir_name
            if dir_path.exists():
                print(f"\n🔄 更新 {dir_name}/ 目录...")
                self.update_directory(dir_path, recursive=True)

    def update_pyproject_toml(self, file_path: Path) -> bool:
        """更新pyproject.toml配置"""
        if not file_path.exists():
            print("⚠️  pyproject.toml 不存在，跳过更新")
            return False

        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            original = content

            # 更新packages配置
            content = re.sub(
                r'packages = \["src"\]', 'packages = ["src.batch_mcp"]', content
            )

            # 更新scripts配置
            content = re.sub(
                r'batch-mcp = "src.main:app"',
                'batch-mcp = "batch_mcp.main:app"',
                content,
            )

            # 添加build配置（如果不存在）
            if "build-backend" not in content:
                build_config = """
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src.batch_mcp"]
"""
                content += build_config

            if content != original:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                print(f"✅ 更新: {file_path}")
                return True

            return False

        except Exception as e:
            print(f"❌ 更新pyproject.toml失败: {e}")
            return False

    def print_summary(self) -> None:
        """打印更新摘要"""
        print("\n📊 迁移摘要:")
        print(f"✅ 更新文件数: {len(self.updated_files)}")
        print(f"🔄 总更新数: {self.total_updates}")

        if self.failed_files:
            print(f"❌ 失败文件数: {len(self.failed_files)}")
            for file_path, error in self.failed_files:
                print(f"  - {file_path}: {error}")


def main():
    """主函数"""
    root_dir = Path()

    print("🚀 开始批量更新导入路径...")
    print("📁 目标包名: batch_mcp")

    migrator = ImportMigrator()

    # 更新外部文件中的src导入
    migrator.update_external_files(root_dir)

    # 更新pyproject.toml
    pyproject_path = root_dir / "pyproject.toml"
    print("\n📝 更新配置文件...")
    migrator.update_pyproject_toml(pyproject_path)

    # 输出摘要
    migrator.print_summary()

    # 返回状态码
    if migrator.failed_files:
        print(f"\n⚠️  有 {len(migrator.failed_files)} 个文件处理失败")
        sys.exit(1)
    else:
        print("\n🎉 所有文件更新成功！")
        sys.exit(0)


if __name__ == "__main__":
    main()
