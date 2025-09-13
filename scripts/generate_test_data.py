#!/usr/bin/env python3
"""
测试数据生成器

为MCP工具测试生成各种格式的样本文件：
- CSV: 包含员工信息、销售数据等
- Excel: 多工作表财务数据
- Word文档: 包含文本、表格、图片说明
- PDF: 报告格式文档
- PowerPoint: 演示文稿

作者: AI Assistant
日期: 2025-08-24
"""

import csv
import json
import os
import random
from datetime import datetime, timedelta
from pathlib import Path

# 测试数据目录
TEST_DATA_DIR = Path(__file__).parent.parent / "test_data"
TEST_DATA_DIR.mkdir(exist_ok=True)


def generate_csv_files():
    """生成CSV测试文件"""
    print("📊 生成CSV文件...")

    # 1. 员工信息表
    employees_data = [
        ["ID", "姓名", "部门", "职位", "薪资", "入职日期", "邮箱"],
        [1, "张三", "技术部", "高级工程师", 15000, "2022-01-15", "zhangsan@company.com"],
        [2, "李四", "产品部", "产品经理", 18000, "2021-08-20", "lisi@company.com"],
        [3, "王五", "设计部", "UI设计师", 12000, "2022-03-10", "wangwu@company.com"],
        [4, "赵六", "技术部", "前端工程师", 13000, "2022-06-01", "zhaoliu@company.com"],
        [5, "钱七", "运营部", "运营专员", 10000, "2022-09-15", "qianqi@company.com"],
        [6, "孙八", "技术部", "架构师", 25000, "2020-05-10", "sunba@company.com"],
        [7, "周九", "人事部", "招聘经理", 14000, "2021-12-01", "zhoujiu@company.com"],
        [8, "吴十", "财务部", "会计", 11000, "2022-02-28", "wushi@company.com"],
    ]

    with open(TEST_DATA_DIR / "employees.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(employees_data)

    # 2. 销售数据
    sales_data = [["日期", "产品", "销量", "单价", "总额", "销售员"]]
    products = ["笔记本电脑", "台式机", "显示器", "键盘", "鼠标", "耳机"]
    salespeople = ["小明", "小红", "小刚", "小美", "小强"]

    base_date = datetime(2024, 1, 1)
    for i in range(100):
        date = base_date + timedelta(days=random.randint(0, 365))
        product = random.choice(products)
        quantity = random.randint(1, 20)
        unit_price = random.randint(500, 8000)
        total = quantity * unit_price
        salesperson = random.choice(salespeople)
        sales_data.append(
            [
                date.strftime("%Y-%m-%d"),
                product,
                quantity,
                unit_price,
                total,
                salesperson,
            ]
        )

    with open(TEST_DATA_DIR / "sales_data.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(sales_data)

    # 3. MCP工具测试数据
    mcp_tools_data = [
        ["工具名称", "类型", "描述", "支持运行时", "是否需要API密钥", "GitHub地址"],
        [
            "Excel MCP Server",
            "数据处理",
            "用于操作Excel文件的MCP服务器",
            "uvx",
            "否",
            "https://github.com/haris-musa/excel-mcp-server",
        ],
        [
            "Context7",
            "文档检索",
            "获取最新的库文档",
            "npx",
            "否",
            "https://github.com/upstash/context7",
        ],
        [
            "Blender MCP",
            "3D建模",
            "通过MCP控制Blender",
            "uvx",
            "否",
            "https://github.com/ahujasid/blender-mcp",
        ],
        [
            "ElevenLabs MCP",
            "语音合成",
            "文本转语音服务",
            "uvx",
            "是",
            "https://github.com/elevenlabs/elevenlabs-mcp",
        ],
    ]

    with open(TEST_DATA_DIR / "mcp_tools.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(mcp_tools_data)

    print("✅ CSV文件生成完成")


def generate_json_files():
    """生成JSON测试文件"""
    print("📄 生成JSON文件...")

    # 1. 配置文件
    config_data = {
        "app_name": "MCP Test Framework",
        "version": "1.0.0",
        "database": {
            "host": "localhost",
            "port": 5432,
            "name": "mcp_test",
            "ssl": True,
        },
        "api_endpoints": {
            "base_url": "https://api.example.com",
            "timeout": 30,
            "retry_count": 3,
        },
        "features": {
            "smart_testing": True,
            "database_export": True,
            "report_generation": True,
        },
    }

    with open(TEST_DATA_DIR / "config.json", "w", encoding="utf-8") as f:
        json.dump(config_data, f, indent=2, ensure_ascii=False)

    # 2. 测试结果数据
    test_results = {
        "test_session": {
            "id": "test_20240824_001",
            "timestamp": datetime.now().isoformat(),
            "total_tests": 25,
            "passed": 20,
            "failed": 5,
            "duration": 120.5,
        },
        "test_cases": [
            {
                "name": "MCP连接测试",
                "status": "passed",
                "duration": 2.3,
                "message": "成功建立MCP连接",
            },
            {
                "name": "工具列表获取",
                "status": "passed",
                "duration": 1.8,
                "message": "成功获取15个可用工具",
            },
            {
                "name": "Excel文件操作",
                "status": "failed",
                "duration": 5.2,
                "message": "文件路径错误",
                "error": "Invalid filename: test.xlsx, must be an absolute path",
            },
        ],
    }

    with open(TEST_DATA_DIR / "test_results.json", "w", encoding="utf-8") as f:
        json.dump(test_results, f, indent=2, ensure_ascii=False)

    print("✅ JSON文件生成完成")


def generate_text_files():
    """生成文本测试文件"""
    print("📝 生成文本文件...")

    # 1. README文件
    readme_content = """# MCP测试框架

这是一个用于测试Model Context Protocol (MCP)工具的自动化框架。

## 主要功能

- 🚀 自动化MCP工具部署 (npx/uvx)
- 🧪 智能测试用例生成
- 📊 详细的测试报告
- 🗄️ 数据库结果存储
- 🔍 GitHub仓库评估

## 快速开始

```bash
# 安装依赖
uv sync

# 测试单个工具
uv run python -m src.main test-url "https://github.com/example/mcp-tool"

# 批量测试
uv run python -m src.main batch-test --input data/test.csv
```

## 支持的文件格式

- CSV: 员工数据、销售记录
- Excel: 多工作表财务数据
- JSON: 配置文件、API响应
- PDF: 报告文档
- PowerPoint: 演示文稿

## 贡献指南

欢迎提交Issue和Pull Request！

## 许可证

MIT License
"""

    with open(TEST_DATA_DIR / "README.md", "w", encoding="utf-8") as f:
        f.write(readme_content)

    # 2. 日志文件样本
    log_content = """2024-08-24 10:30:15 | INFO     | 启动MCP测试框架
2024-08-24 10:30:16 | INFO     | 加载配置文件: config.json
2024-08-24 10:30:17 | INFO     | 连接数据库成功
2024-08-24 10:30:18 | INFO     | 开始测试工具: excel-mcp-server
2024-08-24 10:30:19 | DEBUG    | 执行命令: uvx excel-mcp-server stdio
2024-08-24 10:30:21 | INFO     | MCP连接建立成功
2024-08-24 10:30:22 | INFO     | 发现25个可用工具
2024-08-24 10:30:23 | WARNING  | 工具需要绝对路径参数
2024-08-24 10:30:25 | ERROR    | 测试用例执行失败: 路径格式错误
2024-08-24 10:30:26 | INFO     | 生成测试报告完成
2024-08-24 10:30:27 | INFO     | 清理资源完成
"""

    with open(TEST_DATA_DIR / "test.log", "w", encoding="utf-8") as f:
        f.write(log_content)

    print("✅ 文本文件生成完成")


def generate_advanced_files():
    """生成Excel、Word等高级格式文件（如果库可用）"""
    print("📈 尝试生成高级格式文件...")

    # 尝试生成Excel文件
    try:
        import pandas as pd

        # 创建多工作表Excel文件
        with pd.ExcelWriter(
            TEST_DATA_DIR / "financial_report.xlsx", engine="openpyxl"
        ) as writer:
            # 收入表
            revenue_data = pd.DataFrame(
                {
                    "月份": ["1月", "2月", "3月", "4月", "5月", "6月"],
                    "产品A收入": [50000, 52000, 48000, 55000, 58000, 60000],
                    "产品B收入": [30000, 31000, 29000, 32000, 35000, 38000],
                    "总收入": [80000, 83000, 77000, 87000, 93000, 98000],
                }
            )
            revenue_data.to_sheet(writer, sheet_name="收入报表", index=False)

            # 成本表
            cost_data = pd.DataFrame(
                {
                    "月份": ["1月", "2月", "3月", "4月", "5月", "6月"],
                    "人工成本": [25000, 25000, 25000, 26000, 26000, 27000],
                    "材料成本": [15000, 16000, 14000, 17000, 18000, 19000],
                    "运营成本": [8000, 8200, 7800, 8500, 8800, 9000],
                    "总成本": [48000, 49200, 46800, 51500, 52800, 55000],
                }
            )
            cost_data.to_sheet(writer, sheet_name="成本报表", index=False)

        print("✅ Excel文件生成完成")

    except ImportError:
        print("⚠️ pandas未安装，跳过Excel文件生成")

    # 生成简单的XML文件
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<mcp_tools>
    <tool>
        <name>Excel MCP Server</name>
        <type>data_processing</type>
        <runtime>uvx</runtime>
        <requires_api_key>false</requires_api_key>
        <capabilities>
            <capability>read_excel</capability>
            <capability>write_excel</capability>
            <capability>format_cells</capability>
            <capability>create_charts</capability>
        </capabilities>
    </tool>
    <tool>
        <name>Context7</name>
        <type>documentation</type>
        <runtime>npx</runtime>
        <requires_api_key>false</requires_api_key>
        <capabilities>
            <capability>resolve_library_id</capability>
            <capability>get_library_docs</capability>
        </capabilities>
    </tool>
</mcp_tools>"""

    with open(TEST_DATA_DIR / "mcp_tools.xml", "w", encoding="utf-8") as f:
        f.write(xml_content)

    print("✅ XML文件生成完成")


def generate_binary_placeholders():
    """生成二进制文件的占位符说明"""
    print("📋 生成二进制文件说明...")

    binary_info = """# 二进制文件说明

由于Python环境限制，以下二进制格式文件需要手动创建或使用专门工具生成：

## PDF文件
推荐使用以下Python库生成：
- reportlab: 创建复杂PDF报告
- fpdf2: 轻量级PDF生成
- weasyprint: HTML转PDF

示例命令：
```bash
pip install reportlab
python -c "
from reportlab.pdfgen import canvas
c = canvas.Canvas('test_data/sample_report.pdf')
c.drawString(100, 750, 'MCP测试框架报告')
c.drawString(100, 730, '这是一个测试PDF文件')
c.save()
"
```

## Word文档 (.docx)
推荐使用python-docx库：
```bash
pip install python-docx
python -c "
from docx import Document
doc = Document()
doc.add_heading('MCP测试文档', 0)
doc.add_paragraph('这是一个测试Word文档，包含了MCP工具的相关信息。')
doc.save('test_data/sample_document.docx')
"
```

## PowerPoint演示文稿 (.pptx)
推荐使用python-pptx库：
```bash
pip install python-pptx
python -c "
from pptx import Presentation
prs = Presentation()
title_slide = prs.slides.add_slide(prs.slide_layouts[0])
title_slide.shapes.title.text = 'MCP测试框架'
title_slide.shapes.placeholders[1].text = '自动化MCP工具测试解决方案'
prs.save('test_data/sample_presentation.pptx')
"
```

## 图片文件
可以使用PIL生成测试图片：
```bash
pip install Pillow
python -c "
from PIL import Image, ImageDraw, ImageFont
img = Image.new('RGB', (800, 600), color='white')
draw = ImageDraw.Draw(img)
draw.text((50, 50), 'MCP Test Image', fill='black')
img.save('test_data/sample_image.png')
"
```
"""

    with open(TEST_DATA_DIR / "BINARY_FILES_GUIDE.md", "w", encoding="utf-8") as f:
        f.write(binary_info)

    print("✅ 二进制文件说明生成完成")


def main():
    """主函数"""
    print("🎯 开始生成MCP测试数据文件...")
    print(f"📂 目标目录: {TEST_DATA_DIR}")

    generate_csv_files()
    generate_json_files()
    generate_text_files()
    generate_advanced_files()
    generate_binary_placeholders()

    print(f"\n✅ 测试数据生成完成！")
    print(f"📁 生成的文件保存在: {TEST_DATA_DIR}")

    # 列出生成的文件
    files = list(TEST_DATA_DIR.glob("*"))
    if files:
        print("\n📋 生成的文件列表:")
        for file in sorted(files):
            size = file.stat().st_size if file.is_file() else 0
            print(f"   📄 {file.name} ({size} bytes)")

    print(f"\n🚀 现在您可以使用这些测试文件来测试各种MCP工具了！")


if __name__ == "__main__":
    main()
