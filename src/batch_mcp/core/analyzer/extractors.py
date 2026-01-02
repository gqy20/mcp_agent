"""内容提取函数.

此模块提供从 README 内容中提取 MCP 项目信息的函数。
"""

import re

from .patterns import (
    API_KEY_PATTERNS,
    CARGO_PATTERNS,
    DEPLOYMENT_PATTERNS,
    DEPLOYMENT_PRIORITY,
    NPX_PATTERNS,
    PYTHON_PATTERNS,
    TECH_STACK_PATTERNS,
    TITLE_PATTERNS,
    TOOL_PATTERNS,
    USE_CASE_PATTERNS,
    UVX_PATTERNS,
)


def is_mcp_project(content: str, mcp_keywords: list[str]) -> bool:
    """检查是否为MCP项目.

    Args:
        content: README内容
        mcp_keywords: MCP关键词列表

    Returns:
        是否为MCP项目

    """
    content_lower = content.lower()

    # 检查MCP关键词
    for keyword in mcp_keywords:
        if keyword.lower() in content_lower:
            return True

    # 检查package.json中的依赖
    if "package.json" in content_lower:
        # 简单的package.json内容检查
        if '"@modelcontextprotocol' in content_lower or '"mcp' in content_lower:
            return True

    return False


def extract_description(content: str, repo_info: dict) -> str:
    """提取项目描述.

    Args:
        content: README内容
        repo_info: GitHub仓库信息

    Returns:
        项目描述字符串

    """
    # 优先使用GitHub描述
    if repo_info.get("description"):
        return repo_info["description"]

    # 从README中提取第一段
    lines = content.split("\n")
    description_lines = []

    for line in lines:
        line = line.strip()
        if line and not line.startswith("#"):
            # 跳过徽章和链接
            if not any(char in line for char in ["[", "]", "!", "<"]):
                description_lines.append(line)
                if len(description_lines) >= 2:
                    break

    return " ".join(description_lines) if description_lines else "MCP工具"


def extract_deployment_methods(content: str) -> list[str]:
    """提取部署方式.

    Args:
        content: README内容

    Returns:
        部署方式列表

    """
    methods = []
    content_lower = content.lower()

    for method, patterns in DEPLOYMENT_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, content_lower, re.IGNORECASE):
                methods.append(method)
                break

    return list(set(methods))


def check_api_key_requirement(content: str) -> bool:
    """检查是否需要API密钥.

    Args:
        content: README内容

    Returns:
        是否需要API密钥

    """
    content_lower = content.lower()

    for pattern in API_KEY_PATTERNS:
        if re.search(pattern, content_lower, re.IGNORECASE):
            return True

    return False


def extract_tech_stack(content: str) -> list[str]:
    """提取技术栈.

    Args:
        content: README内容

    Returns:
        技术栈列表

    """
    tech_stack = []
    content_lower = content.lower()

    for tech, patterns in TECH_STACK_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, content_lower, re.IGNORECASE):
                tech_stack.append(tech)
                break

    return list(set(tech_stack))


def extract_tools(content: str) -> list[str]:
    """提取工具列表.

    Args:
        content: README内容

    Returns:
        工具列表

    """
    tools = []

    for pattern in TOOL_PATTERNS:
        matches = re.findall(pattern, content, re.IGNORECASE)
        for match in matches:
            # 分割工具列表
            tool_items = re.split(r"[,;•\-\*]", match)
            tools.extend([item.strip() for item in tool_items if item.strip()])

    return list(set(tools))[:10]  # 限制工具数量


def extract_use_cases(content: str) -> list[str]:
    """提取使用场景.

    Args:
        content: README内容

    Returns:
        使用场景列表

    """
    use_cases = []

    for pattern in USE_CASE_PATTERNS:
        matches = re.findall(pattern, content, re.IGNORECASE)
        for match in matches:
            use_cases.append(match.strip())

    return list(set(use_cases))[:5]  # 限制使用场景数量


