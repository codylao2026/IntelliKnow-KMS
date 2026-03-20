"""
IntelliKnow KMS Configuration
"""

import os
from pathlib import Path

# Project paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
SQLITE_DIR = DATA_DIR / "sqlite"
VECTORS_DIR = DATA_DIR / "vectors"
UPLOADS_DIR = DATA_DIR / "uploads"

# Ensure directories exist
SQLITE_DIR.mkdir(parents=True, exist_ok=True)
VECTORS_DIR.mkdir(parents=True, exist_ok=True)
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

# Database
SQLITE_PATH = SQLITE_DIR / "intelliknow.db"

# API Server
API_HOST = "localhost"
API_PORT = 8000

# Streamlit
STREAMLIT_PORT = 8501

# ============== AI Providers ==============

# SiliconCloud (开发环境 - 免费)
SILICONCLOUD_API_KEY = os.getenv("SILICONCLOUD_API_KEY", "")
SILICONCLOUD_BASE_URL = "https://api.siliconflow.cn/v1"

# Model configs
EMBEDDING_MODEL = "BAAI/bge-m3"
RERANK_MODEL = "BAAI/bge-reranker-v2-m3"
LLM_MODEL = "deepseek-ai/DeepSeek-V3"
INTENT_MODEL = "Qwen/Qwen2.5-7B-Instruct"

# ============== Azure OpenAI (生产环境) ==============

AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY", "")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "")
AZURE_OPENAI_API_VERSION = "2024-02-01"
AZURE_EMBEDDING_MODEL = os.getenv("AZURE_EMBEDDING_MODEL", "text-embedding-3-small")
AZURE_LLM_MODEL = os.getenv("AZURE_LLM_MODEL", "gpt-4")

# ============== Intent Classification ==============

DEFAULT_CONFIDENCE_THRESHOLD = 0.70  # 70%
FALLBACK_INTENT = "General"

# Weighted fusion for intent classification
INTENT_LLM_WEIGHT = 0.7     # Weight for LLM classification (0-1)
INTENT_KEYWORD_WEIGHT = 0.3  # Weight for keyword matching (0-1)
INTENT_KEYWORD_THRESHOLD = 0.3  # Minimum keyword score to use keyword result

DEFAULT_INTENTS = [
    {"name": "HR", "description": "Human resources related questions", "keywords": ["leave", "salary", "benefits", "insurance", "onboarding", "offboarding"]},
    {"name": "Legal", "description": "Legal compliance related questions", "keywords": ["contract", "compliance", "legal", "terms", "agreement"]},
    {"name": "Finance", "description": "Finance and reimbursement related questions", "keywords": ["reimbursement", "invoice", "budget", "expense", "payment"]},
]

# ============== Search Settings ==============

HYBRID_SEARCH_WEIGHTS = {
    "bm25": 0.3,
    "vector": 0.7
}

RRF_K = 60  # RRF parameter for rank fusion

TOP_K_DOCUMENTS = 6  # Number of documents to retrieve
RERANK_TOP_K = 3  # Number of documents after reranking

# ============== Document Processing ==============

CHUNK_SIZE = 500  # Text chunk size for vectorization
CHUNK_OVERLAP = 50  # Overlap between chunks

# ============== Frontend Integration ==============

# WhatsApp Business API
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
WHATSAPP_VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "intelliknow_verify")

# Microsoft Teams
TEAMS_APP_ID = os.getenv("TEAMS_APP_ID", "")
TEAMS_APP_PASSWORD = os.getenv("TEAMS_APP_PASSWORD", "")
TEAMS_TENANT_ID = os.getenv("TEAMS_TENANT_ID", "")
TEAMS_BOT_ID = os.getenv("TEAMS_BOT_ID", "")

# ============== Security ==============

# Encryption key for credentials (32 bytes hex)
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef")

# API authentication
API_KEY = os.getenv("API_KEY", "intelliknow_dev_key")

# ============== Performance ==============

MAX_CONCURRENT_REQUESTS = 10
QUERY_TIMEOUT = 30  # seconds
DOCUMENT_PARSE_TIMEOUT = 60  # seconds

# ============== Logging ==============

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")