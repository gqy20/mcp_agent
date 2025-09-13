# Supabase MCP测试数据访问规范

## 📋 概述

本规范定义了如何通过标准化方式访问MCP测试结果数据库，遵循Linus的"好品味"原则：简洁、高效、无特殊情况。

**作者**: AI Assistant (Linus式设计)
**版本**: 1.0.0
**更新**: 2025-08-21

---

## 🔧 连接配置

### 基本配置
```python
# 必需的配置参数
SUPABASE_URL = "https://vmikqjfxbdvfpakvwoab.supabase.co"
SUPABASE_SERVICE_ROLE_KEY = "your-service-role-key"

# Python连接示例
from supabase import create_client

client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
```

### 连接验证
```python
def verify_connection():
    """连接验证 - 标准方式"""
    try:
        result = client.from_('mcp_test_results').select('test_id').limit(1).execute()
        return len(result.data) >= 0
    except Exception as e:
        print(f"连接失败: {e}")
        return False
```

---

## 📊 数据结构

### 核心表：mcp_test_results

**设计原则**: 单表设计，一次测试一行记录，无复杂JOIN

```sql
CREATE TABLE mcp_test_results (
    -- 主键和时间戳
    test_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    test_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- 工具标识 (核心信息)
    tool_identifier TEXT NOT NULL,  -- URL或package name
    tool_name TEXT,
    tool_author TEXT,
    tool_category TEXT,

    -- 测试状态 (布尔值，无条件分支)
    test_success BOOLEAN NOT NULL,
    deployment_success BOOLEAN NOT NULL,
    communication_success BOOLEAN NOT NULL,

    -- 性能指标 (核心数据)
    available_tools_count INTEGER DEFAULT 0,
    test_duration_seconds FLOAT NOT NULL,

    -- 错误信息
    error_messages TEXT[],

    -- 详细信息 (JSONB - 灵活存储)
    test_details JSONB DEFAULT '{}',    -- 详细测试结果
    environment_info JSONB DEFAULT '{}', -- 环境信息

    -- 审计信息
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

---

## 🔍 标准查询接口

### 1. 基础查询

#### 获取所有测试记录
```python
def get_all_tests(limit=100):
    """获取所有测试记录"""
    result = client.from_('mcp_test_results').select('*').limit(limit).execute()
    return result.data
```

#### 按成功状态查询
```python
def get_tests_by_status(success_status: bool):
    """按成功状态查询"""
    result = client.from_('mcp_test_results').select('*').eq('test_success', success_status).execute()
    return result.data
```

#### 按时间范围查询
```python
def get_tests_by_time_range(start_time: str, end_time: str = None):
    """按时间范围查询"""
    query = client.from_('mcp_test_results').select('*').gte('test_timestamp', start_time)
    if end_time:
        query = query.lte('test_timestamp', end_time)
    result = query.execute()
    return result.data
```

### 2. 聚合查询

#### 成功率统计
```python
def get_success_stats():
    """获取成功率统计"""
    result = client.from_('mcp_test_results').select('test_success', 'deployment_success', 'communication_success').execute()

    total = len(result.data)
    if total == 0:
        return {'total': 0}

    test_success = sum(1 for r in result.data if r['test_success'])
    deployment_success = sum(1 for r in result.data if r['deployment_success'])
    communication_success = sum(1 for r in result.data if r['communication_success'])

    return {
        'total': total,
        'test_success_rate': test_success / total,
        'deployment_success_rate': deployment_success / total,
        'communication_success_rate': communication_success / total
    }
```

#### 工具作者统计
```python
def get_author_stats():
    """获取作者统计 - 无GROUP BY方式"""
    result = client.from_('mcp_test_results').select('tool_author', 'tool_name').execute()

    author_stats = {}
    for record in result.data:
        author = record['tool_author'] or 'Unknown'
        if author not in author_stats:
            author_stats[author] = 0
        author_stats[author] += 1

    return sorted(author_stats.items(), key=lambda x: x[1], reverse=True)
```

### 3. JSONB查询

#### 查询详细测试结果
```python
def get_tests_with_specific_test_count(test_count: int):
    """查询包含特定测试数量的记录"""
    result = client.from_('mcp_test_results').select('*').contains('test_details', {'total_tests': test_count}).execute()
    return result.data
```

#### 查询特定平台测试
```python
def get_tests_by_platform(platform: str):
    """查询特定平台的测试"""
    result = client.from_('mcp_test_results').select('*').contains('environment_info', {'platform': platform}).execute()
    return result.data
```

### 4. 性能优化查询

#### 最新测试记录 (使用索引)
```python
def get_recent_tests(limit=10):
    """获取最新测试记录"""
    result = client.from_('mcp_test_results').select('*').order('test_timestamp', desc=True).limit(limit).execute()
    return result.data
```

#### 特定工具的测试历史
```python
def get_tool_history(tool_identifier: str):
    """获取特定工具的测试历史"""
    result = client.from_('mcp_test_results').select('*').eq('tool_identifier', tool_identifier).order('test_timestamp', desc=True).execute()
    return result.data
