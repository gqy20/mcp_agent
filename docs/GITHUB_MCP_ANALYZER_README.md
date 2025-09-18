# GitHub MCP项目自动分析器

这个功能允许你自动分析GitHub项目，识别MCP工具，并将其添加到现有的MCP工具表格中。

## 功能特点

### 🔍 智能分析
- **自动获取README**: 从GitHub仓库获取README文件
- **MCP项目识别**: 检测项目是否为Model Context Protocol工具
- **部署信息提取**: 自动识别npx、uvx、cargo、python等部署方式
- **技术栈分析**: 识别项目使用的技术栈
- **API密钥检测**: 判断是否需要API密钥

### 📊 数据标准化
- **格式统一**: 生成与现有表格相同格式的记录
- **双表更新**: 同时更新`mcp.csv`和`tashan_verified_mcp.csv`
- **智能评分**: 根据GitHub数据计算项目评分
- **重复检测**: 避免重复添加已存在的项目

## 使用方法

### 方法1: 直接指定URLs
```bash
python -m src.main analyze-github "https://github.com/owner/repo1,https://github.com/owner/repo2"
```

### 方法2: 从文件批量处理
```bash
# 创建URL文件
echo "https://github.com/owner/repo1
https://github.com/owner/repo2
https://github.com/owner/repo3" > urls.txt

# 批量分析
python -m src.main analyze-github urls.txt
```

### 方法3: 编程接口
```python
from src.core.mcp_table_updater import MCPTableUpdater

updater = MCPTableUpdater()
results = updater.update_with_new_repos([
    "https://github.com/owner/repo1",
    "https://github.com/owner/repo2"
])

updater.generate_report(results)
```

## 输出示例

### 控制台输出
```
==================================================
MCP表格更新报告
==================================================
总计处理URLs: 10
已存在项目: 5
新增项目: 5
MCP项目: 2
非MCP项目: 3
分析失败: 0

新增MCP工具 (2):
  • example-mcp by example (150 stars)
  • test-mcp by test (80 stars)
==================================================
```

### JSON报告
系统会生成`auto_update_report.json`文件，包含详细的更新信息。

## 支持的部署方式检测

| 部署方式 | 检测关键词 | 示例 |
|---------|----------|------|
| npx | npx, npm, global | `npx @example/mcp` |
| uvx | uvx, pip install uvx | `uvx example-mcp` |
| cargo | cargo install, build | `cargo install --path .` |
| python | python -m, pip install | `python -m example_mcp` |
| docker | docker run, build | `docker run example-mcp` |

## 技术栈识别

系统能识别以下技术栈：
- **Python**: python, py, .py文件
- **Node.js**: node, javascript, js, typescript, ts, npm
- **Rust**: rust, cargo, .rs文件
- **Go**: go, golang
- **Java**: java, maven, gradle
- **Ruby**: ruby, gem

## 数据字段说明

### mcp.csv新增字段
- `extracted_function_description`: 从README提取的功能描述
- `extracted_tools`: 识别的工具列表
- `extracted_deployment_methods`: 检测到的部署方式
- `extracted_tech_stack`: 技术栈信息
- `extracted_requires_api_key`: 是否需要API密钥
- `extracted_use_cases`: 使用场景

### tashan_verified_mcp.csv字段
- `工具名称`: 项目名称 + "MCP"
- `工具作者`: GitHub用户名
- `他山评分`: 综合评分
- `实用性评分`: 基于功能的评分
- `可持续性评分`: 基于项目活跃度的评分
- `受欢迎度评分`: 基于stars和forks的评分
- `可用工具数量`: 检测到的工具数量

## 错误处理

### 常见错误
1. **仓库不存在**: 404错误，跳过该URL
2. **非MCP项目**: README中未发现MCP相关内容
3. **API限制**: GitHub API访问频率限制
4. **网络问题**: 无法连接到GitHub API

### 错误处理策略
- 自动跳过无法访问的仓库
- 继续处理其他URL
- 生成详细错误报告
- 不中断整个批处理流程

## 高级功能

### GitHub Token配置
为了避免API限制，可以配置GitHub token：

```bash
export GITHUB_TOKEN=your_github_token_here
```

### 自定义分析
可以通过修改`src/core/github_mcp_analyzer.py`来自定义：
- MCP关键词列表
- 部署方式检测规则
- 技术栈识别模式
- 评分算法

## 性能优化

### 批量处理建议
- 每批处理不超过50个URL
- 合理设置请求间隔
- 使用GitHub token提高限制

### 网络优化
- 自动重试失败的请求
- 支持代理设置
- 缓存已访问的仓库信息

## 故障排除

### 问题1: 无法获取README
- 检查网络连接
- 验证GitHub token
- 确认仓库存在

### 问题2: 未识别MCP项目
- 检查README中是否包含MCP关键词
- 确认项目确实是MCP工具
- 尝试手动检查项目

### 问题3: 评分不准确
- 检查stars和forks是否正确获取
- 验证GitHub API数据
- 调整评分算法

## 开发说明

### 代码结构
```
src/core/
├── github_mcp_analyzer.py     # GitHub项目分析器
└── mcp_table_updater.py       # 表格更新器

src/main.py                   # CLI入口
```

### 扩展功能
- 添加更多部署方式检测
- 改进技术栈识别
- 增强评分算法
- 支持更多Git平台

## 贡献指南

1. 测试新功能
2. 更新文档
3. 修复bug
4. 优化性能
5. 添加新特性

## 许可证

此功能遵循项目的许可证条款。
