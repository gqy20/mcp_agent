#!/usr/bin/env python3
"""
冷门推荐分析：基于他山评分≥60分的MCP项目在Lobehub中的推荐价值分析
完善版本：详细算法说明，适当降低标准确保30个推荐，只输出2个CSV文件
"""
import json

import numpy as np
import pandas as pd


def analyze_hidden_gems():
    """分析值得作为冷门推荐的MCP项目"""

    print("=== 他山MCP冷门推荐分析 ===\n")

    # 读取数据
    tashan_df = pd.read_csv("data/tashan_verified_mcp.csv")
    lobehub_df = pd.read_csv("data/mcp.csv")

    print(f"他山项目总数: {len(tashan_df)}")
    print(f"Lobehub项目总数: {len(lobehub_df)}")

    # 筛选他山评分≥60的项目
    qualified_projects = tashan_df[tashan_df["他山评分"] >= 60.0].copy()
    print(f"他山评分≥60分的项目: {len(qualified_projects)}个")

    # 提取GitHub仓库标识
    def extract_repo_key(url):
        if pd.isna(url) or not isinstance(url, str):
            return None
        try:
            if "github.com" in url:
                parts = url.replace("https://github.com/", "").replace(
                    "http://github.com/", ""
                )
                parts = parts.rstrip("/").split("/")
                if len(parts) >= 2:
                    return f"{parts[0]}/{parts[1]}"
        except:
            pass
        return None

    qualified_projects["repo_key"] = qualified_projects["github_url"].apply(
        extract_repo_key
    )
    lobehub_df["repo_key"] = lobehub_df["github_url"].apply(extract_repo_key)

    # 构建Lobehub数据映射
    lobehub_map = {}
    for _, row in lobehub_df.iterrows():
        if pd.notna(row["repo_key"]):
            lobehub_map[row["repo_key"]] = {
                "name": row["name"],
                "lobehub_url": row["url"],
                "description": row["description"],
                "quality_rating": row["evaluate"],
                "star_count": row["star_count"] if pd.notna(row["star_count"]) else 0,
                "fork_count": row["fork_count"] if pd.notna(row["fork_count"]) else 0,
                "tools_count": len(str(row["extracted_tools"]).split(","))
                if pd.notna(row["extracted_tools"])
                else 0,
                "use_cases": row["extracted_use_cases"]
                if pd.notna(row["extracted_use_cases"])
                else row["type"],
                "deployment_methods": row["extracted_deployment_methods"]
                if pd.notna(row["extracted_deployment_methods"])
                else "N/A",
                "api_requirements": row["extracted_api_requirements"]
                if pd.notna(row["extracted_api_requirements"])
                else row["extracted_requires_api_key"],
            }

    # 分析每个项目的冷门推荐价值
    print("\n正在分析冷门推荐价值...")
    hidden_gems = []

    for _, project in qualified_projects.iterrows():
        repo_key = project["repo_key"]
        if not repo_key or repo_key not in lobehub_map:
            continue

        lobehub_data = lobehub_map[repo_key]

        # 计算冷门推荐指数
        hidden_gem_score = calculate_hidden_gem_score(
            tashan_score=project["他山评分"],
            stars=lobehub_data["star_count"]
            if pd.notna(lobehub_data["star_count"])
            else 0,
            forks=lobehub_data["fork_count"]
            if pd.notna(lobehub_data["fork_count"])
            else 0,
            lobehub_rating=lobehub_data["quality_rating"]
            if pd.notna(lobehub_data["quality_rating"])
            else 0,
            tools_count=lobehub_data["tools_count"]
            if pd.notna(lobehub_data["tools_count"])
            else 0,
        )

        # 确定推荐类型
        recommendation_type = determine_recommendation_type(
            hidden_gem_score=hidden_gem_score,
            tashan_score=project["他山评分"],
            stars=lobehub_data["star_count"]
            if pd.notna(lobehub_data["star_count"])
            else 0,
        )

        hidden_gems.append(
            {
                "project_name": project["工具名称"],
                "author": project["工具作者"],
                "github_url": project["github_url"],
                "github_stars": lobehub_data["star_count"]
                if pd.notna(lobehub_data["star_count"])
                else 0,
                "github_forks": lobehub_data["fork_count"]
                if pd.notna(lobehub_data["fork_count"])
                else 0,
                "tashan_score": project["他山评分"],
                "practicality_score": project["实用性评分"],
                "sustainability_score": project["可持续性评分"],
                "popularity_score": project["受欢迎度评分"],
                "tools_available_tashan": project["可用工具数量"],
                "lobehub_url": lobehub_data["lobehub_url"],
                "lobehub_description": lobehub_data["description"],
                "lobehub_rating": lobehub_data["quality_rating"],
                "tools_available": lobehub_data["tools_count"],
                "project_type": lobehub_data["use_cases"],
                "deployment_methods": lobehub_data["deployment_methods"],
                "api_requirements": lobehub_data["api_requirements"],
                "use_cases": lobehub_data["use_cases"],
                "hidden_gem_score": hidden_gem_score,
                "recommendation_type": recommendation_type,
            }
        )

    # 转为DataFrame并排序
    all_df = pd.DataFrame(hidden_gems)
    all_df = all_df.sort_values(
        ["hidden_gem_score", "tashan_score"], ascending=[False, False]
    )

    # 根据用户要求，适当降低标准确保有30个推荐项目
    recommended_df = all_df[all_df["hidden_gem_score"] >= 45.0].copy()  # 降低标准到45分

    if len(recommended_df) < 30:
        print(f"\n当前推荐项目仅{len(recommended_df)}个，取评分最高的30个项目...")
        recommended_df = all_df.head(30).copy()
    else:
        recommended_df = recommended_df.head(30)  # 确保只取30个

    print(f"最终推荐项目: {len(recommended_df)}个")

    # 按照用户要求，只生成2个CSV文件
    all_df.to_csv("complete_analysis.csv", index=False, encoding="utf-8")
    recommended_df.to_csv(
        "hidden_gems_recommendations.csv", index=False, encoding="utf-8"
    )

    # 生成统一的综合分析报告
    print("\n正在生成综合分析报告...")
    generate_comprehensive_report(all_df, recommended_df)

    print(f"\n=== 分析完成 ===")
    print(f"总分析项目: {len(all_df)}个")
    print(f"最终推荐项目: {len(recommended_df)}个")
    print(f"平均冷门指数: {recommended_df['hidden_gem_score'].mean():.1f}分")
    print(f"\n生成文件:")
    print(f"- complete_analysis.csv: 完整分析数据")
    print(f"- hidden_gems_recommendations.csv: 30个冷门推荐")
    print(f"- README.md: 综合分析报告和算法说明")

    return recommended_df


