#!/bin/bash

# Src Layout 迁移脚本
# 将 src/ 下的文件迁移到 src/batch_mcp/

set -e  # 遇到错误立即退出

echo "🚀 开始Src Layout迁移..."
echo "目标包名: batch_mcp"

# 预色输出函数
print_step() {
    echo -e "\n📍 $1"
    echo "----------------------------------------"
}

print_warning() {
    echo -e "\n⚠️  $1"
}

print_success() {
    echo -e "\n✅ $1"
}

# 检查当前状态
check_current_state() {
    print_step "检查当前状态"

    if [ ! -d "src" ]; then
        echo "❌ 错误: src目录不存在"
        exit 1
    fi

    if [ -d "src/batch_mcp" ]; then
        echo "❌ 错误: src/batch_mcp目录已存在"
        exit 1
    fi

    # 检查git状态
    if [ -n "$(git status --porcelain)" ]; then
        print_warning "检测到未提交的更改，建议先提交或保存"
        echo -n "是否继续？(y/N): "
        read -r response
        if [[ ! $response =~ ^[Yy]$ ]]; then
            echo "取消迁移"
            exit 0
        fi
    fi

    print_success "当前状态检查通过"
}

# 创建备份分支
create_backup() {
    print_step "创建备份分支"

    branch_name="src-layout-migration-$(date +%Y%m%d-%H%M%S)"
    git checkout -b "$branch_name"

    print_success "备份分支: $branch_name"
}

# 创建新的包结构
create_package_structure() {
    print_step "创建新的包结构"

    # 创建包目录
    mkdir -p src/batch_mcp
    mkdir -p src/batch_mcp/{agents,core,utils,tools}

    # 创建__init__.py文件
    cat > src/batch_mcp/__init__.py << 'EOF'
"""Batch MCP - 批量MCP工具测试框架

一个用于自动部署、测试和评估Model Context Protocol (MCP)工具的综合框架。

作者: AI Assistant <ai@example.com>
版本: 0.1.0
"""

__version__ = "0.1.0"
__author__ = "AI Assistant"
__email__ = "ai@example.com"

# 导出主要接口
__all__ = [
    "app",
    "MCPTester",
    "SimpleMCPDeployer",
    "AsyncMCPClient",
    "URLMCPProcessor",
    "Evaluator"
]

try:
    from .main import app
    from .core.tester import MCPTester
    from .core.simple_mcp_deployer import SimpleMCPDeployer
    from .core.async_mcp_client import AsyncMCPClient
    from .core.url_mcp_processor import URLMCPProcessor
    from .core.evaluator import Evaluator
except ImportError as e:
    # 如果导入失败，可能是模块还没有迁移完成
    print(f"警告: 无法导入主要模块: {e}")
EOF

    print_success "包结构创建完成"
}

# 迁移核心文件
migrate_files() {
    print_step "迁移核心文件"

    # 迁移主要文件
    echo "移动主文件..."
    mv src/__main__.py src/batch_mcp/
    mv src/main.py src/batch_mcp/

    # 迁移模块目录
    echo "移动模块目录..."
    mv src/agents src/batch_mcp/
    mv src/core src/batch_mcp/
    mv src/utils src/batch_mcp/
    mv src/tools src/batch_mcp/

    # 验证文件迁移
    echo "验证文件迁移..."
    required_dirs=(
        "src/batch_mcp/agents"
        "src/batch_mcp/core"
        "src/batch_mcp/utils"
        "src/batch_mcp/tools"
    )

    for dir in "${required_dirs[@]}"; do
        if [ -d "$dir" ]; then
            echo "✅ $dir"
        else
            echo "❌ $dir (缺失)"
            exit 1
        fi
    done

    required_files=(
        "src/batch_mcp/__init__.py"
        "src/batch_mcp/__main__.py"
        "src/batch_mcp/main.py"
        "src/batch_mcp/agents/__init__.py"
        "src/batch_mcp/core/__init__.py"
        "src/batch_mcp/utils/__init__.py"
        "src/batch_mcp/tools/__init__.py"
    )

    for file in "${required_files[@]}"; do
        if [ -f "$file" ]; then
            echo "✅ $file"
        else
            echo "❌ $file (缺失)"
            exit 1
        fi
    done

    print_success "文件迁移完成"
}

