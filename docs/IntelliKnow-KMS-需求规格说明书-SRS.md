# IntelliKnow KMS 需求规格说明书
# IntelliKnow KMS Requirements Specification (SRS)

**版本/Version**: 1.0
**日期/Date**: 2026-03-19
**项目名称/Project Name**: IntelliKnow KMS (Gen AI-powered Knowledge Management System)
**状态/Status**: Draft

---

## 1. 项目概述 / Project Overview

### 1.1 项目背景 / Project Background

Many enterprises struggle with fragmented information, inefficient knowledge retrieval, and siloed communication channels. This project aims to build a Gen AI-powered Knowledge Management System (KMS) that addresses these core pain points by providing seamless integration with common frontend communication tools, an intelligent document-driven knowledge base, and an advanced query orchestration module.

众多企业面临信息碎片化、知识检索效率低、沟通渠道分散等痛点。本项目旨在构建一个Gen AI驱动的知识管理系统（KMS），通过与主流前端通讯工具的无缝集成、智能文档驱动的知识库，以及先进的查询编排模块来解决这些核心问题。

### 1.2 项目目标 / Project Objectives

- Build a fully functional, production-ready KMS within 7 calendar days
- Support multi-frontend integration (WhatsApp + Microsoft Teams)
- Enable automatic knowledge base construction from uploaded documents (PDF, DOCX)
- Implement intelligent query intent classification and routing (HR, Legal, Finance)
- Achieve ≥70% classification accuracy with configurable confidence thresholds
- Provide comprehensive admin dashboard with analytics capabilities

- 在7天内构建一个功能完备、生产就绪的KMS
- 支持多前端集成（WhatsApp + Microsoft Teams）
- 支持从上传文档（PDF、DOCX）自动构建知识库
- 实现智能查询意图分类和路由（HR、法务、财务）
- 达到≥70%的分类准确率，支持可配置的置信度阈值
- 提供具有分析功能的综合管理后台

### 1.3 目标用户 / Target Users

| 用户类型 / User Type | 描述 / Description |
|----------------------|---------------------|
| 企业员工 / Enterprise Employees | 通过WhatsApp/Teams查询知识库，获取准确答案 |
| 知识管理员 / Knowledge Administrators | 管理文档、上传内容、配置意图空间、监控系统 |
| IT管理员 / IT Administrators | 管理系统配置、集成设置、安全策略 |

---

## 2. 功能需求 / Functional Requirements

### 2.1 多前端集成模块 / Multi-Frontend Integration Module

#### 2.1.1 WhatsApp Business API集成 / WhatsApp Business API Integration

**FR-001**: 系统应支持通过WhatsApp Business API接收用户查询并返回响应
**FR-001**: The system shall support receiving user queries and returning responses via WhatsApp Business API

**FR-002**: 应支持配置WhatsApp Business API凭证（Phone Number ID, Access Token）
**FR-002**: The system shall support configuring WhatsApp Business API credentials (Phone Number ID, Access Token)

**FR-003**: 应显示连接状态（已连接/未连接）并提供测试功能
**FR-003**: The system shall display connection status (Connected/Disconnected) and provide test functionality

**FR-004**: 响应延迟应≤3秒
**FR-004**: Response latency shall be ≤3 seconds

#### 2.1.2 Microsoft Teams Bot集成 / Microsoft Teams Bot Integration

**FR-005**: 系统应支持通过Microsoft Teams Bot接收用户查询并返回响应
**FR-005**: The system shall support receiving user queries and returning responses via Microsoft Teams Bot

**FR-006**: 应支持配置Microsoft Teams Bot凭证（App ID, App Password, Tenant ID）
**FR-006**: The system shall support configuring Microsoft Teams Bot credentials (App ID, App Password, Tenant ID)

**FR-007**: 应显示连接状态并提供测试功能
**FR-007**: The system shall display connection status and provide test functionality

**FR-008**: 响应格式应适配Teams的原生格式（支持卡片、按钮等富文本）
**FR-008**: Response format shall adapt to Teams native format (supporting cards, buttons, etc.)

### 2.2 文档驱动知识库模块 / Document-Driven Knowledge Base Module

#### 2.2.1 文档上传 / Document Upload

