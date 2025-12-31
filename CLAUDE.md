# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**📝 文档管理规则**: 不允许在主目录中随意增加md文件，所有文档应放在 docs/ 目录下。

## Development Environment

This is a Python 3.12+ project using UV as the package manager. The project is a comprehensive MCP (Model Context Protocol) testing framework that can automatically deploy, test, and evaluate MCP tools from GitHub repositories.

### Key Dependencies
- **UV**: Modern Python package management
- **Python 3.12+**: Required minimum version
- **Node.js 18+**: Required for deploying MCP tools via npm/npx
- **Supabase**: Database integration for test results

### Core Libraries
- **agentscope>=0.1.0**: AI agent framework for intelligent testing
- **openai>=1.0.0**: AI model integration
- **supabase>=2.0.0**: Database client for test results storage
- **typer>=0.9.0**: CLI framework for command-line interface
- **rich>=13.0.0**: Terminal output formatting and progress display
- **pandas>=2.2.0**: Data processing and analysis
- **reportlab>=4.4.3**: PDF report generation

## Common Commands

### Environment Setup
```bash
# Install dependencies
uv sync

# Development mode with additional dev dependencies
uv sync --dev

# Environment validation
uv run python -m src.batch_mcp init-env
```

### Testing
```bash
# Run all tests
uv run pytest

# Run unit tests only (fast)
uv run pytest tests/unit/ -v

# Run integration tests (medium speed)
uv run pytest tests/integration/ -v

# Run end-to-end tests (slow)
uv run pytest tests/e2e/ -v

# Run with coverage (HTML and terminal)
uv run pytest --cov=src --cov-report=html --cov-report=term

# Run specific test file
uv run pytest tests/unit/test_simple_mcp_deployer.py -v

# Run by marker (skip slow tests)
uv run pytest -m "not slow" -v

# Run only unit tests (by marker)
uv run pytest -m unit -v

# Run only integration tests (by marker)
uv run pytest -m integration -v
```

### Additional Development Commands
```bash
# Code formatting (Ruff - includes formatting, linting, and import sorting)
uv run ruff check src/ tests/
uv run ruff format src/ tests/

# Run pre-commit hooks
uv run pre-commit run --all-files --show-diff-on-failure

# Security audit
uv run bandit -r src/ -f json -o bandit-report.json

# Check for dependency vulnerabilities
uv run safety check --json --output safety-report.json

# Type checking
uv run mypy src/ --ignore-missing-imports --no-strict-optional

# Verify GitHub Actions runtime
uv run python scripts/verify_action_runtime.py

# Quick test mode (no evaluation)
uv run python -m src.batch_mcp test-package "@upstash/context7-mcp" --no-evaluate

# Test HTTP MCP endpoint
uv run python -m src.batch_mcp test-http http://localhost:8080/mcp

# Batch testing with parallel execution
uv run python -m src.batch_mcp test-batch --parallel 4
```


### Running the Framework
```bash
# Test a GitHub URL (default: AI smart testing, database export, evaluation enabled)
uv run python -m src.batch_mcp test-url "https://github.com/upstash/context7"

# Test with specific options
uv run python -m src.batch_mcp test-url "https://github.com/upstash/context7" --no-smart --no-db-export --no-evaluate

# Test a package directly
uv run python -m src.batch_mcp test-package "@upstash/context7-mcp"

# List available tools
uv run python -m src.batch_mcp list-tools --limit 10

# Search for specific tools
uv run python -m src.batch_mcp list-tools --search "github"

# Analyze GitHub project and update MCP table
uv run python -m src.batch_mcp analyze-github "https://github.com/example/repo"
```

## Architecture Overview

### Project Philosophy
The framework follows Linus Torvalds' programming philosophy: "Good taste" in code design. Key principles:
- **Simplicity**: Small, focused functions with clear responsibilities
- **Modularity**: Each component has a single, well-defined purpose
- **Taste**: Code should be obvious, readable, and elegant
- **No nested abstractions**: Flat structure is preferred over deep hierarchies

