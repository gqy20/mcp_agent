"""MCP 分析器模式定义.

此模块包含所有用于识别和提取 MCP 项目信息的正则表达式模式。
"""

# MCP相关关键词
MCP_KEYWORDS = [
    "model context protocol",
    "mcp server",
    "mcp tool",
    "claude mcp",
    "anthropic mcp",
    "mcp integration",
    "mcp",
]

# 部署方式关键词
DEPLOYMENT_PATTERNS = {
    "npx": [
        r"npx\s+[@a-zA-Z0-9/-]+",
        r"npm install.*global",
        r"install.*-g",
        r"--global",
    ],
    "uvx": [r"uvx\s+[a-zA-Z0-9/-]+", r"pip install.*uvx", r"uv.*run"],
    "cargo": [
        r"cargo install.*--path",
        r"cargo build.*release",
        r"cargo install",
    ],
    "python": [r"python\s+-m\s+[a-zA-Z0-9_]+", r"pip install", r"pip3 install"],
    "docker": [r"docker run", r"docker build", r"container"],
}

# API密钥相关模式
API_KEY_PATTERNS = [
    r"API_KEY",
    r"API_TOKEN",
    r"SECRET_KEY",
    r"environment variable",
    r"env.*=.*YOUR",
    r"requires.*authentication",
    r"needs.*credentials",
]

# 技术栈模式
TECH_STACK_PATTERNS = {
    "python": [r"python", r"py", r"\.py$"],
    "nodejs": [r"node", r"javascript", r"js", r"typescript", r"ts", r"npm"],
    "rust": [r"rust", r"cargo", r"\.rs$"],
    "go": [r"go", r"golang"],
    "java": [r"java", r"maven", r"gradle"],
    "ruby": [r"ruby", r"gem"],
}

# 工具描述模式
TOOL_PATTERNS = [
    r"Tools:?\s*([^\n]+)",
    r"tools:?\s*([^\n]+)",
    r"Features:?\s*([^\n]+)",
    r"features:?\s*([^\n]+)",
    r"Capabilities:?\s*([^\n]+)",
    r"capabilities:?\s*([^\n]+)",
]

# 使用场景模式
USE_CASE_PATTERNS = [
    r"Use cases?:?\s*([^\n]+)",
    r"use cases?:?\s*([^\n]+)",
    r"Usage:?\s*([^\n]+)",
    r"usage:?\s*([^\n]+)",
    r"Applications:?\s*([^\n]+)",
    r"applications:?\s*([^\n]+)",
]

# 包名提取模式
NPX_PATTERNS = [
    r"npx\s+([@a-zA-Z0-9/-]+)",
    r"npm\s+install\s+(-g\s+|global\s+)?([@a-zA-Z0-9/-]+)",
    r"npm\s+i\s+(-g\s+|global\s+)?([@a-zA-Z0-9/-]+)",
]

UVX_PATTERNS = [
    r"uvx\s+([a-zA-Z0-9/-]+)",
    r"pip\s+install\s+([a-zA-Z0-9/-]+)",
    r"uv\s+run\s+([a-zA-Z0-9/-]+)",
]

CARGO_PATTERNS = [
    r"cargo\s+install\s+([a-zA-Z0-9_-]+)",
    r"cargo\s+build.*--path.*?/([a-zA-Z0-9_-]+)",
]

PYTHON_PATTERNS = [
    r"python\s+-m\s+([a-zA-Z0-9_]+)",
    r"pip\s+install\s+([a-zA-Z0-9_-]+)",
    r"pip3\s+install\s+([a-zA-Z0-9_-]+)",
]

TITLE_PATTERNS = [
    r"#\s*([a-zA-Z0-9_-]+)\s+(?:MCP|mcp|Server|server)",
    r"#\s*([a-zA-Z0-9_-]+)\s*",
    r"project\s*name[:：]\s*([a-zA-Z0-9_-]+)",
]

# 部署方法优先级
DEPLOYMENT_PRIORITY = ["uvx", "npx", "cargo", "python"]