**FR-009**: 应支持拖拽或选择文件方式上传文档
**FR-009**: The system shall support document upload via drag-and-drop or file selection

**FR-010**: 应至少支持PDF和DOCX两种文档格式
**FR-010**: The system shall support at least PDF and DOCX document formats

**FR-011**: 上传时应显示处理进度指示器
**FR-011**: The system shall display a progress indicator during document processing

**FR-012**: 应支持批量上传多个文档
**FR-012**: The system shall support batch uploading of multiple documents

#### 2.2.2 文档解析与向量化 / Document Parsing and Vectorization

**FR-013**: 应使用AI能力自动解析文档内容，提取关键信息
**FR-013**: The system shall automatically parse document content and extract key information using AI capabilities

**FR-014**: 应将解析后的内容转换为向量并存储到向量数据库
**FR-014**: The system shall convert parsed content to vectors and store them in the vector database

**FR-015**: 应支持将文档关联到指定的意图空间
**FR-015**: The system shall support associating documents with designated intent spaces

**FR-016**: 应支持重新解析和更新已上传的文档
**FR-016**: The system shall support re-parsing and updating uploaded documents

#### 2.2.3 知识检索 / Knowledge Retrieval

**FR-017**: 应支持基于语义向量的知识检索
**FR-017**: The system shall support semantic vector-based knowledge retrieval

**FR-017A**: 应支持BM25关键词检索
**FR-017A**: The system shall support BM25 keyword search

**FR-017B**: 应实现Hybrid Search混合检索模式，结合向量检索和BM25检索结果，通过RRF(RReciprocal Rank Fusion)算法融合排名，提升检索准确率
**FR-017B**: The system shall implement Hybrid Search combining vector search and BM25 search, using RRF (Reciprocal Rank Fusion) algorithm to fuse rankings and improve retrieval accuracy

**FR-017C**: 应支持查询改写（Query Rewrite），分析对话历史，使用AI生成优化搜索查询。例如：用户问题"如何在好福利上进行理赔?"，输出优化查询"好福利 理赔 流程 步骤"
**FR-017C**: The system shall support query rewrite, analyzing conversation history and using AI to generate optimized search queries. Example: user query "如何在好福利上进行理赔?" → optimized query "好福利 理赔 流程 步骤"

**FR-017D**: 应实现Rerank重排序环节，对Hybrid Search返回的候选文档进行二次精排，提升最终结果的相关性
**FR-017D**: The system shall implement Rerank step to re-rank candidate documents returned by Hybrid Search, improving final result relevance

**FR-018**: 检索结果应显示相关度分数
**FR-018**: Retrieval results shall display relevance scores

**FR-019**: 应支持按意图空间筛选检索结果
**FR-019**: The system shall support filtering retrieval results by intent space

### 2.3 意图编排与意图空间配置模块 / Orchestrator & Intent Space Configuration Module

#### 2.3.1 意图空间管理 / Intent Space Management

**FR-020**: 系统应预设3个默认意图空间：HR、法务、财务
**FR-020**: The system shall have 3 default intent spaces pre-configured: HR, Legal, Finance

**FR-021**: 应支持创建自定义意图空间
**FR-021**: The system shall support creating custom intent spaces

**FR-022**: 应支持编辑意图空间的名称和描述
**FR-022**: The system shall support editing intent space names and descriptions

**FR-023**: 应支持删除意图空间（需确认无关联文档）
**FR-023**: The system shall support deleting intent spaces (with confirmation that no documents are associated)

#### 2.3.2 查询分类 / Query Classification

**FR-024**: 应使用AI能力对用户查询进行意图分类
**FR-024**: The system shall use AI capabilities to classify user query intents

**FR-025**: 分类置信度阈值应可配置（默认70%）
**FR-025**: Classification confidence threshold shall be configurable (default 70%)

**FR-026**: 低于阈值的查询应fallback到"通用"意图空间
**FR-026**: Queries below the threshold shall fall back to the "General" intent space

**FR-027**: 应支持通过配置关键词提升特定意图空间的分类准确率
**FR-027**: The system shall support configuring keywords to improve classification accuracy for specific intent spaces

