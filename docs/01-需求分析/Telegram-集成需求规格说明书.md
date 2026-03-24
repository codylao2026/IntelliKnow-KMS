# Telegram 集成需求规格说明书
# Telegram Integration Requirements Specification

**版本/Version**: 1.0  
**日期/Date**: 2026-03-23  
**项目名称/Project Name**: IntelliKnow KMS - Telegram Integration  
**状态/Status**: Draft  
**参考文档**: IntelliKnow-KMS-需求规格说明书-SRS.md v1.0

---

## 1. 概述 / Overview

### 1.1 集成目标 / Integration Objectives

在现有 WhatsApp + Teams + 飞书集成基础上，新增 **Telegram Bot** 集成，作为企业知识查询的又一前端渠道。

**新增 Telegram 集成的价值**：
- **全球化支持**：Telegram 在全球拥有 8 亿 + 活跃用户，支持跨国企业员工使用
- **开放 API**：Telegram Bot API 完全免费，无需商业账户，集成成本低
- **强大功能**：支持富文本、内联键盘、文件传输、频道广播等高级功能
- **隐私安全**：端到端加密（Secret Chat），符合企业数据安全要求
- **跨平台**：支持 iOS、Android、Desktop、Web 全平台

### 1.2 与现有集成对比 / Comparison with Existing Integrations

| 特性 | WhatsApp | Teams | 飞书 | **Telegram** |
|------|----------|-------|------|--------------|
| API 类型 | Business API (收费) | Bot Framework | 自建应用 | **Bot API (免费)** |
| 配置复杂度 | 中 | 高 | 中 | **低** |
| 富文本支持 | 有限 | 强 | 强 | **强** |
| 文件传输 | 支持 | 支持 | 支持 | **支持 (最大 2GB)** |
| 内联交互 | 有限 | 强 | 强 | **强 (Inline Keyboard)** |
| 频道广播 | 不支持 | 支持 | 支持 | **支持 (Channel)** |
| 群组机器人 | 支持 | 支持 | 支持 | **支持** |
| 隐私保护 | 中 | 高 | 高 | **高 (端到端加密)** |

---

## 2. 功能需求 / Functional Requirements

### 2.1 Telegram Bot 基础集成 / Telegram Bot Basic Integration

#### 2.1.1 Bot 创建与配置

**FR-TG-001**: 系统应支持通过 Telegram Bot API 接收用户查询并返回响应  
**FR-TG-001**: The system shall support receiving user queries and returning responses via Telegram Bot API

**FR-TG-002**: 应支持配置 Telegram Bot 凭证（Bot Token）  
**FR-TG-002**: The system shall support configuring Telegram Bot credentials (Bot Token)

**配置说明 / Configuration Details**:
```env
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_BOT_NAME=IntelliKnow Bot
TELEGRAM_WEBHOOK_URL=https://your-domain.com/webhook/telegram
```

**获取 Bot Token 步骤**:
1. 在 Telegram 中搜索 `@BotFather`
2. 发送 `/newbot` 命令创建新 Bot
3. 按提示设置 Bot 名称和用户名
4. BotFather 返回 Bot Token，保存到配置文件

**FR-TG-003**: 应显示连接状态（已连接/未连接）并提供测试功能  
**FR-TG-003**: The system shall display connection status (Connected/Disconnected) and provide test functionality

**FR-TG-004**: 响应延迟应≤3 秒  
**FR-TG-004**: Response latency shall be ≤3 seconds

---

#### 2.1.2 消息接收模式

**FR-TG-005**: 系统应支持两种消息接收模式：Webhook 和 Long Polling  
**FR-TG-005**: The system shall support two message receiving modes: Webhook and Long Polling

| 模式 | 适用场景 | 优点 | 缺点 |
|------|----------|------|------|
| **Webhook** | 生产环境，有公网域名 | 实时性好，资源消耗低 | 需要 HTTPS 域名 |
| **Long Polling** | 开发/测试环境，无公网 IP | 无需公网域名，配置简单 | 需要持续轮询，资源消耗高 |

**FR-TG-006**: 应支持在管理后台切换消息接收模式  
**FR-TG-006**: The system shall support switching message receiving mode in admin dashboard

