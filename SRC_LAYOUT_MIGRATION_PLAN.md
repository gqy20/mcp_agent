# 🚀 Src Layout 重组实施方案

## 📋 项目概述

**目标包名：** `batch_mcp`
**重构策略：** 最小化风险，通过包名文件夹实现标准src layout

### 📊 影响范围分析

**主要统计：**
- **src目录Python文件：** 18个文件，7638行代码
- **最大文件：** `src/core/cli_handlers.py` (911行)
- **需要更新导入的文件：** 约20个文件

**受影响的文件类型：**
1. **内部导入** - `src/tools/setup_validator.py`
2. **外部导入** - 17个测试和工具文件
3. **配置文件** - `pyproject.toml`
4. **文档文件** - README.md, CLAUDE.md等

## 🎯 目标结构

### 变更前后对比

**当前结构：**
```
src/
├── __init__.py
├── __main__.py
├── main.py
├── agents/
├── core/
├── utils/
└── tools/
```

**目标结构：**
```
src/
├── batch_mcp/
│   ├── __init__.py
│   ├── __main__.py
│   ├── main.py
│   ├── agents/
│   ├── core/
│   ├── utils/
│   └── tools/
└── __init__.py
```

## 🔧 实施步骤

### 第一阶段：准备工作 (30分钟)

#### 1.1 环境验证
- [ ] 检查当前工作目录状态
- [ ] 确保所有更改已提交
- [ ] 创建backup分支
- [ ] 验证测试通过

```bash
git status
git add .
git commit -m "feat: 准备src layout重组 - 备份当前状态"
git checkout -b src-layout-migration
pytest tests/unit/ -v
```

#### 1.2 工具准备
- [ ] 创建路径更新脚本
- [ ] 创建验证脚本
- [ ] 准备回滚方案

### 第二阶段：文件迁移 (45分钟)

#### 2.1 创建包结构
```bash
# 创建包目录
mkdir -p src/batch_mcp

# 创建包__init__.py
touch src/batch_mcp/__init__.py
```

#### 2.2 迁移核心文件
```bash
# 移动主要文件
mv src/__main__.py src/batch_mcp/
mv src/main.py src/batch_mcp/

# 移动模块目录
mv src/agents src/batch_mcp/
mv src/core src/batch_mcp/
mv src/utils src/batch_mcp/
mv src/tools src/batch_mcp/
```

#### 2.3 更新包信息
```python
# src/batch_mcp/__init__.py
__version__ = "0.1.0"
__author__ = "AI Assistant"
__email__ = "ai@example.com"

# 导出主要类和函数
from .main import app
from .core.tester import MCPTester
from .core.deployer import SimpleMCPDeployer
```

### 第三阶段：路径更新 (60分钟)

#### 3.1 更新pyproject.toml
```toml
[project]
name = "batch-mcp"
# ... 其他配置保持不变

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src.batch_mcp"]

[project.scripts]
batch-mcp = "batch_mcp.main:app"
```

#### 3.2 更新内部导入路径
**需要更新的文件：**
- `src/batch_mcp/tools/setup_validator.py`

**路径变更示例：**
```python
# 更新前
from core.async_mcp_client import AsyncMCPClient
from utils.csv_parser import MCPDataParser

# 更新后
from batch_mcp.core.async_mcp_client import AsyncMCPClient
from batch_mcp.utils.csv_parser import MCPDataParser
```

#### 3.3 更新外部导入路径
**需要更新的文件（17个）：**

**脚本文件：**
- `scripts/update_csv_package_names.py`
- `scripts/select_simple_tools.py`

**测试文件：**
- `tests/unit/utils/test_utils.py`
- `tests/unit/agents/test_agents.py`
- `tests/unit/core/test_*`
- `tests/integration/test_*`

**工具文件：**
- `tools/show_comprehensive_scores.py`
- `tools/fix_comprehensive_scores.py`
- `tools/export_comprehensive_scores.py`

**路径变更示例：**
```python
# 更新前
from src.utils.csv_parser import MCPDataParser
from src.core.tester import MCPTester

# 更新后
from src.batch_mcp.utils.csv_parser import MCPDataParser
from src.batch_mcp.core.tester import MCPTester
```

### 第四阶段：配置更新 (30分钟)

#### 4.1 更新CLI入口点
```python
# src/batch_mcp/__main__.py
if __name__ == "__main__":
    from batch_mcp.main import app
    app()
```

#### 4.2 更新文档
**需要更新的文档：**
- `README.md` - 更新安装和使用说明
- `CLAUDE.md` - 更新开发指导
- `.pre-commit-config.yaml` - 更新文件路径

#### 4.3 更新脚本调用
```bash
# 新的调用方式
uv run python -m src.batch_mcp test-url "https://github.com/example/mcp-tool"

# 或者直接调用包
uv run python -c "from src.batch_mcp.main import app; app()"
```

### 第五阶段：测试验证 (30分钟)

#### 5.1 单元测试
```bash
# 运行核心模块测试
pytest tests/unit/ -v

# 运行集成测试
pytest tests/integration/ -v

# 验证导入
python -c "from src.batch_mcp.core.tester import MCPTester; print('✅ 导入成功')"
```

#### 5.2 CLI测试
```bash
# 测试基本命令
uv run python -m src.batch_mcp --help
uv run python -m src.batch_mcp list-tools --limit 5
```

#### 5.3 功能测试
```bash
# 测试核心功能
uv run python -m src.batch_mcp test-package "@upstash/context7-mcp" --no-smart --no-db-export --no-evaluate
```

## 🛠️ 自动化工具

