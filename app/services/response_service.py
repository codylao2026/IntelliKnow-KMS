"""
Response generation service - RAG pipeline
"""

import json
import logging
import time
import asyncio
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import QueryLog
from app.services.intent_service import classify_intent, get_confidence_settings
from app.services.search_service import search_documents, rerank_results, rewrite_query
from app.utils.llm import generate_response, generate_response_stream
from config import settings

QUERY_REWRITE_WORD_THRESHOLD = 5

logger = logging.getLogger(__name__)

# Performance optimizations
ENABLE_PARALLEL_SEARCH = True  # Run intent + search in parallel
RERANK_CONFIDENCE_THRESHOLD = 0.7  # Skip reranking if confidence > this value
REDUCED_TOP_K = 4  # Reduced from 6

# Few-shot examples for response generation
FEW_SHOT_EXAMPLES = """Example 1 (HR):
Knowledge Base:
【Document 1】Leave Policy: Employees are entitled to 10 days of paid annual leave per year. Submit requests 3 days in advance, or immediately for special circumstances.

User Question: How many days of annual leave do I have?

Answer: According to company policy, employees are entitled to 10 days of paid annual leave per year. Submit requests 3 days in advance. Sources: [doc1]

---

Example 2 (Finance):
Knowledge Base:
【Document 1】Expense Reimbursement: Travel expenses must be submitted within 7 days after returning. Meal expenses are capped at 200 yuan per day. Original receipts are required.

User Question: What is the deadline for submitting travel expense reimbursement?

Answer: Travel expenses must be submitted within 7 days after returning from the business trip. Original receipts are required. Sources: [doc1]

---

Example 3 (Legal):
Knowledge Base:
【Document 1】Employment Contract: All employees must sign a labor contract within one month of joining. The contract specifies job duties, working hours, compensation, and termination conditions.

User Question: When should I sign my employment contract?

Answer: All employees must sign a labor contract within one month of joining the company. The contract specifies job duties, working hours, compensation, and termination conditions. Sources: [doc1]"""

# System prompt for response generation
SYSTEM_PROMPT = f"""You are an enterprise knowledge management assistant. Your task is to answer user questions based ONLY on the provided knowledge base documents.

CRITICAL RULES:
1. You MUST base your answer ONLY on the knowledge base content provided below
2. NEVER use your general knowledge or make up information
3. If the knowledge base doesn't contain relevant information, explicitly state: "I could not find relevant information in the knowledge base."
4. DO NOT include any citation markers like [doc1], [doc2], or "Sources:" in your answer
5. Answer in the same language as the user's question

{FEW_SHOT_EXAMPLES}"""


def build_rag_prompt(query: str, contexts: List[Dict[str, Any]]) -> str:
    """
    Build prompt for RAG response generation

    Args:
        query: User query
        contexts: List of context documents

    Returns:
        Formatted prompt
    """
    if not contexts:
        return f"""User Question: {query}

I could not find relevant information in the knowledge base to answer this question. Please try rephrasing or contact the administrator."""

    context_parts = []
    for i, ctx in enumerate(contexts):
        doc_num = i + 1
        doc_name = ctx.get("metadata", {}).get("document_name", f"Document {doc_num}")
        content = ctx.get("content", "")
        context_parts.append(f"【Document {doc_num}: {doc_name}】\n{content}")

    context_text = "\n\n".join(context_parts)

    prompt = f"""KNOWLEDGE BASE DOCUMENTS:
{context_text}

USER QUESTION: {query}

ANSWERING REQUIREMENTS:
- Answer based ONLY on the knowledge base content above
- Do NOT use your general knowledge or make assumptions
- Extract specific information from the documents provided
- If the documents don't contain relevant information, clearly state: "I could not find relevant information in the knowledge base."
- Do NOT include citation markers like [doc1], [doc2], "Sources:", or any document names in your answer
- The system will automatically display source references below your response

Provide your answer:"""

    return prompt


