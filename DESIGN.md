# IntelliKnow KMS - Technical Design Document

## Overview

**IntelliKnow KMS** (Knowledge Management System) is a Gen AI-powered enterprise knowledge management system that enables employees to query internal documents via natural language through integrated messaging platforms.

### Key Capabilities
- **Multi-channel Integration**: Telegram, Feishu (WebSocket)
- **Hybrid Search**: FAISS + BM25 with RRF fusion
- **Intelligent Intent Classification**: LLM + Keyword hybrid classification
- **RAG Pipeline**: Retrieval-augmented generation with source citations
- **Admin Dashboard**: Streamlit-based management interface

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           User Interfaces                                │
│  ┌──────────┐  ┌──────────┐                              ┌────────┐ │
│  │ Telegram │  │  Feishu  │                              │Web UI  │ │
│  │  Bot    │  │  Bot(WS) │                              │        │ │
│  └────┬─────┘  └────┬─────┘                              └────┬───┘ │
└───────┼─────────────┼─────────────────────────────────────────────┼──────┘
        │             │                                             │
        └─────────────┴─────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        FastAPI Backend (Port 8000)                     │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                         API Layer                               │   │
│  │  /api/documents  |  /api/intents  |  /api/query  | /api/...  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                    │                                      │
│                                    ▼                                      │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                      Service Layer                               │   │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌──────────┐  │   │
│  │  │  Document   │ │   Search    │ │  Response   │ │  Intent  │  │   │
│  │  │  Service   │ │  Service    │ │  Service    │ │ Service  │  │   │
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └──────────┘  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         Data Layer                                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                    │
│  │   SQLite    │  │    FAISS    │  │    BM25     │                    │
│  │  (Metadata) │  │  (Vectors)  │  │  (Keyword)  │                    │
│  └─────────────┘  └─────────────┘  └─────────────┘                    │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Core Components

### 1. Document Processing Pipeline

```
Upload → Parse → Chunk → Vectorize → Index
```

| Component | Description |
|----------|-------------|
| Parser | PDF, DOCX, TXT support via pypdf, docx2txt |
| Chunker | Configurable chunk size (default: 800) with overlap (50) |
| Vectorizer | BGE-M3 embeddings via SiliconCloud API |
| Indexer | FAISS + BM25 hybrid indexing |

### 2. Search Pipeline (Hybrid Search)

```
Query → Intent Classification → Hybrid Search → Rerank → Generate Response
```

#### Hybrid Search with RRF

```python
# RRF (Reciprocal Rank Fusion)
RRF_SCORE = Σ (1 / (k + rank(d))) for each retriever
# k = 60 (constant)
# Weights: BM25=0.5, FAISS=0.5
```

#### Reranking
- Uses BGE-Reranker-v2-M3 model
- Top-K results after reranking: 4
- Skipped when search results ≤ 2

### 3. Intent Classification

**Hybrid Approach**: Combines LLM classification with keyword matching

```
Query → [LLM Classification] ─┬─→ Weighted Fusion → Final Intent
              [Keyword Match] ─┘
```

| Parameter | Value |
|----------|-------|
| LLM Weight | 0.5 |
| Keyword Weight | 0.5 |
| Default Threshold | 0.70 |
| Fallback Intent | "General" |

### 4. Response Generation

```python
# Prompt Structure
SYSTEM_PROMPT = """
You are an enterprise knowledge management assistant.
Answer based ONLY on provided knowledge base documents.
Cite sources using [docN] format.
"""

# RAG Prompt
KNOWLEDGE BASE DOCUMENTS:
doc1: filename---content
doc2: filename---content

USER QUESTION: {query}

ANSWERING REQUIREMENTS:
- Answer based ONLY on knowledge base content
- Cite each fact using [docN] format
- Answer in the same language as question
```

---

## Frontend Integration

### Supported Platforms

| Platform | Protocol | Status |
|----------|----------|--------|
| Telegram | Polling | ✅ |
| Feishu | WebSocket (Long Connection) | ✅ |

### Feishu Integration (WebSocket)

- **No public URL required**: Uses long connection mode
- **Automatic reconnection**: With exponential backoff
- **Event handler**: Registered for `im.message.receive_v1`

### Telegram Integration

- **Polling mode**: Long polling with error handling
- **SSL handling**: Proxy configuration support

---

## Data Models

### Database Schema (SQLite)

```
Documents
├── id (PK)
├── name
├── file_type (pdf/docx/txt)
├── file_path
├── content (extracted text)
├── intent_id (FK)
├── status (pending/processing/completed/failed)
├── vector_ids (JSON)
└── metadata (JSON)

Intents
├── id (PK)
├── name
├── description
├── keywords (JSON array)
└── is_default

QueryLogs
├── id (PK)
├── query
├── intent_name
├── intent_id
├── confidence
├── response
├── sources (JSON array)
├── frontend
├── status
└── response_time

Configs
├── key (PK)
└── value
```

