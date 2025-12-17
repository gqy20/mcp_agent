# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

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

### Additional Development Commands
```bash
# Code formatting
uv run black src/ tests/

# Import sorting
uv run isort src/ tests/

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
uv run python -m src.main test-package "@upstash/context7-mcp" --no-evaluate

# Batch testing with parallel execution
uv run python -m src.main test-batch --parallel 4
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

# Analyze GitHub project and update MCP table
uv run python -m src.main analyze-github "https://github.com/example/repo"
```

## Architecture Overview

### Project Philosophy
The framework follows Linus Torvalds' programming philosophy: "Good taste" in code design. Key principles:
- **Simplicity**: Small, focused functions with clear responsibilities
- **Modularity**: Each component has a single, well-defined purpose
- **Taste**: Code should be obvious, readable, and elegant
- **No nested abstractions**: Flat structure is preferred over deep hierarchies

### Core Components

1. **src/main.py**: Minimal CLI entry point (Linus style - < 100 lines)
   - Uses Typer for command-line interface
   - Each command function is a thin wrapper (no business logic)
   - Follows Unix philosophy: do one thing well

2. **src/core/**: Core testing framework modules
   - `simple_mcp_deployer.py`: Universal MCP tool deployment (npx/pip/cargo/docker)
   - `async_mcp_client.py`: Async JSON-RPC STDIO client with robust error handling
   - `url_mcp_processor.py`: GitHub URL → MCP package mapping with fallback strategies
   - `tester.py`: Test orchestration with parallel execution support
   - `evaluator.py`: Multi-dimensional quality scoring (GitHub metrics + code analysis)
   - `report_generator.py`: Multi-format reports (JSON/HTML/PDF/Word/PowerPoint)
   - `github_mcp_analyzer.py`: Repository analysis with LobeHub integration
   - `cli_handlers.py`: Command handlers with comprehensive argument validation

3. **src/agents/**: AI-powered intelligent testing
   - `test_agent.py`: Generates targeted test cases based on tool description
   - `validation_agent.py`: Validates test results and provides intelligent analysis

4. **src/utils/**: Utilities and helpers
   - `csv_parser.py`: Parses MCP tool database (5000+ tools from various sources)
   - `config_loader.py`: Manages environment variables and configuration with validation
   - `lobe_hub_client.py`: LobeHub API integration for tool ratings and metadata

### Data Flow

```
GitHub URL → Package Detection → Deployment → MCP Protocol → Testing → Analysis → Reports
     ↓              ↓                ↓            ↓          ↓         ↓        ↓
URL Processor  → Mapping Logic  → Npx/Pip/  → JSON-RPC  → Basic  → Quality → JSON/
   Fallbacks    Multiple Sources → Cargo/Docker → STDIO  → Protocol +  → Scoring → HTML/
                                                       AI Tests          → PDF/Word/PPT
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
   - Async JSON-RPC over STDIO implementation
   - Robust error handling and timeout management
   - Automatic protocol version negotiation

4. **Testing Strategy**:
   - **Basic Tests**: Protocol compliance (initialize, tools list, call)
   - **Smart Tests**: AI-generated 3-5 targeted test cases
   - **Error Scenarios**: Invalid parameters, missing fields, edge cases

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
- **code-quality.yml**: Automated code quality checks

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
