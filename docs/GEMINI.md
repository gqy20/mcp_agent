# GEMINI.md

## Project Overview

This project is a testing framework for MCP (Model Context Protocol) tools. It is a Python application that provides a command-line interface (CLI) for testing MCP tools from GitHub URLs or package names. The framework is designed to be automated and intelligent, with features like AI-powered test case generation, automatic deployment of MCP tools, and detailed report generation. It also integrates with a Supabase database for storing and analyzing test results.

The project is well-structured, with a clear separation of concerns. The main components include:

*   **CLI:** Built with Typer, it provides a user-friendly interface for interacting with the framework.
*   **Core Logic:** Handles the main workflow of testing, including URL parsing, tool deployment, test execution, and report generation.
*   **AI Agents:** Utilizes AI models (like GPT-4o or DashScope) to generate intelligent test cases and analyze results.
*   **Database Integration:** Stores test results in a Supabase database for historical tracking and analysis.
*   **Utilities:** Provides helper functions for tasks like CSV parsing and configuration loading.

## Building and Running

The project uses `uv` for package management. Here are the key commands for building and running the project:

**1. Installation:**

```bash
# Clone the repository
git clone <repository-url>
cd mcp_agent

# Install dependencies using uv
uv sync
```

**2. Running Tests:**

The main entry point for the application is `src/main.py`. You can use the following commands to run tests:

*   **Test a single GitHub MCP project:**
    ```bash
    uv run python -m src.main test-url "https://github.com/upstash/context7" --smart
    ```
*   **Test and export to the database:**
    ```bash
    uv run python -m src.main test-url "https://github.com/upstash/context7" --smart --db-export
    ```
*   **Test a package directly:**
    ```bash
    uv run python -m src.main test-package "@upstash/context7-mcp"
    ```
*   **Batch test from a CSV file:**
    ```bash
    uv run python -m src.main batch-test --input data/test.csv
    ```

**3. Development:**

*   **Install development dependencies:**
    ```bash
    uv sync --dev
    ```
*   **Run unit tests:**
    ```bash
    uv run pytest
    ```
*   **Format code:**
    ```bash
    uv run black src/
    ```

## Development Conventions

*   **Code Style:** The project follows the Black code style.
*   **Testing:** The project uses pytest for unit testing. Tests are located in the `test/` directory.
*   **Modularity:** The code is organized into modules with specific responsibilities, promoting maintainability and reusability.
*   **Configuration:** The project uses a `.env` file for managing environment variables, such as API keys and database credentials.
*   **Command-Line Interface:** The CLI is built with Typer, providing a clean and consistent interface.
*   **Error Handling:** The application includes robust error handling to provide informative messages to the user.