### 路径更新脚本
```python
#!/usr/bin/env python3
"""
自动化路径更新脚本
"""
import os
import re
from pathlib import Path

def update_imports_in_file(file_path: Path) -> int:
    """更新单个文件的导入路径"""
    if not file_path.exists():
        return 0

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content

    # 更新from导入
    content = re.sub(
        r'from (core|agents|utils|tools)\.',
        r'from batch_mcp.\1.',
        content
    )

    # 更新直接导入
    content = re.sub(
        r'import (core|agents|utils|tools)\.',
        r'import batch_mcp.\1.',
        content
    )

    # 更新src路径导入
    content = re.sub(
        r'from src\.(core|agents|utils|tools)',
        r'from src.batch_mcp.\1',
        content
    )

    if content != original:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return 1

    return 0

def update_all_imports(root_dir: str = "."):
    """批量更新所有Python文件的导入路径"""
    updated_count = 0

    for file_path in Path(root_dir).rglob("*.py"):
        if "__pycache__" in str(file_path):
            continue

        updated = update_imports_in_file(file_path)
        updated_count += updated

        if updated:
            print(f"✅ 更新: {file_path}")

    print(f"\n总计更新文件数: {updated_count}")
    return updated_count

if __name__ == "__main__":
    update_all_imports()
```

### 验证脚本
```python
#!/usr/bin/env python3
"""
验证脚本 - 检查迁移后的功能完整性
"""
import sys
from pathlib import Path

def verify_imports():
    """验证关键导入"""
    test_imports = [
        "from src.batch_mcp.core.tester import MCPTester",
        "from src.batch_mcp.agents.test_agent import TestAgent",
        "from src.batch_mcp.utils.csv_parser import MCPDataParser",
        "from src.batch_mcp.core.deployer import SimpleMCPDeployer",
    ]

    failed_imports = []
    for import_stmt in test_imports:
        try:
            exec(import_stmt)
            print(f"✅ {import_stmt}")
        except ImportError as e:
            failed_imports.append((import_stmt, str(e)))

    if failed_imports:
        print(f"\n❌ 导入失败的文件 ({len(failed_imports)}个):")
        for import_stmt, error in failed_imports:
            print(f"  - {import_stmt}: {error}")
        return False

    print(f"\n✅ 所有核心导入测试通过 ({len(test_imports)}个)")
    return True

def verify_file_structure():
    """验证文件结构"""
    required_files = [
        "src/batch_mcp/__init__.py",
        "src/batch_mcp/__main__.py",
        "src/batch_mcp/main.py",
        "src/batch_mcp/core/__init__.py",
        "src/batch_mcp/agents/__init__.py",
        "src/batch_mcp/utils/__init__.py",
        "src/batch_mcp/tools/__init__.py",
    ]

    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)

    if missing_files:
        print(f"❌ 缺失文件 ({len(missing_files)}个):")
        for file_path in missing_files:
            print(f"  - {file_path}")
        return False

    print(f"✅ 所有必需文件存在 ({len(required_files)}个)")
    return True

if __name__ == "__main__":
    print("🔍 开始验证src layout迁移...")

    structure_ok = verify_file_structure()
    imports_ok = verify_imports()

    if structure_ok and imports_ok:
        print("\n🎉 验证全部通过！")
        sys.exit(0)
    else:
        print("\n❌ 验证失败，请检查上述问题")
        sys.exit(1)
```

## 🔄 回滚方案

### 快速回滚
```bash
# 如果遇到问题，快速回滚
git checkout main
git branch -D src-layout-migration
```

### 完整回滚步骤
1. 恢复原始结构
2. 恢复原始配置
3. 验证功能正常
4. 删除实验分支

## 📈 预期效果

### 使用方式变化
```bash
# 当前方式
uv run python -m src test-url "https://github.com/example/mcp-tool"

# 新方式
uv run python -m src.batch_mcp test-url "https://github.com/example/mcp-tool"
```

### Python导入变化
```python
# 当前方式
from src.core.tester import MCPTester

# 新方式
from src.batch_mcp.core.tester import MCPTester
```

### 包安装后的使用
```python
# 安装包后
from batch_mcp.core.tester import MCPTester
from batch_mcp.agents.test_agent import TestAgent
```

## ⚠️ 风险控制

### 风险点
1. **路径更新遗漏** - 使用自动化脚本减少遗漏
2. **测试失败** - 分阶段验证，及时发现和修复
3. **文档不同步** - 最后统一更新文档

### 风险缓解
1. **分支隔离** - 在独立分支进行所有操作
2. **自动化验证** - 提供完整的验证脚本
3. **分阶段实施** - 分步验证，逐步推进
4. **完整回滚方案** - 确保可以快速恢复

## 📅 时间安排

- **总预计时间：** 3-4小时
- **第一阶段：** 30分钟 (准备)
- **第二阶段：** 45分钟 (文件迁移)
- **第三阶段：** 60分钟 (路径更新)
- **第四阶段：** 30分钟 (配置更新)
- **第五阶段：** 30分钟 (测试验证)
- **缓冲时间：** 30分钟 (问题处理)

## ✅ 完成标准

### 必须满足
- [ ] 所有测试通过
- [ ] CLI命令正常工作
- [ ] 包结构符合Python标准
- [ ] 文档更新完成
- [ ] 回滚方案验证

### 期望效果
- [ ] 导入路径清晰明确
- [ ] 包名简洁易记 (`batch_mcp`)
- [ ] 支持pip安装和分发
- [ ] 符合Python包结构最佳实践

---

*制定时间：2025年12月17日*
*预计完成时间：2025年12月17日*
