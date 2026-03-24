"""
Intent classification service with hierarchical confidence logic
"""
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import Intent, Config
from app.utils.llm import classify_intent as llm_classify_intent
from config import settings

logger = logging.getLogger(__name__)


async def get_confidence_settings(db: AsyncSession) -> Dict[str, float]:
    """Get confidence settings from database or defaults"""
    defaults = {
        "confidence_threshold": settings.DEFAULT_CONFIDENCE_THRESHOLD,
        "llm_weight": 0.5,
        "keyword_weight": 0.5
    }

    result = await db.execute(select(Config).where(Config.key.in_(defaults.keys())))
    configs = {c.key: float(c.value) if c.value else defaults[c.key] for c in result.scalars().all()}

    return {**defaults, **configs}


async def save_confidence_settings(
    db: AsyncSession,
    confidence_threshold: float,
    llm_weight: float = 0.5,
    keyword_weight: float = 0.5
) -> bool:
    """Save confidence settings to database"""
    settings_map = {
        "confidence_threshold": str(confidence_threshold),
        "llm_weight": str(llm_weight),
        "keyword_weight": str(keyword_weight)
    }

    for key, value in settings_map.items():
        result = await db.execute(select(Config).where(Config.key == key))
        config = result.scalar_one_or_none()

        if config:
            config.value = value
        else:
            db.add(Config(key=key, value=value))

    await db.commit()
    logger.info(f"Confidence settings saved: threshold={confidence_threshold}, llm_w={llm_weight}, kw_w={keyword_weight}")
    return True


async def get_all_intents(db: AsyncSession) -> List[Dict[str, Any]]:
    """Get all intents from database"""
    result = await db.execute(select(Intent))
    intents = result.scalars().all()

    return [
        {
            "id": intent.id,
            "name": intent.name,
            "description": intent.description,
            "keywords": intent.keywords or [],
            "is_default": intent.is_default
        }
        for intent in intents
    ]