---

#### 2.1.3 消息类型支持

**FR-TG-007**: 应支持解析以下 Telegram 消息类型：  
**FR-TG-007**: The system shall support parsing the following Telegram message types:

| 消息类型 | 支持状态 | 说明 |
|----------|----------|------|
| 文本消息 | ✅ 必须 | 基础查询 |
| @提及消息 | ✅ 必须 | 群组场景 |
| 图片消息 | ⚠️ 可选 | OCR 识别（二期） |
| 文件消息 | ⚠️ 可选 | 文档上传（二期） |
| 语音消息 | ❌ 暂不支持 | - |
| 视频消息 | ❌ 暂不支持 | - |

---

### 2.2 聊天场景支持 / Chat Scenarios Support

#### 2.2.1 私聊场景 / Private Chat

**FR-TG-008**: 应支持用户与 Bot 的私聊场景  
**FR-TG-008**: The system shall support private chat scenarios between user and Bot

**功能要求**:
- 用户直接在私聊窗口发送查询
- Bot 返回知识查询结果
- 支持对话历史上下文（可选）

---

#### 2.2.2 群组场景 / Group Chat

**FR-TG-009**: 应支持 Telegram 群组（Group）和超级群组（Supergroup）场景  
**FR-TG-009**: The system shall support Telegram Group and Supergroup scenarios

**功能要求**:
- Bot 被 @提及时触发响应
- 支持设置群组白名单（可选）
- 支持群聊隐私模式（Privacy Mode）配置

**配置项**:
```env
TELEGRAM_GROUP_WHITELIST=-1001234567890,-1009876543210  # 允许的群组 ID 列表
TELEGRAM_PRIVACY_MODE=enabled  # enabled/disabled
```

---

#### 2.2.3 频道场景 / Channel (可选)

**FR-TG-010**: 应支持将 Bot 添加到 Telegram 频道作为管理员  
**FR-TG-010**: The system shall support adding Bot to Telegram Channel as admin

**功能要求**:
- Bot 可以接收频道消息（需设置为管理员）
- 支持频道消息自动回复（可选）
- 支持频道广播通知（二期）

---

### 2.3 响应格式适配 / Response Format Adaptation

**FR-TG-011**: 响应格式应适配 Telegram 原生格式  
**FR-TG-011**: Response format shall adapt to Telegram native format

**支持的 Telegram 消息格式**:

#### 2.3.1 HTML 格式
```python
# 支持 HTML 标签
<b>粗体</b>
<i>斜体</i>
<u>下划线</u>
<s>删除线</s>
<a href="http://example.com">链接</a>
<code>代码块</code>
<pre>预格式化文本</pre>
```

#### 2.3.2 Markdown V2 格式
```python
# 支持 Markdown 语法
*粗体*
_斜体_
~删除线~
`代码块`
[链接](http://example.com)
```

**FR-TG-012**: 应支持发送带内联键盘（Inline Keyboard）的交互消息  
**FR-TG-012**: The system shall support sending interactive messages with Inline Keyboard

**示例**:
```python
inline_keyboard = [
    [
        {"text": "📄 查看原文", "callback_data": "view_doc_123"},
        {"text": "🔍 相关搜索", "callback_data": "related_search_123"}
    ],
    [
        {"text": "❓ 帮助", "callback_data": "help"},
        {"text": "⚙️ 设置", "callback_data": "settings"}
    ]
]
```

---

### 2.4 高级功能 / Advanced Features

#### 2.4.1 命令支持 / Commands Support

**FR-TG-013**: 应支持以下 Telegram Bot 命令  
**FR-TG-013**: The system shall support the following Telegram Bot commands

| 命令 | 功能 | 示例 |
|------|------|------|
| `/start` | 启动 Bot，显示欢迎信息 | `/start` |
| `/help` | 显示帮助文档和使用说明 | `/help` |
| `/search` | 显式搜索命令 | `/search 理赔流程` |
| `/history` | 查看查询历史 | `/history` |
| `/settings` | 个人设置 | `/settings` |