```

---

## 📈 性能最佳实践

### 1. 查询优化

- **使用索引字段**: `test_timestamp`, `tool_identifier`, `test_success`
- **限制结果数量**: 始终使用`limit()`
- **避免全表扫描**: 使用WHERE条件
- **JSONB查询**: 使用`contains()`而非复杂嵌套查询

### 2. 批量操作

```python
def batch_insert(records: list, batch_size=100):
    """批量插入 - 提高性能"""
    success_count = 0
    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        try:
            result = client.table('mcp_test_results').insert(batch).execute()
            success_count += len(batch)
        except Exception as e:
            print(f"批次 {i//batch_size + 1} 插入失败: {e}")
    return success_count
```

---

## 🚨 错误处理

### 标准错误码

| 错误类型 | 错误码 | 描述 |
|---------|--------|------|
| 连接错误 | `CONN_001` | 数据库连接失败 |
| 认证错误 | `AUTH_001` | API密钥无效 |
| 查询错误 | `QUERY_001` | SQL语法错误 |
| 数据错误 | `DATA_001` | 数据格式不正确 |
| 网络错误 | `NET_001` | 网络连接超时 |

### 错误处理模式

```python
def safe_query(query_func, *args, **kwargs):
    """安全查询包装器"""
    try:
        return query_func(*args, **kwargs)
    except Exception as e:
        error_code = "UNKNOWN"
        if "connection" in str(e).lower():
            error_code = "CONN_001"
        elif "auth" in str(e).lower():
            error_code = "AUTH_001"
        elif "invalid" in str(e).lower():
            error_code = "QUERY_001"

        return {
            'success': False,
            'error_code': error_code,
            'error_message': str(e),
            'data': []
        }
```

---

## 📝 使用示例

### 完整示例应用

```python
#!/usr/bin/env python3
"""
MCP测试数据访问示例
"""

from supabase import create_client
from datetime import datetime, timedelta

class MCPTestDataAccess:
    """MCP测试数据访问类 - 标准化接口"""

    def __init__(self, url: str, key: str):
        self.client = create_client(url, key)

    def get_daily_summary(self, date: str = None):
        """获取日报摘要"""
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')

        start_time = f"{date}T00:00:00Z"
        end_time = f"{date}T23:59:59Z"

        tests = self.client.from_('mcp_test_results').select('*').gte('test_timestamp', start_time).lte('test_timestamp', end_time).execute()

        if not tests.data:
            return {'date': date, 'total': 0, 'summary': '无测试数据'}

        total = len(tests.data)
        successful = sum(1 for t in tests.data if t['test_success'])

        return {
            'date': date,
            'total': total,
            'successful': successful,
            'success_rate': successful / total,
            'summary': f"{date}: {successful}/{total} 测试成功"
        }

    def get_tool_performance_ranking(self, limit=10):
        """获取工具性能排名"""
        result = self.client.from_('mcp_test_results').select('tool_name', 'test_duration_seconds', 'test_success').order('test_duration_seconds').limit(limit).execute()

        ranking = []
        for i, record in enumerate(result.data, 1):
            status = "✅" if record['test_success'] else "❌"
            ranking.append({
                'rank': i,
                'tool_name': record['tool_name'],
                'duration': record['test_duration_seconds'],
                'status': status
            })

        return ranking

    def health_check(self):
        """系统健康检查"""
        try:
            result = self.client.from_('mcp_test_results').select('test_id').limit(1).execute()
            return {
                'status': 'healthy',
                'connection': 'ok',
                'response_time': 'normal'
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'connection': 'failed',
                'error': str(e)
            }

# 使用示例
if __name__ == "__main__":
    # 初始化
    data_access = MCPTestDataAccess(
        url="https://vmikqjfxbdvfpakvwoab.supabase.co",
        key="your-service-role-key"
    )

    # 健康检查
    health = data_access.health_check()
    print(f"系统状态: {health}")

    # 获取今日摘要
    summary = data_access.get_daily_summary()
    print(f"今日摘要: {summary}")

    # 获取性能排名
    ranking = data_access.get_tool_performance_ranking(5)
    print("性能排名:")
    for item in ranking:
        print(f"  {item['rank']}. {item['tool_name']} - {item['duration']:.2f}s {item['status']}")
```

---

## 🛡️ 安全注意事项

1. **API密钥保护**: 永远不要在代码中硬编码密钥
2. **最小权限**: 使用合适的服务角色权限
3. **连接池**: 复用数据库连接，避免频繁创建
4. **查询限制**: 始终设置合理的查询限制
5. **错误日志**: 记录错误但不暴露敏感信息

---

## 📚 版本更新日志

### v1.0.0 (2025-08-21)
- 初始版本发布
- 单表设计规范
- 标准查询接口
- 完整示例代码
- 错误处理规范

---

**联系方式**: 如有问题或建议，请通过项目Issues反馈。

*"Talk is cheap. Show me the code." - Linus Torvalds*