async def classify_intent(
    query: str,
    db: AsyncSession,
    confidence_threshold: float = None,
    hint: Optional[str] = None
) -> Dict[str, Any]:
    """
    Classify query intent using hierarchical confidence logic

    Logic:
    1. If LLM confidence >= threshold -> use LLM result
    2. Else if keyword score >= threshold -> use keyword result
    3. Else -> weighted fusion (50% LLM + 50% Keyword)

    Args:
        query: User query
        db: Database session
        confidence_threshold: Override default threshold
        hint: Optional intent hint

    Returns:
        Dict with intent_name, intent_id, confidence, confidence_source
    """
    conf_settings = await get_confidence_settings(db)
    if confidence_threshold is None:
        confidence_threshold = conf_settings["confidence_threshold"]

    intents = await get_all_intents(db)

    if not intents:
        logger.warning("No intents found in database")
        return {
            "intent_name": settings.FALLBACK_INTENT,
            "intent_id": None,
            "confidence": 0.0,
            "confidence_source": "none"
        }

    if hint:
        for intent in intents:
            if intent["name"].lower() == hint.lower():
                return {
                    "intent_name": intent["name"],
                    "intent_id": intent["id"],
                    "confidence": 1.0,
                    "confidence_source": "hint"
                }

    try:
        # Step 1: LLM classification
        llm_result = await llm_classify_intent(
            query=query,
            intents=intents,
            confidence_threshold=confidence_threshold
        )
        llm_intent = llm_result.get("intent", settings.FALLBACK_INTENT)
        llm_confidence = llm_result.get("confidence", 0.0)

        # Step 2: Keyword matching
        keyword_scores = {}
        for intent in intents:
            kw_score = calculate_keyword_match(query, intent.get("keywords", []))
            keyword_scores[intent["name"]] = kw_score

        top_kw_intent = max(keyword_scores, key=keyword_scores.get) if keyword_scores else None
        top_kw_score = keyword_scores.get(top_kw_intent, 0.0) if top_kw_intent else 0.0

        # Step 3: Hierarchical decision
        final_intent = settings.FALLBACK_INTENT
        final_confidence = 0.0
        confidence_source = "fallback"

        if llm_confidence >= confidence_threshold:
            # Path A: LLM confidence is sufficient
            final_intent = llm_intent
            final_confidence = llm_confidence
            confidence_source = "llm"

        elif top_kw_score >= confidence_threshold:
            # Path B: Keyword score meets threshold
            final_intent = top_kw_intent
            final_confidence = top_kw_score
            confidence_source = "keyword"

        else:
            # Path C: Weighted fusion (50% LLM + 50% Keyword)
            llm_w = conf_settings["llm_weight"]
            kw_w = conf_settings["keyword_weight"]

            intent_scores = {}
            for intent in intents:
                score = 0.0
                if intent["name"] == llm_intent:
                    score += llm_confidence * llm_w
                kw_score = keyword_scores.get(intent["name"], 0.0)
                score += kw_score * kw_w
                intent_scores[intent["name"]] = score

            if intent_scores:
                final_intent = max(intent_scores, key=intent_scores.get)
                final_confidence = intent_scores.get(final_intent, 0.0)
                confidence_source = "fusion"

            if final_confidence > 1.0:
                final_confidence = 1.0

        # Find intent ID
        intent_id = None
        for intent in intents:
            if intent["name"] == final_intent:
                intent_id = intent["id"]
                break

        logger.info(f"Intent classification: LLM={llm_intent}({llm_confidence:.2f}), "
                   f"Keyword={top_kw_intent}({top_kw_score:.2f}), "
                   f"Final={final_intent}({final_confidence:.2f}) [{confidence_source}]")

        return {
            "intent_name": final_intent,
            "intent_id": intent_id,
            "confidence": final_confidence,
            "confidence_source": confidence_source,
            "llm_intent": llm_intent,
            "llm_confidence": llm_confidence,
            "keyword_intent": top_kw_intent,
            "keyword_score": top_kw_score
        }

    except Exception as e:
        logger.error(f"Intent classification error: {e}")
        return {
            "intent_name": settings.FALLBACK_INTENT,
            "intent_id": None,
            "confidence": 0.0,
            "confidence_source": "error"
        }

    # If hint provided, try to match first
    if hint:
        for intent in intents:
            if intent["name"].lower() == hint.lower():
                return {
                    "intent_name": intent["name"],
                    "intent_id": intent["id"],
                    "confidence": 1.0
                }

    try:
        # 1. LLM classification
        llm_result = await llm_classify_intent(
            query=query,
            intents=intents,
            confidence_threshold=confidence_threshold
        )
        llm_intent = llm_result.get("intent", settings.FALLBACK_INTENT)
        llm_confidence = llm_result.get("confidence", 0.0)

        # 2. Keyword matching
        keyword_scores = {}
        for intent in intents:
            kw_score = calculate_keyword_match(query, intent.get("keywords", []))
            keyword_scores[intent["name"]] = kw_score

        # Get top keyword intent
        top_kw_intent = max(keyword_scores, key=keyword_scores.get) if keyword_scores else None
        top_kw_score = keyword_scores.get(top_kw_intent, 0.0) if top_kw_intent else 0.0

        # 3. Weighted fusion
        intent_scores = {}
        for intent in intents:
            score = 0.0
            
            # LLM score contribution
            if intent["name"] == llm_intent:
                score += llm_confidence * settings.INTENT_LLM_WEIGHT
            
            # Keyword score contribution
            kw_score = keyword_scores.get(intent["name"], 0.0)
            if kw_score >= settings.INTENT_KEYWORD_THRESHOLD:
                score += kw_score * settings.INTENT_KEYWORD_WEIGHT
            
            intent_scores[intent["name"]] = score

        # Select best intent
        final_intent = max(intent_scores, key=intent_scores.get) if intent_scores else settings.FALLBACK_INTENT
        final_confidence = intent_scores.get(final_intent, 0.0) if final_intent else 0.0

        # Normalize confidence
        if final_confidence > 1.0:
            final_confidence = 1.0

        # Find intent ID
        intent_id = None
        for intent in intents:
            if intent["name"] == final_intent:
                intent_id = intent["id"]
                break

        logger.info(f"Intent classification: LLM={llm_intent}({llm_confidence:.2f}), "
                   f"Keyword={top_kw_intent}({top_kw_score:.2f}), "
                   f"Final={final_intent}({final_confidence:.2f})")

        return {
            "intent_name": final_intent,
            "intent_id": intent_id,
            "confidence": final_confidence,
            "llm_intent": llm_intent,
            "llm_confidence": llm_confidence,
            "keyword_intent": top_kw_intent,
            "keyword_score": top_kw_score
        }

    except Exception as e:
        logger.error(f"Intent classification error: {e}")
        return {
            "intent_name": settings.FALLBACK_INTENT,
            "intent_id": None,
            "confidence": 0.0
        }


def calculate_keyword_match(query: str, keywords: List[str]) -> float:
    """
    Calculate keyword-based match score

    Args:
        query: User query
        keywords: List of keywords

    Returns:
        Match score (0-1)
    """
    if not keywords:
        return 0.0

    query_lower = query.lower()
    matches = sum(1 for kw in keywords if kw.lower() in query_lower)
    return matches / len(keywords)