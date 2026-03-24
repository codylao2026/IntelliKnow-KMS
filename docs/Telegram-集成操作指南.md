# IntelliKnow KMS 与 Telegram 集成操作指南

## 一、集成概述

### 1.1 集成方式

- **Polling 模式**：不需要公网域名，本地运行即可
- **消息处理**：接收用户查询 → 调用 RAG 服务 → 返回答案

### 1.2 集成架构

```
用户 (Telegram App)
       ↓
Telegram Bot (Polling)
       ↓
FastAPI (IntelliKnow KMS)
       ↓
RAG Pipeline (Hybrid Search + LLM)
       ↓
回答用户
```

---

## 二、配置步骤

### 2.1 环境变量配置

在 `config/.env` 文件中添加：

```env
# Telegram 配置
TELEGRAM_BOT_TOKEN=你的BotToken
TELEGRAM_TEST_CHAT_ID=你的ChatID

# 代理配置 (如需)
HTTP_PROXY=http://192.168.31.205:7890
HTTPS_PROXY=http://192.168.31.205:7890
```

### 2.2 配置说明

| 配置项 | 说明 | 示例 |
|--------|------|------|
| TELEGRAM_BOT_TOKEN | BotFather 创建的 Token | `8703736061:AAHPhYLyNzXsnZN_cVEgRjDjiVkU936DlPI` |
| TELEGRAM_TEST_CHAT_ID | 测试用聊天ID | `8516506339` |
| HTTP_PROXY | HTTP 代理地址 | `http://192.168.31.205:7890` |
| HTTPS_PROXY | HTTPS 代理地址 | `http://192.168.31.205:7890` |

### 2.3 启动服务

```bash
# 杀掉旧进程
lsof -ti:8000 | xargs -r kill -9

# 启动服务
cd ~/Obsidian-Vault/40-Projects/40-IntelliKnow-KMS
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

---

## 三、代码结构

### 3.1 核心文件

```
app/services/frontend/telegram.py     # Telegram Bot 客户端
app/utils/env_manager.py              # .env 文件读写工具
```

### 3.2 类结构

```
TelegramClient 类
├── __init__()           # 初始化，读取配置
├── start_polling()      # 启动长轮询
├── stop_polling()       # 停止轮询
├── _polling_loop()      # 轮询循环
├── _handle_message()   # 处理接收消息
├── _process_rag_query() # RAG 查询处理
├── _format_response()  # 格式化响应 (Markdown)
├── _send_message()      # 发送消息
├── _send_typing()       # 发送 typing 状态
└── _get_proxy()        # 获取代理配置
```

---

## 四、核心代码

### 4.1 初始化与配置读取

```python
def __init__(self):
    self.bot_token = settings.TELEGRAM_BOT_TOKEN
    self.api_url = f"https://api.telegram.org/bot{self.bot_token}"
    self.proxy = self._get_proxy()
    self.running = False
    self.offset = 0

def _get_proxy(self):
    if settings.HTTP_PROXY:
        return {"http": settings.HTTP_PROXY, "https": settings.HTTP_PROXY}
    return None
```

### 4.2 消息处理流程

```python
def _handle_message(self, chat_id: int, text: str):
    # 1. 发送 typing 状态
    self._send_typing(chat_id)
    
    # 2. 调用 RAG 服务
    result = self._process_rag_query(text)
    response_text = result.get("response", "抱歉，我暂时无法处理您的请求。")
    sources = result.get("sources", [])
    
    # 3. 格式化并发送响应
    response = self._format_response(response_text, sources)
    self._send_message(chat_id, response)
```

### 4.3 RAG 查询调用

```python
def _process_rag_query(self, query: str) -> Dict[str, Any]:
    from app.services.response_service import process_query
    from app.utils.database import async_session_maker
    
    async def run_query():
        async with async_session_maker() as db:
            return await process_query(query=query, db=db, frontend="telegram")
    
    return asyncio.run(run_query())
```

### 4.4 响应格式化 (Markdown)

```python
def _format_response(self, response_text: str, sources: List[Dict]) -> str:
    lines = []
    
    # 斜体格式化段落
    for para in response_text.split("\n\n"):
        if para.strip():
            lines.append(f"_{para.strip()}_")
    
    # 添加来源
    if sources:
        lines.append("\n")
        lines.append("📚 *参考来源:*")
        for i, source in enumerate(sources[:3], 1):
            title = source.get("document_name", "文档")
            lines.append(f"{i}. {title}")
    
    return "\n".join(lines)
```

### 4.5 发送消息

```python
def _send_message(self, chat_id: int, text: str):
    if not self.api_url:
        return
    
    # 转义 Markdown 特殊字符
    escape_chars = r"\_*[]()~`>#+-=|{}.!"
    for char in escape_chars:
        text = text.replace(char, f"\\{char}")
    
    proxies = self._get_proxy()
    
    requests.post(
        f"{self.api_url}/sendMessage",
        json={"chat_id": chat_id, "text": text, "parse_mode": "MarkdownV2"},
        timeout=10,
        proxies=proxies,
    )
```

### 4.6 启动/停止 (main.py)

```python
# 启动时
telegram_client = get_telegram_client()
telegram_client.start_polling()

