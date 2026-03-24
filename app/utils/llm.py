"""
LLM client for SiliconCloud API - Using raw httpx for better compatibility
"""

import os
import json
import logging
from typing import List, Optional, Dict, Any, Generator
import httpx

from config import settings

logger = logging.getLogger(__name__)

# Lazy initialization
_api_key = None


def get_api_key() -> str:
    """Get API key"""
    global _api_key
    if _api_key is None:
        _api_key = settings.SILICONCLOUD_API_KEY or settings.AZURE_OPENAI_API_KEY
    return _api_key


def get_base_url() -> str:
    """Get base URL"""
    if settings.SILICONCLOUD_API_KEY:
        return settings.SILICONCLOUD_BASE_URL
    elif settings.AZURE_OPENAI_API_KEY:
        return f"{settings.AZURE_OPENAI_ENDPOINT}/openai/deployments/{settings.AZURE_LLM_MODEL}"
    return settings.SILICONCLOUD_BASE_URL


async def generate_response(
    prompt: str,
    system_prompt: Optional[str] = None,
    temperature: float = 0.7,
    stream: bool = False,
    model: str = None,
) -> str:
    """
    Generate response from LLM using SiliconCloud API

    Args:
        prompt: User prompt
        system_prompt: System prompt
        temperature: Temperature for generation
        stream: Enable streaming response
        model: Model to use (defaults to LLM_MODEL)

    Returns:
        Generated response text
    """
    if model is None:
        model = settings.LLM_MODEL

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    try:
        async with httpx.AsyncClient(trust_env=False, proxy=None) as client:
            response = await client.post(
                f"{get_base_url()}/chat/completions",
                headers={
                    "Authorization": f"Bearer {get_api_key()}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": 2000,
                    "stream": stream,
                },
                timeout=60.0,
            )

            if response.status_code != 200:
                logger.error(f"API error: {response.status_code} - {response.text}")
                raise Exception(f"API error: {response.status_code}")

            result = response.json()
            return result["choices"][0]["message"]["content"]

    except Exception as e:
        logger.error(f"LLM generation error: {e}")
        raise


async def generate_response_stream(
    prompt: str,
    system_prompt: Optional[str] = None,
    temperature: float = 0.7,
    model: str = None,
) -> Generator[str, None, None]:
    """
    Generate streaming response from LLM

    Args:
        prompt: User prompt
        system_prompt: System prompt
        temperature: Temperature for generation
        model: Model to use

    Yields:
        Response tokens
    """
    if model is None:
        model = settings.LLM_MODEL

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    try:
        async with httpx.AsyncClient(trust_env=False, proxy=None) as client:
            async with client.stream(
                "POST",
                f"{get_base_url()}/chat/completions",
                headers={
                    "Authorization": f"Bearer {get_api_key()}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": 2000,
                    "stream": True,
                },
                timeout=60.0,
            ) as response:
                if response.status_code != 200:
                    logger.error(f"API error: {response.status_code}")
                    raise Exception(f"API error: {response.status_code}")

                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data)
                            delta = chunk.get("choices", [{}])[0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue

    except Exception as e:
        logger.error(f"Streaming error: {e}")
        raise


async def get_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Get embeddings for texts using SiliconCloud API

    Args:
        texts: List of texts to embed

    Returns:
        List of embedding vectors
    """
    try:
        async with httpx.AsyncClient(trust_env=False, proxy=None) as client:
            response = await client.post(
                f"{get_base_url()}/embeddings",
                headers={
                    "Authorization": f"Bearer {get_api_key()}",
                    "Content-Type": "application/json",
                },
                json={"model": settings.EMBEDDING_MODEL, "input": texts},
                timeout=30.0,
            )

            if response.status_code != 200:
                logger.error(f"Embedding API error: {response.status_code}")
                raise Exception(f"Embedding API error: {response.status_code}")

            result = response.json()
            return [item["embedding"] for item in result["data"]]

    except Exception as e:
        logger.error(f"Embedding error: {e}")
        raise


async def classify_intent(
    query: str, intents: List[Dict[str, Any]], confidence_threshold: float = 0.7
) -> Dict[str, Any]:
    """
    Classify query intent using LLM

    Args:
        query: User query
        intents: List of intent dicts with name, description, keywords
        confidence_threshold: Minimum confidence threshold

    Returns:
        Dict with intent_name, confidence
    """
    intent_model = getattr(settings, "INTENT_MODEL", settings.LLM_MODEL)

    intent_list = "\n".join(
        [
            f"- {i['name']}: {i.get('description', '')} (keywords: {', '.join(i.get('keywords', []))})"
            for i in intents
        ]
    )

    prompt = f"""Please classify the user's question into one of the available intents.

Available intents:
{intent_list}

User question: {query}

Return the result in JSON format:
{{"intent": "intent_name", "confidence": 0.0-1.0}}

Only return JSON, no other content."""

    try:
        messages = [{"role": "user", "content": prompt}]

        async with httpx.AsyncClient(trust_env=False, proxy=None) as client:
            response = await client.post(
                f"{get_base_url()}/chat/completions",
                headers={
                    "Authorization": f"Bearer {get_api_key()}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": intent_model,
                    "messages": messages,
                    "temperature": 0.3,
                    "max_tokens": 200,
                },
                timeout=30.0,
            )

            if response.status_code != 200:
                logger.error(f"Intent classification API error: {response.status_code}")
                raise Exception(f"API error: {response.status_code}")

            result = response.json()
            result_text = result["choices"][0]["message"]["content"].strip()

            # Parse JSON
            if result_text.startswith("```json"):
                result_text = result_text[7:]
            if result_text.startswith("```"):
                result_text = result_text[3:]
            if result_text.endswith("```"):
                result_text = result_text[:-3]

            parsed = json.loads(result_text.strip())

            # Apply threshold
            if parsed.get("confidence", 0) < confidence_threshold:
                parsed["intent"] = settings.FALLBACK_INTENT

            logger.info(
                f"Intent classified: {parsed.get('intent')} ({parsed.get('confidence', 0):.2f})"
            )
            return parsed

    except Exception as e:
        logger.error(f"Intent classification error: {e}")
        return {"intent": settings.FALLBACK_INTENT, "confidence": 0.5}
