# IntelliKnow KMS 项目

## 目录结构

```
40-IntelliKnow-KMS/
├── docs/                         # 项目文档
│   ├── IntelliKnow-KMS-需求规格说明书-SRS.md   # 完整需求规格说明书
│   ├── PRD.md                   # 产品需求文档（给Claude Code用）
│   └── CaseStudy-需求映射表.md  # Case Study需求映射
│
├── app/                          # 应用代码
│   ├── api/                      # FastAPI路由
│   ├── services/                 # 业务逻辑
│   ├── models/                   # 数据模型
│   └── utils/                    # 工具函数
│
├── frontend/                     # Streamlit管理后台
│   └── app.py
│
├── data/                         # 数据存储
│   ├── sqlite/                   # SQLite数据库
│   ├── vectors/                  # FAISS向量库
│   └── uploads/                  # 上传文档
│
├── tests/                        # 测试代码
│
├── scripts/                      # 脚本工具
│
├── config/                       # 配置文件
│   └── settings.py
│
├── requirements.txt              # Python依赖
└── README.md                     # 项目说明
```

## 快速访问

```bash
# 访问项目目录
cd ~/Obsidian-Vault/40-Projects/40-IntelliKnow-KMS

# 或在Windows下访问
# C:\Users\alber\Documents\Obsidian-Vault\40-Projects\40-IntelliKnow-KMS
```

## 开发启动

```bash
# 1. 进入项目目录
cd ~/Obsidian-Vault/40-Projects/40-IntelliKnow-KMS

# 2. 创建虚拟环境（首次）
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置环境变量
cp config/.env.example config/.env
# 编辑 .env 填入API密钥

# 5. 启动FastAPI后端
uvicorn app.main:app --reload --port 8000

# 6. 启动Streamlit前端（新终端）
streamlit run frontend/app.py
```

## 项目状态

- [x] 需求规格说明书完成
- [ ] 项目初始化
- [ ] 核心模块开发
- [ ] 前端集成
- [ ] 测试优化
- [ ] 交付物

---

**更新日期**: 2026-03-19