def calculate_hidden_gem_score(tashan_score, stars, forks, lobehub_rating, tools_count):
    """
    计算冷门推荐指数 (Hidden Gem Score)

    算法详解：
    1. 基础分 (权重60%)：以他山评分为主要质量依据
    2. 热度调节分：GitHub热度越低，冷门推荐价值越高
    3. 功能丰富度分：工具数量越多，实用价值越高
    4. 价值差异分析分：他山评分明显高于Lobehub评分时获得加分

    Args:
        tashan_score: 他山总评分 (0-100)
        stars: GitHub Stars数量
        forks: GitHub Forks数量
        lobehub_rating: Lobehub评级 (1-5)
        tools_count: 可用工具数量

    Returns:
        float: 冷门推荐指数 (0-100+)
    """

    # 1. 基础分：他山评分 × 0.6
    base_score = tashan_score * 0.6

    # 2. 热度调节分：根据GitHub Stars调整冷门性
    if stars > 2000:
        popularity_adjustment = -15  # 过于热门
    elif stars > 1000:
        popularity_adjustment = -8  # 热门项目
    elif stars > 500:
        popularity_adjustment = -3  # 中等热度
    elif stars > 100:
        popularity_adjustment = 2  # 适中关注度
    elif stars > 10:
        popularity_adjustment = 5  # 低关注度，适合推荐
    else:
        popularity_adjustment = 8  # 极低关注度，冷门宝藏

    # 3. 功能丰富度分：工具数量奖励 (每个工具+2分，上限10分)
    tools_bonus = (
        min(tools_count * 2, 10) if pd.notna(tools_count) and tools_count > 0 else 0
    )

    # 4. 价值差异分析分：识别被Lobehub低估的项目
    try:
        if pd.notna(lobehub_rating) and str(lobehub_rating) in ["优质", "推荐", "一般"]:
            rating_map = {"优质": 5, "推荐": 4, "一般": 3}
            lobehub_equivalent_score = rating_map.get(str(lobehub_rating), 3) * 20
        else:
            lobehub_equivalent_score = 60  # 默认值
    except:
        lobehub_equivalent_score = 60

    rating_gap_bonus = max(0, (tashan_score - lobehub_equivalent_score) * 0.25)

    # 综合计算
    hidden_gem_score = (
        base_score + popularity_adjustment + tools_bonus + rating_gap_bonus
    )

    return round(hidden_gem_score, 1)


