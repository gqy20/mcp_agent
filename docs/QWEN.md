# Qwen Code Context for `mcp_agent` Project

## Project Overview

This project is the **Batch MCP Testing Framework**, an automated system for testing Model Context Protocol (MCP) tools. Its main features include URL-driven testing, AI-powered smart testing, integration with LobeHub's tool quality scores, and detailed reporting.

- **Purpose**: To dynamically deploy, test, and evaluate MCP tools from various sources (primarily GitHub) and generate comprehensive reports.
- **Core Technologies**: Python 3.12+, Node.js (for deploying MCP tools via `npx`), `uv` (package manager), Supabase (optional database).
- **Architecture**: A Python CLI (`src/main.py`) drives the process. It uses a simplified MCP deployer (`src/core/simple_mcp_deployer.py`) to run tools, a tester (`src/core/tester.py`) to execute basic or smart tests, and generates reports (`src/core/report_generator.py`). It leverages a large local CSV database (`data/mcp.csv`) of MCP tools for metadata and deployment information.

## Key Files and Directories

- `src/main.py`: The main CLI entry point using `typer`. Commands include `test-url`, `test-package`, and `list-tools`.
- `src/core/simple_mcp_deployer.py`: Handles the deployment of MCP tools using `npx` or custom commands found in the CSV data. Manages the subprocess and basic STDIO communication.
- `src/core/tester.py`: Contains the core logic for testing deployed MCP tools, including basic connectivity and smart AI-driven tests.
- `src/core/cli_handlers.py`: Contains the logic for handling CLI commands, orchestrating the flow from input to report generation.
- `src/agents/`: (Not directly read, but inferred from `tester.py`) Contains the AI agents for smart testing if `agentscope` is available.
- `data/mcp.csv`: A large database (8400+ entries) of MCP tools with metadata like package names, deployment commands, and LobeHub scores.
- `pyproject.toml`: Project configuration for `uv`/`pip`, including dependencies and scripts.
- `README.md`: Detailed project documentation.

## Building, Running, and Testing

1.  **Setup**:
    - Ensure Python 3.12+ and Node.js 18+ are installed.
    - Install dependencies using `uv`: `uv sync` or `pip install -e .`.
2.  **Environment Configuration**:
    - Create a `.env` file with API keys for AI services (OpenAI/DashScope) and optionally Supabase for database export.
3.  **Running**:
    - Test a tool from a GitHub URL: `uv run python -m src.main test-url "https://github.com/upstash/context7"`
    - Test a tool by its NPM package name: `uv run python -m src.main test-package "@upstash/context7-mcp"`
    - List available tools: `uv run python -m src.main list-tools`
    - Enable smart AI testing with `--smart` and database export with `--db-export`.
4.  **Development**:
    - Install dev dependencies: `uv sync --dev`.
    - Run tests: `uv run pytest`.
    - Format code: `uv run black src/`.

## Development Conventions

- The codebase follows the "Linus Torvalds' good taste" principle, aiming for simplicity, minimal nesting, clear separation of concerns, and clean error handling.
- CLI commands in `main.py` are thin wrappers that delegate to handlers in `cli_handlers.py`.
- Core logic is encapsulated in classes like `MCPTester` and `SimpleMCPDeployer`.
- Dependencies are managed by `uv` and declared in `pyproject.toml`.
- Code formatting is handled by `black`.