**命令配置** (通过 @BotFather 设置):
```
commands
start - 开始使用 IntelliKnow
help - 查看帮助文档
search - 搜索知识库
history - 查看查询历史
settings - 个人设置
```

---

#### 2.4.2 回调查询处理 / Callback Query Handling

**FR-TG-014**: 应支持处理内联键盘的回调查询（Callback Query）  
**FR-TG-014**: The system shall handle inline keyboard callback queries

**回调数据类型**:
```python
callback_data 格式: action:item_id:extra
示例:
- view_doc:123:hr_policy
- related_search:456:finance
- feedback:good:query_789
```

---

#### 2.4.3 文件传输 / File Transfer

**FR-TG-015**: 应支持用户通过 Telegram 上传文档到知识库（二期）  
**FR-TG-015**: The system shall support users uploading documents to knowledge base via Telegram (Phase 2)

**要求**:
- 支持 PDF、DOCX 格式
- 最大文件大小：2GB（Telegram 限制）
- 上传后自动解析并向量化

---

### 2.5 与现有 SRS 需求映射 / Mapping to Existing SRS Requirements

| Telegram 需求 | 对应 WhatsApp 需求 | 对应 Teams 需求 | 对应飞书需求 |
|---------------|-------------------|----------------|-------------|
| FR-TG-001~004 | FR-001~004 | FR-005~008 | FR-FL-001~004 |
| FR-TG-005~006 | - | - | - |
| FR-TG-007~010 | - | - | FR-FL-005~006 |
| FR-TG-011~012 | - | FR-008 | FR-FL-004 |
| FR-TG-013~015 | - | - | - |

---

## 3. 技术实现 / Technical Implementation

### 3.1 技术选型 / Technology Stack

#### 3.1.1 Python Telegram Bot 库对比

| 库 | Stars | 特点 | 推荐度 |
|----|-------|------|--------|
| **python-telegram-bot** | 20k+ | 最流行，文档完善，支持异步 | ⭐⭐⭐⭐⭐ |
| **aiogram** | 8k+ | 纯异步，性能好，学习曲线陡 | ⭐⭐⭐⭐ |
| **pyrogram** | 5k+ | 支持 MTProto，功能全面 | ⭐⭐⭐⭐ |
| **telebot** | 4k+ | 简单易用，适合快速原型 | ⭐⭐⭐ |

**推荐**: `python-telegram-bot` (v20+)  
**理由**: 社区最活跃、文档最完善、支持异步、与 FastAPI 兼容性好

---

#### 3.1.2 安装依赖

```bash
pip install python-telegram-bot==20.7
```

---

### 3.2 代码结构 / Code Structure

```
app/services/frontend/
├── telegram_bot.py          # Telegram Bot 主服务
│   ├── TelegramBotClient 类
│   │   ├── __init__()              - 初始化配置
│   │   ├── _setup_bot()            - 设置 Bot 命令和回调
│   │   ├── _handle_message()       - 处理文本消息
│   │   ├── _handle_callback()      - 处理回调查询
│   │   ├── _handle_command()       - 处理 Bot 命令
│   │   ├── _send_response()        - 发送响应消息
│   │   ├── _build_inline_keyboard() - 构建内联键盘
│   │   ├── start_polling()         - 启动轮询模式
│   │   └── set_webhook()           - 设置 Webhook 模式
│   ├── init_telegram_bot()  - 启动客户端
│   └── get_telegram_bot()   - 获取单例
├── feishu.py                # 飞书集成（已有）
└── teams_bot.py             # Teams 集成（已有）
```

---

### 3.3 核心代码模板 / Core Code Template

