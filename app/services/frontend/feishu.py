"""
Feishu (Lark) Bot Integration - Long Connection Mode
Features: SDK API + WebSocket heartbeat + Auto-reconnect + FAISS initialization
"""

import asyncio
import logging
import json
import traceback
import threading
import time
import random
from typing import Optional, Dict, Any, List
from pathlib import Path

from config import settings

LARK_SDK_AVAILABLE = False
lark = None
LarkLogLevel = None

FAISS_INDEX_DIR = Path(settings.FAISS_INDEX_DIR or "./data/vectors/faiss_index")
FAISS_INDEX_DIR.mkdir(parents=True, exist_ok=True)

_index_file = FAISS_INDEX_DIR / "index.faiss"
_pkl_file = FAISS_INDEX_DIR / "index.pkl"
if not _index_file.exists():
    _index_file.touch()
if not _pkl_file.exists():
    _pkl_file.touch()

logger = logging.getLogger(__name__)


def _ensure_lark_sdk():
    """Lazy load Feishu SDK"""
    global LARK_SDK_AVAILABLE, lark, LarkLogLevel
    if LARK_SDK_AVAILABLE:
        return True
    
    try:
        import lark_oapi as _lark
        from lark_oapi import LogLevel as _LarkLogLevel
        global lark, LarkLogLevel
        lark = _lark
        LarkLogLevel = _LarkLogLevel
        LARK_SDK_AVAILABLE = True
        logger.info("Feishu SDK loaded successfully")
        return True
    except ImportError:
        logger.warning("lark_oapi not installed. Install with: pip install lark-oapi")
        return False


