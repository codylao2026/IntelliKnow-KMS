"""
Document parser for PDF and DOCX files with table extraction support
"""
import os
import re
import logging
import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from langchain_community.document_loaders import Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import settings

logger = logging.getLogger(__name__)


def normalize_whitespace(text: str) -> str:
    """
    Normalize whitespace in text - reduce multiple newlines to double newlines
    
    Args:
        text: Input text
        
    Returns:
        Text with normalized whitespace
    """
    # Replace more than 2 consecutive newlines with exactly 2 newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    # Remove trailing newlines at end
    text = text.rstrip()
    return text

TEXT_SPLITTER = RecursiveCharacterTextSplitter(
    chunk_size=settings.CHUNK_SIZE,
    chunk_overlap=settings.CHUNK_OVERLAP,
    separators=[
        "\n## ",
        "\n### ",
        "\n\n",
        "\n",
        "第.*条",
        "^[0-9]+\\. ",
        "。", "！", "？",
        ". ", "! ", "? "
    ]
)


def parse_document(file_path: str, extract_tables: bool = True) -> str:
    """
    Parse document and extract text content with table extraction

    Args:
        file_path: Path to document file
        extract_tables: Whether to extract and enhance tables

    Returns:
        Extracted text content with formatted tables
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    ext = path.suffix.lower()

    try:
        if ext == ".pdf":
            return _parse_pdf(file_path, extract_tables=extract_tables)
        elif ext == ".docx":
            return _parse_docx(file_path, extract_tables=extract_tables)
        else:
            raise ValueError(f"Unsupported file type: {ext}")
    except Exception as e:
        logger.error(f"Error parsing document {file_path}: {e}")
        raise


def _parse_pdf(file_path: str, extract_tables: bool = True) -> str:
    """
    Parse PDF file with table extraction using pymupdf
    
    Args:
        file_path: Path to PDF file
        extract_tables: Whether to extract tables
        
    Returns:
        Extracted text with formatted tables
    """
    import fitz
    
    try:
        doc = fitz.open(file_path)
        
        if doc.is_closed or doc.is_encrypted:
            raise ValueError(f"PDF document is closed or encrypted: {file_path}")
        
        all_text_parts = []
        tables_found = 0
        
        for page_num, page in enumerate(doc):
            try:
                page_text = page.get_text()
                
                if extract_tables:
                    tables = _extract_tables_from_page(page, page_num)
                    if tables:
                        tables_found += len(tables)
                        page_text = _integrate_tables_into_text(page_text, tables)
                
                if page_text.strip():
                    all_text_parts.append(page_text)
            except Exception as e:
                logger.warning(f"Failed to extract text from page {page_num + 1}: {e}")
                continue
        
        doc.close()
        
        text = "\n\n".join(all_text_parts)
        
        # Normalize whitespace
        text = normalize_whitespace(text)
        
        logger.info(f"Parsed PDF: {file_path}, {len(doc)} pages, {tables_found} tables found, {len(text)} chars")
        
        if not text.strip():
            logger.warning(f"PDF extracted no text, trying fallback parser: {file_path}")
            return _parse_pdf_fallback(file_path)
        
        return text
        
    except Exception as e:
        logger.error(f"Failed to parse PDF with pymupdf: {e}")
        logger.info(f"Trying fallback parser for: {file_path}")
        return _parse_pdf_fallback(file_path)


def _parse_pdf_fallback(file_path: str) -> str:
    """
    Fallback PDF parser using pypdf
    
    Args:
        file_path: Path to PDF file
        
    Returns:
        Extracted text content
    """
    from langchain_community.document_loaders import PyPDFLoader
    
    try:
        loader = PyPDFLoader(file_path)
        pages = loader.load()
        text = "\n\n".join([page.page_content for page in pages])
        logger.info(f"Fallback parsed PDF: {file_path}, {len(pages)} pages, {len(text)} chars")
        return text
    except Exception as e:
        logger.error(f"Fallback PDF parser also failed: {e}")
        raise ValueError(f"Failed to parse PDF: {file_path}. Error: {e}")


def _extract_tables_from_page(page, page_num: int) -> List[Dict[str, Any]]:
    """
    Extract tables from a PDF page using pymupdf's table finder
    
    Args:
        page: pymupdf page object
        page_num: Page number for logging
        
    Returns:
        List of extracted table data
    """
    import fitz
    
    tables = []
    
    try:
        tabler = page.find_tables()
        table_bboxes = tabler.extract()
        
        if table_bboxes and table_bboxes[0]:
            for table_data in table_bboxes[0]:
                if table_data and isinstance(table_data, dict):
                    rows = table_data.get("rows", [])
                    if rows and len(rows) >= 2:
                        table_dict = {
                            "headers": [cell.strip() if cell else "" for cell in rows[0]],
                            "rows": [[cell.strip() if cell else "" for cell in row] for row in rows[1:]],
                            "bbox": table_data.get("bbox", [])
                        }
                        
                        if _is_meaningful_table(table_dict):
                            tables.append(table_dict)
                            logger.debug(f"Page {page_num + 1}: Found table with {len(rows)} rows, {len(rows[0]) if rows else 0} cols")
    except Exception as e:
        logger.warning(f"Table extraction failed on page {page_num + 1}: {e}")
    
    return tables


def _is_meaningful_table(table_dict: Dict) -> bool:
    """
    Check if table has meaningful content (not just formatting artifacts)
    
    Args:
        table_dict: Table data dict
        
    Returns:
        True if table is meaningful
    """
    if not table_dict.get("rows"):
        return False
    
    rows = table_dict["rows"]
    if len(rows) < 2:
        return False
    
    non_empty_cells = sum(
        1 for row in rows 
        for cell in row 
        if cell and cell.strip()
    )
    
    total_cells = sum(len(row) for row in rows)
    if total_cells == 0:
        return False
    
    return non_empty_cells / total_cells > 0.3


def _integrate_tables_into_text(page_text: str, tables: List[Dict]) -> str:
    """
    Integrate extracted tables into page text as formatted blocks
    
    Args:
        page_text: Original page text
        tables: List of extracted tables
        
    Returns:
        Text with table blocks inserted
    """
    table_blocks = []
    
    for table in tables:
        formatted = _format_table_as_text(table)
        table_blocks.append(formatted)
    
    if table_blocks:
        page_text += "\n\n[TABLES FOUND]\n" + "\n\n".join(table_blocks) + "\n[/TABLES FOUND]"
    
    return page_text


def _format_table_as_text(table_dict: Dict) -> str:
    """
    Format table as readable text (without LLM for speed)
    
    Args:
        table_dict: Table data with headers and rows
        
    Returns:
        Formatted table as markdown-style text
    """
    if not table_dict.get("headers") or not table_dict.get("rows"):
        return ""
    
    lines = []
    headers = table_dict["headers"]
    rows = table_dict["rows"]
    
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
    
    for row in rows:
        cells = row[:len(headers)] + [""] * (len(headers) - len(row))
        lines.append("| " + " | ".join(cells) + " |")
    
    structured_desc = _generate_table_description(headers, rows)
    lines.append("")
    lines.append(structured_desc)
    
    return "\n".join(lines)


def _generate_table_description(headers: List[str], rows: List[List[str]]) -> str:
    """
    Generate natural language description of table for better searchability
    
    Args:
        headers: Table column headers
        rows: Table data rows
        
    Returns:
        Searchable description of table content
    """
    if not headers or not rows:
        return ""
    
    desc_parts = []
    
    for row in rows[:5]:
        row_desc = []
        for i, cell in enumerate(row[:min(len(headers), 6)]):
            if cell and cell.strip():
                row_desc.append(f"{headers[i]}: {cell}")
        if row_desc:
            desc_parts.append(", ".join(row_desc))
    
    if len(rows) > 5:
        desc_parts.append(f"... and {len(rows) - 5} more rows")
    
    return "Table entries: " + " | ".join(desc_parts)


async def format_tables_with_llm_async(tables: List[Dict], document_context: str = "") -> str:
    """
    Use LLM to enhance table extraction with AI understanding (async version)
    
    Args:
        tables: List of extracted table data
        document_context: Surrounding document text for context
        
    Returns:
        Enhanced table descriptions generated by LLM
    """
    if not tables:
        return ""
    
    try:
        from app.utils.llm import generate_response
        
        tables_text = json.dumps(tables, ensure_ascii=False, indent=2)
        
        prompt = f"""You are analyzing structured tabular data extracted from a document.