def determine_recommendation_type(hidden_gem_score, tashan_score, stars):
    """
    根据冷门推荐指数确定推荐级别

    分级标准：
    - S级 (≥70分): 顶级冷门宝藏，极高质量但极低关注
    - A级 (65-69分): 优质冷门推荐，值得重点推广
    - B级 (60-64分): 潜力冷门项目，有明确价值
    - C级 (55-59分): 专业小众工具，特定领域高价值
    - D级 (50-54分): 一般冷门推荐，补充推荐
    """

    if hidden_gem_score >= 70:
        if stars < 50:
            return "S级-顶级冷门宝藏"
        else:
            return "A级-高质量冷门"
    elif hidden_gem_score >= 65:
        if tashan_score >= 85:
            return "A级-被严重低估"
        else:
            return "A级-优质冷门推荐"
    elif hidden_gem_score >= 60:
        if stars < 200:
            return "B级-高质量冷门"
        else:
            return "B级-潜力冷门项目"
    elif hidden_gem_score >= 55:
        if tashan_score >= 75:
            return "C级-专业小众工具"
        else:
            return "C级-特定场景推荐"
    elif hidden_gem_score >= 50:
        return "D级-一般冷门推荐"
    else:
        return "不推荐"


def generate_comprehensive_report(all_df, recommended_df):
    """生成统一的综合分析报告"""

    report = f"""# 他山MCP冷门推荐分析

## 🎯 项目目标

基于他山评分体系，发现Lobehub中值得重点推广的冷门优质MCP项目。通过独创的"冷门推荐指数"算法，识别高质量但关注度不高的项目，为用户提供差异化的推荐内容。

## 📊 冷门推荐指数算法详解

### 计算公式
```
冷门推荐指数 = 基础分 + 热度调节分 + 功能丰富度分 + 价值差异分析分
```

### 详细说明

#### 1. 基础分 (权重60%)
```
基础分 = 他山评分 × 0.6
```
- 以他山的专业评分为主要依据
- 反映项目的综合质量（实用性40% + 可持续性30% + 受欢迎度30%）

#### 2. 热度调节分 (冷门性评估)
```
Stars > 2000: -15分  (过于热门，不适合冷门推荐)
Stars > 1000: -8分   (热门项目)
Stars > 500:  -3分   (中等热度)
Stars > 100:  +2分   (适中关注度)
Stars > 10:   +5分   (低关注度，加分推荐)
Stars ≤ 10:   +8分   (极低关注度，冷门宝藏)
```

#### 3. 功能丰富度分
```
工具丰富度分 = min(工具数量 × 2, 10)
```
- 鼓励推荐功能丰富的项目
- 每个可用工具+2分，上限10分

#### 4. 价值差异分析分
```
差异分 = max(0, (他山评分 - Lobehub评分×20) × 0.25)
```
- 识别被Lobehub低估的高质量项目
- 他山评分明显高于Lobehub评分时获得加分

### 评分范围与推荐级别

| 级别 | 冷门指数范围 | 推荐类型 | 特征描述 |
|------|-------------|----------|----------|
| **S级** | ≥70分 | 顶级冷门宝藏 | Stars<50，极高质量但极低关注 |
| **A级** | 65-69分 | 优质冷门推荐 | Stars<200，值得重点推广 |
| **B级** | 60-64分 | 潜力冷门项目 | 有明确价值，适合分类推荐 |
| **C级** | 55-59分 | 专业小众工具 | 特定领域高价值 |
| **D级** | 50-54分 | 一般冷门推荐 | 补充推荐，丰富选择 |

## 📈 分析结果概览

### 总体统计
- **分析项目总数**: {len(all_df)}个 (他山评分≥60分)
- **符合推荐标准**: {len(all_df[all_df['hidden_gem_score'] >= 45])}个 (冷门指数≥45分)
- **最终推荐项目**: {len(recommended_df)}个
- **平均他山评分**: {all_df['tashan_score'].mean():.1f}分
- **平均冷门指数**: {recommended_df['hidden_gem_score'].mean():.1f}分

### 推荐级别分布
"""

    # 统计推荐级别分布
    level_counts = recommended_df["recommendation_type"].value_counts()
    for level, count in level_counts.items():
        report += f"- **{level}**: {count}个\n"

    report += f"""

## 🏆 顶级推荐项目 (S级和A级)

"""

    top_projects = recommended_df[recommended_df["hidden_gem_score"] >= 65]
    for i, (_, project) in enumerate(top_projects.head(10).iterrows(), 1):
        report += f"""
### {i}. {project['project_name']}
- **冷门指数**: {project['hidden_gem_score']}分 | **他山评分**: {project['tashan_score']}分
- **推荐级别**: {project['recommendation_type']}
- **GitHub**: {project['github_url']} ({project['github_stars']}⭐ {project['github_forks']}🍴)
- **Lobehub**: {project['lobehub_url']}
- **项目类型**: {project['project_type']}
- **可用工具**: {project['tools_available']}个
- **部署方式**: {project['deployment_methods']}
- **核心价值**: {project['lobehub_description'][:100] if project['lobehub_description'] else 'N/A'}...
"""

    report += f"""

## 💡 推荐策略建议

### 高优先级推广 (S级、A级)
1. **顶级冷门宝藏** (S级): 极高质量但几乎无人知晓，应制作专题推荐
2. **优质冷门推荐** (A级): 质量优秀但关注度不高，适合首页推荐位

### 分类推荐策略
1. **按使用场景**: 开发工具、科学教育、旅行交通等垂直分类
2. **按技术门槛**: 无需API密钥 vs 需要配置的项目分开推荐
3. **按部署难度**: npx一键运行 vs 需要环境配置的项目

### 内容包装建议
1. **突出差异化**: 强调"他山发现的隐藏宝藏"
2. **场景化介绍**: 具体使用场景和解决的问题
3. **降低门槛**: 提供详细的部署和使用指南

## 📁 数据文件说明

### complete_analysis.csv
包含所有{len(all_df)}个项目的完整分析数据，字段包括：
- 基础信息：项目名称、作者、GitHub链接等
- 他山评分：总分及各维度评分
- Lobehub信息：描述、评级、URL等
- 冷门分析：冷门推荐指数、推荐级别等

### hidden_gems_recommendations.csv
最终推荐的{len(recommended_df)}个项目，按冷门推荐指数降序排列，可直接用于推广决策。

## ⚖️ 算法说明

本分析采用量化算法，结合：
1. **他山专业评分** (权威性)
2. **GitHub热度数据** (客观性)
3. **功能丰富程度** (实用性)
4. **平台评分差异** (发现性)

确保推荐项目既有专业品质保证，又具备冷门推荐的差异化价值。

## 📊 详细计算示例

以一个具体项目为例说明算法计算过程：

假设某项目：
- 他山评分: 80分
- GitHub Stars: 50个
- 工具数量: 6个
- Lobehub评分: 3分

计算过程：
1. 基础分 = 80 × 0.6 = 48分
2. 热度调节分 = +5分 (Stars在10-100之间)
3. 功能丰富度分 = min(6 × 2, 10) = 10分
4. 价值差异分析分 = max(0, (80 - 3×20) × 0.25) = 5分

最终冷门指数 = 48 + 5 + 10 + 5 = 68分 (A级-优质冷门推荐)

---
*生成时间: 2025年9月2日*
*基于他山MCP评分体系 v1.0*
*算法标准已适当调整以确保30个推荐项目*
"""

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(report)

    print("✅ 综合分析报告已生成: README.md")


if __name__ == "__main__":
    analyze_hidden_gems()
