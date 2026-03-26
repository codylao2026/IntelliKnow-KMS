# 缓存设计与FAISS索引修复方案

## 缓存设计方案

### 架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        TTLCache (通用缓存类)                     │
├─────────────────────────────────────────────────────────────────┤
│  • OrderedDict (LRU淘汰策略)                                     │
│  • TTL过期机制                                                   │
│  • 统计功能 (hits/misses/evictions/hit_rate)                     │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌───────────────┐    ┌────────────────┐    ┌────────────────┐
│ Intent Cache  │    │ LLM Resp Cache │    │ Vector Store   │
├───────────────┤    ├────────────────┤    ├────────────────┤
│ TTL: 24小时   │    │ TTL: 24小时    │    │ 永久(内存常驻) │
│ Max: 100条    │    │ Max: 10000条   │    │ 启动时重建     │
│ 意图列表      │    │ LLM生成结果    │    │ FAISS+BM25索引 │
└───────────────┘    └────────────────┘    └────────────────┘
```

### 缓存配置

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `ENABLE_CACHE` | true | 总开关 |
| `INTENT_CACHE_TTL` | 86400s (24h) | Intent缓存时间 |
| `LLM_RESPONSE_CACHE_TTL` | 86400s (24h) | LLM响应缓存时间 |
| `LLM_RESPONSE_CACHE_MAX_SIZE` | 10000 | 最大缓存条目 |

### 流式查询缓存逻辑

```
流式查询请求
    │
    ▼
检查 LLM 缓存
    │
    ├── 命中 → 逐词输出缓存内容 (模拟流式) ✅
    │
    └── 未命中 → 调用 LLM → 边生成边缓存 → 输出
```

### API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/cache/stats` | 查看所有缓存统计 |
| GET | `/api/cache/config` | 查看缓存配置 |
| POST | `/api/cache/clear` | 清除所有缓存 |
| POST | `/api/cache/clear/intent` | 清除Intent缓存 |
| POST | `/api/cache/clear/llm` | 清除LLM缓存 |
| POST | `/api/cache/clear/vectorstore` | 重置Vector Store |
| POST | `/api/cache/rebuild/vectorstore` | 从数据库重建索引 |

### 日志标识

| 日志 | 含义 |
|------|------|
| `✅ Intent cache HIT` | Intent缓存命中 |
| `❌ Intent cache MISS` | Intent缓存未命中 |
| `✅ LLM response cache HIT` | LLM缓存命中 |
| `❌ LLM response cache MISS` | LLM缓存未命中 |
| `✅ Vector store cache HIT (in memory)` | 向量索引已在内存 |

### 相关文件

| 文件 | 说明 |
|------|------|
| `app/utils/cache.py` | TTLCache通用缓存类 |
| `app/api/cache.py` | 缓存管理API |
| `app/services/intent_service.py` | Intent缓存实现 |
| `app/services/response_service.py` | LLM响应缓存实现 |
| `config/settings.py` | 缓存配置项 |

---

## FAISS 索引修复方案

### 问题根因

```
FAISS索引 (磁盘)          数据库
      │                      │
  doc_id: 1,5,6          doc_id: 8,9 (Finance)
      │                      │
      └────── 不一致 ────────┘
              │
              ▼
       搜索返回 0 结果
```

**原因**：FAISS索引与数据库独立管理，没有事务一致性，导致：
- 文档上传时数据库成功但FAISS可能失败
- 文档删除时FAISS可能失败但数据库成功

### 永久解决方案

**启动时自动重建索引**

```python
# app/main.py lifespan
async with async_session_maker() as session:
    await rebuild_vector_store_from_db(session)
```

### 重建流程

```
服务启动
    │
    ▼
读取数据库 status=completed 的所有文档
    │
    ▼
RecursiveCharacterTextSplitter 分块
    │
    ▼
重新构建 FAISS 索引 + BM25 索引
    │
    ▼
保存到磁盘 + 加载到内存
    │
    ▼
索引与数据库一致 ✅
```

### 效果对比

| 场景 | 修复前 | 修复后 |
|------|--------|--------|
| 每次启动 | 加载旧索引(可能损坏) | 自动重建(保证一致) |
| 文档删除后 | 索引可能不同步 | 重启后自动同步 |
| 文档上传后 | 可能成功/失败不一致 | 重启后保证一致 |

### 相关文件

| 文件 | 说明 |
|------|------|
| `app/main.py` | 启动时自动重建 |
| `app/utils/vectorstore.py` | 重建逻辑实现 |

---

## Analytics 数据说明

### Accuracy 计算

```python
# confidence >= 0.7 的查询视为准确
accurate_queries = WHERE QueryLog.confidence >= 0.7
accuracy = (accurate_queries / total_queries) * 100
```

### 查询记录存储

| 项目 | 说明 |
|------|------|
| 位置 | SQLite: `data/sqlite/intelliknow.db` |
| 表名 | `query_logs` |
| 主要字段 | query, intent_name, confidence, response, sources, status, response_time |

### 常用查询

```sql
-- 查看按日期统计
SELECT COUNT(*) as total, DATE(created_at) as date 
FROM query_logs GROUP BY DATE(created_at) ORDER BY date DESC;

-- 清理历史记录
DELETE FROM query_logs WHERE DATE(created_at) < DATE('now');
```

---

## 更新历史

| 日期 | 变更 |
|------|------|
| 2026-03-26 | 初始版本：缓存设计与FAISS修复方案 |
