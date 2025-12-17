# 项目结构说明

本文件夹已经重组，以下是新的项目结构：

## 📁 目录结构

```
mcp_agent/
├── src/                    # 核心框架代码
│   ├── core/              # 核心功能模块
│   ├── agents/            # AI智能代理
│   ├── utils/             # 工具函数
│   └── tools/             # 数据库工具
├── scripts/               # 工具脚本
├── tests/                 # 测试文件
├── tools/                 # 数据库维护工具
├── data/                  # 重新组织的数据目录
│   ├── test_samples/      # 测试数据样本
│   ├── analysis/          # 分析项目
│   │   └── tashan/       # 他山MCP冷门推荐分析
│   └── mcp_database/     # MCP工具数据库
├── docs/                  # 项目文档
│   ├── BINARY_FILES_GUIDE.md
│   └── test_data_README.md
└── reports/              # 生成的报告（预留）
```

## 🔄 重组说明

### 原结构调整

1. **test_data/ → data/test_samples/**
   - 移动核心测试数据文件（CSV、JSON、XML）
   - 删除可重新生成的二进制文件（PDF、Word、PowerPoint、PNG）
   - 保留测试所需的配置文件

2. **tashan/ → data/analysis/tashan/**
   - 完整保留"他山"MCP冷门推荐分析项目
   - 更新内部文件路径引用
   - 保持分析算法和结果的完整性

3. **新建文件夹**
   - `data/mcp_database/`: 集中管理MCP工具数据库CSV文件
   - `docs/`: 统一管理项目文档
   - `reports/`: 预留给生成的测试报告

### 路径更新

已更新的文件路径：
- `scripts/generate_test_data.py`: 测试数据生成路径
- `data/analysis/tashan/final_hidden_gems_analyzer.py`: 数据文件读取路径

## 📝 使用说明

### 测试数据
测试数据现在位于 `data/test_samples/` 目录：
- CSV文件：员工数据、销售记录、MCP工具列表等
- JSON文件：配置文件、产品信息等
- XML文件：应用配置等

### 运行分析项目
```bash
# 运行他山冷门推荐分析
cd data/analysis/tashan
python final_hidden_gems_analyzer.py
```

### 生成测试数据
```bash
# 生成测试样本文件
python scripts/generate_test_data.py
```

## ✅ 优势

1. **更清晰的结构**：按功能分类，便于理解和维护
2. **减少冗余**：删除不必要的临时文件
3. **保持价值**：保留有价值的分析项目和测试数据
4. **便于扩展**：为未来的数据和文档预留空间
5. **路径统一**：所有数据文件集中在data目录下

---
*重组时间：2025年12月17日*