```python
import logging
from typing import Optional, Dict, Any
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
from telegram.constants import ParseMode

logger = logging.getLogger(__name__)


class TelegramBotClient:
    """Telegram Bot 客户端"""
    
    def __init__(self, bot_token: str):
        self.bot_token = bot_token
        self.application: Optional[Application] = None
        self._running = False
        
    async def _setup_bot(self):
        """设置 Bot 命令和回调"""
        # 创建 Application
        self.application = Application.builder().token(self.bot_token).build()
        
        # 添加命令处理器
        self.application.add_handler(CommandHandler("start", self._handle_start))
        self.application.add_handler(CommandHandler("help", self._handle_help))
        self.application.add_handler(CommandHandler("search", self._handle_search))
        
        # 添加消息处理器（仅处理文本和@消息）
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_message)
        )
        
        # 添加回调查询处理器
        self.application.add_handler(
            CallbackQueryHandler(self._handle_callback)
        )
        
    async def _handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /start 命令"""
        welcome_text = """
👋 欢迎使用 IntelliKnow 企业知识助手！

我可以帮您快速查询公司知识库，包括：
• HR 政策与流程
• 法务合规文档
• 财务制度与报销
• 其他企业知识

💡 使用方式：
1. 直接发送您的问题
2. 或使用 /search 命令搜索
3. 查看 /help 了解更多功能

让我们开始吧！🚀
"""
        await update.message.reply_text(
            welcome_text,
            parse_mode=ParseMode.HTML
        )
        
    async def _handle_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /help 命令"""
        help_text = """
📖 IntelliKnow 使用帮助

<b>基础查询</b>
直接发送您的问题，例如：
"如何在好福利上进行理赔？"

<b>命令列表</b>
/start - 开始使用
/help - 查看帮助
/search - 搜索知识库
/history - 查询历史
/settings - 个人设置

<b>群组使用</b>
在群组中 @我 即可触发查询：
@IntelliKnowBot 理赔流程

<b>更多功能</b>
• 支持文档链接查看
• 支持相关搜索推荐
• 支持查询反馈

有任何问题请联系管理员。
"""
        await update.message.reply_text(
            help_text,
            parse_mode=ParseMode.HTML
        )
        
    async def _handle_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /search 命令"""
        if context.args:
            query = " ".join(context.args)
            await self._process_query(update, query)
        else:
            await update.message.reply_text(
                "❗ 请提供搜索关键词\n\n"
                "示例：/search 理赔流程",
                parse_mode=ParseMode.HTML
            )
            
    async def _handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理文本消息"""
        # 检查是否是群组中的@消息
        if update.message.chat.type in ["group", "supergroup"]:
            if not update.message.entities or \
               not any(e.type == "mention" for e in update.message.entities):
                # 群组中非@消息，忽略
                return
                
        text = update.message.text.strip()
        if text:
            await self._process_query(update, text)
            
    async def _process_query(self, update: Update, query: str):
        """处理查询（调用 RAG 引擎）"""
        # 发送"正在处理"提示
        processing_msg = await update.message.reply_text("🔍 正在查询知识库...")
        
        try:
            # TODO: 调用 RAG 引擎
            # response = await rag_engine.query(query)
            response = {
                "answer": "这是测试回答",
                "sources": [
                    {"doc_id": "123", "title": "理赔流程文档", "url": "http://example.com/doc1"}
                ],
                "confidence": 0.85
            }
            
            # 构建响应消息
            answer_text = f"""
📝 <b>查询结果</b>

{response["answer"]}

📚 <b>来源文档</b>
"""
            for i, source in enumerate(response["sources"], 1):
                answer_text += f"\n[{i}] <a href=\"{source['url']}\">{source['title']}</a>"
                
            answer_text += f"\n\n💡 <b>置信度</b>: {response['confidence']*100:.1f}%"
            
            # 构建内联键盘
            keyboard = await self._build_inline_keyboard(response)
            
            # 编辑"正在处理"消息
            await processing_msg.edit_text(
                answer_text,
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            
        except Exception as e:
            logger.error(f"Query processing error: {e}")
            await processing_msg.edit_text(
                "❌ 查询失败，请稍后重试\n\n"
                f"错误信息：{str(e)}",
                parse_mode=ParseMode.HTML
            )
            
    async def _build_inline_keyboard(self, response: Dict[str, Any]) -> list:
        """构建内联键盘"""
        keyboard = []
        
        # 第一行：查看原文按钮
        if response.get("sources"):
            row = []
            for source in response["sources"][:2]:  # 最多显示 2 个
                row.append(
                    InlineKeyboardButton(
                        text=f"📄 {source['title'][:15]}...",
                        callback_data=f"view_doc:{source['doc_id']}"
                    )
                )
            keyboard.append(row)
        
        # 第二行：相关搜索和反馈
        keyboard.append([
            InlineKeyboardButton("🔍 相关搜索", callback_data="related_search"),
            InlineKeyboardButton("👍 有用", callback_data="feedback:good"),
            InlineKeyboardButton("👎 无用", callback_data="feedback:bad"),
        ])
        
        return keyboard
        
    async def _handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理回调查询"""
        query = update.callback_query
        data = query.data
        
        logger.info(f"Callback received: {data}")
        
        # 解析 callback_data
        parts = data.split(":")
        action = parts[0]
        
        if action == "view_doc":
            doc_id = parts[1]
            await query.answer("正在打开文档...")
            # TODO: 发送文档链接或内容
            
        elif action == "related_search":
            await query.answer("正在生成相关搜索...")
            # TODO: 生成相关搜索建议
            
        elif action == "feedback":
            feedback_type = parts[1]
            await query.answer(f"感谢您的{'好评' if feedback_type == 'good' else '反馈'}！")
            # TODO: 记录反馈
            
    async def start_polling(self):
        """启动轮询模式"""
        await self._setup_bot()
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True,
        )
        self._running = True
        logger.info("Telegram Bot polling started")
        
    async def stop_polling(self):
        """停止轮询"""
        if self.application and self._running:
            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()
            self._running = False
            logger.info("Telegram Bot polling stopped")
            
    async def set_webhook(self, webhook_url: str) -> bool:
        """设置 Webhook 模式"""
        await self._setup_bot()
        await self.application.initialize()
        
        # 设置 webhook
        await self.application.bot.set_webhook(
            url=webhook_url,
            allowed_updates=Update.ALL_TYPES,
        )
        
        logger.info(f"Telegram webhook set to: {webhook_url}")
        return True


# 单例模式
_telegram_bot: Optional[TelegramBotClient] = None


def init_telegram_bot(bot_token: str) -> TelegramBotClient:
    """初始化 Telegram Bot"""
    global _telegram_bot
    if _telegram_bot is None:
        _telegram_bot = TelegramBotClient(bot_token)
    return _telegram_bot


def get_telegram_bot() -> Optional[TelegramBotClient]:
    """获取 Telegram Bot 实例"""
    return _telegram_bot
```

