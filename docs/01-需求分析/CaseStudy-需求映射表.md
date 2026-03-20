# Case Study 需求点映射表
# Case Study Requirements Mapping Table

## 项目目标映射 / Project Objectives Mapping

| Case Study 原文需求 | 对应SRS章节 | 需求ID | 备注 |
|---------------------|-------------|--------|------|
| Build a fully functional, deployed KMS | 1.2 项目目标 | - | 7天完成 |
| Configure and use the KMS via at least 2 common frontend tools | 2.1 多前端集成 | FR-001~FR-008 | WhatsApp+Teams |
| Upload documents to automatically build/update the backend knowledge base | 2.2 文档驱动知识库 | FR-009~FR-019 | PDF+DOCX |
| Define and manage intent spaces | 2.3 意图编排 | FR-020~FR-029 | HR/法务/财务+自定义 |
| Submit queries via integrated frontends, categorized by the orchestrator | 2.3 查询分类+2.4 响应生成 | FR-024~FR-033 | ≥70%准确率 |
| Receive accurate, context-aware responses | 2.4 响应生成 | FR-030~FR-033 | 标注来源 |
| View query history, classification accuracy, and knowledge base analytics | 2.5 管理后台+2.6 统计分析 | FR-034~FR-049 | 支持导出 |

---

## 功能需求详细映射 / Functional Requirements Detailed Mapping

### 3.1 Multi-Frontend Integration (Case Study Section 2)

| Case Study需求 | 对应SRS需求 | 需求ID |
|----------------|-------------|--------|
| Integrate 2 tools (Telegram/Teams/WhatsApp) | WhatsApp + Teams集成 | FR-001~FR-008 |
| Admin credential configuration (secure storage) | 凭证配置与安全存储 | FR-002, FR-006 |
| Real-time query/response sync (≤3s latency) | 响应延迟≤3秒 | FR-004 |
| Status monitoring + error logging | 状态监控+错误日志 | FR-003, FR-007 |
| End-to-end test function | 测试按钮 | FR-003, FR-007 |

### 3.2 Document-Driven Backend KB (Case Study Section 3.1)

| Case Study需求 | 对应SRS需求 | 需求ID |
|----------------|-------------|--------|
| Support 2+ document formats (PDF, DOCX recommended) | PDF+DOCX支持 | FR-010 |
| AI-powered parsing/structuring of content | AI自动解析 | FR-013 |
| Intent space association | 关联意图空间 | FR-015 |
| Manual updates + re-parsing | 重新解析 | FR-016 |
| Semantic search | 语义向量检索 | FR-017~FR-019 |
| Basic error handling | 错误处理 | - |

### 3.3 Orchestrator (Case Study Section 3.1)

| Case Study需求 | 对应SRS需求 | 需求ID |
|----------------|-------------|--------|
| 3 default spaces (HR, Legal, Finance) + custom add/edit/delete | 默认3空间+自定义CRUD | FR-020~FR-023 |
| AI-powered (≥70% configurable confidence) | AI分类+可配置阈值 | FR-024~FR-025 |
| Fallback to "General" space | fallback机制 | FR-026 |
| Admin-guided accuracy improvement | 关键词配置提升准确率 | FR-027 |
| Route queries to relevant KB domains | 自动路由 | FR-028~FR-029 |

### 3.4 Knowledge Retrieval & Response (Case Study Section 3.1)

| Case Study需求 | 对应SRS需求 | 需求ID |
|----------------|-------------|--------|
| Generate concise, cited responses | 生成引用回答 | FR-030~FR-031 |
| Adapt format to frontend tools | 格式适配 | FR-033 |
| Clear "no match" messaging | 无匹配提示 | FR-032 |

### 3.5 Admin UI/UX (Case Study Section 2)

| Case Study需求 | 对应SRS需求 | 需求ID |
|----------------|-------------|--------|
| 5 core screens (Dashboard, Frontend Integration, KB Management, Intent Configuration, Analytics) | 5个管理页面 | FR-034~FR-049 |
| Clean, intuitive, mobile-responsive (optional) | 清晰直观导航 | NFR-004~NFR-006 |
| Document List: Table view with columns | 文档表格 | FR-038 |
| Upload Area: drag-and-drop | 拖拽上传 | FR-009, FR-011 |
| Search/Filter | 搜索筛选 | FR-039~FR-040 |
| Intent Space List: Card view | 意图空间卡片 | FR-042~FR-043 |
| Query Classification Log | 分类日志 | FR-044 |
| Integration Cards: status indicator | 连接状态卡片 | FR-035~FR-037 |

### 3.6 Analytics & History (Case Study Section 3.1)

| Case Study需求 | 对应SRS需求 | 需求ID |
|----------------|-------------|--------|
| Log queries + metrics (timestamp, intent, confidence, response) | 查询日志 | FR-045 |
| Track KB usage | 使用统计 | FR-046~FR-048 |
| Exportable data | 数据导出 | FR-049 |

---

## 非功能需求映射 / Non-Functional Requirements Mapping

| Case Study约束/要求 | 对应SRS需求 | 需求ID |
|---------------------|-------------|--------|
| 7 calendar days | 7天里程碑 | M1~M6 |
| Solo Work, no external collaboration | 单人开发 | - |
| MVP-focused, no over-engineering | MVP优先 | - |
| AI Guidance: document strategic usage | AI使用反思文档 | 交付要求 |
| Tech Stack: Python (FastAPI/Streamlit) + SQLite/FAISS | 技术选型 | 6.1 |
| ≤3s latency | 性能要求 | NFR-001 |

---

## 交付要求映射 / Delivery Requirements Mapping

| Case Study交付要求 | 对应SRS章节 | 说明 |
|--------------------|-------------|------|
| Public GitHub repo (code, docs, AI Usage Reflection) | 8. 交付物 | GitHub仓库 |
| Working demo with 2 frontend integrations, 2+ sample docs, testable query flow | 8. 交付物 | 演示系统 |
| Detailed README (setup, tech stack, integration guide) | 8. 交付物 | README文档 |

---

## ✅ 映射完整性确认

| Case Study核心需求 | SRS覆盖状态 |
|-------------------|------------|
| 多前端集成（2个） | ✅ 完全覆盖 |
| 文档自动解析建KB（2+格式） | ✅ 完全覆盖 |
| 意图分类+路由（≥70%准确率） | ✅ 完全覆盖 |
| 知识检索+回答生成 | ✅ 完全覆盖 |
| 管理后台（5个页面） | ✅ 完全覆盖 |
| 统计分析+导出 | ✅ 完全覆盖 |
| 7天时间约束 | ✅ 已体现 |
| AI使用反思 | ✅ 已包含 |

**额外增强（本次更新）**：
- ✅ Hybrid Search：BM25 + Vector Search 混合检索
- ✅ WhatsApp + Teams（根据用户选择调整）