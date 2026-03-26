# IntelliKnow KMS

Gen AI-powered Knowledge Management System with RAG (Retrieval-Augmented Generation) for enterprise knowledge base Q&A.

## Overview

IntelliKnow KMS enables employees to query enterprise knowledge base via AI-powered chat interfaces (Telegram, Feishu). It features:
- **Intent Classification**: LLM-based + keyword fallback for accurate query routing
- **Hybrid Search**: FAISS vector store + BM25 with RRF fusion
- **Reranking**: BAAI/bge-reranker-v2-m3 for improved relevance
- **Multi-channel**: Telegram (Polling) and Feishu (WebSocket) support

## Tech Stack

- **Backend**: FastAPI
- **Frontend**: Streamlit
- **Database**: SQLite (metadata), FAISS (vectors)
- **AI**: LangChain + SiliconCloud API (BGE-M3, Reranker, Qwen)
- **Search**: BM25 + FAISS hybrid with RRF fusion

## Directory Structure

```
IntelliKnow-KMS/
├── app/                    # FastAPI application
│   ├── api/               # API routes
│   ├── services/          # Business logic
│   ├── models/            # DB models
│   └── utils/             # Utilities
├── frontend/              # Streamlit dashboard
├── data/                  # Data storage
│   ├── sqlite/            # SQLite DB
│   ├── vectors/          # FAISS index
│   └── uploads/           # Uploaded files
├── config/                # Configuration
└── requirements.txt       # Python dependencies
```

## Quick Start

```bash
# 1. Clone and enter directory
git clone https://github.com/Albertlsy588/IntelliKnow-KMS.git
cd IntelliKnow-KMS

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp config/.env.example config/.env
# Edit .env with your API keys

# 5. Start backend (port 8000)
uvicorn app.main:app --reload --port 8000

# 6. Start frontend (new terminal, port 8501)
streamlit run frontend/app.py
```

## Access

- Backend API: http://localhost:8000
- Frontend Dashboard: http://localhost:8501
- API Docs: http://localhost:8000/docs

## Project Status

- [x] Requirement specification
- [x] Project initialization
- [x] Core module development (RAG, intent classification, hybrid search)
- [x] Frontend integration (Telegram, Feishu)
- [x] Testing & optimization
- [ ] Production deployment

---

**Last Updated**: 2026-03-26