#### 2.3.3 查询路由 / Query Routing

**FR-028**: 分类后的查询应自动路由到对应的知识库领域
**FR-028**: Classified queries shall be automatically routed to the corresponding knowledge base domain

**FR-029**: 应记录每次分类和路由的详细信息到日志
**FR-029**: The system shall log detailed information for each classification and routing operation

### 2.4 响应生成模块 / Response Generation Module

**FR-030**: 应基于检索到的知识生成简洁、准确的回答
**FR-030**: The system shall generate concise, accurate responses based on retrieved knowledge

**FR-030A**: 回答应生成文档链接标注，如[doc1]、[doc2]，用户可点击查看原文
**FR-030A**: Responses shall generate document link references like [doc1], [doc2], allowing users to view the original text

**FR-030B**: 应提取相关文档内容并格式化输出，包含关键信息摘录和引用来源
**FR-030B**: The system shall extract relevant document content and format output with key information excerpts and citation sources

**FR-030C**: 应构建提示工程（Prompt Engineering），注入系统提示、插入少样本示例、约束回答必须基于源内容
**FR-030C**: The system shall build prompt engineering with system prompts, few-shot examples, and constraints that responses must be based on source content

**FR-031**: 回答应标注来源文档
**FR-031**: Responses shall cite source documents

**FR-032**: 当无匹配知识时，应返回清晰的"无相关答案"提示
**FR-032**: When no matching knowledge is found, the system shall return a clear "No relevant answer" message

**FR-033**: 回答格式应适配不同前端工具（WhatsApp/Teams的原生格式）
**FR-033**: Response format shall adapt to different frontend tools (native format for WhatsApp/Teams)

### 2.5 管理后台模块 / Admin Dashboard Module

#### 2.5.1 仪表盘 / Dashboard

**FR-034**: 应显示核心指标概览：查询总量、今日查询量、分类准确率、知识库文档数
**FR-034**: The system shall display core metrics overview: total queries, today's queries, classification accuracy, knowledge base document count

#### 2.5.2 前端集成管理 / Frontend Integration Management

**FR-035**: 应显示各前端工具的连接状态卡片
**FR-035**: The system shall display connection status cards for each frontend tool

**FR-036**: 应支持配置和修改前端凭证
**FR-036**: The system shall support configuring and modifying frontend credentials

**FR-037**: 应提供测试按钮，发送测试查询验证集成
**FR-037**: The system shall provide a test button to send test queries for integration verification

#### 2.5.3 知识库管理 / Knowledge Base Management

**FR-038**: 应以表格形式列出所有文档（名称、上传时间、格式、大小、状态）
**FR-038**: The system shall list all documents in table format (name, upload date, format, size, status)

**FR-038A**: 文档表格应包含以下列：Document Name（文档名称）、Upload Date（上传日期）、Format（格式）、Size（大小）、Status（状态：Processed/Pending/Error处理中/已处理/错误）、Actions（操作：View/查看、Delete/删除、Update/更新）**
**FR-038A**: Document list table shall include columns: Document Name, Upload Date, Format, Size, Status (Processed/Pending/Error), Actions (View/Delete/Update)

**FR-039**: 应支持搜索文档名称/关键词

**FR-039A**: 应支持Search/Filter（搜索/筛选）功能：
- 搜索栏：可通过文档名称或关键词搜索文档
- 筛选器：支持按格式（Format）、上传日期（Upload Date）、意图空间关联（Intent Space Association）进行筛选
**FR-039A**: The system shall support Search/Filter functionality: Search bar to find documents by name/keyword; filter by format, upload date, or intent space association
**FR-039**: The system shall support searching documents by name/keywords

**FR-040**: 应支持按格式、上传时间、意图空间筛选
**FR-040**: The system shall support filtering by format, upload date, and intent space

**FR-041**: 应支持查看、删除文档操作
**FR-041**: The system shall support viewing and deleting documents

#### 2.5.4 意图配置 / Intent Configuration

**FR-042**: 应以卡片形式展示意图空间列表
**FR-042**: The system shall display intent space list in card format

**FR-043**: 每个卡片应显示：名称、描述、关联文档数、分类准确率
**FR-043**: Each card shall display: name, description, number of associated documents, **classification accuracy rate**