# 更新配置文件
update_configuration() {
    print_step "更新配置文件"

    # 更新pyproject.toml
    if [ -f "pyproject.toml" ]; then
        echo "更新pyproject.toml..."

        # 备份原文件
        cp pyproject.toml pyproject.toml.backup

        # 更新包配置
        sed -i 's/packages = \["src"\]/packages = ["src.batch_mcp"]/g' pyproject.toml
        sed -i 's/batch-mcp = "src.main:app"/batch-mcp = "batch_mcp.main:app"/g' pyproject.toml

        # 添加build系统配置（如果不存在）
        if ! grep -q "build-backend" pyproject.toml; then
            cat >> pyproject.toml << 'EOF'

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src.batch_mcp"]
EOF
        fi

        print_success "pyproject.toml更新完成"
    else
        print_warning "pyproject.toml不存在，跳过更新"
    fi

    # 更新.pre-commit-config.yaml
    if [ -f ".pre-commit-config.yaml" ]; then
        echo "更新.pre-commit-config.yaml..."

        # 备份原文件
        cp .pre-commit-config.yaml .pre-commit-config.yaml.backup

        # 更新路径配置
        sed -i 's|- src/|- src.batch_mcp/|g' .pre-commit-config.yaml
        sed -i 's|- src/|- src.batch_mcp/|g' .pre-commit-config.yaml

        print_success ".pre-commit-config.yaml更新完成"
    fi
}

# 更新导入路径
update_import_paths() {
    print_step "更新导入路径"

    echo "运行自动化导入路径更新脚本..."

    if [ -f "scripts/migrate_imports.py" ]; then
        uv run python scripts/migrate_imports.py
        print_success "导入路径更新完成"
    else
        print_warning "自动化更新脚本不存在，需要手动更新"
    fi
}

# 验证迁移结果
verify_migration() {
    print_step "验证迁移结果"

    if [ -f "scripts/verify_migration.py" ]; then
        echo "运行验证脚本..."
        uv run python scripts/verify_migration.py

        if [ $? -eq 0 ]; then
            print_success "迁移验证通过！"
        else
            print_warning "迁移验证失败，请检查上述问题"
        fi
    else
        print_warning "验证脚本不存在，请手动验证"
    fi
}

# 提供回滚选项
offer_rollback() {
    echo -e "\n🔄 发现验证问题，是否回滚？(y/N): "
    read -r response

    if [[ $response =~ ^[Yy]$ ]]; then
        echo "执行回滚..."

        # 删除新结构
        rm -rf src/batch_mcp

        # 恢复原始结构
        git checkout HEAD -- src/

        # 恢复配置文件
        if [ -f "pyproject.toml.backup" ]; then
            mv pyproject.toml.backup pyproject.toml
        fi

        if [ -f ".pre-commit-config.yaml.backup" ]; then
            mv .pre-commit-config.yaml.backup .pre-commit-config.yaml
        fi

        print_success "回滚完成"
        exit 0
    else
        print_warning "继续使用当前状态，请手动修复问题"
    fi
}

# 主函数
main() {
    echo -e "\n🎯 目标包名: batch_mcp"
    echo "⏱️  预计时间: 3-4分钟"

    check_current_state
    create_backup
    create_package_structure
    migrate_files
    update_configuration
    update_import_paths
    verify_migration

    echo -e "\n🎉 Src Layout迁移完成！"
    echo -e "\n📋 下一步操作:"
    echo "1. 运行测试验证功能: uv run pytest tests/unit/ -v"
    echo "2. 测试CLI命令: uv run python -m src.batch_mcp --help"
    echo "3. 提交更改: git add . && git commit -m 'feat: 实现src layout，包名batch_mcp'"
    echo -e "\n🚀 新的CLI调用方式:"
    echo "   uv run python -m src.batch_mcp test-url \"https://github.com/example/mcp-tool\""

    # 检查是否需要回滚
    if [ $? -ne 0 ]; then
        offer_rollback
    fi
}

# 错误处理
trap 'print_error "迁移过程中发生错误，请检查上述输出"; exit 1' ERR

print_error() {
    echo -e "\n❌ $1"
    echo -e "\n💡 可能的解决方案:"
    echo "   1. 检查git状态和权限"
    echo "   2. 确保没有其他进程占用文件"
    echo "   3. 手动恢复文件并重试"
}

# 执行主函数
main "$@"