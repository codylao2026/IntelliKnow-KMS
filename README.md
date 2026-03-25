# IntelliKnow KMS Project

## Directory Structure

```
40-IntelliKnow-KMS/
├── docs/                         # Project documentation
│   ├── IntelliKnow-KMS-需求规格说明书-SRS.md   # Full requirement specification
│   ├── PRD.md                   # Product requirements (for Claude Code)
│   └── CaseStudy-需求映射表.md  # Case Study requirement mapping
│
├── app/                          # Application code
│   ├── api/                      # FastAPI routes
│   ├── services/                 # Business logic
│   ├── models/                   # Data models
│   └── utils/                    # Utilities
│
├── frontend/                     # Streamlit admin dashboard
│   └── app.py
│
├── data/                         # Data storage
│   ├── sqlite/                   # SQLite database
│   ├── vectors/                  # FAISS vector store
│   └── uploads/                  # Uploaded documents
│
├── tests/                        # Test code
│
├── scripts/                      # Script tools
│
├── config/                       # Configuration
│   └── settings.py
│
├── requirements.txt              # Python dependencies
└── README.md                     # Project documentation
```

## Quick Access

```bash
# Access project directory
cd ~/Obsidian-Vault/40-Projects/40-IntelliKnow-KMS

# Or on Windows
# C:\Users\alber\Documents\Obsidian-Vault\40-Projects\40-IntelliKnow-KMS
```

## Development Setup

```bash
# 1. Enter project directory
cd ~/Obsidian-Vault/40-Projects/40-IntelliKnow-KMS

# 2. Create virtual environment (first time)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp config/.env.example config/.env
# Edit .env with API keys

# 5. Start FastAPI backend
uvicorn app.main:app --reload --port 8000

# 6. Start Streamlit frontend (new terminal)
streamlit run frontend/app.py
```

## Project Status

- [x] Requirement specification complete
- [x] Project initialization
- [x] Core module development
- [x] Frontend integration
- [ ] Testing & optimization
- [ ] Delivery

---

**Last Updated**: 2026-03-19