**FR-043A**: 意图空间卡片视图应显示：
- 意图空间名称（Name）
- 意图空间描述（Description）
- 关联文档数（Number of associated documents）
- 分类准确率（Classification accuracy rate）

**FR-044A**: 查询分类日志表格应显示：
- 时间（Time）
- 查询内容（Query content）
- 识别到的意图空间（Detected intent space）
- 分类置信度分数（Classification confidence score）
- 响应状态（Response status: Success/Failed）
**FR-044A**: Query Classification Log table shall display: Time, Query content, Detected intent space, Classification confidence score, Response status (Success/Failed)

#### 2.5.5 统计分析 / Analytics

**FR-045**: 应记录所有查询日志（时间、用户、意图、置信度、响应状态）
**FR-045**: The system shall log all query details (time, user, intent, confidence, response status)

**FR-046**: 应统计并展示分类准确率趋势图
**FR-046**: The system shall calculate and display classification accuracy trend chart

**FR-047**: 应展示各意图空间的使用频率（热门意图Top10）
**FR-047**: The system shall display usage frequency by intent space (Top 10 popular intents)

**FR-048**: 应展示热门文档Top10（按访问次数）
**FR-048**: The system shall display Top 10 popular documents (by access count)

**FR-049**: 应支持导出查询日志数据为CSV格式
**FR-049**: The system shall support exporting query log data in CSV format

---

## 3. 非功能需求 / Non-Functional Requirements

### 3.1 性能要求 / Performance Requirements

| 指标 / Metric | 要求 / Requirement |
|---------------|-------------------|
| 查询响应时间 / Query Response Time | ≤3秒 / ≤3 seconds |
| 文档解析时间 / Document Parsing Time | 单个文档≤30秒 / Single document ≤30 seconds |
| 系统可用性 / System Availability | ≥99.5% |
| 并发支持 / Concurrent Support | 支持≥10个并发用户 / Support ≥10 concurrent users |

### 3.2 安全要求 / Security Requirements

**NFR-001**: 凭证应安全存储，加密保存
**NFR-001**: Credentials shall be stored securely with encryption

**NFR-002**: API接口应实现基础的身份验证
**NFR-002**: API interfaces shall implement basic authentication

**NFR-003**: 敏感操作应记录审计日志
**NFR-003**: Sensitive operations shall be logged for audit

### 3.3 可用性要求 / Usability Requirements

**NFR-004**: 管理后台应提供清晰、直观的导航
**NFR-004**: Admin dashboard shall provide clear, intuitive navigation

**NFR-005**: 管理后台界面应符合以下设计规范：
- **布局**：清洁、模块化设计，4个核心板块可通过顶部/侧边导航菜单访问：前端集成（Frontend Integration）、知识库管理（Knowledge Base Management）、意图空间配置（Intent Space Configuration）、统计分析（Analytics）
- **配色方案**：柔和、专业的浅色基调（白色/浅灰背景），每个模块使用区分明显的强调色：
  - 前端集成模块 = 蓝色（blue）
  - 知识库管理模块 = 绿色（green）
  - 意图空间配置模块 = 紫色（purple）
  - 统计分析模块 = 橙色（orange）
- **模块化设计**：每个区域为圆角卡片（12px圆角），内边距16px，标题清晰；避免杂乱布局，优先展示关键操作按钮（如"添加前端集成"、"上传文档"、"创建意图空间"）
- **响应式设计**：支持桌面端访问，移动端可选适配

**NFR-005**: The admin dashboard interface shall follow these design guidelines:
- **Layout**: Clean, modular dashboard with 4 key sections accessible via top/side navigation: Frontend Integration, Knowledge Base Management, Intent Space Configuration, and Analytics
- **Color Scheme**: Soft, professional neutral base (white/light gray background) with distinct accent colors for each module (Frontend Integration = blue, Knowledge Base = green, Intent Space = purple, Analytics = orange)
- **Modular Design**: Each section is a card with rounded corners (12px radius), padding (16px), and clear headings; avoid cluttered layouts—prioritize key actions ("Add Frontend Integration," "Upload Document," "Create Intent Space")
- **Responsive Design**: Desktop-first, mobile-optional

