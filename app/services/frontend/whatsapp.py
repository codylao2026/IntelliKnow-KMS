"""
WhatsApp Business API integration
"""
import logging
import hashlib
import hmac
import json
from typing import Optional, Dict, Any
import httpx

from config import settings

logger = logging.getLogger(__name__)


class WhatsAppClient:
    """WhatsApp Business API client"""

    def __init__(self):
        self.phone_number_id = settings.WHATSAPP_PHONE_NUMBER_ID
        self.access_token = settings.WHATSAPP_ACCESS_TOKEN
        self.verify_token = settings.WHATSAPP_VERIFY_TOKEN
        self.api_url = f"https://graph.facebook.com/v18.0/{self.phone_number_id}"

    def verify_webhook(self, mode: str, token: str, challenge: str) -> str:
        """Verify webhook for WhatsApp"""
        if mode == "subscribe" and token == self.verify_token:
            return challenge
        return None

    def verify_signature(self, payload: bytes, signature: str) -> bool:
        """Verify request signature"""
        if not self.access_token:
            return True  # Skip verification if no token

        expected = hmac.new(
            self.access_token.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(f"sha256={expected}", signature)

    async def send_message(self, to: str, message: str) -> Dict[str, Any]:
        """Send message via WhatsApp"""
        if not self.phone_number_id or not self.access_token:
            logger.warning("WhatsApp credentials not configured")
            return {"success": False, "error": "WhatsApp not configured"}

        url = f"{self.api_url}/messages"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

        # Format message for WhatsApp (markdown support)
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": message}
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=payload)
                result = response.json()

                if response.status_code == 200:
                    return {"success": True, "data": result}
                else:
                    logger.error(f"WhatsApp API error: {result}")
                    return {"success": False, "error": result}

        except Exception as e:
            logger.error(f"WhatsApp send error: {e}")
            return {"success": False, "error": str(e)}

    def parse_webhook_payload(self, payload: dict) -> Optional[Dict[str, Any]]:
        """Parse incoming WhatsApp webhook"""
        try:
            entry = payload.get("entry", [{}])[0]
            changes = entry.get("changes", [{}])[0]
            value = changes.get("value", {})

            if not value.get("messages"):
                return None

            message = value["messages"][0]
            from_number = message.get("from")

            # Get message text
            if message.get("type") == "text":
                text = message.get("text", {}).get("body", "")
            else:
                text = f"[{message.get('type')} message]"

            return {
                "from": from_number,
                "message": text,
                "message_id": message.get("id"),
                "timestamp": message.get("timestamp")
            }

        except Exception as e:
            logger.error(f"Parse webhook error: {e}")
            return None

    def format_response_for_whatsapp(self, response: str, sources: list) -> str:
        """Format response for WhatsApp"""
        # WhatsApp supports limited markdown
        formatted = response

        # Add source references
        if sources:
            formatted += "\n\n📚 参考来源:"
            for i, source in enumerate(sources[:3], 1):
                formatted += f"\n[{i}] {source.get('document_name', '文档')}"

        return formatted


# Singleton instance
_whatsapp_client: Optional[WhatsAppClient] = None


def get_whatsapp_client() -> WhatsAppClient:
    """Get WhatsApp client instance"""
    global _whatsapp_client
    if _whatsapp_client is None:
        _whatsapp_client = WhatsAppClient()
    return _whatsapp_client


async def handle_whatsapp_webhook(payload: dict) -> Optional[str]:
    """
    Handle incoming WhatsApp webhook

    Returns:
        Response message to send back
    """
    client = get_whatsapp_client()
    parsed = client.parse_webhook_payload(payload)

    if not parsed:
        return None

    from_number = parsed["from"]
    user_message = parsed["message"]

    logger.info(f"WhatsApp message from {from_number}: {user_message}")

    # Process through RAG pipeline
    from app.services.response_service import process_query
    from app.utils.database import async_session_maker

    async with async_session_maker() as db:
        result = await process_query(
            query=user_message,
            db=db,
            frontend="whatsapp"
        )

    # Format response for WhatsApp
    response_text = client.format_response_for_whatsapp(
        result["response"],
        result.get("sources", [])
    )

    # Send response
    await client.send_message(from_number, response_text)

    return response_text