---

### 3.4 配置文件更新 / Configuration Updates

#### 3.4.1 .env 文件

```env
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_BOT_NAME=IntelliKnow Bot
TELEGRAM_WEBHOOK_URL=https://your-domain.com/webhook/telegram
TELEGRAM_MODE=long_polling  # long_polling / webhook
TELEGRAM_GROUP_WHITELIST=-1001234567890,-1009876543210
TELEGRAM_PRIVACY_MODE=enabled
```

#### 3.4.2 requirements.txt

```txt
# Frontend Integrations
python-telegram-bot==20.7  # Telegram Bot SDK
lark-oapi==1.5.3           # Feishu SDK
botbuilder-core==4.15.0    # Teams Bot SDK
botbuilder-integration-aiohttp==4.15.0
```

---

## 4. 管理后台集成 / Admin Dashboard Integration

### 4.1 前端集成管理页面更新 / Frontend Integration Page Updates

在现有的"前端集成管理"页面中，新增 **Telegram 集成卡片**：

```
┌─────────────────────────────────────────────────────────┐
│  前端集成管理 / Frontend Integration                    │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐       │
│  │  WhatsApp   │ │   Teams     │ │   飞书      │       │
│  │  🟢 已连接  │ │  🟢 已连接  │ │  🟢 已连接  │       │
│  │  [配置]     │ │  [配置]     │ │  [配置]     │       │
│  │  [测试]     │ │  [测试]     │ │  [测试]     │       │
│  └─────────────┘ └─────────────┘ └─────────────┘       │
│                                                         │
│  ┌─────────────┐                                        │
│  │  Telegram   │  ← 新增                               │
│  │  ⚪ 未配置  │                                        │
│  │  [配置]     │                                        │
│  │  [测试]     │                                        │
│  └─────────────┘                                        │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

### 4.2 Telegram 配置弹窗 / Telegram Configuration Modal

```
┌─────────────────────────────────────────────────────────┐
│  Telegram Bot 配置                              [×]     │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Bot Token *                                            │
│  ┌─────────────────────────────────────────────────┐   │
│  │ 1234567890:ABCdefGHIjklMNOpqrsTUVwxyz           │   │
│  └─────────────────────────────────────────────────┘   │
│  💡 从 @BotFather 获取                                   │
│                                                         │
│  接收模式                                               │
│  ○ Webhook (需要 HTTPS 域名)                            │
│  ● Long Polling (开发/测试)                             │
│                                                         │
│  Webhook URL (仅 Webhook 模式)                          │
│  ┌─────────────────────────────────────────────────┐   │
│  │ https://your-domain.com/webhook/telegram        │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  群组白名单 (可选)                                      │
│  ┌─────────────────────────────────────────────────┐   │
│  │ -1001234567890,-1009876543210                   │   │
│  └─────────────────────────────────────────────────┘   │
│  💡 填写群组 ID，留空表示允许所有群组                  │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │  连接状态：⚪ 未测试                              │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│         [保存配置]    [测试连接]    [取消]              │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

