# data-agent

基于 FastAPI + CrewAI 的多 Agent 数据助手。

[English](./README.md) | [中文](./README_zh.md)

## 这是什么

`dataagent.main` 暴露两个端点：

- `POST /api/analyze` — 跑一个 3 个 Agent 的 CrewAI 流程（研究员 → 分析师 → 报告员）
- `POST /api/knowledge/query` — 跑一个知识库管理 Agent

另外有 `python -m dataagent.cli` 提供的交互式命令行版本，同样对应这两个流程。

剩下的代码（`core/`、`routers/`、`app/`、`services/`）是支撑层：认证、知识库、设置、会话、WebSocket、工作区文件等。

## 跑起来

```bash
cd dataagent
pip install -r requirements.txt
export OPENAI_API_KEY=sk-...
python main.py            # API 监听 :8000
# 或者
python cli.py             # 交互式命令行
```

API 文档：<http://localhost:8000/docs>
健康检查：<http://localhost:8000/health>

## 目录结构

```
dataagent/
├── main.py            # FastAPI 入口
├── cli.py             # CLI 入口
├── config.py          # pydantic-settings，从环境变量读
├── core/              # config / db / auth / knowledge / websocket / workspace / logging
├── routers/           # FastAPI 路由
├── services/          # 文档服务、润色服务
├── agents/            # CrewAI agent 工厂
├── crews/             # CrewAI crew 定义
├── app/knowledge/     # 路由实际接入的轻量知识库
├── config/            # TOML/JSON 配置示例
├── static/            # 前端资源（目前 main.py 没有挂载）
└── templates/         # 占位的 index.html
```

## 配置

配置走环境变量（见 `dataagent/config.py`），可选地从 `config/` 下的 TOML 读取。
各 provider 的示例在 `config/config.example-model-*.toml`。

## 注意事项

- `static/` 和 `templates/` 里的前端**目前没有**被 `main.py` 挂载。如果要用 UI，请直接调 JSON 端点。
- 代码里"高级"特性（浏览器自动化、MCP、多模态、Agent 市场）只有骨架，没接完整。**真正端到端能跑的就是上面那两个端点。**

## 协议

MIT
