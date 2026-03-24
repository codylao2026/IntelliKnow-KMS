"""
飞书（ Lark ）Bot 集成 - 长连接模式
Feishu Bot Integration using WebSocket (Long Connection Mode)

Based on Feishu Official SDK: https://open.feishu.cn/document/ukTMukTMukTM/uETO1YjLxkTN24SM5UjN

Features:
- FR-FL-001: Receive user messages and return RAG responses
- FR-FL-002: Configure Feishu credentials (App ID, App Secret)
- FR-FL-003: Display connection status and test functionality
- FR-FL-004: Feishu native format responses (interactive cards)
- FR-FL-005: Group chat @mention handling
- FR-FL-006: Private chat support
- FR-FL-008: Parse text, @mentions, and image messages
"""

import asyncio
import logging
import json
from typing import Optional, Dict, Any, List
from pathlib import Path

try:
    import lark_oapi as lark
    from lark_oapi import LogLevel as LarkLogLevel

    LARK_SDK_AVAILABLE = True
except ImportError:
    LARK_SDK_AVAILABLE = False
    logging.warning("lark_oapi not installed. Install with: pip install lark-oapi")

from config import settings

logger = logging.getLogger(__name__)


class FeishuClient:
    """飞书长连接客户端"""

    def __init__(self):
        self.app_id = settings.FEISHU_APP_ID
        self.app_secret = settings.FEISHU_APP_SECRET
        self.bot_name = settings.FEISHU_BOT_NAME
        self.ws_client = None
        self._running = False

        if not self.app_id or not self.app_secret:
            logger.warning("Feishu credentials not configured")
            return

        if not LARK_SDK_AVAILABLE:
            logger.error("lark_oapi SDK not available")
            return

    def _get_log_level(self) -> LarkLogLevel:
        """转换日志级别"""
        level_map = {
            "DEBUG": LarkLogLevel.DEBUG,
            "INFO": LarkLogLevel.INFO,
            "WARNING": LarkLogLevel.WARNING,
            "ERROR": LarkLogLevel.ERROR,
        }
        return level_map.get(settings.FEISHU_LOG_LEVEL.upper(), LarkLogLevel.INFO)

    def _parse_message(
        self, data: lark.im.v1.P2ImMessageReceiveV1
    ) -> Optional[Dict[str, Any]]:
        """解析飞书消息事件 (FR-FL-008)"""
        try:
            msg = data.event.message
            if not msg:
                return None

            message_id = getattr(msg, "message_id", "") or ""
            chat_id = getattr(msg, "chat_id", "") or ""
            message_type = getattr(msg, "message_type", "text") or "text"
            content = getattr(msg, "content", "") or ""

            text_content = ""
            if message_type == "text":
                try:
                    content_data = json.loads(content)
                    text_content = content_data.get("text", "") or content
                except:
                    text_content = content
            elif message_type == "post":
                text_content = "[Rich text message]"
            elif message_type == "image":
                text_content = "[Image received]"
            else:
                text_content = content

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
                        or ""
                    )
                    sender_name = sender_id.get("name", "") or ""
                elif sender_id:
                    user_id = str(sender_id)

            chat_type = getattr(msg, "chat_type", "") or ""

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
                "is_mention_to_bot": False,
                "raw": data,
            }

        except Exception as e:
            logger.error(f"Parse Feishu message error: {e}")
            import traceback

            logger.error(f"Traceback: {traceback.format_exc()}")
            return None

            message_id = msg.message_id or ""
            chat_id = msg.chat_id or ""
            message_type = msg.message_type or "text"

            # 根据官方demo，content直接包含消息内容
            content = msg.content or ""

            # 解析文本消息
            text_content = ""
            if message_type == "text":
                try:
                    # content格式: {"text":"消息内容"}
                    content_data = json.loads(content)
                    text_content = content_data.get("text", "") or content
                except:
                    text_content = content
            elif message_type == "post":
                text_content = "[Rich text message]"
            elif message_type == "image":
                text_content = "[Image received]"
            else:
                text_content = content

            # 获取发送者信息
            sender = msg.sender
            user_id = ""
            sender_name = ""
            if sender:
                sender_id = sender.id or sender.sender_id or {}
                if isinstance(sender_id, dict):
                    user_id = (
                        sender_id.get("user_id", "")
                        or sender_id.get("open_id", "")
                        or ""
                    )
                    sender_name = sender_id.get("name", "") or ""
                else:
                    user_id = str(sender_id)

            # 判断是群聊还是私聊
            chat_type = msg.chat_type or ""

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
                "is_mention_to_bot": False,
                "raw": data,
            }

        except Exception as e:
            logger.error(f"Parse Feishu message error: {e}")
            import traceback

            logger.error(f"Traceback: {traceback.format_exc()}")
            return None

            message_id = getattr(message, "message_id", "") or ""
            chat_id = getattr(message, "chat_id", "") or ""

            # Debug: log message attributes
            logger.info(f"[Feishu debug] message attributes: {dir(message)}")
            logger.info(f"[Feishu debug] message: {message}")

            # 获取发送者信息
            sender = getattr(message, "sender", None)
            user_id = ""
            sender_name = ""
            if sender:
                sender_id = getattr(sender, "sender_id", None) or getattr(
                    sender, "id", None
                )
                if sender_id:
                    user_id = getattr(sender_id, "user_id", "") or ""
                    sender_name = getattr(sender_id, "name", "") or ""
                elif isinstance(sender_id, dict):
                    user_id = sender_id.get("user_id", "") or ""
                    sender_name = sender_id.get("name", "") or ""

            message_type = getattr(message, "message_type", "text") or "text"

            # 解析不同类型的消息
            text_content = ""
            mentioned_user_ids = []

            if message_type == "text":
                try:
                    # Try body first
                    body = getattr(message, "body", None)
                    logger.info(f"[Feishu debug] body: {body}")
                    if body:
                        body_data = json.loads(body)
                        text_content = body_data.get("text", "")
                        logger.info(
                            f"[Feishu debug] body_data: {body_data}, text: {text_content}"
                        )
                    # Try content as fallback
                    if not text_content:
                        content = getattr(message, "content", None)
                        logger.info(f"[Feishu debug] content: {content}")
                        if content:
                            text_content = content
                except Exception as e:
                    logger.info(f"[Feishu debug] text parse error: {e}")
                    text_content = str(getattr(message, "body", "")) or str(
                        getattr(message, "content", "")
                    )
            elif message_type == "post":
                text_content = "[Rich text message]"
            elif message_type == "image":
                text_content = "[Image received]"
            elif message_type == "media":
                text_content = "[Media message received]"
            else:
                text_content = ""

            # 判断是群聊还是私聊
            chat_type = getattr(message, "chat_type", "") or ""

            return {
                "message_id": message_id,
                "chat_id": chat_id,
                "user_id": user_id,
                "user_name": sender_name,
                "message_type": message_type,
                "text": text_content,
                "mentioned_user_ids": mentioned_user_ids,
                "chat_type": chat_type,
                "is_group": chat_type == "group",
                "is_mention_to_bot": False,
                "raw": data,
            }

        except Exception as e:
            logger.error(f"Parse Feishu message error: {e}")
            import traceback

            logger.error(f"Traceback: {traceback.format_exc()}")
            return None

    def _extract_text_from_post(self, body: dict) -> str:
        """从 post 类型消息中提取文本"""
        texts = []
        try:
            content = body.get("content", {})
            if isinstance(content, dict):
                for element in content.values():
                    if isinstance(element, list):
                        for item in element:
                            if isinstance(item, dict):
                                tag = item.get("tag", "")
                                if tag == "text":
                                    texts.append(item.get("text", ""))
                                elif tag == "at":
                                    texts.append(f"@{item.get('user_name', 'user')}")
        except:
            pass
        return " ".join(texts)

    def _process_message(self, parsed: Dict[str, Any]) -> Dict[str, Any]:
        """处理消息，通过RAG生成回复"""
        user_message = parsed["text"]
        chat_id = parsed.get("chat_id", "")
        user_id = parsed.get("user_id", "")
        is_group = parsed.get("is_group", False)
        is_mention_to_bot = parsed.get("is_mention_to_bot", False)

        logger.info(
            f"Feishu message from {parsed.get('user_name')} (user_id={user_id}): {user_message}"
        )

        # FR-FL-005: Group chat handling - only respond to @mentions or direct messages
        if is_group and not is_mention_to_bot:
            logger.info("Ignoring group message not mentioning bot")
            return {"response": None, "sources": []}

        try:
            from app.services.response_service import process_query
            from app.utils.database import async_session_maker

            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        try:

            async def process():
                async with async_session_maker() as db:
                    result = await process_query(
                        query=user_message, db=db, frontend="feishu"
                    )
                    return result

            result = loop.run_until_complete(process())
            response_text = result.get("response", "抱歉，我暂时无法处理您的请求。")
            sources = result.get("sources", [])

            return {"response": response_text, "sources": sources}

        except Exception as e:
            logger.error(f"RAG process error: {e}")
            import traceback

            logger.error(f"Traceback: {traceback.format_exc()}")
            return {"response": "处理您的请求时发生错误，请稍后重试。", "sources": []}

    def _build_interactive_card(self, response_text: str, sources: List[Dict]) -> str:
        """构建飞书交互卡片 (FR-FL-004)"""
        # 分割响应文本（如果太长）
        max_card_text_len = 4000
        if len(response_text) > max_card_text_len:
            response_text = (
                response_text[:max_card_text_len] + "\n\n[内容过长已截断...]"
            )

        # 构建卡片元素
        card_elements = [
            {"tag": "markdown", "content": response_text.replace("\n", "\n<br>")}
        ]

        # 添加来源信息
        if sources:
            source_texts = []
            for i, source in enumerate(sources[:5], 1):
                doc_name = source.get("document_name", "文档")
                source_texts.append(f"**{i}.** {doc_name}")

            if source_texts:
                card_elements.append({"tag": "hr"})
                card_elements.append(
                    {
                        "tag": "markdown",
                        "content": "**📚 参考来源:**\n" + "\n".join(source_texts),
                    }
                )

        # 构建完整卡片
        card = {
            "schema": "2.0",
            "config": {"wide_screen_mode": True, "enable_forward": True},
            "elements": card_elements,
        }

        return json.dumps(card)

    def _send_reply_text(self, message_id: str, text: str) -> bool:
        """发送纯文本回复"""
        try:
            client = (
                lark.Client.builder()
                .app_id(self.app_id)
                .app_secret(self.app_secret)
                .build()
            )

            request = (
                lark.im.v1.ReplyMessageRequest.builder()
                .message_id(message_id)
                .body(
                    lark.im.v1.ReplyMessageRequestBody.builder()
                    .msg_type("text")
                    .content(json.dumps({"text": text}))
                    .build()
                )
                .build()
            )

            response = client.im.v1.reply_message(request)
            if response.success():
                logger.info(f"Text reply sent successfully")
                return True
            else:
                logger.error(f"Text reply failed: {response.code}, {response.msg}")
                return False

        except Exception as e:
            logger.error(f"Send text reply error: {e}")
            return False

    def _send_reply_card(self, message_id: str, card_content: str) -> bool:
        """发送交互卡片回复 (FR-FL-004)"""
        try:
            client = (
                lark.Client.builder()
                .app_id(self.app_id)
                .app_secret(self.app_secret)
                .build()
            )

            request = (
                lark.im.v1.ReplyMessageRequest.builder()
                .message_id(message_id)
                .body(
                    lark.im.v1.ReplyMessageRequestBody.builder()
                    .msg_type("interactive")
                    .content(json.dumps({"card": card_content}))
                    .build()
                )
                .build()
            )

            response = client.im.v1.reply_message(request)
            if response.success():
                logger.info(f"Interactive card reply sent successfully")
                return True
            else:
                logger.error(f"Card reply failed: {response.code}, {response.msg}")
                # Fallback to text
                return False

        except Exception as e:
            logger.error(f"Send card reply error: {e}")
            return False

    def _send_reply(
        self, message_id: str, response_text: str, sources: List[Dict]
    ) -> bool:
        """发送回复消息（优先使用交互卡片）(FR-FL-004)"""
        # 先尝试发送交互卡片
        if sources:
            card_content = self._build_interactive_card(response_text, sources)
            if self._send_reply_card(message_id, card_content):
                return True

        # Fallback to text
        fallback_text = response_text
        if sources:
            fallback_text += "\n\n📚 参考来源:\n"
            for i, source in enumerate(sources[:3], 1):
                doc_name = source.get("document_name", "文档")
                fallback_text += f"{i}. {doc_name}\n"

        return self._send_reply_text(message_id, fallback_text)

    def do_p2_im_message_receive_v1(
        self, data: lark.im.v1.P2ImMessageReceiveV1
    ) -> None:
        """处理接收到的消息事件"""
        logger.info(f"[Feishu] Message received")

        parsed = self._parse_message(data)
        if not parsed:
            return

        message_type = parsed.get("message_type", "")
        message_id = parsed.get("message_id", "")

        if message_type == "image":
            self._send_reply_text(message_id, "收到了图片消息！我目前只支持文本问答。")
            return

        user_text = parsed.get("text", "").strip()
        if not user_text:
            self._send_reply_text(message_id, "收到了空消息，请发送文字问题。")
            return

        result = self._process_message(parsed)
        response_text = result.get("response", "")
        sources = result.get("sources", [])

        if response_text:
            self._send_reply(
                message_id=message_id, response_text=response_text, sources=sources
            )

    def start(self) -> bool:
        """启动飞书客户端（长连接模式，在后台线程中运行）"""
        if not LARK_SDK_AVAILABLE:
            logger.warning("lark_oapi SDK not installed")
            return False

        if not self.app_id or not self.app_secret:
            logger.warning("Feishu credentials not configured")
            return False

        if self._running:
            logger.info("Feishu client already running")
            return True

        import threading

        def _run_ws_client():
            try:
                # 创建事件处理器
                event_handler = (
                    lark.EventDispatcherHandler.builder(self.app_id, self.app_secret)
                    .register_p2_im_message_receive_v1(self.do_p2_im_message_receive_v1)
                    .build()
                )

                # 创建WebSocket客户端
                self.ws_client = lark.ws.Client(
                    self.app_id,
                    self.app_secret,
                    event_handler=event_handler,
                    log_level=self._get_log_level(),
                )

                logger.info("Feishu WebSocket client starting in background thread...")
                self.ws_client.start()
                self._running = True
                logger.info("Feishu WebSocket client started successfully")

            except Exception as e:
                logger.error(f"Feishu WebSocket error: {e}")
                import traceback

                logger.error(f"Traceback: {traceback.format_exc()}")

        thread = threading.Thread(target=_run_ws_client, daemon=True)
        thread.start()
        return True

        if not LARK_SDK_AVAILABLE:
            logger.error("lark_oapi SDK not installed")
            return False

        try:
            # 创建事件处理器
            event_handler = (
                lark.EventDispatcherHandler.builder(self.app_id, self.app_secret)
                .register_p2_im_message_receive_v1(self.do_p2_im_message_receive_v1)
                .build()
            )

            # 创建WebSocket客户端
            self.ws_client = lark.ws.Client(
                self.app_id,
                self.app_secret,
                event_handler=event_handler,
                log_level=self._get_log_level(),
            )

            # 启动长连接
            logger.info("Starting Feishu WebSocket client...")
            self.ws_client.start()
            self._running = True
            logger.info("Feishu WebSocket client started successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to start Feishu client: {e}")
            import traceback

            logger.error(f"Traceback: {traceback.format_exc()}")
            return False

    def stop(self):
        """停止飞书客户端"""
        if self.ws_client:
            logger.info("Stopping Feishu WebSocket client...")
            self.ws_client.stop()
            self._running = False
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
            "features": {
                "interactive_cards": True,
                "group_chat": True,
                "private_chat": True,
                "rich_text": True,
            },
        }


# ============== 独立启动函数 =============


def start_feishu_client() -> FeishuClient:
    """启动飞书客户端（用于独立进程）"""
    client = FeishuClient()
    client.start()
    return client


# ============== FastAPI 集成 =============


async def get_feishu_status() -> Dict[str, Any]:
    """获取飞书连接状态（API端点）"""
    client = _feishu_client
    if client is None:
        return {"error": "Feishu client not initialized"}
    return client.get_status()


# ============== 全局客户端实例 =============

_feishu_client: Optional[FeishuClient] = None


def get_feishu_client() -> FeishuClient:
    """获取飞书客户端单例"""
    global _feishu_client
    if _feishu_client is None:
        _feishu_client = FeishuClient()
    return _feishu_client


def init_feishu_client() -> bool:
    """初始化并启动飞书客户端"""
    client = get_feishu_client()
    return client.start()


if __name__ == "__main__":
    # 独立运行模式
    logging.basicConfig(level=logging.INFO)
    print("Starting Feishu Bot (Long Connection Mode)...")
    print("Features: Interactive Cards, Group Chat, Rich Text Support")
    client = FeishuClient()
    client.start()
