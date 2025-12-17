#!/usr/bin/env python3
"""自动修复常见的代码质量问题"""

import re
from pathlib import Path


def fix_unused_imports(file_path):
    """修复未使用的导入"""
    with open(file_path, encoding="utf-8") as f:
        content = f.read()

    # 常见的不必要导入
    patterns_to_remove = [
        r"^import asyncio$",  # 移除未使用的asyncio导入
        r"^from typing import.*Tuple.*$",  # 移除未使用的Tuple导入
        r"^from typing import.*Any.*$",  # 移除未使用的Any导入
        r"^import json$",  # 如果json被重新定义
    ]

    lines = content.split("\n")
    new_lines = []

    for line in lines:
        should_remove = False
        for pattern in patterns_to_remove:
            if re.match(pattern, line.strip()):
                should_remove = True
                break

        if not should_remove:
            new_lines.append(line)

    # 检查json是否被使用
    new_content = "\n".join(new_lines)
    if (
        "json." not in new_content
        and "json.loads" not in new_content
        and "json.dumps" not in new_content
    ):
        # 移除json导入
        new_lines = [line for line in new_lines if not line.strip() == "import json"]

    new_content = "\n".join(new_lines)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(new_content)


def fix_long_lines(file_path):
    """修复过长的代码行"""
    with open(file_path, encoding="utf-8") as f:
        content = f.read()

    lines = content.split("\n")
    new_lines = []

    for line in lines:
        if len(line) > 88 and 'f"' in line and "f'" in line:
            # 尝试分割长的f-string
            if 'f"' in line:
                # 找到f-string的位置
                f_string_start = line.find('f"')
                f_string_end = line.rfind('"')
                if f_string_start != -1 and f_string_end != -1:
                    f_string_content = line[f_string_start + 2 : f_string_end]
                    # 如果f-string中有多个变量，尝试分割
                    if '{"' in f_string_content and f_string_content.count("{") > 1:
                        # 简单的分割策略
                        parts = f_string_content.split(", ")
                        if len(parts) > 1:
                            indent = len(line) - len(line.lstrip())
                            new_line1 = line[:f_string_start] + 'f"' + parts[0] + '"'
                            new_line2 = " " * indent + 'f"' + ", ".join(parts[1:]) + '"'
                            new_lines.append(new_line1)
                            new_lines.append(new_line2)
                            continue

        new_lines.append(line)

    new_content = "\n".join(new_lines)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(new_content)


def fix_bare_excepts(file_path):
    """修复裸露的except子句"""
    with open(file_path, encoding="utf-8") as f:
        content = f.read()

    # 替换裸露的except
    content = re.sub(r"except:\s*$", "except Exception:", content, flags=re.MULTILINE)
    content = re.sub(
        r"except:\s*#", "except Exception:  #", content, flags=re.MULTILINE
    )

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)


def fix_missing_placeholders(file_path):
    """修复没有占位符的f-string"""
    with open(file_path, encoding="utf-8") as f:
        content = f.read()

    # 找到没有占位符的f-string
    lines = content.split("\n")
    new_lines = []

    for line in lines:
        if 'f"' in line and "{" not in line:
            # 移除f前缀
            line = line.replace('f"', '"')
        elif "f'" in line and "{" not in line:
            # 移除f前缀
            line = line.replace("f'", "'")

        new_lines.append(line)

    new_content = "\n".join(new_lines)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(new_content)


def main():
    """主函数"""
    src_dir = Path("src")

    for py_file in src_dir.rglob("*.py"):
        if py_file.name.startswith("test_"):  # 跳过测试文件
            continue

        print(f"处理文件: {py_file}")

        try:
            fix_unused_imports(py_file)
            fix_long_lines(py_file)
            fix_bare_excepts(py_file)
            fix_missing_placeholders(py_file)
            print(f"✅ 已修复: {py_file}")
        except Exception as e:
            print(f"❌ 修复失败: {py_file} - {e}")


if __name__ == "__main__":
    main()
