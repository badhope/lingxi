# DataAgent 统一架构说明

## 🎯 架构整理完成！

已成功执行方案一，统一了项目架构！

---

## 📁 当前项目结构

```
dataagent/
├── main.py                          # ✅ 统一入口（唯一！）
├── core/                           # 核心模块
│   ├── __init__.py
│   ├── config.py
│   ├── config_manager.py
│   ├── database.py
│   ├── database_compat.py
│   ├── plugins_builtin.py
│   ├── plugins_extended.py
│   ├── websocket.py
│   └── ... (其他核心文件)
├── routers/                        # API 路由
│   ├── auth.py
│   ├── settings.py
│   ├── knowledge.py
│   └── ... (其他路由)
├── services/                       # 业务服务
│   ├── agent_service.py
│   ├── polish_service.py
│   ├── intent_router.py
│   └── ... (其他服务)
├── static/                        # ✅ 静态资源（唯一！）
│   ├── css/
│   │   ├── app.css
│   │   ├── chat.css
│   │   ├── modern.css
│   │   └── ... (其他 CSS)
│   └── js/
│       ├── app.js              # ✅ 已修复语法错误！
│       ├── conversations.js
│       ├── knowledge.js
│       └── ... (其他 JS)
├── templates/                     # ✅ HTML 模板（唯一！）
│   ├── index.html              # 主聊天界面
│   ├── logs.html
│   └── plugins.html
├── web_archive/                   # ⏳ 已归档（旧 web/ 目录
│   └── ... (旧的 web/ 目录内容)
├── config/                        # 配置文件
│   ├── config.toml
│   └── config.example.toml
├── data/                          # 数据存储
├── .env                          # 环境变量
├── requirements.txt               # 依赖
└── ... (其他文件)
```

---

## 🚀 快速启动

### 唯一的启动方式！

```bash
cd /workspace/Data-Agent/dataagent
python main.py
```

或者使用 uvicorn：

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**访问地址：** http://localhost:8000

---

## 📋 已完成的整理

### ✅ 1. 统一了入口文件
- **删除：** start.py, start_simple.py, core_app.py, run.py, data_ai_full.py
- **保留：** main.py（原 web_app.py）
- **现在只有一个入口文件了！

### ✅ 2. 整理了目录结构
- **归档：** web/ → web_archive/
- **保留：** static/ 和 templates/
- **现在只有一套前端目录！

### ✅ 3. 修复了问题
- 修复了 [static/js/app.js](file:///workspace/Data-Agent/dataagent/static/js/app.js) 的语法错误
- 修复了 [core/plugins_builtin.py](file:///workspace/Data-Agent/dataagent/core/plugins_builtin.py) 的 eval 安全问题
- 修复了 [core/database.py](file:///workspace/Data-Agent/dataagent/core/database.py) 的 Pydantic 序列化
- 修复了 [core/websocket.py](file:///workspace/Data-Agent/dataagent/core/websocket.py) 的字典迭代问题
- 修复了 [core/config_manager.py](file:///workspace/Data-Agent/dataagent/core/config_manager.py) 的容器兼容性

---

## 🔧 配置说明

### 配置文件位置

1. **环境变量：** [.env](file:///workspace/Data-Agent/dataagent/.env)
2. **主配置：** [config/config.toml](file:///workspace/Data-Agent/dataagent/config/config.toml)

### 配置 API Key

编辑 [config/config.toml：

```toml
[llm]
model = "qwen-plus-latest"
base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
api_key = "你的真实API密钥"  # ← 替换这个！
```

---

## 📚 相关文档

- [启动指南](file:///workspace/Data-Agent/STARTUP_GUIDE.md)
- [问题修复总结](file:///workspace/Data-Agent/ISSUE_FIX_SUMMARY.md)
- [完整问题报告](file:///workspace/Data-Agent/COMPREHENSIVE_ISSUE_REPORT.md)
- [前端修复报告](file:///workspace/Data-Agent/FRONTEND_FIX_REPORT.md)

---

## 📌 重要提示

1. **只使用 `main.py` 启动，不要用其他文件！
2. 如果需要查看旧的 web/ 架构，查看 `web_archive/`
3. API 端点：`/ws`（WebSocket），`/api/health`（健康检查）
4. 静态文件路径：`/static/`

---

**整理完成时间：** 2026-05-24
**架构状态：** ✅ 统一完成！
