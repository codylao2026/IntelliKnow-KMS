# Feishu 飞书集成总结

## 一、环境准备

### 1. 安装飞书 SDK

```bash
pip install lark-oapi
```

### 2. 配置凭据 (.env)

```env
FEISHU_APP_ID=cli_a937adaccdb95cd3
FEISHU_APP_SECRET=你的密钥
FEISHU_BOT_NAME=IntelliKnow Bot
```

### 3. 飞书开发者后台配置

- 开启权限：`im:message`、`im:message:send_as_bot`
- 订阅事件：`im.message.receive_v1`
- 开启长连接（WebSocket）

---

## 二、关键代码结构

```
app/services/frontend/feishu.py
├── FeishuClient 类
│   ├── __init__()           - 初始化配置
│   ├── _parse_message()     - 解析消息事件
│   ├── _process_message()   - 异步处理消息（RAG）
│   ├── _send_message()      - 通用发送消息
│   ├── _build_interactive_card() - 构建卡片
│   └── do_p2_im_message_receive_v1() - 事件处理
├── init_feishu_client()     - 启动客户端
└── get_feishu_client()      - 获取单例
```

---

## 三、核心修复（踩坑记录）

### 1. SDK API 调用错误

```python
# 错误（旧版本文档）
client.im.v1.reply_message(request)

# 正确（lark-oapi 1.5.3）
client.im.v1.message.reply(request)
```

### 2. 卡片消息格式

```python
# 错误 - 多嵌套了一层
json.dumps({"card": card})

# 正确 - 直接发送卡片内容
json.dumps(card)
```

### 3. 事件循环冲突

```python
# WebSocket 重连时需要捕获 RuntimeError
except RuntimeError as e:
    if "event loop" in str(e).lower():
        logger.warning("Event loop conflict, waiting...")
        time.sleep(5)
        self._reconnect_count += 1
    else:
        raise
```

### 4. FAISS 空文件错误

```python
# 启动时创建占位文件
_index_file = FAISS_INDEX_DIR / "index.faiss"
_pkl_file = FAISS_INDEX_DIR / "index.pkl"
if not _index_file.exists():
    _index_file.touch()
if not _pkl_file.exists():
    _pkl_file.touch()
```

### 5. 回复消息 Request Body

```python
# 错误
request_body = lark.im.v1.ReplyMessageRequestBody.builder()
    .msg_type("text")
    .content(json.dumps({"text": text}))  # 双重序列化
    .build()

# 正确
request_body = lark.im.v1.ReplyMessageRequestBody.builder()
    .msg_type("text")
    .content(json.dumps({"text": text}))
    .reply_in_thread(True)  # 在线程中回复
    .build()
```

---

## 四、完整 FeishuClient 代码模板

```python
import lark_oapi as lark
import json
import threading
import asyncio
from typing import Optional, Dict, Any, List

class FeishuClient:
    def __init__(self, app_id: str, app_secret: str):
        self.app_id = app_id
        self.app_secret = app_secret
        self._running = False
        self._thread = None
        self._client = None

    def _create_client(self):
        return lark.Client.builder() \
            .app_id(self.app_id) \
            .app_secret(self.app_secret) \
            .log_level(lark.LogLevel.INFO) \
            .build()

    def _send_message(self, message_id: str, msg_type: str, content: str) -> bool:
        """通用发送消息"""
        try:
            if self._client is None:
                self._client = self._create_client()

            request_body = lark.im.v1.ReplyMessageRequestBody.builder() \
                .msg_type(msg_type) \
                .content(content) \
                .reply_in_thread(True) \
                .build()

            request = lark.im.v1.ReplyMessageRequest.builder() \
                .message_id(message_id) \
                .request_body(request_body) \
                .build()

            response = self._client.im.v1.message.reply(request)
            return response.success()
        except Exception as e:
            print(f"Send error: {e}")
            return False

    def _parse_message(self, data) -> Optional[Dict]:
        """解析消息"""
        msg = data.event.message
        content = json.loads(msg.content)
        return {
            "message_id": msg.message_id,
            "text": content.get("text", "").strip(),
            "chat_type": msg.chat_type,
        }

    def do_p2_im_message_receive_v1(self, data):
        """处理接收消息"""
        parsed = self._parse_message(data)
        if not parsed or not parsed["text"]:
            return

        # 这里调用你的 RAG 处理逻辑
        response = "处理结果"

        self._send_message(
            parsed["message_id"],
            "text",
            json.dumps({"text": response})
        )

    def start(self):
        """启动"""
        def run():
            handler = lark.EventDispatcherHandler.builder(
                self.app_id, self.app_secret
            ).register_p2_im_message_receive_v1(
                self.do_p2_im_message_receive_v1
            ).build()

            ws = lark.ws.Client(
                self.app_id, self.app_secret,
                event_handler=handler
            )
            self._running = True
            ws.start()

            while self._running:
                import time
                time.sleep(1)

        self._thread = threading.Thread(target=run, daemon=False)
        self._thread.start()
```

---

## 五、常见错误对照表

| 错误信息 | 原因 | 解决方案 |
|---------|------|---------|
| `AttributeError: 'V1' has no attribute 'reply_message'` | API 路径错误 | 改为 `client.im.v1.message.reply()` |
| `230099 - parse card json err` | 卡片格式错误 | 移除 `{"card": card}` 包装 |
| `event loop is already running` | 异步冲突 | 重连时捕获 RuntimeError，等待后重试 |
| `Failed to create card content` | 卡片 JSON 格式 | 确保 `json.dumps(card)` 而非 `json.dumps({"card": card})` |
| `FAISS index: read error` | 空索引文件 | 创建占位文件或上传文档 |

---

## 六、测试验证

```bash
# 1. 启动后端
uvicorn app.main:app --reload --port 8000

# 2. 检查日志
# 应该看到: "Feishu WebSocket client started successfully"

# 3. 在飞书发送消息测试
/test
```

日志确认项：

- ✅ `Message received`
- ✅ `Message sent successfully`
- ⚠️ `Message send failed` → 检查错误码和格式

---

## 七、最终集成代码

项目中的完整代码位于：`app/services/frontend/feishu.py`

### 关键特性

1. **长连接模式**：使用 WebSocket 接收消息，无需公网回调
2. **自动重连**：指数退避策略，最多 10 次重试
3. **线程隔离**：避免事件循环冲突
4. **交互卡片**：支持富文本回复和来源引用
5. **群聊支持**：仅响应 @ 机器人的消息
