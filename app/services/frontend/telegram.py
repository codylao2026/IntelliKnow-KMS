"""
Telegram Bot Integration - Polling Mode
"""

import asyncio
import logging
import time
import threading
import json
import requests
from urllib3.exceptions import InsecureRequestWarning
from typing import Optional, Dict, Any, List

import warnings

warnings.filterwarnings("ignore", category=InsecureRequestWarning)

from config import settings

logger = logging.getLogger(__name__)


class TelegramClient:
    """Telegram Bot Client - Polling Mode"""

    def __init__(self):
        self._token = None
        self._api_url = None
        self._running = False
        self._offset = 0
        self._thread: Optional[threading.Thread] = None
        self._client = None

        if not self.is_configured():
            logger.warning("Telegram credentials not configured")

    @property
    def token(self) -> str:
        """Get token from environment (reload each time)"""
        from app.utils.env_manager import load_env

        load_env()
        return settings.TELEGRAM_BOT_TOKEN

    @property
    def api_url(self) -> Optional[str]:
        """Get API URL"""
        token = self.token
        return f"https://api.telegram.org/bot{token}" if token else None

    def _get_proxy(self) -> Optional[Dict[str, str]]:
        """Get proxy settings"""
        proxy = settings.HTTPS_PROXY or settings.HTTP_PROXY
        if proxy:
            return {"http": proxy, "https": proxy}
        return None

    def is_configured(self) -> bool:
        return bool(self.token)

    def is_running(self) -> bool:
        return self._running

    def get_status(self) -> Dict[str, Any]:
        return {
            "is_configured": self.is_configured(),
            "configured": self.is_configured(),
            "running": self._running,
            "mode": "Polling",
        }

    def start(self) -> bool:
        if not self.is_configured():
            logger.warning("Telegram not configured, cannot start")
            return False

        if self._running:
            logger.info("Telegram polling already running")
            return True

        self._running = True
        self._thread = threading.Thread(target=self._polling_loop, daemon=True)
        self._thread.start()
        logger.info("Telegram polling started")
        return True

    def _test_connection(self) -> bool:
        """Test bot connection"""
        proxies = self._get_proxy()
        session = requests.Session()
        session.trust_env = False

        try:
            resp = session.get(
                f"{self.api_url}/getMe", proxies=proxies, verify=False, timeout=10
            )
            data = resp.json()
            if data.get("ok"):
                bot_info = data.get("result", {})
                logger.info(f"Telegram bot verified: @{bot_info.get('username')}")
                return True
            logger.error(f"Telegram getMe failed: {data}")
        except Exception as e:
            logger.error(f"Telegram connection test error: {e}")
        return False

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("Telegram polling stopped")

    def _get_updates(self) -> List[Dict]:
        if not self.api_url:
            return []

        proxies = self._get_proxy()
        session = requests.Session()
        session.trust_env = False

        for attempt in range(3):
            try:
                resp = session.get(
                    f"{self.api_url}/getUpdates",
                    params={"offset": self._offset, "timeout": 30},
                    timeout=35,
                    proxies=proxies,
                    verify=False,
                )
                data = resp.json()
                if data.get("ok"):
                    updates = data.get("result", [])
                    if updates:
                        self._offset = updates[-1].get("update_id", 0) + 1
                    return updates
                elif data.get("error_code") == 409:
                    logger.warning(
                        f"Telegram conflict detected: {data.get('description')}"
                    )
                    return []
            except Exception as e:
                logger.error(f"Get updates attempt {attempt + 1} error: {e}")
                if attempt < 2:
                    time.sleep(2)

        return []

    def _polling_loop(self):
        while self._running:
            try:
                updates = self._get_updates()
                for update in updates:
                    self._handle_update(update)
            except Exception as e:
                logger.error(f"Polling error: {e}")
                time.sleep(5)

    def _handle_update(self, update: Dict):
        message = update.get("message", {})
        if not message:
            return

        text = message.get("text", "").strip()
        chat = message.get("chat", {})
        chat_id = chat.get("id")

        if not text or not chat_id:
            return

        if text.startswith("/"):
            self._send_message(chat_id, "发送问题给我，我会尝试从知识库中找到答案。")
            return

        logger.info(f"Telegram message from {chat_id}: {text}")

        result = self._process_rag_query(text)
        response_text = result.get("response", "抱歉，我暂时无法处理您的请求。")
        sources = result.get("sources", [])

        response = self._format_response(response_text, sources)
        self._send_message(chat_id, response)

    def _process_rag_query(self, query: str) -> Dict[str, Any]:
        try:
            from app.services.response_service import process_query
            from app.utils.database import async_session_maker

            async def run_query():
                async with async_session_maker() as db:
                    return await process_query(query=query, db=db, frontend="telegram")

            result = asyncio.run(run_query())
            return result

        except Exception as e:
            logger.error(f"RAG process error: {e}")
            return {"response": "处理请求失败，请稍后重试", "sources": []}

    def _format_response(self, response_text: str, sources: List[Dict]) -> str:
        lines = []

        for para in response_text.split("\n\n"):
            if para.strip():
                lines.append(f"_{para.strip()}_")

        if sources:
            lines.append("\n")
            lines.append("📚 *参考来源:*")
            for i, source in enumerate(sources[:3], 1):
                title = source.get("document_name", source.get("title", "文档"))
                lines.append(f"{i}. {title}")

        return "\n".join(lines)

    def _send_message(self, chat_id: int, text: str):
        if not self.api_url:
            return

        try:
            escape_chars = r"\_*[]()~`>#+-=|{}.!"
            for char in escape_chars:
                text = text.replace(char, f"\\{char}")

            proxies = self._get_proxy()
            session = requests.Session()
            session.trust_env = False

            for attempt in range(3):
                try:
                    resp = session.post(
                        f"{self.api_url}/sendMessage",
                        json={
                            "chat_id": chat_id,
                            "text": text,
                            "parse_mode": "MarkdownV2",
                        },
                        timeout=10,
                        proxies=proxies,
                        verify=False,
                    )
                    if resp.status_code == 200:
                        return
                    logger.warning(
                        f"Send message attempt {attempt + 1} failed: {resp.status_code}"
                    )
                except Exception as e:
                    logger.error(f"Send message attempt {attempt + 1} error: {e}")
                if attempt < 2:
                    time.sleep(1)
        except Exception as e:
            logger.error(f"Send message error: {e}")

    def test_connection(self, chat_id: Optional[int] = None) -> bool:
        target_chat_id = chat_id or int(settings.TELEGRAM_TEST_CHAT_ID)
        self._send_message(
            target_chat_id, "🔔 *测试消息*\\n\\nIntelliKnow Bot 连接成功！"
        )
        return True


_telegram_client: Optional[TelegramClient] = None


def get_telegram_client() -> TelegramClient:
    global _telegram_client
    if _telegram_client is None:
        _telegram_client = TelegramClient()
    return _telegram_client


async def get_telegram_status() -> Dict[str, Any]:
    global _telegram_client
    if _telegram_client is None:
        return {
            "error": "Telegram client not initialized",
            "configured": False,
            "running": False,
        }
    return _telegram_client.get_status()


def init_telegram_client() -> bool:
    client = get_telegram_client()
    return client.start()
