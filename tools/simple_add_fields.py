#!/usr/bin/env python3
"""
简化的数据库字段添加脚本 - 使用Supabase客户端直接操作
"""
import os

from dotenv import load_dotenv
from supabase import Client, create_client

# 加载.env文件
load_dotenv()


def main():
    """执行数据库迁移"""
    print("🚀 开始添加综合评分字段...")

    try:
        # 从环境变量读取配置
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

        if not url or not key:
            print("❌ 缺少 SUPABASE_URL 或 SUPABASE_SERVICE_ROLE_KEY 环境变量")
            return False

        supabase: Client = create_client(url, key)
        print("✅ 数据库连接成功")

        # 验证表是否存在
        try:
            result = (
                supabase.table("mcp_repository_evaluations")
                .select("github_url")
                .limit(1)
                .execute()
            )
            print(f"✅ 找到 mcp_repository_evaluations 表，当前记录数: {len(result.data)}")
        except Exception as e:
            print(f"❌ 表不存在或无法访问: {e}")
            return False

        # 尝试查询新字段以验证是否已存在
        try:
            result = (
                supabase.table("mcp_repository_evaluations")
                .select(
                    "github_url,success_rate,total_score,test_count,last_calculated_at"
                )
                .limit(1)
                .execute()
            )
            print("✅ 新字段已存在，迁移可能已完成")
            return True
        except Exception as e:
            print(f"⚠️ 新字段不存在，这是正常的: {e}")

        print("💡 由于Supabase RPC限制，请手动执行以下SQL语句:")
        print("=" * 60)

        sql_statements = [
            "ALTER TABLE mcp_repository_evaluations ADD COLUMN IF NOT EXISTS success_rate FLOAT DEFAULT NULL;",
            "ALTER TABLE mcp_repository_evaluations ADD COLUMN IF NOT EXISTS total_score INTEGER DEFAULT NULL;",
            "ALTER TABLE mcp_repository_evaluations ADD COLUMN IF NOT EXISTS test_count INTEGER DEFAULT 0;",
            "ALTER TABLE mcp_repository_evaluations ADD COLUMN IF NOT EXISTS last_calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NULL;",
            "ALTER TABLE mcp_repository_evaluations ADD CONSTRAINT IF NOT EXISTS check_success_rate CHECK (success_rate IS NULL OR (success_rate >= 0.0 AND success_rate <= 100.0));",
            "ALTER TABLE mcp_repository_evaluations ADD CONSTRAINT IF NOT EXISTS check_total_score CHECK (total_score IS NULL OR (total_score >= 0 AND total_score <= 100));",
        ]

        for i, stmt in enumerate(sql_statements, 1):
            print(f"{i}. {stmt}")

        print("=" * 60)
        print("💡 请在Supabase SQL编辑器中执行上述SQL语句")
        print("💡 然后重新运行此脚本进行验证")

        return False  # 返回False表示需要手动操作

    except Exception as e:
        print(f"❌ 操作失败: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
