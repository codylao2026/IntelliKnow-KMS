"""
Document parser for PDF and DOCX files
"""
import os
import logging
from pathlib import Path
from typing import List, Optional
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import settings

logger = logging.getLogger(__name__)

# Text splitter configuration
TEXT_SPLITTER = RecursiveCharacterTextSplitter(
    chunk_size=settings.CHUNK_SIZE,
    chunk_overlap=settings.CHUNK_OVERLAP,
    separators=[
        "\n## ",              # Markdown section headers
        "\n### ",             # Markdown subsection headers
        "\n\n",              # Paragraph breaks
        "\n",                 # Line breaks
        "第.*条",             # Legal clause numbers (Chinese)
        "^[0-9]+\\. ",        # Numbered lists (English)
        "。", "！", "？",     # Chinese sentence endings
        ". ", "! ", "? "      # English sentence endings
    ]
)


def parse_document(file_path: str) -> str:
    """
    Parse document and extract text content

    Args:
        file_path: Path to document file

    Returns:
        Extracted text content

    Raises:
        ValueError: If file type is not supported
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    ext = path.suffix.lower()

    try:
        if ext == ".pdf":
            return _parse_pdf(file_path)
        elif ext == ".docx":
            return _parse_docx(file_path)
        else:
            raise ValueError(f"Unsupported file type: {ext}")
    except Exception as e:
        logger.error(f"Error parsing document {file_path}: {e}")
        raise


def _parse_pdf(file_path: str) -> str:
    """Parse PDF file using PyPDFLoader"""
    loader = PyPDFLoader(file_path)
    pages = loader.load()

    # Extract text from all pages
    text = "\n\n".join([page.page_content for page in pages])
    logger.info(f"Parsed PDF: {file_path}, {len(pages)} pages, {len(text)} chars")
    return text


def _parse_docx(file_path: str) -> str:
    """Parse DOCX file using Docx2txtLoader"""
    loader = Docx2txtLoader(file_path)
    documents = loader.load()

    # Extract text from all documents
    text = "\n\n".join([doc.page_content for doc in documents])
    logger.info(f"Parsed DOCX: {file_path}, {len(text)} chars")
    return text


def split_text_into_chunks(text: str) -> List[str]:
    """
    Split text into chunks for vectorization

    Args:
        text: Text content to split

    Returns:
        List of text chunks
    """
    chunks = TEXT_SPLITTER.split_text(text)
    logger.info(f"Split text into {len(chunks)} chunks")
    return chunks


def get_document_metadata(file_path: str, file_size: int) -> dict:
    """
    Extract metadata from document

    Args:
        file_path: Path to document
        file_size: File size in bytes

    Returns:
        Metadata dict
    """
    path = Path(file_path)
    ext = path.suffix.lower().lstrip(".")

    return {
        "filename": path.name,
        "file_type": ext,
        "file_size": file_size,
        "file_name": path.stem
    }