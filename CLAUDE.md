# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Environment

This is a Python 3.12+ project using UV as the package manager. The project is a comprehensive MCP (Model Context Protocol) testing framework that can automatically deploy, test, and evaluate MCP tools from GitHub repositories.

### Key Dependencies
- **UV**: Modern Python package management
- **Python 3.12+**: Required minimum version
- **Node.js 18+**: Required for deploying MCP tools via npm/npx
- **Supabase**: Database integration for test results

## Common Commands

### Environment Setup
```bash
# Install dependencies
uv sync

# Development mode with additional dev dependencies
uv sync --dev

# Environment validation
uv run python -m src.main init-env
```

### Testing
```bash
# Run all tests
uv run pytest

# Run unit tests only
uv run pytest tests/unit/ -v

# Run integration tests (excluding slow ones)
uv run pytest tests/integration/ -v -m "not slow"

# Run with coverage
uv run pytest tests/unit/ -v --tb=short --cov=src --cov-report=xml
```

### Code Quality
```bash
# Run pre-commit hooks
uv run pre-commit run --all-files --show-diff-on-failure

# Type checking
uv run mypy src/ --ignore-missing-imports --no-strict-optional

# Security checks
uv run bandit -r src/ -f json -o bandit-report.json

# Dependency vulnerability check
uv run safety check --json --output safety-report.json
```

### Running the Framework
```bash
# Test a GitHub URL (default: AI smart testing, database export, evaluation enabled)
uv run python -m src.main test-url "https://github.com/upstash/context7"

# Test with specific options
uv run python -m src.main test-url "https://github.com/upstash/context7" --no-smart --no-db-export --no-evaluate

# Test a package directly
uv run python -m src.main test-package "@upstash/context7-mcp"

# List available tools
uv run python -m src.main list-tools --limit 10

# Search for specific tools
uv run python -m src.main list-tools --search "github"
```

## Architecture Overview

### Core Components

1. **src/main.py**: CLI entry point using Typer for command-line interface
2. **src/core/**: Core testing framework modules
   - `simple_mcp_deployer.py`: Handles MCP tool deployment via npm/npx, pip, cargo, etc.
   - `async_mcp_client.py`: JSON-RPC over STDIO client for MCP protocol communication
   - `url_mcp_processor.py`: GitHub URL to MCP package mapping and processing
   - `tester.py`: Core test execution logic
   - `evaluator.py`: GitHub repository analysis and quality scoring
   - `report_generator.py`: Test report generation (JSON/HTML)
   - `github_mcp_analyzer.py`: GitHub repository analysis

3. **src/agents/**: AI-powered intelligent testing
   - `test_agent.py`: AI agent for generating test cases
   - `validation_agent.py`: AI agent for test validation and analysis

4. **src/utils/**: Utilities and helpers
   - `csv_parser.py`: MCP tool database parsing (5000+ tools)
   - `config_loader.py`: Configuration and environment management

### Data Flow
1. **Input**: GitHub URL → URL processor extracts MCP package info
2. **Deployment**: Deployer installs MCP tool using appropriate package manager
3. **Communication**: Async client establishes JSON-RPC connection
4. **Testing**: Basic protocol tests + AI-generated intelligent test cases
5. **Evaluation**: Optional repository quality scoring and analysis
6. **Reporting**: JSON/HTML reports + optional Supabase database export

### Key Features
- **Smart Testing**: AI generates targeted test cases for each MCP tool
- **Multi-language Support**: Handles Node.js (npx), Python (pip/uvx), Rust (cargo), Docker
- **Protocol Compliance**: MCP STDIO protocol with automatic parameter adaptation
- **Quality Evaluation**: GitHub repository analysis with sustainability and popularity scoring
- **Database Integration**: Supabase for test result storage and historical tracking

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
- **code-quality.yml**: Automated code quality checks

### Runtime Requirements
The workflows require specific runtime validation. Use the verification script:
```bash
uv run python scripts/verify_action_runtime.py
```

## Important Notes

### Path Handling
The framework handles both local development and GitHub Actions environments. When running in GitHub Actions, ensure all file paths are relative to avoid absolute path issues.

### Database Integration
The Supabase integration uses a single-table design for tracking test results with comprehensive metadata including quality scores, test outcomes, and environment information.

### AI Testing
Smart testing requires either OpenAI or DashScope API keys. The AI agents analyze tool functionality and generate targeted test cases for comprehensive validation.
