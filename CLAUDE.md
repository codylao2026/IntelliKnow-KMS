# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**IntelliKnow KMS** - Gen AI-powered Knowledge Management System designed as a 7-day MVP for interview assessment. Enables enterprise employees to query knowledge via WhatsApp/Teams with AI-powered intent classification and hybrid search (BM25 + FAISS with RRF fusion).

## Development Commands

```bash
# Setup (one-time)
cd ~/Obsidian-Vault/40-Projects/40-IntelliKnow-KMS
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
cp config/.env.example config/.env
# Edit .env with your API keys

# Run Backend
uvicorn app.main:app --reload --port 8000

# Run Frontend (new terminal)
streamlit run frontend/app.py
```

## Architecture

```
Admin Dashboard (Streamlit)
          │
          ▼
   API Layer (FastAPI)
   ├── /api/documents   - Document upload, parsing, vectorization
   ├── /api/intents    - Intent space CRUD
   ├── /api/query      - Query classification + RAG pipeline
   └── /api/analytics  - Statistics, logs, exports
          │
          ▼
   Service Layer
   ├── DocumentService     - PDF/DOCX parsing via LangChain
   ├── SearchService       - Hybrid Search (BM25 + FAISS RRF)
   ├── IntentService       - LLM-based classification
   └── ResponseService     - Prompt engineering, source citation
          │
          ▼
   Data Layer
   ├── SQLite  - Metadata, configs, query logs
   ├── FAISS   - Vector store
   └── Uploads - Raw documents
```

## Key Implementation Patterns

### Hybrid Search (RRF Fusion)
Use LangChain's `EnsembleRetriever` combining:
- `FAISSVectorStore` with BGE-M3 embeddings
- `BM25Retriever` from rank_bm25 library
- RRF algorithm fuses both ranking results

### Intent Classification
- Use LLM (MiniMax2.5 via SiliconCloud) with structured output
- Configurable confidence threshold (default 70%)
- Fallback to "General" intent when below threshold
- Keywords enhancement for domain-specific terms

### RAG Pipeline
1. Query rewrite (analyze history, generate optimized query)
2. Hybrid search (BM25 + Vector with RRF)
3. Rerank (BGE-Reranker-v2-M3)
4. Prompt engineering with few-shot examples
5. LLM generates response with citations

### Frontend Integration
- WhatsApp: Markdown-formatted responses
- Teams: Adaptive Cards for rich formatting

## Tech Stack

- **Backend**: FastAPI
- **Frontend**: Streamlit
- **DB**: SQLite (metadata), FAISS (vectors)
- **AI**: LangChain + SiliconCloud (BGE-M3, Rerank-v2, MiniMax2.5)
- **Search**: BM25 + FAISS hybrid with RRF

## Development Order

1. **Day 1**: Project init, dependencies, folder structure
2. **Day 2**: Document parsing + vector storage (SQLite + FAISS)
3. **Day 3**: Hybrid Search (BM25 + Vector RRF)
4. **Day 4**: Intent classification + response generation
5. **Day 5**: WhatsApp/Teams Bot integration
6. **Day 6**: Streamlit admin dashboard + testing
7. **Day 7**: Polish, docs, demo

## Critical Files

- `docs/PRD.md` - Full product requirements for Claude Code
- `docs/IntelliKnow-KMS-需求规格说明书-SRS.md` - Detailed SRS with acceptance criteria
- `config/settings.py` - All configuration

## Performance Targets

- Query response: ≤3 seconds
- Document parsing: ≤30 seconds per document
- Classification accuracy: ≥70%
- System availability: ≥99.5%