"""
飞书（ Lark ）Bot 集成 - 长连接模式
Feishu Bot Integration using WebSocket (Long Connection Mode)

基于飞书官方 SDK: https://open.feishu.cn/document/ukTMukTMukTM/uETO1YjLxkTN24SM5UjN
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

    def _parse_message(self, data: lark.im.v1.P2ImMessageReceiveV1) -> Optional[Dict[str, Any]]:
        """解析飞书消息事件"""
        try:
            message = data.event.message
            if not message:
                return None

            # 获取消息内容
            message_id = message.message_id
            chat_id = message.chat_id
            user_id = message.sender_id.get("user_id", "") if message.sender_id else ""
            message_type = message.message_type
            
            # 解析消息文本
            text_content = ""
            if message_type == "text" and message.body:
                try:
                    body = json.loads(message.body)
                    text_content = body.get("text", "")
                except:
                    text_content = message.body if hasattr(message.body, '__iter__') else str(message.body)

            # 获取发送者信息
            sender = message.sender
            sender_name = ""
            if sender and hasattr(sender, 'sender_id'):
                sender_name = sender.sender_id.get("name", "") if isinstance(sender.sender_id, dict) else ""

            return {
                "message_id": message_id,
                "chat_id": chat_id,
                "user_id": user_id,
                "user_name": sender_name,
                "message_type": message_type,
                "text": text_content,
                "raw": data
            }

        except Exception as e:
            logger.error(f"Parse Feishu message error: {e}")
            return None

    def _process_message(self, parsed: Dict[str, Any]) -> Optional[str]:
        """处理消息，通过RAG生成回复"""
        if not parsed or not parsed.get("text"):
            return None

        user_message = parsed["text"]
        chat_id = parsed.get("chat_id", "")
        user_id = parsed.get("user_id", "")

        logger.info(f"Feishu message from {parsed.get('user_name')}: {user_message}")

        try:
            # 导入RAG处理模块
            from app.services.response_service import process_query
            from app.utils.database import async_session_maker

            # 同步调用异步函数
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        try:
            # 在异步上下文中处理查询
            async def process():
                async with async_session_maker() as db:
                    result = await process_query(
                        query=user_message,
                        db=db,
                        frontend="feishu"
                    )
                    return result

            result = loop.run_until_complete(process())
            response_text = result.get("response", "抱歉，我暂时无法处理您的请求。")

            # 添加来源标注
            sources = result.get("sources", [])
            if sources:
                response_text += "\n\n📚 参考来源:\n"
                for i, source in enumerate(sources[:3], 1):
                    doc_name = source.get("document_name", "文档")
                    response_text += f"{i}. {doc_name}\n"

            return response_text

        except Exception as e:
            logger.error(f"RAG process error: {e}")
            return "处理您的请求时发生错误，请稍后重试。"

    def _send_reply(self, chat_id: str, message_id: str, text: str) -> bool:
        """发送回复消息"""
        try:
            # 使用 Reply API 回复消息
            client = lark.Client.builder() \
                .app_id(self.app_id) \
                .app_secret(self.app_secret) \
                .build()

            request = lark.im.v1.ReplyMessageRequest.builder() \
                .message_id(message_id) \
                .body(lark.im.v1.ReplyMessageRequestBody.builder()
                    .msg_type("text")
                    .content(json.dumps({"text": text}))
                    .build()) \
                .build()

            response = client.im.v1.reply_message(request)
            if response.success():
                logger.info(f"Reply sent to {chat_id}")
                return True
            else:
                logger.error(f"Reply failed: {response.code}, {response.msg}")
                return False

        except Exception as e:
            logger.error(f"Send reply error: {e}")
            return False

    def do_p2_im_message_receive_v1(self, data: lark.im.v1.P2ImMessageReceiveV1) -> None:
        """处理接收到的消息事件"""
        logger.info(f"[Feishu message received]: {data}")

        # 解析消息
        parsed = self._parse_message(data)
        if not parsed:
            return

        # 忽略非文本消息（可扩展）
        if parsed.get("message_type") != "text":
            logger.info(f"Ignored message type: {parsed.get('message_type')}")
            return

        # 处理消息并生成回复
        response_text = self._process_message(parsed)
        if response_text:
            # 发送回复
            self._send_reply(
                chat_id=parsed.get("chat_id", ""),
                message_id=parsed.get("message_id", ""),
                text=response_text
            )

    def start(self) -> bool:
        """启动飞书长连接客户端"""
        if not self.app_id or not self.app_secret:
            logger.error("Feishu App ID or Secret not configured")
            return False

        if not LARK_SDK_AVAILABLE:
            logger.error("lark_oapi SDK not installed")
            return False

        try:
            # 创建事件处理器
            event_handler = lark.EventDispatcherHandler.builder(
                self.app_id,
                self.app_secret
            ).register_p2_im_message_receive_v1(
                self.do_p2_im_message_receive_v1
            ).build()

            # 创建WebSocket客户端
            self.ws_client = lark.ws.Client(
                self.app_id,
                self.app_secret,
                event_handler=event_handler,
                log_level=self._get_log_level()
            )

            # 启动长连接
            logger.info("Starting Feishu WebSocket client...")
            self.ws_client.start()
            self._running = True
            logger.info("Feishu WebSocket client started successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to start Feishu client: {e}")
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
            "bot_name": self.bot_name
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
    client = FeishuClient()
    client.start()