**NFR-005**: 上传区域应有明确的拖拽提示和支持格式说明
**NFR-005**: Upload area shall have clear drag-and-drop hints and supported format descriptions

**NFR-006**: 所有错误应有友好的提示信息
**NFR-006**: All errors shall have user-friendly error messages

### 3.4 可扩展性要求 / Scalability Requirements

**NFR-007**: 系统架构应支持轻松添加新的前端集成
**NFR-007**: System architecture shall support easily adding new frontend integrations

**NFR-008**: 知识库应支持横向扩展（增加向量库容量）
**NFR-008**: Knowledge base shall support horizontal scaling (increasing vector database capacity)

**NFR-009**: 大模型调用应抽象为独立模块，便于切换不同provider
**NFR-009**: LLM calls shall be abstracted as independent module for easy provider switching

---

## 4. 用户故事 / User Stories

| ID | 用户 / User | 故事 / Story | 优先级 / Priority |
|----|-------------|--------------|-------------------|
| US-001 | 企业员工 | 作为企业员工，我想通过WhatsApp/Teams查询公司知识库，快速获取准确答案，这样就不需要四处寻找资料或等待同事回复 | P0 |
| US-001 | Enterprise Employee | As an enterprise employee, I want to query the company knowledge base via WhatsApp/Teams to get accurate answers quickly, so I don't have to search around or wait for colleague responses | P0 |
| US-002 | 知识管理员 | 作为知识管理员，我想上传PDF/DOCX文档到知识库，系统自动解析并向量化，这样就能快速构建公司知识资产 | P0 |
| US-002 | Knowledge Administrator | As a knowledge administrator, I want to upload PDF/DOCX documents to the knowledge base with automatic parsing and vectorization, so I can quickly build company knowledge assets | P0 |
| US-003 | 知识管理员 | 作为知识管理员，我想管理意图空间（HR、法务、财务等），配置分类规则，这样查询能被准确路由到相关领域 | P0 |
| US-003 | Knowledge Administrator | As a knowledge administrator, I want to manage intent spaces (HR, Legal, Finance, etc.) and configure classification rules, so queries can be accurately routed to relevant domains | P0 |
| US-004 | IT管理员 | 作为IT管理员，我想配置WhatsApp和Teams的Bot凭证，测试连接状态，这样能确保前端集成正常工作 | P1 |
| US-004 | IT Administrator | As an IT administrator, I want to configure WhatsApp and Teams Bot credentials and test connection status, so I can ensure frontend integrations work properly | P1 |
| US-005 | 知识管理员 | 作为知识管理员，我想查看查询统计和分析数据，了解知识库使用情况和分类准确率，这样能持续优化系统 | P1 |
| US-005 | Knowledge Administrator | As a knowledge administrator, I want to view query statistics and analytics to understand knowledge base usage and classification accuracy, so I can continuously optimize the system | P1 |

---

## 5. 验收标准 / Acceptance Criteria

### 5.1 多前端集成 / Multi-Frontend Integration

| ID | 验收条件 / Acceptance Criteria | 测试方法 / Test Method |
|----|-------------------------------|----------------------|
| AC-001 | 通过WhatsApp发送查询，能在3秒内收到准确回答 | 手动测试 |
| AC-001 | Sending a query via WhatsApp returns an accurate response within 3 seconds | Manual test |
| AC-002 | 通过Microsoft Teams发送查询，能在3秒内收到准确回答 | 手动测试 |
| AC-002 | Sending a query via Microsoft Teams returns an accurate response within 3 seconds | Manual test |
| AC-003 | 管理后台显示两个前端的连接状态 | 手动测试 |
| AC-003 | Admin dashboard displays connection status for both frontends | Manual test |

### 5.2 文档知识库 / Document Knowledge Base

| ID | 验收条件 / Acceptance Criteria | 测试方法 / Test Method |
|----|-------------------------------|----------------------|
| AC-004 | 上传PDF文档，系统自动解析并可检索到内容 | 手动测试 |
| AC-004 | Uploading a PDF document, system automatically parses and content is searchable | Manual test |
| AC-005 | 上传DOCX文档，系统自动解析并可检索到内容 | 手动测试 |
| AC-005 | Uploading a DOCX document, system automatically parses and content is searchable | Manual test |
| AC-006 | 文档列表显示所有上传文档的详细信息 | 手动测试 |
| AC-006 | Document list displays detailed information for all uploaded documents | Manual test |

