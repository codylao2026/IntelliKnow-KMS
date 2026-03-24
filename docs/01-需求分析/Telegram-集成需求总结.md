# Telegram 集成需求总结
# Telegram Integration Requirements Summary

**创建时间**: 2026-03-23  
**参考文档**: Telegram-集成需求规格说明书.md  
**状态**: ✅ 已完成

---

## 📋 一句话总结

在现有 WhatsApp + Teams + 飞书集成基础上，新增 **Telegram Bot** 集成，利用其**免费 API、强大交互、全球化用户**优势，为企业提供又多一种知识查询前端渠道。

---

## 🎯 核心价值

| 维度 | 价值点 |
|------|--------|
| **成本** | Bot API 完全免费，无需商业账户 |
| **功能** | 支持内联键盘、回调查询、文件传输（2GB） |
| **覆盖** | 8 亿 + 全球活跃用户，跨国企业首选 |
| **安全** | 端到端加密，符合企业数据安全要求 |
| **集成** | 配置简单，开发成本低（1-2 天完成） |

---

## 📦 需求范围

### 必须实现（P0）

| 需求 ID | 功能 | 说明 |
|--------|------|------|
| FR-TG-001~004 | 基础消息收发 | 接收查询 + 返回响应 + 状态监控 + ≤3s 延迟 |
| FR-TG-008 | 私聊场景 | 用户与 Bot 一对一对话 |
| FR-TG-009 | 群组场景 | 群组中@Bot 触发响应 |
| FR-TG-011 | 响应格式 | 适配 Telegram HTML/Markdown 格式 |
| FR-TG-013 | Bot 命令 | /start、/help 基础命令 |

### 推荐实现（P1）

| 需求 ID | 功能 | 说明 |
|--------|------|------|
| FR-TG-005~006 | 双模式接收 | Webhook（生产）+ Long Polling（开发） |
| FR-TG-012 | 内联键盘 | 查看原文、相关搜索、反馈按钮 |
| FR-TG-014 | 回调处理 | 处理用户点击事件 |

### 可选实现（P2）

| 需求 ID | 功能 | 说明 |
|--------|------|------|
| FR-TG-007 | 图片 OCR | 图片消息识别（二期） |
| FR-TG-010 | 频道支持 | Channel 场景（二期） |
| FR-TG-015 | 文件上传 | 用户通过 Telegram 上传文档（二期） |

---

## 🛠️ 技术实现

### 技术选型

```python
# 推荐库
python-telegram-bot==20.7  # 20k+ Stars，最流行

# 安装
pip install python-telegram-bot
```

### 代码结构

```
app/services/frontend/
├── telegram_bot.py          # 新增：Telegram Bot 服务
├── feishu.py                # 已有：飞书集成
└── teams_bot.py             # 已有：Teams 集成
```

### 配置文件

```env
# .env
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_MODE=long_polling  # long_polling / webhook
TELEGRAM_GROUP_WHITELIST=-1001234567890
```

---

## 📊 与现有集成对比

| 特性 | WhatsApp | Teams | 飞书 | **Telegram** |
|------|----------|-------|------|--------------|
| API 成本 | 收费 | 免费 | 免费 | **免费** |
| 配置难度 | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | **⭐⭐** |
| 响应速度 | ≤3s | ≤3s | ≤3s | **≤3s** |
| 富文本 | 有限 | 强 | 强 | **强** |
| 内联交互 | 有限 | 强 | 强 | **强** |
| 文件传输 | 16MB | 支持 | 支持 | **2GB** |
| 全球化 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ | **⭐⭐⭐⭐⭐** |

---

## 🎨 管理后台集成

### 新增 Telegram 集成卡片

在"前端集成管理"页面新增卡片：

```
┌─────────────┐
│  Telegram   │
│  ⚪ 未配置  │
│  [配置]     │
│  [测试]     │
└─────────────┘
```

### 配置弹窗

- Bot Token 输入框
- 接收模式选择（Webhook/Long Polling）
- Webhook URL（可选）
- 群组白名单（可选）
- 连接状态显示
- 测试连接按钮

---

## ✅ 测试用例

| 测试项 | 测试步骤 | 预期结果 |
|--------|----------|----------|
| Bot 启动 | 发送 `/start` | 收到欢迎消息 |
| 基础查询 | 发送"理赔流程" | 3 秒内收到回答 |
| 帮助命令 | 发送 `/help` | 收到帮助文档 |
| 搜索命令 | 发送 `/search 报销` | 收到搜索结果 |
| 群组@ | 在群组中@Bot | Bot 响应查询 |
| 内联键盘 | 点击"查看原文" | 打开文档链接 |
| 连接测试 | 管理后台点击"测试" | 显示 Bot 信息 |

---

## ⚠️ 踩坑预警

| 问题 | 解决方案 |
|------|----------|
| Bot Token 泄露 | 使用环境变量，不要提交 Git |
| Webhook 设置失败 | 确保域名有 HTTPS 证书 |
| 群组中无响应 | 在 @BotFather 关闭隐私模式 |
| callback_data 超时 | 有效期仅 1 分钟，及时响应 |
| 消息频率限制 | 30 条/秒，批量发送需控制 |

---

## 📈 开发计划

| 阶段 | 任务 | 工时 |
|------|------|------|
| **Day 1** | 环境搭建 + Bot 创建 + 基础消息收发 | 4h |
| **Day 1** | 命令处理（/start, /help, /search） | 2h |
| **Day 2** | 内联键盘 + 回调处理 | 3h |
| **Day 2** | 管理后台集成 + 测试验证 | 3h |

**总计**: 12 小时（1.5 天）

---

## 📚 交付物

- [ ] `telegram_bot.py` - Bot 服务代码
- [ ] `.env.example` - 配置模板
- [ ] `Telegram-集成需求规格说明书.md` - 完整需求文档
- [ ] `Telegram-集成配置指南.md` - 配置教程
- [ ] `Telegram-测试报告.md` - 测试报告

---

## 🔗 参考资料

- **官方 API**: https://core.telegram.org/bots/api
- **Python SDK**: https://docs.python-telegram-bot.org/
- **示例代码**: https://github.com/python-telegram-bot/python-telegram-bot
- **需求文档**: `/40-Projects/40-IntelliKnow-KMS/docs/01-需求分析/Telegram-集成需求规格说明书.md`

---

## 💡 下一步行动

1. **确认需求优先级** - 与用户确认 P0/P1/P2 范围
2. **创建 Telegram Bot** - 通过 @BotFather 获取 Token
3. **开发实现** - 按照需求文档开发
4. **集成测试** - 管理后台 + 端到端测试
5. **文档更新** - 更新主 SRS 和 README

---

**状态**: ✅ 需求分析完成，等待用户确认优先级后启动开发
