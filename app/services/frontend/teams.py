"""
Microsoft Teams Bot Integration

Based on Microsoft Bot Framework and Azure AD OAuth 2.0
Handles incoming messages via webhook and sends RAG responses

Features (SRS):
- FR-005: Receive user queries and return RAG responses
- FR-006: Configure Teams Bot credentials (App ID, App Password, Tenant ID)
- FR-007: Display connection status and test functionality
- FR-008: Adaptive Card format for rich responses
"""

import logging
import json
import time
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import httpx

from config import settings

logger = logging.getLogger(__name__)


@dataclass
class OAuthToken:
    """OAuth access token with expiration tracking"""

    access_token: str
    expires_at: float  # Unix timestamp


class TeamsClient:
    """Microsoft Teams Bot client with OAuth token management"""

    def __init__(self):
        self.app_id = settings.TEAMS_APP_ID
        self.app_password = settings.TEAMS_APP_PASSWORD
        self.tenant_id = settings.TEAMS_TENANT_ID
        self.bot_id = settings.TEAMS_BOT_ID or self.app_id
        self._token: Optional[OAuthToken] = None

        # Microsoft OAuth endpoints
        self.authority = (
            f"https://login.microsoftonline.com/{self.tenant_id}"
            if self.tenant_id
            else "https://login.microsoftonline.com/common"
        )
        self.service_url = "https://smba.trafficmanager.net/teams/v3.0"
        self.webchat_url = "https://webchat.botframework.com"

    async def _acquire_token(self) -> Optional[str]:
        """Acquire OAuth access token using client credentials flow"""
        # Check if we have a valid cached token
        if self._token and time.time() < self._token.expires_at - 60:
            return self._token.access_token

        if not self.app_id or not self.app_password:
            logger.warning("Teams credentials not configured")
            return None

        try:
            # OAuth 2.0 client credentials flow
            token_url = f"{self.authority}/oauth2/v2.0/token"

            async with httpx.AsyncClient(trust_env=False, timeout=30.0) as client:
                response = await client.post(
                    token_url,
                    data={
                        "grant_type": "client_credentials",
                        "client_id": self.app_id,
                        "client_secret": self.app_password,
                        "scope": "https://api.botframework.com/.default",
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )

                if response.status_code == 200:
                    data = response.json()
                    self._token = OAuthToken(
                        access_token=data["access_token"],
                        expires_at=time.time() + data.get("expires_in", 3600),
                    )
                    logger.info("Teams OAuth token acquired successfully")
                    return self._token.access_token
                else:
                    logger.error(
                        f"Failed to acquire Teams token: {response.status_code} - {response.text}"
                    )
                    return None

        except Exception as e:
            logger.error(f"Teams token acquisition error: {e}")
            return None

    def _get_send_url(
        self, conversation_id: str, service_url: Optional[str] = None
    ) -> str:
        """Get the correct send URL based on service URL type"""
        if service_url and "webchat.botframework.com" in service_url:
            return f"{self.webchat_url}/v3/conversations/{conversation_id}/activities"
        return f"{service_url or self.service_url}/conversations/{conversation_id}/activities"

    async def send_message(
        self, conversation_id: str, message: str, service_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send plain text message to Teams conversation (FR-005/FR-008)"""
        if not self.app_id or not self.app_password:
            logger.warning("Teams credentials not configured")
            return {"success": False, "error": "Teams not configured"}

        token = await self._acquire_token()
        if not token:
            return {"success": False, "error": "Failed to acquire access token"}

        url = self._get_send_url(conversation_id, service_url)
        logger.info(f"Sending Teams message to: {url}")

        # Teams uses markdown in text format
        payload = {
            "type": "message",
            "text": message,
            "from": {"id": self.bot_id, "name": "IntelliKnow Bot"},
            "recipient": {"id": "user"},
        }

        try:
            async with httpx.AsyncClient(trust_env=False, timeout=30.0) as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                    },
                )

                if response.status_code in (200, 201):
                    logger.info(f"Teams message sent to {conversation_id}")
                    return {"success": True, "data": response.json()}
                else:
                    logger.error(
                        f"Teams API error: {response.status_code} - {response.text}"
                    )
                    return {
                        "success": False,
                        "error": f"{response.status_code}: {response.text}",
                    }

        except httpx.TimeoutException:
            logger.error(f"Teams send timeout for {conversation_id}")
            return {"success": False, "error": "Request timeout"}
        except httpx.ConnectError as e:
            logger.error(f"Teams connection error: {e}")
            return {"success": False, "error": f"Connection error: {e}"}
        except Exception as e:
            logger.error(f"Teams send error: {type(e).__name__}: {e}")
            import traceback

            logger.error(f"Traceback: {traceback.format_exc()}")
            return {"success": False, "error": f"{type(e).__name__}: {e}"}

    async def send_adaptive_card(
        self,
        conversation_id: str,
        title: str,
        content: str,
        sources: List[Dict[str, Any]],
        intent: Optional[str] = None,
        confidence: Optional[float] = None,
        service_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Send Adaptive Card to Teams (FR-008 - rich format)"""
        if not self.app_id or not self.app_password:
            return {"success": False, "error": "Teams not configured"}

        token = await self._acquire_token()
        if not token:
            return {"success": False, "error": "Failed to acquire access token"}

        # Truncate content if too long (Adaptive Card limit)
        max_content_len = 8000
        if len(content) > max_content_len:
            content = content[:max_content_len] + "\n\n[内容过长已截断...]"

        # Build enhanced Adaptive Card
        card = {
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "type": "AdaptiveCard",
            "version": "1.4",
            "body": [
                {
                    "type": "Container",
                    "items": [
                        {
                            "type": "TextBlock",
                            "text": "🧠 IntelliKnow 智能问答",
                            "weight": "bolder",
                            "size": "medium",
                            "color": "Accent",
                        },
                        {
                            "type": "TextBlock",
                            "text": title,
                            "wrap": True,
                            "spacing": "Small",
                        },
                    ],
                },
                {
                    "type": "TextBlock",
                    "text": content,
                    "wrap": True,
                    "spacing": "Medium",
                },
            ],
            "actions": [],
        }

        # Add classification info if available
        if intent:
            card["body"].insert(
                1,
                {
                    "type": "FactSet",
                    "facts": [{"title": "📌 意图", "value": intent}]
                    + (
                        [{"title": "🎯 置信度", "value": f"{confidence:.0%}"}]
                        if confidence
                        else []
                    ),
                },
            )

        # Add sources section
        if sources:
            facts = [
                {"title": f"[{i + 1}]", "value": s.get("document_name", "文档")}
                for i, s in enumerate(sources[:5])
            ]
            card["body"].append(
                {
                    "type": "TextBlock",
                    "text": "📚 参考来源",
                    "weight": "bolder",
                    "spacing": "Medium",
                }
            )
            card["body"].append({"type": "FactSet", "facts": facts})

        # Add action buttons
        card["actions"].extend(
            [
                {
                    "type": "Action.Submit",
                    "title": "👍 有用",
                    "data": {"feedback": "helpful"},
                },
                {
                    "type": "Action.Submit",
                    "title": "👎 不准确",
                    "data": {"feedback": "unhelpful"},
                },
            ]
        )

        url = self._get_send_url(conversation_id, service_url)
        logger.info(f"Sending Adaptive Card to: {url}")

        payload = {
            "type": "message",
            "attachments": [
                {
                    "contentType": "application/vnd.microsoft.card.adaptive",
                    "content": card,
                }
            ],
            "from": {"id": self.bot_id, "name": "IntelliKnow Bot"},
        }

        try:
            async with httpx.AsyncClient(trust_env=False, timeout=30.0) as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                    },
                )

                if response.status_code in (200, 201):
                    logger.info(f"Adaptive Card sent to {conversation_id}")
                    return {"success": True}
                else:
                    logger.error(
                        f"Adaptive Card error: {response.status_code} - {response.text}"
                    )
                    return {"success": False, "error": response.text}

        except Exception as e:
            logger.error(f"Teams Adaptive Card error: {e}")
            return {"success": False, "error": str(e)}

    def parse_activity(self, activity: dict) -> Optional[Dict[str, Any]]:
        """Parse Teams activity into standardized format (FR-005)"""
        try:
            activity_type = activity.get("type")

            # Handle different message types
            if activity_type == "message":
                # Get text content (may be in text field or content field)
                text = activity.get("text", "")

                # Handle markdown format messages
                if not text and activity.get("channelData", {}).get("markdown"):
                    text = activity.get("channelData", {}).get("markdown", "")

                # Handle formatted content
                if not text and activity.get("attachments"):
                    for att in activity.get("attachments", []):
                        if (
                            att.get("contentType")
                            == "application/vnd.microsoft.card.adaptive"
                        ):
                            content = att.get("content", {})
                            for elem in content.get("body", []):
                                if elem.get("type") == "TextBlock":
                                    text = elem.get("text", "")
                                    break

                if not text:
                    # Try to extract from textFormat field
                    text = activity.get("textFormat", "")

                if not text or not text.strip():
                    logger.info(
                        f"Ignoring empty message, type: {activity.get('channelData', {}).get('clientActivityId', 'unknown')}"
                    )
                    return None

                # Get conversation ID
                conversation = activity.get("conversation", {})
                conversation_id = conversation.get("id")

                # Get sender info
                from_user = activity.get("from", {})
                user_id = from_user.get("id", "")
                user_name = from_user.get("name", "")

                # Get channel ID for service URL
                channel_data = activity.get("channelData", {})
                service_url = channel_data.get("serviceUrl", self.service_url)

                return {
                    "conversation_id": conversation_id,
                    "user_id": user_id,
                    "user_name": user_name,
                    "message": text.strip(),
                    "service_url": service_url,
                    "channel_id": channel_data.get("channel", {}).get("id")
                    if isinstance(channel_data.get("channel"), dict)
                    else None,
                }

            elif activity_type == "conversationUpdate":
                logger.info("Conversation update event received")
                return None

            elif activity_type == "typing":
                logger.debug("User is typing")
                return None

            else:
                logger.info(f"Ignoring activity type: {activity_type}")
                return None

        except Exception as e:
            logger.error(f"Parse Teams activity error: {e}")
            import traceback

            logger.error(f"Traceback: {traceback.format_exc()}")
            return None

    def format_response_for_teams(
        self, response: str, sources: List[Dict[str, Any]], intent: Optional[str] = None
    ) -> str:
        """Format response for Teams plain text (FR-008)"""
        formatted_parts = []

        # Add intent if available
        if intent:
            formatted_parts.append(f"📌 意图: {intent}")

        # Add main response
        formatted_parts.append(response)

        # Add sources
        if sources:
            formatted_parts.append("\n📚 参考来源:")
            for i, source in enumerate(sources[:5], 1):
                doc_name = source.get("document_name", "文档")
                formatted_parts.append(f"  [{i}] {doc_name}")

        return "\n".join(formatted_parts)

    def get_status(self) -> Dict[str, Any]:
        """Get Teams client status"""
        return {
            "configured": bool(self.app_id and self.app_password),
            "app_id": self.app_id[:10] + "..." if self.app_id else "",
            "tenant_id": self.tenant_id[:8] + "..." if self.tenant_id else "",
            "features": {"adaptive_cards": True, "markdown": True, "feedback": True},
        }


