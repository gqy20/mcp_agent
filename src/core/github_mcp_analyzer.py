"""
GitHub MCP项目自动分析器

功能：
1. 获取GitHub项目的README文件
2. 分析MCP部署信息
3. 提取关键数据
4. 生成标准化的MCP工具记录
"""

import json
import re
import urllib.parse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests


class GitHubMCPAnalyzer:
    """GitHub MCP项目自动分析器"""

    def __init__(self, github_token: Optional[str] = None):
        """
        初始化分析器

        Args:
            github_token: GitHub API token (可选，提高API限制)
        """
        self.github_token = github_token
        self.headers = {"Accept": "application/vnd.github.v3+json"}
        if github_token:
            self.headers["Authorization"] = f"token {github_token}"

        # MCP相关关键词
        self.mcp_keywords = [
            "model context protocol",
            "mcp server",
            "mcp tool",
            "claude mcp",
            "anthropic mcp",
            "mcp integration",
            "mcp",
        ]

        # 部署方式关键词
        self.deployment_patterns = {
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
        self.api_key_patterns = [
            r"API_KEY",
            r"API_TOKEN",
            r"SECRET_KEY",
            r"environment variable",
            r"env.*=.*YOUR",
            r"requires.*authentication",
            r"needs.*credentials",
        ]

        # 技术栈模式
        self.tech_stack_patterns = {
            "python": [r"python", r"py", r"\.py$"],
            "nodejs": [r"node", r"javascript", r"js", r"typescript", r"ts", r"npm"],
            "rust": [r"rust", r"cargo", r"\.rs$"],
            "go": [r"go", r"golang"],
            "java": [r"java", r"maven", r"gradle"],
            "ruby": [r"ruby", r"gem"],
        }

    def analyze_github_repo(self, github_url: str) -> Optional[Dict]:
        """
        分析GitHub仓库并生成MCP工具记录

        Args:
            github_url: GitHub仓库URL

        Returns:
            包含MCP工具信息的字典，如果不是MCP项目则返回None
        """
        try:
            # 解析GitHub URL
            owner, repo = self._parse_github_url(github_url)
            if not owner or not repo:
                return {"success": False, "error": "无法解析GitHub URL"}

            # 获取仓库信息
            repo_info = self._get_repo_info(owner, repo)
            if not repo_info:
                return {"success": False, "error": "无法获取仓库信息"}

            # 获取README内容
            readme_content = self._get_readme_content(owner, repo)
            if not readme_content:
                return {"success": False, "error": "无法获取README内容"}

            # 检查是否为MCP项目
            if not self._is_mcp_project(readme_content):
                return {"success": False, "error": "项目不是MCP工具", "is_mcp_project": False}

            # 分析MCP项目
            analysis_result = self._analyze_mcp_content(readme_content, repo_info)

            # 生成标准化记录
            mcp_record = self._generate_mcp_record(
                github_url, repo_info, analysis_result
            )

            return {"success": True, "record": mcp_record}

        except Exception as e:
            print(f"分析GitHub仓库时出错: {e}")
            return {"success": False, "error": str(e)}

    def _parse_github_url(self, url: str) -> Tuple[Optional[str], Optional[str]]:
        """解析GitHub URL获取owner和repo"""
        try:
            # 标准化URL
            url = url.lower().strip()
            if not url.startswith("https://github.com/"):
                return None, None

            # 移除.git后缀
            url = url.replace(".git", "")

            # 解析路径
            parsed = urllib.parse.urlparse(url)
            path_parts = parsed.path.strip("/").split("/")

            if len(path_parts) >= 2:
                return path_parts[0], path_parts[1]

            return None, None

        except Exception:
            return None, None

    def _get_repo_info(self, owner: str, repo: str) -> Optional[Dict]:
        """获取GitHub仓库信息"""
        try:
            url = f"https://api.github.com/repos/{owner}/{repo}"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"获取仓库信息失败: {e}")
            return None

    def _get_readme_content(self, owner: str, repo: str) -> Optional[str]:
        """获取README内容"""
        try:
            # 尝试不同的README文件名
            readme_names = ["README.md", "README", "readme.md", "readme"]

            for readme_name in readme_names:
                url = f"https://api.github.com/repos/{owner}/{repo}/contents/{readme_name}"
                response = requests.get(url, headers=self.headers)

                if response.status_code == 200:
                    # 解码base64内容
                    import base64

                    content = base64.b64decode(response.json()["content"]).decode(
                        "utf-8"
                    )
                    return content
                elif response.status_code == 404:
                    continue
                else:
                    print(f"获取README失败: {response.status_code}")
                    return None

            print("未找到README文件")
            return None

        except Exception as e:
            print(f"获取README内容失败: {e}")
            return None

    def _is_mcp_project(self, content: str) -> bool:
        """检查是否为MCP项目"""
        content_lower = content.lower()

        # 检查MCP关键词
        for keyword in self.mcp_keywords:
            if keyword.lower() in content_lower:
                return True

        # 检查package.json中的依赖
        if "package.json" in content_lower:
            # 简单的package.json内容检查
            if '"@modelcontextprotocol' in content_lower or '"mcp' in content_lower:
                return True

        return False

    def _analyze_mcp_content(self, content: str, repo_info: Dict) -> Dict:
        """分析MCP项目内容"""
        analysis = {
            "description": self._extract_description(content, repo_info),
            "deployment_methods": self._extract_deployment_methods(content),
            "requires_api_key": self._check_api_key_requirement(content),
            "tech_stack": self._extract_tech_stack(content),
            "tools": self._extract_tools(content),
            "use_cases": self._extract_use_cases(content),
            "installation": self._extract_installation_instructions(content),
        }
        
        # 提取包名和部署命令信息
        package_info = self._extract_package_info(content, analysis["deployment_methods"])
        analysis.update(package_info)
        
        return analysis

    def _extract_description(self, content: str, repo_info: Dict) -> str:
        """提取项目描述"""
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

    def _extract_deployment_methods(self, content: str) -> List[str]:
        """提取部署方式"""
        methods = []
        content_lower = content.lower()

        for method, patterns in self.deployment_patterns.items():
            for pattern in patterns:
                if re.search(pattern, content_lower, re.IGNORECASE):
                    methods.append(method)
                    break

        return list(set(methods))

    def _check_api_key_requirement(self, content: str) -> bool:
        """检查是否需要API密钥"""
        content_lower = content.lower()

        for pattern in self.api_key_patterns:
            if re.search(pattern, content_lower, re.IGNORECASE):
                return True

        return False

    def _extract_tech_stack(self, content: str) -> List[str]:
        """提取技术栈"""
        tech_stack = []
        content_lower = content.lower()

        for tech, patterns in self.tech_stack_patterns.items():
            for pattern in patterns:
                if re.search(pattern, content_lower, re.IGNORECASE):
                    tech_stack.append(tech)
                    break

        return list(set(tech_stack))

    def _extract_tools(self, content: str) -> List[str]:
        """提取工具列表"""
        tools = []

        # 查找工具描述
        tool_patterns = [
            r"Tools:?\s*([^\n]+)",
            r"tools:?\s*([^\n]+)",
            r"Features:?\s*([^\n]+)",
            r"features:?\s*([^\n]+)",
            r"Capabilities:?\s*([^\n]+)",
            r"capabilities:?\s*([^\n]+)",
        ]

        for pattern in tool_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                # 分割工具列表
                tool_items = re.split(r"[,;•\-\*]", match)
                tools.extend([item.strip() for item in tool_items if item.strip()])

        return list(set(tools))[:10]  # 限制工具数量

    def _extract_use_cases(self, content: str) -> List[str]:
        """提取使用场景"""
        use_cases = []

        # 查找使用场景描述
        use_case_patterns = [
            r"Use cases?:?\s*([^\n]+)",
            r"use cases?:?\s*([^\n]+)",
            r"Usage:?\s*([^\n]+)",
            r"usage:?\s*([^\n]+)",
            r"Applications:?\s*([^\n]+)",
            r"applications:?\s*([^\n]+)",
        ]

        for pattern in use_case_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                use_cases.append(match.strip())

        return list(set(use_cases))[:5]  # 限制使用场景数量

    def _extract_installation_instructions(self, content: str) -> str:
        """提取安装说明"""
        lines = content.split("\n")
        install_section = False
        install_instructions = []

        for line in lines:
            line_lower = line.lower()
            if any(
                keyword in line_lower
                for keyword in ["install", "setup", "getting started"]
            ):
                install_section = True
            elif install_section and line.startswith("#"):
                break
            elif install_section and line.strip():
                install_instructions.append(line.strip())

        return "\n".join(install_instructions[:10]) if install_instructions else ""

    def _extract_package_info(self, content: str, deployment_methods: List[str]) -> Dict[str, str]:
        """从README内容中提取包名和部署命令"""
        package_info = {
            "package_name": "",
            "deployment_method": "",
            "install_command": "",
            "run_command": ""
        }
        
        if not deployment_methods:
            return package_info
            
        # 获取主要部署方法 - 优先选择uvx/npx而不是python
        priority_order = ["uvx", "npx", "cargo", "python"]
        primary_deployment = ""
        
        for method in priority_order:
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
            npx_patterns = [
                r"npx\s+([@a-zA-Z0-9/-]+)",
                r"npm\s+install\s+(-g\s+|global\s+)?([@a-zA-Z0-9/-]+)",
                r"npm\s+i\s+(-g\s+|global\s+)?([@a-zA-Z0-9/-]+)"
            ]
            
            for pattern in npx_patterns:
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
            uvx_patterns = [
                r"uvx\s+([a-zA-Z0-9/-]+)",
                r"pip\s+install\s+([a-zA-Z0-9/-]+)",
                r"uv\s+run\s+([a-zA-Z0-9/-]+)"
            ]
            
            for pattern in uvx_patterns:
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
            cargo_patterns = [
                r"cargo\s+install\s+([a-zA-Z0-9_-]+)",
                r"cargo\s+build.*--path.*?/([a-zA-Z0-9_-]+)"
            ]
            
            for pattern in cargo_patterns:
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
            python_patterns = [
                r"python\s+-m\s+([a-zA-Z0-9_]+)",
                r"pip\s+install\s+([a-zA-Z0-9_-]+)",
                r"pip3\s+install\s+([a-zA-Z0-9_-]+)"
            ]
            
            for pattern in python_patterns:
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
            title_patterns = [
                r"#\s*([a-zA-Z0-9_-]+)\s+(?:MCP|mcp|Server|server)",
                r"#\s*([a-zA-Z0-9_-]+)\s*",
                r"project\s*name[:：]\s*([a-zA-Z0-9_-]+)"
            ]
            
            for pattern in title_patterns:
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

    def _generate_mcp_record(
        self, github_url: str, repo_info: Dict, analysis: Dict
    ) -> Dict:
        """生成标准化的MCP记录"""
        owner = repo_info.get("owner", {}).get("login", "")
        repo_name = repo_info.get("name", "")

        # 生成评分
        stars = repo_info.get("stargazers_count", 0)
        forks = repo_info.get("forks_count", 0)

        # 简单评分算法
        popularity_score = min((stars / 100) + (forks / 10), 100)
        
        # 生成MCP配置JSON
        mcp_config = {
            "package_name": analysis.get("package_name", ""),
            "deployment_method": analysis.get("deployment_method", ""),
            "install_command": analysis.get("install_command", ""),
            "run_command": analysis.get("run_command", "")
        }

        return {
            "name": f"{repo_name} MCP",
            "url": "",
            "author": owner,
            "github_url": github_url,
            "evaluate": self._calculate_evaluate_score(stars, forks),
            "score": "",
            "description": analysis["description"],
            "date": datetime.now().strftime("%Y-%m-%d"),
            "type": "开发工具",
            "usage": "推荐",
            "star_count": stars,
            "fork_count": forks,
            "readme_path": "",
            "extraction_status": "success",
            "extraction_error": "",
            "extraction_timestamp": datetime.now().isoformat(),
            "extracted_function_description": analysis["description"],
            "extracted_tools": ", ".join(analysis["tools"]),
            "extracted_deployment_methods": ", ".join(analysis["deployment_methods"]),
            "extracted_tech_stack": ", ".join(analysis["tech_stack"]),
            "extracted_requires_api_key": analysis["requires_api_key"],
            "extracted_mcp_config": json.dumps(mcp_config, ensure_ascii=False),
            "extracted_api_requirements": "",
            "extracted_use_cases": ", ".join(analysis["use_cases"]),
            # 添加直接字段以便其他组件使用
            "package_name": analysis.get("package_name", ""),
            "deployment_method": analysis.get("deployment_method", ""),
            "install_command": analysis.get("install_command", ""),
            "run_command": analysis.get("run_command", ""),
        }

    def _calculate_evaluate_score(self, stars: int, forks: int) -> str:
        """计算评估分数"""
        score = (stars / 100) + (forks / 10)

        if score >= 80:
            return "优质"
        elif score >= 50:
            return "中等"
        else:
            return "一般"

    def batch_analyze_repos(self, github_urls: List[str]) -> List[Dict]:
        """批量分析GitHub仓库"""
        results = []

        for url in github_urls:
            print(f"正在分析: {url}")
            result = self.analyze_github_repo(url)

            if result:
                results.append(result)
                print(f"✅ 成功分析: {result['name']}")
            else:
                print(f"❌ 分析失败或非MCP项目: {url}")

        return results

    def export_to_csv(self, results: List[Dict], output_file: str):
        """导出结果到CSV文件"""
        import csv

        if not results:
            print("没有结果可导出")
            return

        # 获取所有字段
        fieldnames = set()
        for result in results:
            fieldnames.update(result.keys())
        fieldnames = sorted(fieldnames)

        with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for result in results:
                writer.writerow(result)

        print(f"结果已导出到: {output_file}")


def main():
    """测试函数"""
    analyzer = GitHubMCPAnalyzer()

    # 测试分析一个GitHub仓库
    test_url = "https://github.com/microsoft/playwright-mcp"
    result = analyzer.analyze_github_repo(test_url)

    if result:
        print("分析结果:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print("分析失败")


if __name__ == "__main__":
    main()
