"""
Response generation service - RAG pipeline
"""
import json
import logging
import time
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import QueryLog
from app.services.intent_service import classify_intent, get_confidence_settings
from app.services.search_service import search_documents, rerank_results, rewrite_query
from app.utils.llm import generate_response, generate_response_stream
from config import settings

QUERY_REWRITE_WORD_THRESHOLD = 5

logger = logging.getLogger(__name__)

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
SYSTEM_PROMPT = f"""You are an enterprise knowledge management assistant. Your tasks are:
1. Answer user questions based on the provided knowledge base content
2. Be concise, accurate, and factual
3. If the knowledge base does not have relevant information, clearly inform the user
4. Always cite source documents
5. Answer in the same language as the user's question

Answer format requirements:
- Provide the answer first
- Then list reference sources [doc1], [doc2], etc.
- Do not fabricate information

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
    context_text = "\n\n".join([
        f"【Document {i+1}】{ctx.get('content', '')}"
        for i, ctx in enumerate(contexts)
    ])

    prompt = f"""Based on the following knowledge base content, answer the user's question.

Knowledge Base Content:
{context_text}

User Question: {query}

Please answer based on the above knowledge base content. If the knowledge base does not have relevant information, simply state "No relevant information found in the knowledge base"."""

    return prompt


async def generate_response_from_rag(
    query: str,
    contexts: List[Dict[str, Any]],
    stream: bool = False
):
    """
    Generate response using RAG

    Args:
        query: User query
        contexts: Retrieved contexts
        stream: Enable streaming

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
                    prompt=prompt,
                    system_prompt=SYSTEM_PROMPT,
                    temperature=0.3
                ):
                    yield f"data: {json.dumps({'token': token})}\n\n"
                yield f"data: {json.dumps({'done': True})}\n\n"

            return stream_generator()
        else:
            return await generate_response(
                prompt=prompt,
                system_prompt=SYSTEM_PROMPT,
                temperature=0.3
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
        Formatted sources
    """
    sources = []
    seen_ids = set()

    for ctx in contexts:
        doc_id = ctx.get("document_id")
        if doc_id and doc_id not in seen_ids:
            seen_ids.add(doc_id)
            sources.append({
                "document_id": doc_id,
                "document_name": ctx.get("metadata", {}).get("document_name", f"Document {doc_id}"),
                "content": ctx.get("content", "")[:200],
                "score": ctx.get("score", 0)
            })

    return sources


async def _get_conversation_history(
    db: AsyncSession,
    frontend: str,
    limit: int = 3
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
            history.insert(0, {
                "query": log.query,
                "response": log.response or ""
            })

        return history[-limit:] if len(history) > limit else history

    except Exception as e:
        logger.warning(f"Failed to get conversation history: {e}")
        return []


async def process_query(
    query: str,
    db: AsyncSession,
    frontend: str = "web",
    intent_hint: Optional[str] = None
) -> Dict[str, Any]:
    """
    Full RAG pipeline for query processing

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
        # Step 1: Intent classification
        intent_result = await classify_intent(
            query=query,
            db=db,
            hint=intent_hint
        )

        intent_name = intent_result["intent_name"]
        intent_id = intent_result["intent_id"]
        confidence = intent_result["confidence"]
        confidence_source = intent_result.get("confidence_source", "unknown")

        logger.info(f"Query classified as '{intent_name}' with confidence {confidence} [{confidence_source}]")

        # Step 2: Query rewrite (LLM-based)
        # Only rewrite short queries (< 5 words) with conversation history
        if len(query.split()) < QUERY_REWRITE_WORD_THRESHOLD:
            # Get conversation history from recent queries
            conversation_history = await _get_conversation_history(db, frontend)
            rewritten_query = await rewrite_query(query, conversation_history)
            if rewritten_query != query:
                logger.info(f"Query rewritten: '{query}' -> '{rewritten_query}'")
        else:
            rewritten_query = query

        # Step 3: Hybrid search
        search_results = await search_documents(
            query=rewritten_query,
            intent_id=intent_id,
            top_k=settings.TOP_K_DOCUMENTS
        )

        logger.info(f"Found {len(search_results)} search results")

        # Step 4: Rerank
        reranked_results = await rerank_results(
            query=rewritten_query,
            results=search_results,
            top_k=settings.RERANK_TOP_K
        )

        # Step 5: Get dynamic confidence threshold and check
        conf_settings = await get_confidence_settings(db)
        threshold = conf_settings["confidence_threshold"]

        # Check confidence threshold
        if confidence < threshold:
            response_text = "I couldn't find a suitable answer to your question in the knowledge base. Please try rephrasing your question or contact the administrator for assistance."
            sources = []
            status = "low_confidence"
            response_time = (time.time() - start_time) * 1000
        else:
            # Step 6: Generate response
            response_text = await generate_response_from_rag(
                query=query,
                contexts=reranked_results
            )

            # Step 7: Format sources
            sources = format_sources(reranked_results)
            response_time = (time.time() - start_time) * 1000

            # Determine status
            if not search_results:
                status = "no_results"
            else:
                status = "success"

        # Step 7: Log query
        query_log = QueryLog(
            query=query,
            intent_name=intent_name,
            intent_id=intent_id,
            confidence=confidence,
            confidence_source=confidence_source,
            response=response_text,
            sources=[s["document_id"] for s in sources],
            frontend=frontend,
            status=status,
            response_time=response_time
        )
        db.add(query_log)
        await db.commit()

        return {
            "query": query,
            "response": response_text,
            "intent": intent_name,
            "confidence": confidence,
            "confidence_source": confidence_source,
            "sources": sources,
            "response_time": response_time,
            "status": status
        }

    except Exception as e:
        logger.error(f"Query processing error: {e}")
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
            response_time=response_time
        )
        db.add(query_log)
        await db.commit()

        return {
            "query": query,
            "response": "Sorry, an error occurred while processing your query. Please try again later.",
            "intent": "error",
            "confidence": 0.0,
            "sources": [],
            "response_time": response_time,
            "status": "failed"
        }