# Singleton instance
_teams_client: Optional[TeamsClient] = None


def get_teams_client() -> TeamsClient:
    """Get Teams client instance"""
    global _teams_client
    if _teams_client is None:
        _teams_client = TeamsClient()
    return _teams_client


async def handle_teams_activity(activity: dict) -> Optional[str]:
    """Handle incoming Teams activity (FR-005)"""
    client = get_teams_client()
    parsed = client.parse_activity(activity)

    if not parsed:
        return None

    conversation_id = parsed["conversation_id"]
    user_message = parsed["message"]
    user_id = parsed.get("user_id", "unknown")
    service_url = parsed.get("service_url")

    logger.info(
        f"Teams message from {user_id}: {user_message}, service_url={service_url}"
    )

    # 如果是首次连接或测试消息，返回 Conversation ID
    msg_lower = user_message.lower().strip()
    if (
        msg_lower in ["test", "测试", "/start", "hello", "hi"]
        or msg_lower.startswith("test")
        or msg_lower.startswith("测试")
    ):
        test_response = f"""✅ IntelliKnow Bot 已连接！

📋 Conversation ID: `{conversation_id}`

你可以用这个 ID 在管理后台发送测试消息。

请发送你的问题，我会从知识库中查找答案。"""
        logger.info(f"Sending test response to conversation {conversation_id}")
        result = await client.send_message(conversation_id, test_response, service_url)
        logger.info(f"Test response result: {result}")
        return None

    # Process through RAG pipeline
    try:
        from app.services.response_service import process_query
        from app.utils.database import async_session_maker

        logger.info("Starting RAG pipeline for Teams query")
        async with async_session_maker() as db:
            result = await process_query(query=user_message, db=db, frontend="teams")
        logger.info(f"RAG pipeline completed, status: {result.get('status')}")
    except Exception as e:
        logger.error(f"RAG pipeline error: {e}")
        import traceback

        logger.error(f"Traceback: {traceback.format_exc()}")
        result = {
            "response": "抱歉，处理您的请求时出现错误。",
            "sources": [],
            "intent": {},
            "status": "error",
        }

    response_text = result.get("response", "抱歉，我暂时无法处理您的请求。")
    sources = result.get("sources", [])
    intent_info = result.get("intent", {})
    intent_name = intent_info.get("intent") if isinstance(intent_info, dict) else None
    confidence = (
        intent_info.get("confidence") if isinstance(intent_info, dict) else None
    )

    # Try to send as Adaptive Card first (FR-008 - rich format)
    try:
        card_result = await client.send_adaptive_card(
            conversation_id=conversation_id,
            title=user_message,
            content=response_text,
            sources=sources,
            intent=intent_name or "",
            confidence=confidence or 0.0,
            service_url=service_url,
        )

        if card_result.get("success"):
            logger.info("Response sent as Adaptive Card")
            return None  # Already sent as card

    except Exception as e:
        logger.warning(f"Adaptive Card failed, using text: {e}")

    # Fallback to plain text message
    response_text = client.format_response_for_teams(
        response_text, sources, intent_name or ""
    )

    send_result = await client.send_message(conversation_id, response_text, service_url)

    if send_result.get("success"):
        logger.info("Response sent as text message")
    else:
        logger.error(f"Failed to send response: {send_result.get('error')}")

    return response_text