def extract_installation_instructions(content: str) -> str:
    """提取安装说明.

    Args:
        content: README内容

    Returns:
        安装说明字符串

    """
    lines = content.split("\n")
    install_section = False
    install_instructions = []

    for line in lines:
        line_lower = line.lower()
        if any(
            keyword in line_lower for keyword in ["install", "setup", "getting started"]
        ):
            install_section = True
        elif install_section and line.startswith("#"):
            break
        elif install_section and line.strip():
            install_instructions.append(line.strip())

    return "\n".join(install_instructions[:10]) if install_instructions else ""


def extract_package_info(
    content: str,
    deployment_methods: list[str],
) -> dict[str, str]:
    """从README内容中提取包名和部署命令.

    Args:
        content: README内容
        deployment_methods: 部署方式列表

    Returns:
        包含包名和命令的字典

    """
    package_info = {
        "package_name": "",
        "deployment_method": "",
        "install_command": "",
        "run_command": "",
    }

    if not deployment_methods:
        return package_info

    # 获取主要部署方法 - 优先选择uvx/npx而不是python
    primary_deployment = ""

    for method in DEPLOYMENT_PRIORITY:
        if method in deployment_methods:
            primary_deployment = method
            break

    # 如果没有找到优先方法，使用第一个
    if not primary_deployment and deployment_methods:
        primary_deployment = deployment_methods[0]

    package_info["deployment_method"] = primary_deployment

    # 根据部署方法提取不同的信息
    if primary_deployment == "npx":
        # 查找npx相关的包名和命令
        for pattern in NPX_PATTERNS:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                if isinstance(matches[0], tuple):
                    # 处理带捕获组的情况
                    package_name = matches[0][1] if matches[0][1] else matches[0][0]
                else:
                    package_name = matches[0]

                if package_name and package_name not in ["-g", "global"]:
                    package_info["package_name"] = package_name
                    package_info["install_command"] = f"npm install -g {package_name}"
                    package_info["run_command"] = f"npx {package_name}"
                    break

    elif primary_deployment == "uvx":
        # 查找uvx相关的包名和命令
        for pattern in UVX_PATTERNS:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                package_name = matches[0]
                if package_name:
                    package_info["package_name"] = package_name
                    package_info["install_command"] = f"pip install {package_name}"
                    package_info["run_command"] = f"uvx {package_name}"
                    break

    elif primary_deployment == "cargo":
        # 查找cargo相关的包名和命令
        for pattern in CARGO_PATTERNS:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                package_name = matches[0]
                if package_name:
                    package_info["package_name"] = package_name
                    package_info["install_command"] = f"cargo install {package_name}"
                    package_info["run_command"] = f"cargo run --bin {package_name}"
                    break

    elif primary_deployment == "python":
        # 查找python模块相关的包名和命令
        for pattern in PYTHON_PATTERNS:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                package_name = matches[0]
                if package_name:
                    package_info["package_name"] = package_name
                    package_info["install_command"] = f"pip install {package_name}"
                    package_info["run_command"] = f"python -m {package_name}"
                    break

    # 如果没有找到包名，尝试从项目名称推断
    if not package_info["package_name"]:
        # 尝试从README中的项目标题推断
        for pattern in TITLE_PATTERNS:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                package_name = matches[0].lower()
                package_info["package_name"] = package_name

                # 根据部署方法设置默认命令
                if primary_deployment == "npx":
                    package_info["install_command"] = f"npm install -g {package_name}"
                    package_info["run_command"] = f"npx {package_name}"
                elif primary_deployment == "uvx":
                    package_info["install_command"] = f"pip install {package_name}"
                    package_info["run_command"] = f"uvx {package_name}"
                elif primary_deployment == "cargo":
                    package_info["install_command"] = f"cargo install {package_name}"
                    package_info["run_command"] = f"cargo run --bin {package_name}"
                elif primary_deployment == "python":
                    package_info["install_command"] = f"pip install {package_name}"
                    package_info["run_command"] = f"python -m {package_name}"
                break

    return package_info