async def process_query_streaming(
    query: str,
    db: AsyncSession,
    frontend: str = "web",
    intent_hint: Optional[str] = None
):
    """
    Streaming version of query processing for better UX.
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

        intent_result = await classify_intent(
            query=query,
            db=db,
            hint=intent_hint
        )

        intent_name = intent_result["intent_name"]
        intent_id = intent_result["intent_id"]
        confidence = intent_result["confidence"]
        confidence_source = intent_result.get("confidence_source", "unknown")

        yield f"data: {json.dumps({'event': 'intent', 'data': {'intent': intent_name, 'confidence': confidence, 'source': confidence_source}})}\n\n"

        # Step 2: Query rewrite (LLM-based)
        if len(query.split()) < QUERY_REWRITE_WORD_THRESHOLD:
            conversation_history = await _get_conversation_history(db, frontend)
            rewritten_query = await rewrite_query(query, conversation_history)
            if rewritten_query != query:
                logger.info(f"Query rewritten: '{query}' -> '{rewritten_query}'")
                yield f"data: {json.dumps({'event': 'rewrite', 'data': {'original': query, 'rewritten': rewritten_query}})}\n\n"
        else:
            rewritten_query = query

        # Step 3: Hybrid search
        yield f"data: {json.dumps({'event': 'search', 'data': {'status': 'searching'}})}\n\n"

        search_results = await search_documents(
            query=rewritten_query,
            intent_id=intent_id,
            top_k=settings.TOP_K_DOCUMENTS
        )

        yield f"data: {json.dumps({'event': 'search', 'data': {'count': len(search_results)}})}\n\n"

        # Step 4: Rerank
        yield f"data: {json.dumps({'event': 'rerank', 'data': {'status': 'reranking'}})}\n\n"

        reranked_results = await rerank_results(
            query=rewritten_query,
            results=search_results,
            top_k=settings.RERANK_TOP_K
        )

        # Step 5: Get dynamic threshold and check
        conf_settings = await get_confidence_settings(db)
        threshold = conf_settings["confidence_threshold"]

        if confidence < threshold:
            response_text = "I couldn't find a suitable answer to your question in the knowledge base. Please try rephrasing your question or contact the administrator for assistance."
            sources = []
            status = "low_confidence"
            response_time = (time.time() - start_time) * 1000

            yield f"data: {json.dumps({'event': 'done', 'data': {'response': response_text, 'status': status, 'response_time': response_time}})}\n\n"

            # Log query
            query_log = QueryLog(
                query=query,
                intent_name=intent_name,
                intent_id=intent_id,
                confidence=confidence,
                confidence_source=confidence_source,
                response=response_text,
                sources=[],
                frontend=frontend,
                status=status,
                response_time=response_time
            )
            db.add(query_log)
            await db.commit()
            return

        # Step 6: Stream response
        yield f"data: {json.dumps({'event': 'response', 'data': {'status': 'generating'}})}\n\n"

        sources = format_sources(reranked_results)
        response_time = (time.time() - start_time) * 1000

        prompt = build_rag_prompt(query, reranked_results)

        full_response = ""
        async for token in generate_response_stream(
            prompt=prompt,
            system_prompt=SYSTEM_PROMPT,
            temperature=0.3
        ):
            full_response += token
            yield f"data: {json.dumps({'event': 'token', 'data': {'token': token}})}\n\n"

        response_time = (time.time() - start_time) * 1000

        yield f"data: {json.dumps({'event': 'done', 'data': {'response': full_response, 'sources': sources, 'response_time': response_time, 'status': 'success'}})}\n\n"

        # Log query
        query_log = QueryLog(
            query=query,
            intent_name=intent_name,
            intent_id=intent_id,
            confidence=confidence,
            confidence_source=confidence_source,
            response=full_response,
            sources=[s["document_id"] for s in sources],
            frontend=frontend,
            status="success",
            response_time=response_time
        )
        db.add(query_log)
        await db.commit()

    except Exception as e:
        logger.error(f"Streaming query processing error: {e}")
        yield f"data: {json.dumps({'event': 'error', 'data': {'message': 'An error occurred while processing your query.'}})}\n\n"