Context (surrounding document text):
{document_context[:500]}

Extracted Tables:
{tables_text}

Task:
1. Identify what type of data this table contains (e.g., salary grid, inventory list, pricing table)
2. Generate natural language descriptions that make this data easily searchable
3. Create queryable summaries that capture key relationships in the data
4. Output in the same language as the table content (keep Chinese tables in Chinese)

Format your response as structured, searchable text that can be chunked and vectorized.
Focus on making numerical and structured data findable through natural language queries."""

        response = await generate_response(
            prompt=prompt,
            system_prompt="You are a data analyst specializing in making structured data searchable.",
            temperature=0.3,
            model=settings.LLM_MODEL
        )
        
        return response if response else ""
        
    except Exception as e:
        logger.warning(f"LLM table formatting failed: {e}")
        return ""


def format_tables_with_llm(tables: List[Dict], document_context: str = "") -> str:
    """
    Use LLM to enhance table extraction with AI understanding (sync wrapper)
    
    Args:
        tables: List of extracted table data
        document_context: Surrounding document text for context
        
    Returns:
        Enhanced table descriptions generated by LLM
    """
    import asyncio
    
    if not tables:
        return ""
    
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run,
                    format_tables_with_llm_async(tables, document_context)
                )
                return future.result(timeout=30)
        else:
            return asyncio.run(format_tables_with_llm_async(tables, document_context))
    except Exception as e:
        logger.warning(f"LLM table formatting failed: {e}")
        return ""


def _parse_docx(file_path: str, extract_tables: bool = True) -> str:
    """
    Parse DOCX file with basic table support
    
    Args:
        file_path: Path to DOCX file
        extract_tables: Whether to extract tables
        
    Returns:
        Extracted text with tables
    """
    loader = Docx2txtLoader(file_path)
    documents = loader.load()
    text = "\n\n".join([doc.page_content for doc in documents])
    
    if extract_tables:
        try:
            from docx import Document as DocxDocument
            doc = DocxDocument(file_path)
            table_text = _extract_docx_tables(doc)
            if table_text:
                text += "\n\n[TABLES FOUND]\n" + table_text + "\n[/TABLES FOUND]"
        except Exception as e:
            logger.warning(f"DOCX table extraction failed: {e}")
    
    # Normalize whitespace
    text = normalize_whitespace(text)
    
    logger.info(f"Parsed DOCX: {file_path}, {len(text)} chars")
    return text


def _extract_docx_tables(doc) -> str:
    """
    Extract tables from DOCX document
    
    Args:
        doc: python-docx Document object
        
    Returns:
        Formatted table text
    """
    table_blocks = []
    
    for table in doc.tables:
        rows_data = []
        headers = []
        
        for i, row in enumerate(table.rows):
            cells = [cell.text.strip() for cell in row.cells]
            if i == 0:
                headers = cells
            rows_data.append(cells)
        
        if headers and len(rows_data) > 1:
            table_dict = {"headers": headers, "rows": rows_data[1:]}
            formatted = _format_table_as_text(table_dict)
            table_blocks.append(formatted)
    
    return "\n\n".join(table_blocks)


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
