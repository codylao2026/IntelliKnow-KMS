"""
Microsoft Teams Bot integration
"""
import logging
import json
from typing import Optional, Dict, Any, List
import httpx

from config import settings

logger = logging.getLogger(__name__)


class TeamsClient:
    """Microsoft Teams Bot client"""

    def __init__(self):
        self.app_id = settings.TEAMS_APP_ID
        self.app_password = settings.TEAMS_APP_PASSWORD
        self.tenant_id = settings.TEAMS_TENANT_ID
        self.bot_id = settings.TEAMS_BOT_ID

    async def send_message(self, conversation_id: str, message: str) -> Dict[str, Any]:
        """Send message to Teams conversation"""
        if not self.app_id or not self.app_password:
            logger.warning("Teams credentials not configured")
            return {"success": False, "error": "Teams not configured"}

        # Microsoft Bot Framework API
        service_url = f"https://smba.trafficmanager.net/teams/v3.0"
        url = f"{service_url}/conversations/{conversation_id}/activities"

        payload = {
            "type": "message",
            "text": message,
            "from": {"id": self.bot_id, "name": "IntelliKnow Bot"},
            "recipient": {"id": "user"}
        }

        try:
            async with httpx.AsyncClient(trust_env=False) as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {self._get_token()}",
                        "Content-Type": "application/json"
                    }
                )

                if response.status_code in (200, 201):
                    return {"success": True, "data": response.json()}
                else:
                    logger.error(f"Teams API error: {response.text}")
                    return {"success": False, "error": response.text}

        except Exception as e:
            logger.error(f"Teams send error: {e}")
            return {"success": False, "error": str(e)}

    async def send_adaptive_card(
        self,
        conversation_id: str,
        title: str,
        content: str,
        sources: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Send Adaptive Card to Teams"""
        if not self.app_id or not self.app_password:
            return {"success": False, "error": "Teams not configured"}

        # Build Adaptive Card
        card = {
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "type": "AdaptiveCard",
            "version": "1.4",
            "body": [
                {
                    "type": "TextBlock",
                    "text": title,
                    "weight": "bolder",
                    "size": "medium"
                },
                {
                    "type": "TextBlock",
                    "text": content,
                    "wrap": True,
                    "spacing": "medium"
                }
            ]
        }

        # Add sources as fact set
        if sources:
            facts = [
                {"title": f"[{i+1}]", "value": s.get("document_name", "文档")}
                for i, s in enumerate(sources[:5])
            ]
            card["body"].append({
                "type": "FactSet",
                "facts": facts
            })

        service_url = f"https://smba.trafficmanager.net/teams/v3.0"
        url = f"{service_url}/conversations/{conversation_id}/activities"

        payload = {
            "type": "message",
            "attachments": [{
                "contentType": "application/vnd.microsoft.card.adaptive",
                "content": card
            }]
        }

        try:
            async with httpx.AsyncClient(trust_env=False) as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {self._get_token()}",
                        "Content-Type": "application/json"
                    }
                )

                return {"success": response.status_code in (200, 201)}

        except Exception as e:
            logger.error(f"Teams Adaptive Card error: {e}")
            return {"success": False, "error": str(e)}

    def _get_token(self) -> str:
        """Get OAuth token for Teams"""
        # Simplified - in production, implement proper OAuth flow
        # This would require Azure AD token acquisition
        return "placeholder_token"

    def parse_activity(self, activity: dict) -> Optional[Dict[str, Any]]:
        """Parse Teams activity"""
        try:
            if activity.get("type") != "message":
                return None

            text = activity.get("text", "")
            if not text:
                return None

            # Get conversation ID
            conversation = activity.get("conversation", {})
            conversation_id = conversation.get("id")

            # Get from user
            from_user = activity.get("from", {})
            user_id = from_user.get("id")

            return {
                "conversation_id": conversation_id,
                "user_id": user_id,
                "message": text.strip()
            }

        except Exception as e:
            logger.error(f"Parse Teams activity error: {e}")
            return None

    def format_response_for_teams(
        self,
        response: str,
        sources: List[Dict[str, Any]]
    ) -> str:
        """Format response for Teams (supports markdown)"""
        formatted = response

        if sources:
            formatted += "\n\n**📚 参考来源:**\n"
            for i, source in enumerate(sources[:5], 1):
                formatted += f"- [{i}] {source.get('document_name', '文档')}\n"

        return formatted


# Singleton instance
_teams_client: Optional[TeamsClient] = None


def get_teams_client() -> TeamsClient:
    """Get Teams client instance"""
    global _teams_client
    if _teams_client is None:
        _teams_client = TeamsClient()
    return _teams_client


async def handle_teams_activity(activity: dict) -> Optional[str]:
    """Handle incoming Teams activity"""
    client = get_teams_client()
    parsed = client.parse_activity(activity)

    if not parsed:
        return None

    conversation_id = parsed["conversation_id"]
    user_message = parsed["message"]

    logger.info(f"Teams message from {parsed.get('user_id')}: {user_message}")

    # Process through RAG pipeline
    from app.services.response_service import process_query
    from app.utils.database import async_session_maker

    async with async_session_maker() as db:
        result = await process_query(
            query=user_message,
            db=db,
            frontend="teams"
        )

    # Try to send as Adaptive Card first
    try:
        card_result = await client.send_adaptive_card(
            conversation_id=conversation_id,
            title="IntelliKnow 回答",
            content=result["response"],
            sources=result.get("sources", [])
        )

        if card_result.get("success"):
            return None  # Already sent as card
    except Exception as e:
        logger.warning(f"Adaptive Card failed, using text: {e}")

    # Fallback to text message
    response_text = client.format_response_for_teams(
        result["response"],
        result.get("sources", [])
    )

    await client.send_message(conversation_id, response_text)

    return response_text