### 4.3 测试功能 / Test Function

**测试流程**:
1. 用户点击"测试连接"按钮
2. 后端调用 Telegram Bot API 的 `getMe` 方法
3. 返回 Bot 信息（名称、用户名等）
4. 显示测试结果

**测试代码**:
```python
async def test_telegram_connection(bot_token: str) -> Dict[str, Any]:
    """测试 Telegram 连接"""
    try:
        async with telegram.Bot(token=bot_token) as bot:
            me = await bot.get_me()
            return {
                "success": True,
                "bot_name": me.first_name,
                "bot_username": me.username,
                "message": f"成功连接到 Bot: @{me.username}"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "连接失败，请检查 Bot Token 是否正确"
        }
```

---

## 5. 踩坑记录 / Gotchas

### 5.1 常见问题与解决方案

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| `Unauthorized` 错误 | Bot Token 错误 | 从 @BotFather 重新获取 Token |
| Webhook 设置失败 | 域名无 HTTPS | 使用 ngrok 或配置 SSL 证书 |
| 群组中无响应 | 隐私模式未关闭 | 在 @BotFather 中设置 `/setprivacy` |
| 消息发送失败 | 用户拉黑 Bot | 检查用户是否 blocked |
| 回调查询无响应 | callback_data 超时 | Telegram 回调数据有效期 1 分钟 |

---

### 5.2 Telegram API 限制

| 限制项 | 数值 | 说明 |
|--------|------|------|
| 消息频率限制 | 30 条/秒 | 同一 Bot 每秒最多发送 30 条消息 |
| 群组数量限制 | 无限制 | Bot 可加入无限个群组 |
| callback_data 长度 | ≤64 字节 | 回调数据不能太长 |
| 消息长度限制 | 4096 字符 | 单条消息最大长度 |
| 文件大小限制 | 2GB | 上传文件最大 2GB |

---

### 5.3 安全注意事项

1. **Bot Token 保护**:
   - 不要将 Token 提交到 Git 仓库
   - 使用环境变量或加密存储
   - 定期轮换 Token

2. **用户隐私**:
   - 不要存储用户敏感信息
   - 遵守 Telegram API 条款
   - 提供用户数据删除接口

3. **群组安全**:
   - 设置群组白名单
   - 限制 Bot 权限（仅必要权限）
   - 监控异常访问

---

## 6. 测试验证 / Testing & Verification

### 6.1 测试用例 / Test Cases

| 测试项 | 测试步骤 | 预期结果 |
|--------|----------|----------|
| Bot 启动 | 发送 `/start` | 收到欢迎消息 |
| 基础查询 | 发送"理赔流程" | 3 秒内收到回答 |
| 帮助命令 | 发送 `/help` | 收到帮助文档 |
| 搜索命令 | 发送 `/search 报销` | 收到搜索结果 |
| 群组@ | 在群组中@Bot | Bot 响应查询 |
| 内联键盘 | 点击"查看原文" | 打开文档链接 |
| 回调反馈 | 点击"👍 有用" | 收到感谢消息 |
| 连接测试 | 管理后台点击"测试" | 显示 Bot 信息 |

