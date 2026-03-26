"""
Vector store service - FAISS + BM25 Hybrid Search
"""

import os
import json
import logging
import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np

from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
from rank_bm25 import BM25Okapi

from config import settings

logger = logging.getLogger(__name__)

# Path for vector store persistence
VECTOR_STORE_PATH = settings.VECTORS_DIR / "faiss_index"
BM25_STORE_PATH = settings.VECTORS_DIR / "bm25_index"
METADATA_PATH = settings.VECTORS_DIR / "metadata.json"


class VectorStore:
    """Hybrid vector store combining FAISS and BM25"""

    def __init__(self):
        self.faiss_store: Optional[FAISS] = None
        self.bm25: Optional[BM25Okapi] = None
        self.documents: List[Document] = []
        self.doc_id_map: Dict[int, int] = {}  # Maps FAISS index to doc ID

    def _get_embedding_function(self):
        """Get embedding function for FAISS"""
        import os

        api_key = os.getenv("SILICONCLOUD_API_KEY", "")

        if api_key:
            logger.info("Using SiliconCloud API for embeddings")
            os.environ.pop("HTTP_PROXY", None)
            os.environ.pop("HTTPS_PROXY", None)
            os.environ.pop("http_proxy", None)
            os.environ.pop("https_proxy", None)
            os.environ.pop("ALL_PROXY", None)
            os.environ.pop("all_proxy", None)

            return OpenAIEmbeddings(
                api_key=api_key,
                base_url="https://api.siliconflow.cn/v1",
                model="BAAI/bge-m3",
            )
        else:
            logger.error(
                "No API key configured for embeddings. Please set SILICONCLOUD_API_KEY in .env"
            )
            raise ValueError("SILICONCLOUD_API_KEY not configured")

    def _load_or_create(self):
        """Load existing vector store or create new one"""
        if VECTOR_STORE_PATH.exists():
            try:
                self.faiss_store = FAISS.load_local(
                    str(VECTOR_STORE_PATH),
                    self._get_embedding_function(),
                    allow_dangerous_deserialization=True,
                )
                logger.info("Loaded existing FAISS index")
            except Exception as e:
                logger.warning(f"Could not load FAISS index: {e}, creating new one")
                self.faiss_store = None

        if BM25_STORE_PATH.exists():
            try:
                with open(BM25_STORE_PATH, "rb") as f:
                    data = pickle.load(f)
                    self.bm25 = data["bm25"]
                    self.documents = data["documents"]
                logger.info("Loaded existing BM25 index")
            except Exception as e:
                logger.warning(f"Could not load BM25 index: {e}")
                self.bm25 = None

        self._load_metadata()

    def _load_metadata(self):
        """Load document metadata"""
        if METADATA_PATH.exists():
            try:
                with open(METADATA_PATH, "r") as f:
                    data = json.load(f)
                    self.doc_id_map = data.get("doc_id_map", {})
            except Exception as e:
                logger.warning(f"Could not load metadata: {e}")

    def _save_metadata(self):
        """Save document metadata"""
        data = {"doc_id_map": self.doc_id_map}
        with open(METADATA_PATH, "w") as f:
            json.dump(data, f)

    def _save(self):
        """Save vector store to disk"""
        if self.faiss_store:
            self.faiss_store.save_local(str(VECTOR_STORE_PATH))
            logger.info("Saved FAISS index")

        if self.bm25 and self.documents:
            with open(BM25_STORE_PATH, "wb") as f:
                pickle.dump({"bm25": self.bm25, "documents": self.documents}, f)
            logger.info("Saved BM25 index")

        self._save_metadata()

    def add_documents(
        self,
        texts: List[str],
        document_id: int,
        intent_id: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[int]:
        """
        Add documents to the vector store

        Args:
            texts: List of text chunks
            document_id: Database document ID
            intent_id: Intent ID for filtering
            metadata: Additional metadata

        Returns:
            List of vector IDs
        """
        if metadata is None:
            metadata = {}

        # Create LangChain documents
        docs = [
            Document(
                page_content=text,
                metadata={
                    "document_id": document_id,
                    "intent_id": intent_id,
                    **metadata,
                },
            )
            for text in texts
        ]

        # Add to FAISS
        if self.faiss_store is None:
            self.faiss_store = FAISS.from_documents(
                docs, self._get_embedding_function()
            )
        else:
            self.faiss_store.add_documents(docs)

        # Get the starting index for new documents
        start_idx = len(self.documents)
        vector_ids = list(range(start_idx, start_idx + len(texts)))

        # Add to BM25
        tokenized_texts = [text.split() for text in texts]
        if self.bm25 is None:
            self.bm25 = BM25Okapi(tokenized_texts)
        else:
            # BM25Okapi doesn't support adding to corpus, need to rebuild
            # Collect all existing tokenized texts
            existing_corpus = []
            for doc in self.documents:
                existing_corpus.append(doc.page_content.split())
            # Add new texts and rebuild
            all_corpus = existing_corpus + tokenized_texts
            self.bm25 = BM25Okapi(all_corpus)

        self.documents.extend(docs)

        # Update doc_id_map
        for vid in vector_ids:
            self.doc_id_map[vid] = document_id

        self._save()

        logger.info(f"Added {len(texts)} chunks for document {document_id}")
        return vector_ids

    def search(
        self, query: str, intent_id: Optional[int] = None, top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Hybrid search using FAISS and BM25 with RRF (Reciprocal Rank Fusion)

        Args:
            query: Query text
            intent_id: Filter by intent ID
            top_k: Number of results

        Returns:
            List of results with document content and scores
        """
        # Initialize if needed
        if self.faiss_store is None or self.bm25 is None:
            self._load_or_create()

        if self.faiss_store is None or self.bm25 is None:
            logger.warning("No vector store available")
            return []

        logger.info(
            f"Searching with query='{query}', intent_id={intent_id}, top_k={top_k}"
        )
        logger.info(f"Total documents in vector store: {len(self.documents)}")

        # RRF parameter (default 60)
        rrf_k = settings.RRF_K

        # FAISS search - get more results for fusion
        faiss_results = self.faiss_store.similarity_search_with_score(
            query, k=top_k * 3
        )
        logger.info(f"FAISS returned {len(faiss_results)} results")

        # BM25 search
        tokenized_query = query.split()
        bm25_scores = self.bm25.get_scores(tokenized_query)
        bm25_top_indices = np.argsort(bm25_scores)[::-1][: top_k * 3]
        logger.info(
            f"BM25 returned {len(bm25_top_indices)} results with non-zero scores"
        )

        # Build a content-to-index map to avoid object identity issues
        content_to_idx = {}
        for idx, doc in enumerate(self.documents):
            content_to_idx[doc.page_content] = idx

        # DEBUG: Show what FAISS returned vs what we have
        if faiss_results:
            faiss_doc_ids = [
                d.metadata.get("document_id") for d, _ in faiss_results[:3]
            ]
            self_doc_ids = [
                self.documents[i].metadata.get("document_id")
                for i in content_to_idx.values()
            ]
            logger.info(f"DEBUG FAISS result doc_ids: {faiss_doc_ids}")
            logger.info(f"DEBUG self.documents doc_ids (first 10): {self_doc_ids[:10]}")

        # Get top results (filter out deleted documents)
        results = []

        # RRF fusion: score = Σ 1/(k + rank) for each retriever
        rrf_scores = {}

        # Add FAISS RRF scores
        for rank, (doc, score) in enumerate(faiss_results):
            doc_idx = content_to_idx.get(doc.page_content)
            if doc_idx is None:
                logger.warning(
                    f"DEBUG: FAISS doc not found in self.documents by content! FAISS doc_id={doc.metadata.get('document_id')}"
                )
                # Skip mismatched documents - this indicates index corruption
                continue
            rrf_scores[doc_idx] = rrf_scores.get(doc_idx, 0) + 1.0 / (rrf_k + rank)

        # Add BM25 RRF scores
        for rank, idx in enumerate(bm25_top_indices):
            if idx < len(self.documents):
                rrf_scores[idx] = rrf_scores.get(idx, 0) + 1.0 / (rrf_k + rank)

        # Sort by RRF score
        sorted_results = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
        logger.info(f"RRF fusion returned {len(sorted_results)} results")
        for doc_idx, score in sorted_results[: top_k * 3]:
            if len(results) >= top_k:
                break

            if doc_idx >= len(self.documents):
                continue

            doc = self.documents[doc_idx]

            # Skip deleted documents
            if doc.metadata.get("deleted", False):
                logger.debug(f"Skipping deleted document {doc_idx}")
                continue

            # Skip documents without content
            if not doc.page_content or not doc.page_content.strip():
                logger.debug(f"Skipping empty document {doc_idx}")
                continue

            # Store intent_id for later filtering in response_service
            doc_intent_id = doc.metadata.get("intent_id")

            # Normalize RRF score to 0-1 range for display
            max_rrf = max(rrf_scores.values()) if rrf_scores else 1.0
            normalized_score = score / max_rrf if max_rrf > 0 else 0

            results.append(
                {
                    "document_id": doc.metadata.get("document_id"),
                    "intent_id": doc_intent_id,
                    "content": doc.page_content,
                    "score": normalized_score,
                    "rrf_score": score,
                    "metadata": doc.metadata,
                }
            )
            logger.debug(
                f"Added document {doc_idx} with RRF score {score}, normalized {normalized_score:.3f}"
            )

        logger.info(f"Final search returned {len(results)} results for query '{query}'")
        return results

    def delete_document(self, document_id: int) -> bool:
        """
        Delete all chunks associated with a document from FAISS and documents list

        Args:
            document_id: Database document ID

        Returns:
            True if successful
        """
        # 1. 找出要删除的向量索引
        indices_to_delete = []
        for i, doc in enumerate(self.documents):
            if doc.metadata.get("document_id") == document_id:
                indices_to_delete.append(i)

        if not indices_to_delete:
            logger.warning(f"Document {document_id} not found in vector store")
            return False

        logger.info(
            f"Deleting document {document_id} with {len(indices_to_delete)} chunks from FAISS"
        )

        # 2. 从FAISS中删除向量（按索引从后往前删，防止索引偏移）
        if self.faiss_store and self.faiss_store.index.ntotal > 0:
            try:
                # 删除向量
                for idx in sorted(indices_to_delete, reverse=True):
                    try:
                        self.faiss_store.index.remove_ids(np.array([idx]))
                    except Exception as e:
                        logger.warning(
                            f"Failed to remove FAISS vector at index {idx}: {e}"
                        )
            except Exception as e:
                logger.warning(f"FAISS remove error, will rebuild index: {e}")
                # 如果单个删除失败，重建整个索引
                self._rebuild_from_documents()
                self._save()
                return True

        # 3. 从documents列表中移除（从后往前删，防止索引偏移）
        for idx in sorted(indices_to_delete, reverse=True):
            self.documents.pop(idx)

        # 4. 重建BM25索引
        if self.documents:
            tokenized_corpus = [doc.page_content.split() for doc in self.documents]
            self.bm25 = BM25Okapi(tokenized_corpus)

        # 5. 保存
        self._save()
        logger.info(
            f"Deleted document {document_id} from vector store ({len(indices_to_delete)} chunks)"
        )
        return True

    def _rebuild_from_documents(self):
        """Rebuild FAISS index from current documents list"""
        logger.info("Rebuilding FAISS index from documents...")

        # 重新添加所有文档到FAISS
        if not self.documents:
            self.faiss_store = FAISS.from_documents(
                [Document(page_content="", metadata={})], self.embedding_function
            )
            self.faiss_store.index.ntotal = 0
            return

        texts = [doc.page_content for doc in self.documents]
        metadatas = [doc.metadata for doc in self.documents]

        # 创建新索引
        self.faiss_store = FAISS.from_texts(
            texts, self.embedding_function, metadatas=metadatas
        )
        # 重建BM25
        if self.documents:
            tokenized_corpus = [doc.page_content.split() for doc in self.documents]
            self.bm25 = BM25Okapi(tokenized_corpus)
        logger.info(f"Rebuilt FAISS index with {len(self.documents)} documents")


# Singleton instance
_vector_store: Optional[VectorStore] = None


def get_vector_store() -> VectorStore:
    """Get singleton vector store instance (cached in memory)"""
    global _vector_store
    if _vector_store is None:
        logger.info("🔄 Vector store: Loading from disk (first access)...")
        _vector_store = VectorStore()
        _vector_store._load_or_create()
        logger.info(
            f"✅ Vector store LOADED: FAISS={_vector_store.faiss_store.index.ntotal if _vector_store.faiss_store else 0} vectors, BM25={len(_vector_store.documents)} docs"
        )
    else:
        logger.info(
            f"✅ Vector store cache HIT (in memory): FAISS={_vector_store.faiss_store.index.ntotal if _vector_store.faiss_store else 0} vectors"
        )
    return _vector_store


def rebuild_vector_store():
    """Rebuild vector store from database"""
    global _vector_store
    _vector_store = VectorStore()
    # Will be populated from documents in database
    logger.info("Vector store reset")


async def rebuild_vector_store_from_db(db_session):
    """
    Rebuild vector store from database documents

    Args:
        db_session: SQLAlchemy async session
    """
    global _vector_store

    from sqlalchemy import select
    from app.models.database import Document, DocumentChunk
    from langchain_core.documents import Document as LangchainDocument

    logger.info("🔄 Starting vector store rebuild from database...")

    # Create new vector store
    _vector_store = VectorStore()
    _vector_store.faiss_store = None
    _vector_store.bm25 = None
    _vector_store.documents = []
    _vector_store.doc_id_map = {}

    # Fetch all document chunks from database
    result = await db_session.execute(
        select(DocumentChunk, Document)
        .join(Document, DocumentChunk.document_id == Document.id)
        .where(Document.status == "indexed")
    )
    chunks = result.all()

    if not chunks:
        logger.warning("No document chunks found in database")
        return

    logger.info(f"Found {len(chunks)} chunks to index")

    # Prepare texts and metadata
    texts = []
    metadatas = []
    doc_ids = []

    for chunk, doc in chunks:
        texts.append(chunk.content)
        metadatas.append(
            {
                "document_id": doc.id,
                "intent_id": doc.intent_id,
                "document_name": doc.name,
            }
        )
        doc_ids.append(doc.id)

    # Build FAISS index
    try:
        _vector_store.faiss_store = FAISS.from_texts(
            texts, _vector_store._get_embedding_function(), metadatas=metadatas
        )
        logger.info(f"✅ FAISS index built with {len(texts)} vectors")
    except Exception as e:
        logger.error(f"FAISS index build failed: {e}")
        raise

    # Build BM25 index
    tokenized_texts = [text.split() for text in texts]
    _vector_store.bm25 = BM25Okapi(tokenized_texts)
    logger.info(f"✅ BM25 index built with {len(texts)} documents")

    # Build documents list
    for i, (chunk, doc) in enumerate(chunks):
        _vector_store.documents.append(
            LangchainDocument(
                page_content=chunk.content,
                metadata={
                    "document_id": doc.id,
                    "intent_id": doc.intent_id,
                    "document_name": doc.name,
                },
            )
        )
        _vector_store.doc_id_map[i] = doc.id

    # Save to disk
    _vector_store._save()

    logger.info(f"✅ Vector store rebuild complete: {len(texts)} chunks indexed")