### 5.3 意图分类 / Intent Classification

| ID | 验收条件 / Acceptance Criteria | 测试方法 / Test Method |
|----|-------------------------------|----------------------|
| AC-007 | 查询能自动分类到正确的意图空间，准确率≥70% | 统计100次查询 |
| AC-007 | Queries are automatically classified to correct intent spaces with accuracy ≥70% | Statistics from 100 queries |
| AC-008 | 低于置信度阈值的查询自动fallback到"通用" | 手动测试 |
| AC-008 | Queries below confidence threshold automatically fall back to "General" | Manual test |
| AC-009 | 可创建、编辑、删除自定义意图空间 | 手动测试 |
| AC-009 | Can create, edit, delete custom intent spaces | Manual test |

### 5.4 管理后台 / Admin Dashboard

| ID | 验收条件 / Acceptance Criteria | 测试方法 / Test Method |
|----|-------------------------------|----------------------|
| AC-010 | 仪表盘显示核心指标数据 | 手动测试 |
| AC-010 | Dashboard displays core metric data | Manual test |
| AC-011 | 可通过后台配置前端凭证并测试连接 | 手动测试 |
| AC-011 | Can configure frontend credentials via backend and test connection | Manual test |
| AC-012 | 可查看查询历史和统计数据 | 手动测试 |
| AC-012 | Can view query history and statistics | Manual test |
| AC-013 | 可导出查询日志为CSV | 手动测试 |
| AC-013 | Can export query logs as CSV | Manual test |

---

## 6. 技术架构 / Technical Architecture

### 6.1 技术选型 / Technology Stack

#### 6.1.1 开发阶段模型选型（推荐）

| 用途 | 模型 | API提供商 | 说明 |
|------|------|-----------|------|
| 向量嵌入 / Embedding | BGE-M3 (BAAI/bge-m3) | SiliconCloud (免费) | 多语言+长文本(8K)+混合检索 |
| 重排序 / Rerank | BGE-Reranker-v2-M3 (BAAI/bge-reranker-v2-m3) | SiliconCloud (免费) | 轻量高效(0.5B) |
| 大语言模型 / LLM | MiniMax2.5 (abab6.5s-chat) | SiliconCloud (免费) | 中文理解强，性价比高 |
| 意图分类 / Intent Classification | MiniMax2.5 | SiliconCloud (免费) | 通过LLM函数调用实现 |

#### 6.1.2 生产环境可选（预留切换接口）

| 用途 | 模型 | 说明 |
|------|------|------|
| 向量嵌入 | Azure OpenAI text-embedding-3-small | AIA生产环境使用 |
| 重排序 | BCE-Reranker | 网易有道开源，可本地部署 |
| 大语言模型 | Azure OpenAI GPT-4 | 企业合规要求 |

#### 6.1.3 基础技术栈

| 层级 / Layer | 技术 / Technology | 说明 / Description |
|--------------|------------------|---------------------|
| 后端框架 / Backend Framework | FastAPI | 高性能Python Web框架，支持自动API文档 / High-performance Python web framework with automatic API docs |
| 前端框架 / Frontend Framework | Streamlit | 快速构建数据应用管理后台 / Rapid development of data app admin dashboard |
| 关系数据库 / Relational Database | SQLite | 轻量级嵌入式数据库 / Lightweight embedded database |
| 向量数据库 / Vector Database | FAISS | 高效向量相似度检索 / Efficient vector similarity search |
| 检索增强 / Retrieval Enhancement | BM25 + RRF混合检索 | 关键词+向量混合，使用RRF算法融合排名 |
| AI编排 / AI Orchestration | LangChain | 文档解析、意图分类、回答生成 / Document parsing, intent classification, response generation |
| 前端集成 / Frontend Integration | WhatsApp Business API, Microsoft Teams Bot API | 消息收发、响应适配 / Message sending/receiving, response adaptation |

