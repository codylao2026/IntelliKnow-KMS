"""
Pydantic schemas for API request/response
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ============== Intent Schemas ==============

class IntentBase(BaseModel):
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    keywords: List[str] = []


class IntentCreate(IntentBase):
    pass


class IntentUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    keywords: Optional[List[str]] = None


class IntentResponse(IntentBase):
    id: int
    is_default: bool
    created_at: datetime
    updated_at: datetime
    document_count: int = 0

    class Config:
        from_attributes = True


# ============== Document Schemas ==============

class DocumentBase(BaseModel):
    name: str = Field(..., max_length=255)
    intent_id: Optional[int] = None


class DocumentUploadResponse(BaseModel):
    id: int
    name: str
    status: str
    message: str


class DocumentResponse(BaseModel):
    id: int
    name: str
    file_path: str
    file_size: int
    file_type: str
    intent_id: Optional[int]
    intent_name: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    items: List[DocumentResponse]
    total: int


# ============== Query Schemas ==============

class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    frontend: Optional[str] = "web"  # whatsapp, teams, web
    intent_hint: Optional[str] = None  # Optional hint for classification


class QuerySource(BaseModel):
    document_id: int
    document_name: str
    content: str
    score: float


class QueryResponse(BaseModel):
    query: str
    response: str
    intent: str
    confidence: float
    confidence_source: Optional[str] = None  # llm, keyword, fusion, hint, error
    sources: List[QuerySource]
    response_time: float  # milliseconds
    status: str


# ============== Analytics Schemas ==============

class DashboardStats(BaseModel):
    total_queries: int
    today_queries: int
    accuracy: float
    document_count: int
    intent_count: int


class QueryLogResponse(BaseModel):
    id: int
    query: str
    intent_name: Optional[str]
    confidence: Optional[float]
    confidence_source: Optional[str] = None
    response: Optional[str]
    frontend: Optional[str]
    status: str
    response_time: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True


class QueryLogListResponse(BaseModel):
    items: List[QueryLogResponse]
    total: int


class IntentStats(BaseModel):
    intent_name: str
    query_count: int
    accuracy: float


class PopularDocument(BaseModel):
    document_id: int
    document_name: str
    access_count: int


class AnalyticsResponse(BaseModel):
    dashboard: DashboardStats
    top_intents: List[IntentStats]
    popular_documents: List[PopularDocument]


# ============== Credential Schemas ==============

class CredentialUpdate(BaseModel):
    credentials: dict


class CredentialResponse(BaseModel):
    frontend_type: str
    is_active: bool
    updated_at: datetime

    class Config:
        from_attributes = True