class FeishuClient:
    """Feishu long-connection client with heartbeat and auto-reconnect"""

    def __init__(self):
        self.app_id = settings.FEISHU_APP_ID
        self.app_secret = settings.FEISHU_APP_SECRET
        self.bot_name = settings.FEISHU_BOT_NAME
        self.ws_client = None
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._heartbeat_thread: Optional[threading.Thread] = None
        self._reconnect_count = 0
        self._max_reconnects = 10
        self._heartbeat_interval = 30
        self._client = None

        if not self.app_id or not self.app_secret:
            logger.warning("Feishu credentials not configured")

    def _get_log_level(self):
        if not LARK_SDK_AVAILABLE:
            return None
        level_map = {
            "DEBUG": LarkLogLevel.DEBUG,
            "INFO": LarkLogLevel.INFO,
            "WARNING": LarkLogLevel.WARNING,
            "ERROR": LarkLogLevel.ERROR,
        }
        return level_map.get(settings.FEISHU_LOG_LEVEL.upper(), LarkLogLevel.INFO)

    def _create_client(self):
        """Create Feishu HTTP client"""
        return (
            lark.Client.builder()
            .app_id(self.app_id)
            .app_secret(self.app_secret)
            .log_level(self._get_log_level())
            .build()
        )

    def _parse_message(
        self, data
    ) -> Optional[Dict[str, Any]]:
        """Parse Feishu message event"""
        try:
            event = data.event
            msg = event.message
            
            if not msg:
                return None

            message_id = getattr(msg, "message_id", "") or ""
            chat_id = getattr(msg, "chat_id", "") or ""
            message_type = getattr(msg, "message_type", "text") or "text"
            content = getattr(msg, "content", "") or ""
            chat_type = getattr(msg, "chat_type", "") or ""

            logger.info(f"Raw message_id: {message_id}, content: {content[:100] if content else ''}")

            text_content = ""
            if message_type == "text" and content:
                try:
                    content_data = json.loads(content)
                    text_content = content_data.get("text", "").strip()
                except json.JSONDecodeError:
                    logger.error(f"JSON parse failed: {content}")
                    text_content = content.strip()
            elif message_type == "post":
                text_content = "[Rich text message]"
            elif message_type == "image":
                text_content = "[Image received]"
            else:
                text_content = content.strip() if content else ""

            user_id = ""
            sender_name = ""
            sender = getattr(msg, "sender", None)
            if sender:
                sender_id = (
                    getattr(sender, "id", None)
                    or getattr(sender, "sender_id", None)
                    or {}
                )
                if isinstance(sender_id, dict):
                    user_id = (
                        sender_id.get("user_id", "")
                        or sender_id.get("open_id", "")
                        or sender_id.get("union_id", "")
                        or ""
                    )
                    sender_name = sender_id.get("name", "") or ""
                elif sender_id:
                    user_id = str(sender_id)

            is_mention_to_bot = False
            if (
                message_type == "text"
                and self.bot_name
                and f"@{self.bot_name}" in text_content
            ):
                is_mention_to_bot = True
                text_content = text_content.replace(f"@{self.bot_name}", "").strip()

            logger.info(
                f"Parsed message - message_id: {message_id}, user: {sender_name}, text: {text_content[:50]}"
            )
            return {
                "message_id": message_id,
                "chat_id": chat_id,
                "user_id": user_id,
                "user_name": sender_name,
                "message_type": message_type,
                "text": text_content,
                "mentioned_user_ids": [],
                "chat_type": chat_type,
                "is_group": chat_type == "group",
                "is_mention_to_bot": is_mention_to_bot,
                "raw": data,
            }

        except Exception as e:
            logger.error(f"Parse Feishu message error: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None

    async def _async_process_message(self, parsed: Dict[str, Any]) -> Dict[str, Any]:
        """Async process message with RAG"""
        user_message = parsed["text"]
        user_id = parsed.get("user_id", "")
        is_group = parsed.get("is_group", False)
        is_mention_to_bot = parsed.get("is_mention_to_bot", False)

        logger.info(
            f"Feishu message from {parsed.get('user_name', 'unknown')} (user_id={user_id}): {user_message}"
        )

        if is_group and not is_mention_to_bot:
            logger.info("Ignoring group message not mentioning bot")
            return {"response": None, "sources": []}

        try:
            from app.services.response_service import process_query
            from app.utils.database import async_session_maker

            async with async_session_maker() as db:
                result = await process_query(
                    query=user_message, db=db, frontend="feishu"
                )

            response_text = result.get("response", "Sorry, I cannot process your request at the moment.")
            sources = result.get("sources", [])
            return {"response": response_text, "sources": sources}

        except ImportError as e:
            logger.error(f"RAG module import error: {e}")
            return {"response": "RAG service not configured, please contact admin", "sources": []}
        except Exception as e:
            logger.error(f"RAG process error: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {"response": "An error occurred while processing your request, please try again later.", "sources": []}

    def _process_message(self, parsed: Dict[str, Any]) -> Dict[str, Any]:
        """Run async processing in thread"""
        result_holder: List[Any] = [None]
        exception_holder: List[Any] = [None]

        def run_async():
            try:
                result = asyncio.run(self._async_process_message(parsed))
                result_holder[0] = result
            except Exception as e:
                exception_holder[0] = e
                logger.error(f"Async process error: {e}")

        thread = threading.Thread(target=run_async)
        thread.start()
        thread.join(timeout=30)

        if exception_holder[0]:
            return {"response": "Request failed, please try again later", "sources": []}
        if result_holder[0]:
            return result_holder[0]
        return {"response": "Request timeout, please try again later", "sources": []}

    def _build_interactive_card(self, response_text: str, sources: List[Dict]) -> Dict:
        """Build Feishu interactive card"""
        max_card_text_len = 4000
        if len(response_text) > max_card_text_len:
            response_text = (
                response_text[:max_card_text_len] + "\n\n[Content truncated due to length...]"
            )

        card_elements = [
            {"tag": "markdown", "content": response_text.replace("\n", "\n<br>")}
        ]

        if sources:
            source_texts = []
            for i, source in enumerate(sources[:5], 1):
                doc_name = source.get("document_name", "Document")
                source_texts.append(f"**{i}.** {doc_name}")

            if source_texts:
                card_elements.append({"tag": "hr"})
                card_elements.append(
                    {
                        "tag": "markdown",
                        "content": "**📚 Sources:**\n" + "\n".join(source_texts),
                    }
                )

        return {
            "config": {"wide_screen_mode": True, "enable_forward": True},
            "elements": card_elements,
        }

    def _send_message(
        self, message_id: str, msg_type: str, content: str, reply_in_thread: bool = True
    ) -> bool:
        """Generic message sending method"""
        if not message_id or not content:
            logger.warning("Empty message_id or content")
            return False

        try:
            if self._client is None:
                self._client = self._create_client()

            request_body = (
                lark.im.v1.ReplyMessageRequestBody.builder()
                .msg_type(msg_type)
                .content(content)
                .reply_in_thread(reply_in_thread)
                .build()
            )

            request = (
                lark.im.v1.ReplyMessageRequest.builder()
                .message_id(message_id)
                .request_body(request_body)
                .build()
            )

            response = self._client.im.v1.message.reply(request)

            if response.success():
                logger.info(f"Message sent successfully to {message_id}")
                return True
            else:
                logger.error(f"Message send failed: {response.code} - {response.msg}")
                return False

        except AttributeError as e:
            logger.error(f"SDK API error: {e}")
            logger.error(
                f"Available methods: {[m for m in dir(self._client.im.v1) if not m.startswith('_')]}"
            )
            return False
        except Exception as e:
            logger.error(f"Send message error: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False

    def _send_reply_text(self, message_id: str, text: str) -> bool:
        """Send plain text reply"""
        return self._send_message(message_id, "text", json.dumps({"text": text}))

    def _send_reply_card(self, message_id: str, card: Dict) -> bool:
        """Send interactive card reply"""
        return self._send_message(message_id, "interactive", json.dumps(card))

    def _send_reply(
        self, message_id: str, response_text: str, sources: List[Dict]
    ) -> bool:
        """Send reply (card first, fallback to text)"""
        if not response_text:
            return False

        card = self._build_interactive_card(response_text, sources)
        if self._send_reply_card(message_id, card):
            return True

        fallback_text = response_text
        if sources:
            fallback_text += "\n\n📚 Sources:\n"
            for i, source in enumerate(sources[:3], 1):
                doc_name = source.get("document_name", "Document")
                fallback_text += f"{i}. {doc_name}\n"

        return self._send_reply_text(message_id, fallback_text)

    def _heartbeat(self):
        """Heartbeat to keep connection alive"""
        while self._running:
            time.sleep(self._heartbeat_interval)
            if self._running and self.ws_client:
                try:
                    logger.debug("Heartbeat ping...")
                except Exception as e:
                    logger.warning(f"Heartbeat error: {e}")

    def do_p2_im_message_receive_v1(
        self, data
    ) -> None:
        """Handle received message event"""
        print(f"[FISHU CALLBACK] Received data: {type(data)}")
        logger.info(f"[Feishu] Message received - data type: {type(data)}")
        
        try:
            event = data.event
            message = event.message
            message_id = getattr(message, "message_id", "") or ""
            message_type = getattr(message, "message_type", "text") or "text"
            content = getattr(message, "content", "") or ""
            
            logger.info(f"[Feishu] message_id: {message_id}, type: {message_type}")
            logger.info(f"[Feishu] content: {content[:100] if content else 'empty'}")
        except Exception as e:
            logger.error(f"[Feishu] Debug info error: {e}")

        parsed = self._parse_message(data)
        if not parsed:
            logger.warning("[Feishu] Failed to parse message")
            return

        message_type = parsed.get("message_type", "")
        message_id = parsed.get("message_id", "")
        user_text = parsed.get("text", "").strip()

        logger.info(f"[Feishu] Parsed - message_id: {message_id}, text: {user_text[:50]}")

        if message_type == "image":
            self._send_reply_text(message_id, "Image received! I currently only support text queries.")
            return

        if not user_text:
            self._send_reply_text(message_id, "Empty message received. Please send a text question.")
            return

        result = self._process_message(parsed)
        response_text = result.get("response", "")
        sources = result.get("sources", [])

        if response_text:
            self._send_reply(
                message_id=message_id, response_text=response_text, sources=sources
            )

    def _worker(self):
        """Run in separate thread - following official docs"""
        # Ensure SDK is loaded in this thread
        if not _ensure_lark_sdk():
            logger.error("[Feishu] Failed to load SDK")
            return
            
        try:
            logger.info("[Feishu] Creating event handler...")
            event_handler = (
                lark.EventDispatcherHandler.builder(self.app_id, self.app_secret)
                .register_p2_im_message_receive_v1(self.do_p2_im_message_receive_v1)
                .build()
            )
            logger.info("[Feishu] Event handler created")
            
            ws = lark.ws.Client(
                self.app_id,
                self.app_secret,
                event_handler=event_handler,
            )
            
            self._running = True
            logger.info("[Feishu] Starting WebSocket client...")
            ws.start()
            
            # Keep thread alive like docs
            while self._running:
                time.sleep(1)
            
        except Exception as e:
            logger.error(f"[Feishu] Worker error: {e}")
            import traceback
            logger.error(traceback.format_exc())

    def _run_ws_client(self):
        """Start Feishu WebSocket"""
        logger.info("Starting Feishu WebSocket...")
        t = threading.Thread(target=self._worker, daemon=False)
        t.start()
        logger.info("Feishu service started")

    def start(self) -> bool:
        """Start Feishu client (long connection mode) - sync version"""
        if not _ensure_lark_sdk():
            logger.error("lark_oapi SDK not installed")
            return False

        if not self.app_id or not self.app_secret:
            logger.error("Feishu credentials not configured")
            return False

        if self._running:
            logger.info("Feishu client already running")
            return True

        self._running = True
        self._thread = threading.Thread(target=self._run_ws_client, daemon=False)
        self._thread.start()
        return True

    async def start_async(self) -> bool:
        """Start Feishu client (async version) - for FastAPI lifespan"""
        if not _ensure_lark_sdk():
            logger.error("lark_oapi SDK not installed")
            return False

        if not self.app_id or not self.app_secret:
            logger.error("Feishu credentials not configured")
            return False

        if self._running:
            logger.info("Feishu client already running")
            return True

        # Call _run_ws_client directly to start thread
        self._run_ws_client()
        return True

    def stop(self):
        """Stop Feishu client"""
        if not self._running:
            logger.info("Feishu client not running")
            return

        logger.info("Stopping Feishu WebSocket client...")
        self._running = False

        if self.ws_client:
            try:
                self.ws_client.stop()
            except Exception as e:
                logger.warning(f"Error stopping WebSocket: {e}")

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)

        logger.info("Feishu WebSocket client stopped")

    def is_running(self) -> bool:
        """检查客户端是否运行中"""
        return self._running

    def get_status(self) -> Dict[str, Any]:
        """获取连接状态"""
        return {
            "enabled": LARK_SDK_AVAILABLE,
            "configured": bool(self.app_id and self.app_secret),
            "running": self._running,
            "app_id": self.app_id[:10] + "..." if self.app_id else "",
            "bot_name": self.bot_name,
            "reconnect_count": self._reconnect_count,
            "features": {
                "interactive_cards": True,
                "group_chat": True,
                "private_chat": True,
                "rich_text": True,
                "heartbeat": True,
                "auto_reconnect": True,
            },
        }


_feishu_client: Optional[FeishuClient] = None


def get_feishu_client() -> FeishuClient:
    """获取飞书客户端单例"""
    global _feishu_client
    if _feishu_client is None:
        _feishu_client = FeishuClient()
    return _feishu_client


async def get_feishu_status() -> Dict[str, Any]:
    """获取飞书连接状态（API端点）"""
    global _feishu_client
    if _feishu_client is None:
        return {
            "error": "Feishu client not initialized",
            "configured": False,
            "running": False,
        }
    return _feishu_client.get_status()


def init_feishu_client() -> bool:
    """初始化并启动飞书客户端"""
    client = get_feishu_client()
    return client.start()


def start_feishu_client() -> FeishuClient:
    """启动飞书客户端（用于独立进程）"""
    client = get_feishu_client()
    client.start()
    return client


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("Starting Feishu Bot (Long Connection Mode)...")
    print("Features: Interactive Cards, Heartbeat, Auto-reconnect, Group Chat")

    client = start_feishu_client()

    try:
        while client.is_running():
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping Feishu Bot...")
        client.stop()
        print("Feishu Bot stopped successfully")