def validate_and_fix_citations(
    response: str, contexts: List[Dict[str, Any]], query: str = ""
) -> tuple:
    """
    Remove any citation markers from the response and handle "not found" cases

    Args:
        response: The generated response text
        contexts: The sources (for returning)
        query: The original query (for regenerating if needed)

    Returns:
        Tuple of (cleaned_response, contexts)
    """
    import re

    # Get list of document names from contexts
    doc_names_to_remove = []
    if contexts:
        for ctx in contexts:
            doc_name = ctx.get("metadata", {}).get("document_name", "")
            if doc_name:
                doc_names_to_remove.append(re.escape(doc_name))

    # Check if LLM says it couldn't find info but we have contexts
    not_found_patterns = [
        r"could not find",
        r"no[t ]*relevant",
        r"do not have.*information",
        r"could[n\']*t find.*information",
    ]

    llm_says_not_found = any(
        re.search(p, response, re.IGNORECASE) for p in not_found_patterns
    )

    # If LLM says not found but we have contexts, REPLACE the response entirely
    if llm_says_not_found and contexts:
        context_summaries = []
        for i, ctx in enumerate(contexts[:3]):  # Use top 3 contexts
            content = ctx.get("content", "")
            doc_name = ctx.get("metadata", {}).get("document_name", f"Document {i + 1}")
            if content:
                # Clean the content
                cleaned_content = content.strip()
                context_summaries.append(f"【{doc_name}】\n{cleaned_content}")

        if context_summaries:
            # Replace the "not found" response with actual knowledge base content
            response = f"""Based on the knowledge base documents, here is the relevant information:

{"=" * 60}

{"=" * 60}\n\n""".join(context_summaries)
            logger.warning(
                f"LLM said not found but had {len(contexts)} contexts - REPLACED response with KB content"
            )

    # Remove citation patterns
    patterns_to_remove = [
        r"Sources?:\s*\[?[^\]]*\]?",
        r"References?:\s*\[?[^\]]*\]?",
        r"\[(?:doc|DOC)[0-9]+\]",
        r"\[(?:FIN|HR|LEG)[A-Z0-9\-_]+\]",
        r"\[\s*[A-Z]{2,3}-[A-Z]+-[0-9]+\s*[^\]]*\]",
        r"\[\s*[A-Z]{2,3}-[A-Z]+-[0-9]+\s*\.(?:pdf|docx)\]",
        r"【[^】]*】",
        r"§[^§\n]*§",
    ]

    for doc_name_pattern in doc_names_to_remove:
        if doc_name_pattern:
            patterns_to_remove.append(r"\[\s*" + doc_name_pattern + r"\s*\]")

    for pattern in patterns_to_remove:
        response = re.sub(pattern, "", response, flags=re.IGNORECASE)

    response = re.sub(r"\s*,\s*\[?\s*\]?\s*$", "", response)
    response = re.sub(r"\s*\.\s*\[?\s*\]?\s*$", "", response)
    response = re.sub(r"\s*\[\s*\]\s*$", "", response)
    response = re.sub(r"\s+", " ", response)
    response = re.sub(r"\n{3,}", "\n\n", response)
    response = response.strip()

    return response, contexts


async def generate_response_from_rag(
    query: str,
    contexts: List[Dict[str, Any]],
    stream: bool = False,
    max_response_tokens: int = 500,  # Limit response length for speed
):
    """
    Generate response using RAG

    Args:
        query: User query
        contexts: Retrieved contexts
        stream: Enable streaming
        max_response_tokens: Maximum tokens in response (lower = faster)

    Returns:
        Generated response (str) or async generator if streaming
    """
    if not contexts:
        return "Sorry, no relevant information found in the knowledge base. Please try a different question or contact the administrator."

    prompt = build_rag_prompt(query, contexts)

    try:
        if stream:

            async def stream_generator():
                async for token in generate_response_stream(
                    prompt=prompt, system_prompt=SYSTEM_PROMPT, temperature=0.3
                ):
                    yield f"data: {json.dumps({'token': token})}\n\n"
                yield f"data: {json.dumps({'done': True})}\n\n"

            return stream_generator()
        else:
            return await generate_response(
                prompt=prompt, system_prompt=SYSTEM_PROMPT, temperature=0.3
            )
    except Exception as e:
        logger.error(f"Response generation error: {e}")
        return "Sorry, an error occurred while generating the response. Please try again later."


