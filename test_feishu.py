"""
飞书 WebSocket 独立测试脚本 - 官方方式
用法: python test_feishu.py
"""

import logging
import sys
import os
import threading

# 设置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 加载环境变量
from pathlib import Path
from dotenv import load_dotenv
env_path = Path(__file__).parent / "config" / ".env"
load_dotenv(env_path)

from config import settings


# ==================== 配置 ====================
APP_ID = settings.FEISHU_APP_ID
APP_SECRET = settings.FEISHU_APP_SECRET


# ==================== 回调函数 ====================
def do_p2_im_message_receive_v1(data) -> None:
    """接收消息回调 - 官方方式"""
    import lark_oapi as lark
    import json
    
    print(f'[收到消息]')
    logger.info(f"📨 收到飞书消息")
    
    try:
        # 打印原始数据结构
        logger.info(f"数据类型: {type(data)}")
        
        # 直接访问 protobuf 对象属性 (data.event.message)
        # 这是官方 SDK 的标准访问方式
        event = data.event
        message = event.message
        
        # 使用 getattr 获取属性
        message_id = getattr(message, "message_id", "") or ""
        message_type = getattr(message, "message_type", "text") or "text"
        content = getattr(message, "content", "") or ""
        
        logger.info(f"消息ID: {message_id}, 类型: {message_type}")
        logger.info(f"原始content: {content}")
        
        # 解析文本内容 - content 是 JSON 字符串
        text_content = ""
        if message_type == "text" and content:
            try:
                content_data = json.loads(content)
                text_content = content_data.get("text", "").strip()
            except json.JSONDecodeError:
                logger.error(f"JSON 解析失败: {content}")
                text_content = content.strip()
        
        logger.info(f"用户消息: {text_content}")
        
        if text_content and message_id:
            # 回复消息
            reply_text = f"收到消息: {text_content}\n\n(自动回复)"
            send_reply(message_id, reply_text)
        else:
            logger.warning(f"无法解析消息: message_id={message_id}, text={text_content}")
            
    except Exception as e:
        logger.error(f"处理消息错误: {e}")
        import traceback
        traceback.print_exc()


def send_reply(message_id: str, text: str):
    """发送回复消息"""
    import lark_oapi as lark
    import json
    
    try:
        # 创建 HTTP API 客户端
        client = (
            lark.Client.builder()
            .app_id(APP_ID)
            .app_secret(APP_SECRET)
            .build()
        )
        
        # 构建回复请求
        request = (
            lark.im.v1.ReplyMessageRequest.builder()
            .message_id(message_id)
            .request_body(
                lark.im.v1.ReplyMessageRequestBody.builder()
                .msg_type("text")
                .content(json.dumps({"text": text}))
                .build()
            )
            .build()
        )
        
        # 发送回复
        response = client.im.v1.message.reply(request)
        
        if response.success():
            logger.info(f"✅ 回复成功: {text[:50]}...")
        else:
            logger.error(f"❌ 回复失败: {response.code} - {response.msg}")
            
    except Exception as e:
        logger.error(f"发送回复错误: {e}")


def main():
    """主函数 - 官方方式"""
    import lark_oapi as lark
    
    app_id = settings.FEISHU_APP_ID
    app_secret = settings.FEISHU_APP_SECRET
    
    print(f"App ID: {app_id}")
    
    # 创建 event handler（官方方式）
    event_handler = (
        lark.EventDispatcherHandler.builder(app_id, app_secret)
        .register_p2_im_message_receive_v1(do_p2_im_message_receive_v1)
        .build()
    )
    
    # 创建客户端（官方方式）
    cli = lark.ws.Client(
        app_id,
        app_secret,
        event_handler=event_handler,
        log_level=lark.LogLevel.DEBUG
    )
    
    print("🚀 启动飞书 WebSocket...")
    
    # 直接调用 start() - 这是阻塞调用
    cli.start()
    
    print("🔄 连接已断开")


if __name__ == "__main__":
    # 直接运行（不是线程）
    main()
