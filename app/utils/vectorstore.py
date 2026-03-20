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
                model="BAAI/bge-m3"
            )
        else:
            logger.error("No API key configured for embeddings. Please set SILICONCLOUD_API_KEY in .env")
            raise ValueError("SILICONCLOUD_API_KEY not configured")

    def _load_or_create(self):
        """Load existing vector store or create new one"""
        if VECTOR_STORE_PATH.exists():
            try:
                self.faiss_store = FAISS.load_local(
                    str(VECTOR_STORE_PATH),
                    self._get_embedding_function(),
                    allow_dangerous_deserialization=True
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
        metadata: Optional[Dict[str, Any]] = None
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
                    **metadata
                }
            )
            for text in texts
        ]

        # Add to FAISS
        if self.faiss_store is None:
            self.faiss_store = FAISS.from_documents(
                docs,
                self._get_embedding_function()
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
            self.bm25.corpus.extend(tokenized_texts)

        self.documents.extend(docs)

        # Update doc_id_map
        for vid in vector_ids:
            self.doc_id_map[vid] = document_id

        self._save()

        logger.info(f"Added {len(texts)} chunks for document {document_id}")
        return vector_ids

    def search(
        self,
        query: str,
        intent_id: Optional[int] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Hybrid search using FAISS and BM25 with weighted RRF fusion

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

        # Get weights from settings
        weights = settings.HYBRID_SEARCH_WEIGHTS
        vector_weight = weights.get("vector", 0.6)
        bm25_weight = weights.get("bm25", 0.4)

        # FAISS search
        faiss_results = self.faiss_store.similarity_search_with_score(
            query,
            k=top_k * 2
        )

        # BM25 search
        tokenized_query = query.split()
        bm25_scores = self.bm25.get_scores(tokenized_query)
        bm25_top_indices = np.argsort(bm25_scores)[::-1][:top_k * 2]

        # Normalize scores
        faiss_max = max(score for _, score in faiss_results) if faiss_results else 1
        bm25_max = max(bm25_scores) if len(bm25_scores) > 0 else 1

        # Weighted fusion
        fusion_scores = {}

        # Add normalized FAISS scores with weight
        for rank, (doc, score) in enumerate(faiss_results):
            doc_idx = self.documents.index(doc)
            # Normalize distance to similarity (lower distance = higher similarity)
            normalized_score = 1 - (score / faiss_max) if faiss_max > 0 else 0
            fusion_scores[doc_idx] = fusion_scores.get(doc_idx, 0) + normalized_score * vector_weight

        # Add normalized BM25 scores with weight
        for rank, idx in enumerate(bm25_top_indices):
            normalized_score = bm25_scores[idx] / bm25_max if bm25_max > 0 else 0
            fusion_scores[idx] = fusion_scores.get(idx, 0) + normalized_score * bm25_weight

        # Sort by fusion score
        sorted_results = sorted(fusion_scores.items(), key=lambda x: x[1], reverse=True)

        # Get top results
        results = []
        for doc_idx, score in sorted_results[:top_k]:
            doc = self.documents[doc_idx]
            results.append({
                "document_id": doc.metadata.get("document_id"),
                "intent_id": doc.metadata.get("intent_id"),
                "content": doc.page_content,
                "score": score,
                "metadata": doc.metadata
            })

        logger.info(f"Hybrid search for '{query}': {len(results)} results, "
                   f"weights: vector={vector_weight}, bm25={bm25_weight}")

        return results

    def delete_document(self, document_id: int) -> bool:
        """
        Delete all chunks associated with a document

        Note: FAISS doesn't support efficient deletion,
        so we mark them as deleted in metadata

        Args:
            document_id: Database document ID

        Returns:
            True if successful
        """
        # Update metadata to mark as deleted
        for doc in self.documents:
            if doc.metadata.get("document_id") == document_id:
                doc.metadata["deleted"] = True

        self._save()
        logger.info(f"Marked document {document_id} as deleted")
        return True


# Singleton instance
_vector_store: Optional[VectorStore] = None


def get_vector_store() -> VectorStore:
    """Get singleton vector store instance"""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
        _vector_store._load_or_create()
    return _vector_store


def rebuild_vector_store():
    """Rebuild vector store from database"""
    global _vector_store
    _vector_store = VectorStore()
    # Will be populated from documents in database
    logger.info("Vector store reset")