"""
Database models for IntelliKnow KMS
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Intent(Base):
    """Intent space model"""
    __tablename__ = "intents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    keywords = Column(JSON, default=list)  # List of keywords for classification
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    documents = relationship("Document", back_populates="intent")
    query_logs = relationship("QueryLog", back_populates="intent")


class Document(Base):
    """Document model"""
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_size = Column(Integer, nullable=False)  # bytes
    file_type = Column(String(50), nullable=False)  # pdf, docx
    content = Column(Text, nullable=True)  # Extracted text content
    intent_id = Column(Integer, ForeignKey("intents.id"), nullable=True)
    status = Column(String(20), default="pending")  # pending, processing, completed, failed
    vector_ids = Column(JSON, default=list)  # FAISS vector IDs
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    intent = relationship("Intent", back_populates="documents")
    query_logs = relationship("QueryLog", back_populates="document")


class QueryLog(Base):
    """Query log for analytics"""
    __tablename__ = "query_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    query = Column(Text, nullable=False)
    intent_id = Column(Integer, ForeignKey("intents.id"), nullable=True)
    intent_name = Column(String(100), nullable=True)  # Denormalized for easier querying
    confidence = Column(Float, nullable=True)
    confidence_source = Column(String(20), nullable=True)  # llm, keyword, fusion
    response = Column(Text, nullable=True)
    sources = Column(JSON, default=list)  # List of source document IDs
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)
    response_time = Column(Float, nullable=True)  # milliseconds
    frontend = Column(String(50), nullable=True)  # whatsapp, teams, web
    status = Column(String(20), default="success")  # success, failed, fallback
    created_at = Column(DateTime, default=datetime.utcnow)

    intent = relationship("Intent", back_populates="query_logs")
    document = relationship("Document", back_populates="query_logs")


class Credential(Base):
    """Frontend credentials storage (encrypted)"""
    __tablename__ = "credentials"

    id = Column(Integer, primary_key=True, autoincrement=True)
    frontend_type = Column(String(50), unique=True, nullable=False, index=True)  # whatsapp, teams
    credentials_json = Column(Text, nullable=False)  # Encrypted JSON
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Config(Base):
    """System configuration"""
    __tablename__ = "configs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)