---

## API Endpoints

### Documents
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/documents` | List all documents |
| POST | `/api/documents/upload` | Upload new document |
| GET | `/api/documents/{id}` | Get document details |
| DELETE | `/api/documents/{id}` | Delete document |
| PUT | `/api/documents/{id}/content` | Update content |
| POST | `/api/documents/reparse-batch` | Batch reprocess |

### Intents
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/intents` | List all intents |
| POST | `/api/intents` | Create intent |
| PUT | `/api/intents/{id}` | Update intent |
| DELETE | `/api/intents/{id}` | Delete intent |

### Query
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/query` | Process query (non-streaming) |
| POST | `/api/query/stream` | Process query (streaming) |

### Analytics
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/analytics/logs` | Query logs |
| GET | `/api/analytics/stats` | Statistics |

---

## Configuration

### Environment Variables

```env
# AI Models
SILICONCLOUD_API_KEY=your_key
EMBEDDING_MODEL=BAAI/bge-m3
RERANK_MODEL=BAAI/bge-reranker-v2-m3
LLM_MODEL = Qwen2.5-14B-Instruct  
INTENT_MODEL = Qwen/Qwen2.5-7B-Instruct 

# Search Settings
HYBRID_SEARCH_WEIGHTS={"bm25": 0.5, "vector": 0.5}
RRF_K=60
TOP_K_DOCUMENTS=6
RERANK_TOP_K=4

# Intent Classification
DEFAULT_CONFIDENCE_THRESHOLD=0.70
INTENT_LLM_WEIGHT=0.5
INTENT_KEYWORD_WEIGHT=0.5

# Frontend Integration
TELEGRAM_BOT_TOKEN=your_token
FEISHU_APP_ID=your_app_id
FEISHU_APP_SECRET=your_secret
```

---

## Admin Dashboard (Streamlit)

### Pages

| Page | Features |
|------|----------|
| **Dashboard** | System stats, health status, recent queries |
| **KB Management** | Upload, view, edit, reparse, delete documents |
| **Intent Configuration** | Create/edit intents, keyword management |
| **Frontend Integration** | Telegram/Feishu bot settings |
| **Analytics** | Query logs, response metrics, export |

### KB Management Features

1. **Document Upload**: Batch upload with auto-parse
2. **View Document**: View content, metadata, chunks
3. **Edit Content**: Modify text with reparse options
4. **Reparse**:
   - "Only reparse text (keep chunks)" - Fix extraction errors
   - "Re-chunk and re-vectorize" - Improve retrieval quality
5. **Delete**: Remove document and vectors

---

## Performance

| Metric | Target |
|--------|--------|
| Query Response | ≤ 3 seconds |
| Document Processing | ≤ 30 seconds |
| Intent Classification | < 500ms |
| Search | < 1 second |

---

## Security

- API Key authentication for external endpoints
- Credential encryption for third-party integrations
- CORS configuration for web UI

---

## File Structure

```
IntelliKnow-KMS/
├── app/
│   ├── api/                    # API endpoints
│   │   ├── documents.py
│   │   ├── intents.py
│   │   ├── query.py
│   │   ├── analytics.py
│   │   └── webhooks.py
│   ├── models/
│   │   ├── database.py        # SQLAlchemy models
│   │   └── schemas.py         # Pydantic schemas
│   ├── services/
│   │   ├── document_service.py
│   │   ├── search_service.py
│   │   ├── response_service.py
│   │   ├── intent_service.py
│   │   └── frontend/           # Bot integrations
│   │       ├── telegram.py
│   │       └── feishu.py
│   ├── utils/
│   │   ├── vectorstore.py     # FAISS + BM25
│   │   ├── llm.py             # LLM utilities
│   │   ├── cache.py           # Caching
│   │   └── document_parser.py
│   └── main.py
├── config/
│   ├── settings.py
│   └── .env.example
├── frontend/
│   └── app.py                 # Streamlit dashboard
└── data/
    ├── sqlite/               # Database
    ├── vectors/              # FAISS/BM25 indexes
    └── uploads/              # Raw files
```

---

## Dependencies

### Core
- FastAPI
- SQLAlchemy (async)
- LangChain
- FAISS
- Rank-BM25

### AI Models
- Embeddings: BGE-M3
- Reranker: BGE-Reranker-v2-M3
- LLM: Qwen2.5-7B/Qwen2.5-14B (via SiliconCloud)

### Frontend
- Streamlit

---

## Deployment

```bash
# Backend
uvicorn app.main:app --reload --port 8000

# Frontend (separate terminal)
streamlit run frontend/app.py
```

---

## Future Enhancements

1. **Multi-tenant support**: Isolated knowledge bases per department
2. **Feedback loop**: User feedback on answer quality
3. **Analytics dashboard**: Detailed usage metrics
4. **Document versioning**: Track changes over time
5. **Cache optimization**: Redis for production deployment