### Core Components

1. **src/batch_mcp/main.py**: Minimal CLI entry point (Linus style - < 100 lines)
   - Uses Typer for command-line interface
   - Each command function is a thin wrapper (no business logic)
   - Follows Unix philosophy: do one thing well

2. **src/batch_mcp/core/**: Core testing framework modules
   - `simple_mcp_deployer.py`: Universal MCP tool deployment (npx/pip/cargo/docker)
   - `async_mcp_client.py`: Async JSON-RPC STDIO client with robust error handling
   - `url_mcp_processor.py`: GitHub URL → MCP package mapping with fallback strategies
   - `tester.py`: Test orchestration with parallel execution support
   - `evaluator.py`: Multi-dimensional quality scoring (GitHub metrics + code analysis)
   - `report_generator.py`: Multi-format reports (JSON/HTML/PDF/Word/PowerPoint)
   - `github_mcp_analyzer.py`: Repository analysis with LobeHub integration
   - `cli_handlers.py`: Command handlers with comprehensive argument validation
   - `http_mcp_client.py`: HTTP MCP client for web-based MCP tools
   - `http_mcp_handler.py`: HTTP MCP request/response handler
   - `test_runner.py`: Unified test execution runner (supports both STDIO and HTTP)
   - `config.py`: Centralized configuration management with path handling
   - `error_handler.py`: Centralized error handling and classification
   - `database_exporter.py`: Supabase database export functionality
   - `input_type_detector.py`: Detects input type (URL, package, or HTTP endpoint)
   - `tool_finder.py`: Finds MCP tools in database by name or URL
   - `result_presenter.py`: Formats and presents test results
   - `mcp_table_updater.py`: Updates MCP tools database table

3. **src/batch_mcp/agents/**: AI-powered intelligent testing
   - `test_agent.py`: Generates targeted test cases based on tool description
   - `validation_agent.py`: Validates test results and provides intelligent analysis

4. **src/batch_mcp/utils/**: Utilities and helpers
   - `csv_parser.py`: Parses MCP tool database (5000+ tools from various sources)
   - `config_loader.py`: Manages environment variables and configuration with validation
   - `lobe_hub_client.py`: LobeHub API integration for tool ratings and metadata

5. **src/batch_mcp/tools/**: Utility scripts and tools
   - `setup_validator.py`: Environment validation and setup verification
   - `verify_database.py`: Database connection and data verification
   - `test_direct_db.py`: Direct database testing utilities

### Data Flow

```
GitHub URL → Package Detection → Deployment → MCP Protocol → Testing → Analysis → Reports
     ↓              ↓                ↓            ↓          ↓         ↓        ↓
URL Processor  → Mapping Logic  → Npx/Pip/  → JSON-RPC  → Basic  → Quality → JSON/
   Fallbacks    Multiple Sources → Cargo/Docker  STDIO  → Protocol +  → Scoring → HTML/
                                            (or HTTP)   AI Tests          → PDF/Word/PPT
```

1. **Input Processing**:
   - GitHub URL analysis with multiple fallback strategies
   - Direct package name support for known MCP tools
   - Integration with LobeHub database for metadata

2. **Deployment Phase**:
   - Automatic deployment method detection
   - Support for npx, pip/uvx, cargo, docker
   - Graceful fallback for unsupported tools

3. **Communication Layer**:
   - Async JSON-RPC over STDIO implementation (`async_mcp_client.py`)
   - HTTP MCP support (`http_mcp_client.py`, `http_mcp_handler.py`)
   - Robust error handling and timeout management
   - Automatic protocol version negotiation

4. **Testing Strategy**:
   - **Basic Tests**: Protocol compliance (initialize, tools list, call)
   - **Smart Tests**: AI-generated 3-5 targeted test cases
   - **Error Scenarios**: Invalid parameters, missing fields, edge cases
   - **Unified Runner**: `test_runner.py` handles both STDIO and HTTP MCP testing

5. **Analysis & Evaluation**:
   - GitHub repository metrics (stars, forks, issues, commits)
   - Code quality indicators (documentation, tests, CI/CD)
   - LobeHub community rating integration
   - Sustainability scoring (activity, maintenance)

6. **Output Generation**:
   - JSON: Machine-readable detailed results
   - HTML: Interactive visual reports
   - PDF/Word/PowerPoint: Executive summaries
   - Supabase: Historical data storage

### Key Features
- **Universal Deployment**: Supports all major package managers and Docker
- **AI-Powered Testing**: Intelligent test case generation based on tool functionality
- **Multi-Language Support**: Node.js, Python, Rust, Go, Java via package managers
- **Protocol Compliance**: Full MCP STDIO protocol support with parameter adaptation
- **Quality Evaluation**: Comprehensive scoring system using multiple data sources
- **Database Integration**: Supabase for persistent storage and trend analysis
- **LobeHub Integration**: Community ratings and metadata from LobeHub platform
- **Parallel Execution**: Batch testing with configurable parallelism

## Configuration

### Environment Variables
```bash
# AI Configuration (OpenAI or DashScope)
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o

# Alternative AI Configuration
DASHSCOPE_API_KEY=your_dashscope_key
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/api/v1
DASHSCOPE_MODEL=qwen-plus

# Supabase Database (optional)
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_supabase_key
```

### Default Parameters
From v2.1.0, these features are enabled by default:
- `--smart`: AI intelligent testing
- `--db-export`: Export to Supabase database
- `--evaluate`: Code quality evaluation

Use `--no-smart`, `--no-db-export`, `--no-evaluate` to disable them.

## GitHub Actions

### Workflows
- **single-mcp-test.yml**: Manual testing of individual MCP tools
- **parallel-stress-test.yml**: Batch testing with parallel execution
- **http-mcp-test.yml**: HTTP MCP endpoint testing
- **code-quality.yml**: Automated code quality checks
- **auto-release.yml**: Automatic release workflow

### Runtime Requirements
The workflows require specific runtime validation. Use the verification script:
```bash
uv run python scripts/verify_action_runtime.py
```

## Important Notes

### Current Limitations
1. **Local Clone Requirements**: Cannot test tools that need local repository cloning
2. **API Key Dependencies**: Tools requiring third-party API keys cannot be auto-tested
3. **Complex Configurations**: Limited support for tools with complex environment setup
4. **Technology Coverage**: Primarily supports Node.js, Python, Rust, Docker deployments

### Path Handling
The framework handles both local development and GitHub Actions environments. When running in GitHub Actions, ensure all file paths are relative to avoid absolute path issues.

### Database Design
Supabase uses a single-table design:
```sql
CREATE TABLE mcp_test_results (
    test_id UUID PRIMARY KEY,
    test_timestamp TIMESTAMP WITH TIME ZONE,
    tool_identifier TEXT NOT NULL,
    tool_name TEXT,
    tool_author TEXT,
    test_success BOOLEAN NOT NULL,
    deployment_success BOOLEAN NOT NULL,
    communication_success BOOLEAN NOT NULL,
    available_tools_count INTEGER,
    test_duration_seconds FLOAT,
    error_messages TEXT[],
    test_details JSONB,
    quality_score JSONB,
    environment_info JSONB,
    created_at TIMESTAMP WITH TIME ZONE
);
```

### AI Testing Requirements
Smart testing requires either OpenAI or DashScope API keys:
- **OpenAI**: `OPENAI_API_KEY`, `OPENAI_BASE_URL`, `OPENAI_MODEL` (default: gpt-4o)
- **DashScope**: `DASHSCOPE_API_KEY`, `DASHSCOPE_BASE_URL`, `DASHSCOPE_MODEL` (default: qwen-plus)

The AI agents perform:
- Tool functionality analysis
- Targeted test case generation (3-5 cases per tool)
- Result validation and intelligent feedback
- Error classification and reporting

## 🐛 调试和故障排除

### 常见问题解决方案

#### MCP 部署失败
```bash
# 检查 Node.js 版本
node --version

# 验证网络连接
ping github.com

# 启用详细日志
uv run python -m src.batch_mcp test-url <url> --verbose

# 清理临时文件
rm -rf data/temp/*
```

#### AI 测试失败
```bash
# 验证 API 密钥配置
echo $OPENAI_API_KEY

# 测试 AI 连接
uv run python -c "import openai; print('OpenAI client initialized')"

# 检查网络代理设置
echo $HTTP_PROXY
echo $HTTPS_PROXY
```

#### 数据库连接问题
```bash
# 验证 Supabase 连接
uv run python -m src.batch_mcp.tools.verify_database

# 测试数据库配置
uv run python -c "from supabase import create_client; print('Supabase client ready')"
```

### 调试命令
```bash
# 启用调试日志
uv run python -m src.batch_mcp test-url <url> --verbose

# 测试数据库连接
uv run python -m src.batch_mcp.tools.verify_database

# 验证环境配置
uv run python -m src.batch_mcp init-env

# 检查 GitHub Actions 运行时
uv run python scripts/verify_action_runtime.py
```

## 🌐 HTTP MCP 支持

框架支持通过 HTTP 协议测试 MCP 工具，适用于 Web 服务形式的 MCP 实现：

### HTTP MCP 测试
```bash
# 测试 HTTP MCP 端点
uv run python -m src.batch_mcp test-http http://localhost:8080/mcp

# 带认证的 HTTP MCP
uv run python -m src.batch_mcp test-http https://api.example.com/mcp --auth-token "your_token"
```

### HTTP vs STDIO MCP
- **STDIO MCP**: 通过标准输入输出通信，适用于命令行工具
- **HTTP MCP**: 通过 HTTP API 通信，适用于 Web 服务

## 🛠️ 实用工具脚本

项目包含多个实用脚本位于 `scripts/` 目录：

### 数据库工具
```bash
# 验证数据库完整性
uv run python scripts/verify_action_runtime.py

# GitHub 分析器演示
uv run python scripts/demo_github_analyzer.py

# 智能工具选择器
uv run python scripts/intelligent_tool_selector.py
```

### 开发工具
```bash
# 生成测试数据
uv run python scripts/generate_test_data.py

# 修复代码质量问题
uv run python scripts/fix_code_quality.py

# 更新 CSV 包名映射
uv run python scripts/update_csv_package_names.py
```

## ⚡ 性能优化建议

### 批量测试优化
```bash
# 控制并发数（推荐 2-4）
uv run python -m src.batch_mcp test-batch --parallel 3

# 限制单工具超时时间
uv run python -m src.batch_mcp test-url <url> --timeout 300

# 快速测试模式（禁用评估）
uv run python -m src.batch_mcp test-package <package> --no-evaluate
```

### 内存管理
```bash
# 清理临时文件
rm -rf data/temp/*

# 检查磁盘空间
df -h

# 监控进程资源
htop
```

## 开发规则

### GitHub 指令
项目遵循以下开发规则（定义在 `.github/instructions/main.instructions.md`）：

- **脚本长度限制**: 脚本不允许超过 500 行
- **测试入口**: 每次测试从 `main.py` 进入，不允许产生冗余的测试文件
- **环境管理**: 使用 UV 管理环境
- **配置管理**: 配置信息在 `.env` 文件中
- **数据保护**: 不要动 `data/` 文件夹的 CSV 文件

### 代码风格

项目使用 **Ruff** 作为统一的代码格式化和检查工具：
- **行长度**: 88 字符
- **引号风格**: 保留原样（preserve）
- **类型注解**: 允许 `Any` 类型，不要求 `self`/`cls` 类型注解
- **中文支持**: 忽略中文标点符号相关规则