---

### 6.2 日志确认项 / Log Checklist

启动 Bot 后，日志应包含：

```
✅ INFO: Telegram Bot polling started
✅ INFO: Message received from user: {user_id}
✅ INFO: Query processed: "理赔流程"
✅ INFO: Response sent to user: {user_id}
⚠️  WARNING: Group message ignored (not @mentioned)
❌ ERROR: Query processing failed: {error}
```

---

## 7. 与现有集成对比总结 / Integration Comparison Summary

| 特性 | WhatsApp | Teams | 飞书 | **Telegram** |
|------|----------|-------|------|--------------|
| **配置难度** | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| **API 成本** | 收费 | 免费 | 免费 | **免费** |
| **响应速度** | ≤3s | ≤3s | ≤3s | **≤3s** |
| **富文本** | 有限 | 强 | 强 | **强** |
| **内联交互** | 有限 | 强 | 强 | **强** |
| **文件传输** | 支持 | 支持 | 支持 | **支持 (2GB)** |
| **群组支持** | 支持 | 支持 | 支持 | **支持** |
| **隐私保护** | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | **⭐⭐⭐⭐⭐** |
| **全球化** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ | **⭐⭐⭐⭐⭐** |

---

## 8. 里程碑更新 / Milestones Update

在原有 SRS 里程碑基础上，更新如下：

| 里程碑 | 任务 | 计划日期 | 状态 |
|--------|------|----------|------|
| M3: 意图分类 + 前端集成完成 | 增加 Telegram Bot 对接 | 第 4 天 | **更新** |
| M5: 测试与优化完成 | 增加 Telegram 测试用例 | 第 6 天 | **更新** |
| M6: PPT 演示制作 | 增加 Telegram 集成截图 | 第 6 天 | **更新** |

---

## 9. 交付物更新 / Deliverables Update

新增交付物：

| 交付物 | 描述 |
|--------|------|
| Telegram Bot 源码 | `app/services/frontend/telegram_bot.py` |
| 配置文档 | Telegram 集成配置说明 |
| 测试报告 | Telegram 功能测试报告 |
| 用户手册 | Telegram Bot 使用指南 |

---

## 10. 参考资料 / References

### 10.1 官方文档

- **Telegram Bot API**: https://core.telegram.org/bots/api
- **python-telegram-bot**: https://docs.python-telegram-bot.org/
- **Telegram Bot 示例**: https://github.com/python-telegram-bot/python-telegram-bot

### 10.2 相关 Case Study

- Design Case Study: How to increase the use of Telegram? (Medium)
- A Comprehensive Overview of Telegram Services - A Case Study (Academia.edu)
- 探索 Telegram API：集成即时通讯功能的技术指南 (CSDN)

---

## 11. 附录：完整需求清单 / Appendix: Complete Requirements Checklist

### P0 优先级（必须实现）

- [ ] FR-TG-001: 基础消息收发
- [ ] FR-TG-002: Bot Token 配置
- [ ] FR-TG-003: 连接状态显示
- [ ] FR-TG-004: ≤3 秒响应
- [ ] FR-TG-008: 私聊场景
- [ ] FR-TG-009: 群组@场景
- [ ] FR-TG-011: 响应格式适配
- [ ] FR-TG-013: 基础命令（/start, /help）

### P1 优先级（推荐实现）

- [ ] FR-TG-005: Webhook/Long Polling 双模式
- [ ] FR-TG-006: 模式切换功能
- [ ] FR-TG-012: 内联键盘交互
- [ ] FR-TG-014: 回调查询处理

### P2 优先级（可选实现）

- [ ] FR-TG-007: 图片消息 OCR
- [ ] FR-TG-010: 频道场景
- [ ] FR-TG-015: 文件上传功能

---

**文档结束 / End of Document**

---

## 📝 更新日志 / Change Log

| 版本 | 日期 | 更新内容 | 作者 |
|------|------|----------|------|
| 1.0 | 2026-03-23 | 初始版本：完整 Telegram 集成需求 | AITom |