> **备注**: 开发阶段使用SiliconCloud免费API，生产环境可无缝切换到Azure OpenAI，只需修改配置文件中的API端点和密钥。

### 6.2 系统架构图 / System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        Admin Dashboard (Streamlit)             │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌───────────┐ │
│  │  Dashboard  │ │  Frontend   │ │     KB      │ │  Intent   │ │
│  │             │ │ Integration │ │ Management  │ │ Config    │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └───────────┘ │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API Layer (FastAPI)                        │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌───────────┐ │
│  │  Document   │ │   Intent    │ │   Query     │ │ Analytics │ │
│  │   API       │ │   API       │ │   API       │ │   API     │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └───────────┘ │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Service Layer                                │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌───────────┐ │
│  │  Document   │ │   Intent    │ │   RAG       │ │ Response  │ │
│  │  Processor  │ │ Classifier  │ │  Engine     │ │ Generator │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └───────────┘ │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Data Layer                                 │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌───────────┐ │
│  │   SQLite    │ │    FAISS    │ │   Config    │ │   Log     │ │
│  │  (Metadata) │ │  (Vectors)  │ │   Store     │ │   Store   │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └───────────┘ │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                   External Integrations                         │
│  ┌─────────────┐ ┌─────────────┐ ┌───────────────────────────┐ │
│  │  WhatsApp   │ │   MS Teams  │ │   SiliconCloud API        │ │
│  │  Business   │ │    Bot      │ │ (BGE-M3 + Rerank + LLM)  │ │
│  └─────────────┘ └─────────────┘ └───────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘

```

### 6.3 检索增强流程 / Retrieval Enhancement Flow

```
用户查询 ──▶ 查询改写(FR-017C) ──▶ Hybrid Search (BM25+Vector)
            (AI分析历史+优化查询)      (RRF融合)
                        │
                        ▼
               Rerank二次精排(FR-017D) ──▶ 提示工程构建(FR-030C)
                        │                      │
                        ▼                      ▼
                   文档链接生成          LLM生成回答
                    [doc1],[doc2]        (格式+引用)
```
```

---

## 7. 里程碑 / Milestones

| 里程碑 / Milestone | 任务 / Tasks | 计划日期 / Planned Date |
|-------------------|-------------|---------------------|
| M1: 环境搭建完成 | 项目目录结构创建、依赖安装、SiliconCloud API配置 | 第1天 / Day 1 |
| M2: 核心模块开发完成 | 文档解析、Hybrid Search、Rerank、查询改写、提示工程、响应生成 | 第2-3天 / Day 2-3 |
| M3: 意图分类+前端集成完成 | 意图分类器开发、WhatsApp/Teams Bot对接、消息同步 | 第4天 / Day 4 |
| M4: 管理后台完成 | 5个核心页面开发完成 | 第5天 / Day 5 |
| M5: 测试与优化完成 | 全流程测试、Bug修复、性能优化 | 第6天 / Day 6 |
| M6: PPT演示制作 | 5-7页演示PPT：架构设计、高精度低延迟方案、实施计划、技术选型、Demo截图、关键解决方案 | 第6天 / Day 6 |
| M7: 交付物完成 | GitHub仓库、README、演示视频、PPT演示 | 第7天 / Day 7 |

> **注意**：AIA要求提供5-7页演示PPT，包含：架构设计、如何获得高精度和低延迟、Demo后实施计划、技术选择考量、Demo截图、关键技术与解决方案/亮点/优势
|                                                 |                               |                     |

---

## 8. 交付物 / Deliverables

| 交付物 / Deliverable | 描述 / Description |
|---------------------|---------------------|
| 公开GitHub仓库 | 包含完整代码、文档、AI使用反思 |
| 工作演示 | 本地可运行的完整系统，支持WhatsApp+Teams查询 |
| 示例文档 | 至少2个示例文档（PDF/DOCX） |
| 测试流程 | 可测试的完整查询流程 |
| 详细README | 安装说明、技术栈说明、集成指南 |
| **演示PPT (新增)** | **5-7页PPT，包含：架构设计、高精度低延迟方案、实施计划、技术选型、Demo截图、关键解决方案/亮点/优势** |

---

**文档结束 / End of Document**