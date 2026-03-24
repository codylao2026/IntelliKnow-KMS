# IntelliKnow KMS - 产品需求文档 (PRD)
# For Claude Code Development

**版本**: 1.0  
**日期**: 2026-03-19  
**状态**: Ready for Development

---

## 1. 项目概述 / Project Overview

**项目名称**: IntelliKnow KMS (Gen AI-powered Knowledge Management System)  
**项目类型**: 7天MVP开发 - 面试考核项目  
**核心目标**: 构建一个企业级知识管理系统，支持多前端集成、智能文档解析、意图分类路由

### 目标用户
- 企业员工（通过WhatsApp/Teams查询知识）
- 知识管理员（管理文档和意图空间）
- IT管理员（配置集成和安全）

---

## 2. 核心功能 / Core Features

### 2.1 多前端集成 (Multi-Frontend Integration)
| 功能 | 描述 |
|------|------|
| WhatsApp Business API | 接收查询，返回响应，≤3秒延迟 |
| Microsoft Teams Bot | 接收查询，返回响应，支持富文本卡片 |
| 凭证管理 | 安全存储API凭证 |
| 状态监控 | 显示连接状态，提供测试按钮 |

### 2.2 文档驱动知识库 (Document-Driven KB)
| 功能 | 描述 |
|------|------|
| 文档上传 | 拖拽上传PDF/DOCX，支持批量 |
| AI解析 | 自动解析文档内容，提取关键信息 |
| 向量化存储 | 转换为向量存入FAISS |
| 意图关联 | 将文档关联到指定意图空间 |
| **Hybrid Search** | **BM25 + Vector Search 混合检索 (RRF融合)** |
| 重新解析 | 支持更新已上传文档 |

### 2.3 意图编排器 (Orchestrator)
| 功能 | 描述 |
|------|------|
| 默认意图空间 | HR、法务、财务（可自定义增删改） |
| AI分类 | 自动分类用户查询意图 |
| 置信度阈值 | 可配置（默认70%），低于阈值fallback到"通用" |
| 关键词优化 | 支持配置关键词提升分类准确率 |
| 自动路由 | 分类后自动路由到对应知识库 |

### 2.4 响应生成 (Response Generation)
| 功能 | 描述 |
|------|------|
| 生成回答 | 基于检索知识生成简洁回答 |
| 引用来源 | 回答必须标注来源文档 |
| 无匹配处理 | 无相关答案时返回明确提示 |
| 格式适配 | 自动适配WhatsApp/Teams原生格式 |

### 2.5 管理后台 (Admin Dashboard - Streamlit)
| 页面 | 功能 |
|------|------|
| 仪表盘 | 核心指标：查询量、准确率、文档数 |
| 前端集成 | 连接状态、凭证配置、测试按钮 |
| 知识库管理 | 文档列表、搜索筛选、上传删除 |
| 意图配置 | 意图卡片、分类日志、编辑表单 |
| 统计分析 | 查询历史、准确率趋势、热门文档、CSV导出 |

---

## 3. 技术架构 / Technical Architecture

### 技术栈
| 层级 | 技术 |
|------|------|
| 后端框架 | FastAPI |
| 前端框架 | Streamlit |
| 关系数据库 | SQLite |
| 向量数据库 | FAISS |
| 检索引擎 | **BM25 + FAISS Hybrid Search (RRF)** |
| AI能力 | LangChain + 大模型API |
| 前端集成 | WhatsApp Business API, MS Teams Bot API |

### 项目结构
```
IntelliKnow-KMS/
├── app/
│   ├── api/              # FastAPI路由
│   │   ├── documents.py  # 文档API
│   │   ├── intents.py    # 意图API
│   │   ├── query.py      # 查询API
│   │   └── analytics.py  # 统计API
│   ├── services/         # 业务逻辑
│   │   ├── document_service.py
│   │   ├── search_service.py   # Hybrid Search
│   │   ├── intent_service.py
│   │   └── response_service.py
│   ├── models/           # 数据模型
│   └── utils/
│       ├── llm.py        # 大模型调用
│       └── vectorstore.py # FAISS + BM25
├── frontend/
│   └── app.py            # Streamlit管理后台
├── data/
│   ├── sqlite/           # SQLite数据库
│   ├── vectors/          # FAISS索引
│   └── uploads/          # 上传文档
├── config/
│   └── settings.py       # 配置管理
├── requirements.txt
└── README.md
```

---

## 4. 验收标准 / Acceptance Criteria

### 必须达标的6个目标
- [ ] 2个前端工具（WhatsApp + Teams）可正常使用
- [ ] 支持2种文档格式（PDF、DOCX）上传解析
- [ ] 可管理意图空间（HR、法务、财务+自定义）
- [ ] 查询自动分类准确率≥70%
- [ ] 回答准确且标注来源，无幻觉
- [ ] 管理后台有统计分析，支持数据导出

### 性能要求
- 查询响应 ≤3秒
- 单文档解析 ≤30秒
- 系统可用性 ≥99.5%

---

## 5. 开发配合指南 / Claude Code Collaboration

### 快速启动命令
```bash
# 1. 创建并激活虚拟环境
cd ~/ai-projects/IntelliKnow-KMS
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env 填入API密钥

# 4. 启动FastAPI后端
uvicorn app.main:app --reload --port 8000

# 5. 启动Streamlit前端（新终端）
streamlit run frontend/app.py
```

### 模块开发顺序建议
1. **第1天**: 项目初始化、依赖安装、目录结构
2. **第2天**: 文档解析 + 向量存储（SQLite + FAISS）
3. **第3天**: Hybrid Search实现（BM25 + Vector RRF融合）
4. **第4天**: 意图分类 + 响应生成
5. **第5天**: WhatsApp/Teams Bot对接
6. **第6天**: Streamlit管理后台 + 测试优化
7. **第7天**: 文档整理、GitHub推送、演示录制

### 关键实现提示
- **Hybrid Search**: 使用LangChain的EnsembleRetriever，结合FAISS向量检索和BM25（rank_bm25库），按RRF算法融合
- **文档解析**: 使用LangChain的PyPDFLoader和Docx2txtLoader
- **意图分类**: 可用大模型API直接分类，或用BGE嵌入+简单分类器
- **前端适配**: WhatsApp用markdown解析，Teams用Adaptive Cards

### 与我(AITom)配合方式
1. **代码审查**: 完成后可以发给我Review
2. **问题讨论**: 遇到技术难题可以一起讨论
3. **文档更新**: 需要更新需求文档时可以协助
4. **进度同步**: 每天同步一下进度，确保7天完成

---

## 6. 参考资源

- [FastAPI文档](https://fastapi.tiangolo.com/)
- [Streamlit文档](https://docs.streamlit.io/)
- [FAISS Wiki](https://github.com/facebookresearch/faiss/wiki)
- [LangChain文档](https://python.langchain.com/docs/)
- [WhatsApp Business API](https://developers.facebook.com/docs/whatsapp)
- [MS Teams Bot](https://learn.microsoft.com/en-us/microsoftteams/platform/bots/)

---

**Ready to start coding!** 🚀