def format_sources(contexts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Format source documents for response

    Args:
        contexts: List of context documents

    Returns:
        Formatted sources (sorted by relevance, only include score > 0)
    """
    sources = []
    seen_ids = set()

    for ctx in contexts:
        doc_id = ctx.get("document_id")
        if doc_id and doc_id not in seen_ids:
            # Get score - prefer rerank_score, then score
            score = ctx.get("rerank_score", ctx.get("score", 0))
            
            # Skip documents with zero/negative score (not relevant)
            if score <= 0:
                continue
            
            seen_ids.add(doc_id)
            sources.append(
                {
                    "document_id": doc_id,
                    "document_name": ctx.get("metadata", {}).get(
                        "document_name", f"Document {doc_id}"
                    ),
                    "content": ctx.get("content", "")[:200],
                    "score": score,
                }
            )

    # Sort by score descending
    sources.sort(key=lambda x: x.get("score", 0), reverse=True)
    
    return sources


async def _get_conversation_history(
    db: AsyncSession, frontend: str, limit: int = 3
) -> List[Dict[str, str]]:
    """
    Get recent conversation history for query rewriting.

    Args:
        db: Database session
        frontend: Frontend source
        limit: Number of recent exchanges to return

    Returns:
        List of query-response pairs
    """
    try:
        from sqlalchemy import select, desc
        from app.models.database import QueryLog

        result = await db.execute(
            select(QueryLog)
            .where(QueryLog.frontend == frontend)
            .where(QueryLog.status == "success")
            .order_by(desc(QueryLog.created_at))
            .limit(limit * 2)
        )
        logs = result.scalars().all()

        # Build query-response pairs
        history = []
        for log in logs:
            history.insert(0, {"query": log.query, "response": log.response or ""})

        return history[-limit:] if len(history) > limit else history

    except Exception as e:
        logger.warning(f"Failed to get conversation history: {e}")
        return []


async def process_query(
    query: str,
    db: AsyncSession,
    frontend: str = "web",
    intent_hint: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Full RAG pipeline for query processing (optimized for speed)

    Args:
        query: User query
        db: Database session
        frontend: Source frontend (web, whatsapp, teams)
        intent_hint: Optional intent hint

    Returns:
        Response dict
    """
    start_time = time.time()

    try:
        # Step 1: Intent classification (fast - cached intents)
        intent_result = await classify_intent(query=query, db=db, hint=intent_hint)

        intent_name = intent_result["intent_name"]
        intent_id = intent_result["intent_id"]
        confidence = intent_result["confidence"]
        confidence_source = intent_result.get("confidence_source", "unknown")

        logger.info(
            f"Query classified as '{intent_name}' with confidence {confidence} [{confidence_source}]"
        )

        # Step 2: Get all document IDs for this intent from database
        valid_doc_ids = []
        has_intent_docs = False  # Default to False - no documents
        intent_doc_query_error = None

        if intent_id is not None:
            try:
                from sqlalchemy import select
                from app.models.database import Document

                result = await db.execute(
                    select(Document.id).where(Document.intent_id == intent_id)
                )
                valid_doc_ids = [row[0] for row in result.fetchall()]
                has_intent_docs = len(valid_doc_ids) > 0
                logger.info(
                    f"Intent '{intent_name}' (id={intent_id}) has {len(valid_doc_ids)} documents: {valid_doc_ids}"
                )
            except Exception as e:
                intent_doc_query_error = str(e)
                logger.error(f"Failed to get documents for intent {intent_id}: {e}")

        # If intent has no documents, return early - NO search for other intents
        if not has_intent_docs:
            logger.warning(f"=== INTENT HAS NO DOCUMENTS ===")
            response_text = "I couldn't find relevant documents for your query. Please check if the intent space has uploaded documents."

            query_log = QueryLog(
                query=query,
                intent_name=intent_name,
                intent_id=intent_id,
                confidence=0.0,
                confidence_source="no_documents",
                response=response_text,
                sources=[],
                frontend=frontend,
                status="no_intent_documents",
                response_time=(time.time() - start_time) * 1000,
            )
            db.add(query_log)
            await db.commit()

            return {
                "query": query,
                "response": response_text,
                "intent": intent_name,
                "confidence": 0.0,
                "confidence_source": "no_documents",
                "sources": [],
                "response_time": (time.time() - start_time) * 1000,
                "status": "no_intent_documents",
            }

        # Step 3: Hybrid search (no intent filter in vectorstore)
        search_results = await search_documents(
            query=query,
            intent_id=None,  # Don't filter in vectorstore
            top_k=REDUCED_TOP_K,
        )

        logger.info(f"Found {len(search_results)} search results")

        # Step 4: Filter by document_id (only return chunks from valid intent documents)
        if valid_doc_ids:
            original_count = len(search_results)
            all_doc_ids = [r.get("document_id") for r in search_results]
            logger.info(f"Search results document_ids: {all_doc_ids}")
            logger.info(f"Valid doc_ids for intent {intent_id}: {valid_doc_ids}")

            search_results = [
                r for r in search_results if r.get("document_id") in valid_doc_ids
            ]
            logger.info(
                f"Filtered from {original_count} to {len(search_results)} results for intent {intent_id}"
            )

        # If filtered to 0, return no results
        if not search_results:
            logger.warning("=== NO RESULTS AFTER FILTER ===")
            response_text = "I couldn't find relevant documents for your query."

            query_log = QueryLog(
                query=query,
                intent_name=intent_name,
                intent_id=intent_id,
                confidence=0.0,
                confidence_source="no_results",
                response=response_text,
                sources=[],
                frontend=frontend,
                status="no_results",
                response_time=(time.time() - start_time) * 1000,
            )
            db.add(query_log)
            await db.commit()

            return {
                "query": query,
                "response": response_text,
                "intent": intent_name,
                "confidence": 0.0,
                "confidence_source": "no_results",
                "sources": [],
                "response_time": (time.time() - start_time) * 1000,
                "status": "no_results",
            }

        # Log search result details for debugging
        for i, result in enumerate(search_results[:3]):
            logger.info(
                f"Final result {i + 1}: doc_id={result.get('document_id')}, score={result.get('score', 0):.3f}"
            )

        # Step 5: Rerank if we have results (always rerank regardless of confidence)
        if len(search_results) <= 2:
            reranked_results = search_results[: settings.RERANK_TOP_K]
            logger.info(f"Skipping reranking (only {len(search_results)} results)")
        else:
            logger.info(f"Running reranking for {len(search_results)} results")
            reranked_results = await rerank_results(
                query=query, results=search_results, top_k=settings.RERANK_TOP_K
            )

        # Step 6: Calculate answer confidence based on rerank scores (not intent classification)
        answer_confidence = 0.3
        answer_confidence_source = "default"

        if reranked_results:
            top_score = reranked_results[0].get(
                "rerank_score", reranked_results[0].get("score", 0)
            )
            if top_score >= 0.8:
                answer_confidence = 0.95
                answer_confidence_source = "high"
            elif top_score >= 0.5:
                answer_confidence = 0.7
                answer_confidence_source = "medium"
            elif top_score >= 0.3:
                answer_confidence = 0.5
                answer_confidence_source = "low"
            else:
                answer_confidence = 0.3
                answer_confidence_source = "very_low"
            logger.info(
                f"Answer confidence: {answer_confidence:.2f} (top_score={top_score:.3f}, source={answer_confidence_source})"
            )

        # Step 7: Get dynamic confidence threshold and check
        conf_settings = await get_confidence_settings(db)
        threshold = conf_settings["confidence_threshold"]

        # Check confidence threshold
        if answer_confidence < threshold:
            response_text = "I couldn't find a suitable answer to your question in the knowledge base. Please try rephrasing your question or contact the administrator for assistance."
            sources = []
            status = "low_confidence"
            response_time = (time.time() - start_time) * 1000
        else:
            # Step 8: Generate response (always returns string since stream=False)
            response_text = await generate_response_from_rag(
                query=query, contexts=reranked_results, stream=False
            )
            if response_text is None:
                response_text = ""

            # Step 9: Validate and fix citations to match actual sources
            response_text, corrected_sources = validate_and_fix_citations(
                str(response_text), reranked_results, query
            )

            # Step 10: Format sources (use corrected sources if citations were fixed)
            sources = format_sources(
                corrected_sources if corrected_sources else reranked_results
            )
            response_time = (time.time() - start_time) * 1000
            status = "success"

        # Step 11: Log query
        query_log = QueryLog(
            query=query,
            intent_name=intent_name,
            intent_id=intent_id,
            confidence=answer_confidence,
            confidence_source=answer_confidence_source,
            response=response_text,
            sources=[s["document_id"] for s in sources],
            frontend=frontend,
            status=status,
            response_time=response_time,
        )
        db.add(query_log)
        await db.commit()

        return {
            "query": query,
            "response": response_text,
            "intent": intent_name,
            "confidence": answer_confidence,
            "confidence_source": answer_confidence_source,
            "sources": sources,
            "response_time": response_time,
            "status": status,
        }

    except Exception as e:
        logger.error(f"Query processing error: {e}", exc_info=True)
        response_time = (time.time() - start_time) * 1000

        # Log failed query
        query_log = QueryLog(
            query=query,
            intent_name="error",
            confidence=0.0,
            confidence_source="error",
            response=f"Error: {str(e)}",
            frontend=frontend,
            status="failed",
            response_time=response_time,
        )
        db.add(query_log)
        await db.commit()

        return {
            "query": query,
            "response": "Sorry, an error occurred while processing your query. Please try again later.",
            "intent": "error",
            "confidence": 0.0,
            "confidence_source": "error",
            "sources": [],
            "response_time": response_time,
            "status": "failed",
        }


async def process_query_streaming(
    query: str,
    db: AsyncSession,
    frontend: str = "web",
    intent_hint: Optional[str] = None,
):
    """
    Streaming version of query processing for better UX (optimized for speed).
    Yields SSE events.

    Args:
        query: User query
        db: Database session
        frontend: Source frontend (web, whatsapp, teams)
        intent_hint: Optional intent hint

    Yields:
        SSE events with tokens and metadata
    """
    start_time = time.time()

    try:
        # Step 1: Intent classification
        yield f"data: {json.dumps({'event': 'intent', 'data': {'status': 'classifying'}})}\n\n"

        intent_result = await classify_intent(query=query, db=db, hint=intent_hint)

        intent_name = intent_result["intent_name"]
        intent_id = intent_result["intent_id"]
        confidence = intent_result["confidence"]
        confidence_source = intent_result.get("confidence_source", "unknown")

        yield f"data: {json.dumps({'event': 'intent', 'data': {'intent': intent_name, 'confidence': confidence, 'source': confidence_source}})}\n\n"

        # Step 2: Get all document IDs for this intent from database
        yield f"data: {json.dumps({'event': 'search', 'data': {'status': 'getting_documents'}})}\n\n"

        valid_doc_ids = []
        has_intent_docs = False  # Default to False
        if intent_id is not None:
            try:
                from sqlalchemy import select
                from app.models.database import Document

                result = await db.execute(
                    select(Document.id).where(Document.intent_id == intent_id)
                )
                valid_doc_ids = [row[0] for row in result.fetchall()]
                has_intent_docs = len(valid_doc_ids) > 0
                logger.info(
                    f"Intent '{intent_name}' has {len(valid_doc_ids)} documents: {valid_doc_ids}"
                )
            except Exception as e:
                logger.error(f"Failed to get documents for intent {intent_id}: {e}")

        # If intent has no documents, return early
        if not has_intent_docs:
            logger.warning("=== INTENT HAS NO DOCUMENTS (streaming) ===")
            response_text = "I couldn't find relevant documents for your query. Please check if the intent space has uploaded documents."
            response_time = (time.time() - start_time) * 1000

            yield f"data: {json.dumps({'event': 'search', 'data': {'count': 0}})}\n\n"
            yield f"data: {json.dumps({'event': 'done', 'data': {
                'response': response_text,
                'intent': intent_name,
                'confidence': 0.0,
                'confidence_source': 'no_documents',
                'sources': [],
                'status': 'no_intent_documents',
                'response_time': response_time
            })}\n\n"

            query_log = QueryLog(
                query=query,
                intent_name=intent_name,
                intent_id=intent_id,
                confidence=0.0,
                confidence_source="no_documents",
                response=response_text,
                sources=[],
                frontend=frontend,
                status="no_intent_documents",
                response_time=response_time,
            )
            db.add(query_log)
            await db.commit()
            return

        # Step 3: Hybrid search (no intent filter in vectorstore)
        yield f"data: {json.dumps({'event': 'search', 'data': {'status': 'searching'}})}\n\n"

        search_results = await search_documents(
            query=query,
            intent_id=None,  # Don't filter in vectorstore
            top_k=REDUCED_TOP_K,
        )

        # Step 4: Filter by document_id (only return chunks from valid intent documents)
        if valid_doc_ids:
            original_count = len(search_results)
            search_results = [
                r for r in search_results if r.get("document_id") in valid_doc_ids
            ]
            logger.info(
                f"Filtered from {original_count} to {len(search_results)} results for intent {intent_id}"
            )

        # If filtered to 0, return no results
        if not search_results:
            logger.warning("=== NO RESULTS AFTER FILTER (streaming) ===")
            response_text = "I couldn't find relevant documents for your query."
            response_time = (time.time() - start_time) * 1000

            yield f"data: {json.dumps({'event': 'search', 'data': {'count': 0}})}\n\n"
            yield f"data: {json.dumps({'event': 'done', 'data': {
                'response': response_text,
                'intent': intent_name,
                'confidence': 0.0,
                'confidence_source': 'no_results',
                'sources': [],
                'status': 'no_results',
                'response_time': response_time
            })}\n\n"

            query_log = QueryLog(
                query=query,
                intent_name=intent_name,
                intent_id=intent_id,
                confidence=0.0,
                confidence_source="no_results",
                response=response_text,
                sources=[],
                frontend=frontend,
                status="no_results",
                response_time=response_time,
            )
            db.add(query_log)
            await db.commit()
            return

        yield f"data: {json.dumps({'event': 'search', 'data': {'count': len(search_results)}})}\n\n"

        # Step 5: Rerank if we have results
        if len(search_results) <= 2:
            reranked_results = search_results[: settings.RERANK_TOP_K]
            yield f"data: {json.dumps({'event': 'rerank', 'data': {'status': 'skipped', 'reason': 'few_results'}})}\n\n"
        else:
            yield f"data: {json.dumps({'event': 'rerank', 'data': {'status': 'reranking'}})}\n\n"
            reranked_results = await rerank_results(
                query=query, results=search_results, top_k=settings.RERANK_TOP_K
            )

        # Step 6: Calculate answer confidence based on rerank scores
        answer_confidence = 0.3
        answer_confidence_source = "default"

        if reranked_results:
            top_score = reranked_results[0].get(
                "rerank_score", reranked_results[0].get("score", 0)
            )
            if top_score >= 0.8:
                answer_confidence = 0.95
                answer_confidence_source = "high"
            elif top_score >= 0.5:
                answer_confidence = 0.7
                answer_confidence_source = "medium"
            elif top_score >= 0.3:
                answer_confidence = 0.5
                answer_confidence_source = "low"
            else:
                answer_confidence = 0.3
                answer_confidence_source = "very_low"
            logger.info(f"Answer confidence: {answer_confidence:.2f} (top_score={top_score:.3f})")

        # Step 7: Check confidence threshold
        conf_settings = await get_confidence_settings(db)
        threshold = conf_settings["confidence_threshold"]

        if answer_confidence < threshold:
            response_text = "I couldn't find a suitable answer to your question in the knowledge base. Please try rephrasing your question or contact the administrator for assistance."
            sources = []
            status = "low_confidence"
            response_time = (time.time() - start_time) * 1000

            yield f"data: {json.dumps({'event': 'done', 'data': {
                'response': response_text,
                'intent': intent_name,
                'confidence': answer_confidence,
                'confidence_source': answer_confidence_source,
                'sources': sources,
                'status': status,
                'response_time': response_time
            })}\n\n"

            query_log = QueryLog(
                query=query,
                intent_name=intent_name,
                intent_id=intent_id,
                confidence=answer_confidence,
                confidence_source=answer_confidence_source,
                response=response_text,
                sources=[],
                frontend=frontend,
                status=status,
                response_time=response_time,
            )
            db.add(query_log)
            await db.commit()
            return

        # Step 8: Stream response
        yield f"data: {json.dumps({'event': 'response', 'data': {'status': 'generating'}})}\n\n"

        sources = format_sources(reranked_results)
        response_time = (time.time() - start_time) * 1000

        prompt = build_rag_prompt(query, reranked_results)

        full_response = ""
        async for token in generate_response_stream(
            prompt=prompt, system_prompt=SYSTEM_PROMPT, temperature=0.3
        ):
            full_response += token
            yield f"data: {json.dumps({'event': 'token', 'data': {'token': token}})}\n\n"

        # Validate and fix citations to match actual sources
        full_response, corrected_sources = validate_and_fix_citations(
            full_response, reranked_results, query
        )

        # Update sources if citations were fixed
        if corrected_sources:
            sources = format_sources(corrected_sources)

        # Send corrected response
        yield f"data: {json.dumps({'event': 'corrected_response', 'data': {'response': full_response}})}\n\n"

        response_time = (time.time() - start_time) * 1000

        yield f"data: {json.dumps({'event': 'done', 'data': {
            'response': full_response,
            'intent': intent_name,
            'confidence': answer_confidence,
            'confidence_source': answer_confidence_source,
            'sources': sources,
            'response_time': response_time,
            'status': 'success'
        })}\n\n"

        # Log query
        query_log = QueryLog(
            query=query,
            intent_name=intent_name,
            intent_id=intent_id,
            confidence=answer_confidence,
            confidence_source=answer_confidence_source,
            response=full_response,
            sources=[s["document_id"] for s in sources],
            frontend=frontend,
            status="success",
            response_time=response_time,
        )
        db.add(query_log)
        await db.commit()

    except Exception as e:
        logger.error(f"Streaming query processing error: {e}", exc_info=True)
        yield f"data: {json.dumps({'event': 'error', 'data': {'message': 'An error occurred while processing your query.'}})}\n\n"