# 关闭时
telegram_client.stop_polling()
```

---

## 五、问题及解决方案

### 问题1: 网络不通 (代理)

**现象**: Telegram Bot 连接失败，Network is unreachable

**原因**:
- uvicorn 不继承 shell 环境变量中的代理设置
- `requests` 库默认不使用环境变量代理

**解决**:
```python
# config/settings.py 添加
HTTP_PROXY = os.getenv("HTTP_PROXY", "")
HTTPS_PROXY = os.getenv("HTTPS_PROXY", "")

# telegram.py 中读取并使用
def _get_proxy(self):
    if settings.HTTP_PROXY:
        return {"http": settings.HTTP_PROXY, "https": settings.HTTP_PROXY}
    return None
```

---

### 问题2: 端口占用

**现象**: uvicorn 启动报错 Address already in use

**解决**:
```bash
lsof -ti:8000 | xargs -r kill -9
```

---

### 问题3: 向量索引数据混乱

**现象**: 搜索返回错误内容

**原因**: metadata.json 中 doc_id 映射与实际 chunk 内容不匹配

**解决**:
```bash
# 删除旧索引文件
rm -rf data/vectors/*

# 重新处理文档 (Python 代码)
from app.services.document_service import reprocess_document
from app.utils.database import get_db
import asyncio

async def rebuild():
    async for db in get_db():
        result = await db.execute(select(Document))
        docs = result.scalars().all()
        for doc in docs:
            await reprocess_document(doc.id, db)
        break

asyncio.run(rebuild())
```

---

### 问题4: RAG 返回错误答案 (置信度问题)

**现象**: 置信度 90% 但答案内容错误

**原因**:
1. Intent 无文档时返回了所有文档
2. 置信度是意图分类置信度，不是答案准确性

**解决** (response_service.py):

```python
# 1. 添加 intent 无文档检查
if not has_intent_docs:
    return {
        "response": "I couldn't find relevant documents for your query...",
        "confidence": 0.0,
        "confidence_source": "no_documents",
        "status": "no_intent_documents",
    }

# 2. 置信度改为基于 rerank 得分
top_score = reranked_results[0].get("rerank_score", reranked_results[0].get("score", 0))
if top_score >= 0.8:
    answer_confidence = 0.95
elif top_score >= 0.5:
    answer_confidence = 0.7
elif top_score >= 0.3:
    answer_confidence = 0.5
else:
    answer_confidence = 0.3
```

---

## 六、代码改动汇总

### 6.1 新增文件

| 文件 | 说明 |
|------|------|
| `app/services/frontend/telegram.py` | Telegram Bot 客户端 (Polling 模式) |
| `app/utils/env_manager.py` | .env 文件读写工具 |

### 6.2 修改文件

| 文件 | 改动 |
|------|------|
| `config/settings.py` | 添加 HTTP_PROXY、HTTPS_PROXY、TELEGRAM_* 配置 |
| `config/.env` | 添加 Telegram、代理配置 |
| `config/.env.example` | 添加 TELEGRAM 配置模板 |
| `app/main.py` | 添加 Telegram 启动/停止逻辑 |
| `app/api/credentials.py` | 改为读写 .env 文件而非 SQLite |
| `app/api/webhooks.py` | 添加 /test/telegram 端点 |
| `frontend/app.py` | 添加 Telegram 配置 UI |
| `app/services/response_service.py` | 添加 intent 无文档检查、置信度改为答案准确性 |

### 6.3 数据更新

| 操作 | 说明 |
|------|------|
| 重建向量索引 | `data/vectors/*` - 删除并重建 |
| 更新 Intent 关键词 | `intents` 表 - 添加 recruitment、finance 等关键词 |

---

## 七、测试验证

### 7.1 启动测试

```bash
# 启动服务后，检查日志中是否有 Telegram 初始化信息
uvicorn app.main:app --reload --port 8000
```

### 7.2 发送测试消息

```python
# 在 Python 中测试
from app.services.frontend.telegram import get_telegram_client
client = get_telegram_client()
client.test_connection(chat_id=8516506339)
```

### 7.3 功能测试

| 测试项 | 预期结果 |
|--------|----------|
| 发送 "what is the Recruitment Principles ?" | 返回正确的招聘原则答案 |
| 发送 "what is the company finance policy?" | 返回"未找到相关文档" |
| 发送任意消息 | 显示 typing 状态后返回响应 |

---

## 八、流式响应 (可选)

当前实现采用**方式2: typing 状态 + 完整响应**，用户体验已较好。

如需实现真正的流式输出（逐字显示），可参考以下方案：

```python
# 1. 先发送 "正在处理..." 消息
msg = self._send_message(chat_id, "⏳ 正在思考...")

# 2. 使用 process_query_streaming 逐个获取 token
from app.services.response_service import process_query_streaming
full_response = ""
async for event in process_query_streaming(query, db, frontend="telegram"):
    if event.get("token"):
        full_response += event["token"]
        # 每 50 个字符更新一次消息
        if len(full_response) % 50 == 0:
            self._edit_message(msg, full_response)

# 3. 发送最终完整消息 + 来源
self._send_message(chat_id, full_response, sources=sources)
```

**注意**: Telegram 每秒最多允许 1 次消息编辑，过于频繁会报错。

---

## 九、相关文件路径

- Telegram 客户端: `app/services/frontend/telegram.py`
- RAG 服务: `app/services/response_service.py`
- 配置文件: `config/settings.py`, `config/.env`
- 向量存储: `data/vectors/`
- 数据库: `data/sqlite/intelliknow.db`

---

*文档更新时间: 2026-03-23*