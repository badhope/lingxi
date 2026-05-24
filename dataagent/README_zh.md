# Data-Agent

智能数据助手 - 全能 AI Agent 平台

## 简介

Data-Agent 是一个功能完整的智能数据助手平台，基于 OpenManus 构建，集成了先进的文档处理能力、语音交互功能和企业级知识库系统。

## 核心功能

### Agent 与工具
- **8 种 Agent 类型**: Data, DataAnalysis, Browser, SWE, MCP, ReAct, Sandbox, ToolCall
- **15+ 真实工具**: 网页搜索、浏览器自动化、文件操作、Python 执行、数据可视化等
- **多模型支持**: OpenAI, Anthropic, Azure, Google, Ollama, PPIO 等
- **多种运行方式**: CLI、Web API、Flow 编排、MCP 协议

### 文档处理与办公自动化
- **PPT 生成**: 一键生成商务/学术/会议 PPT，支持多种模板
- **会议纪要**: 自动从文本提取议程、讨论要点、待办事项
- **文档摘要**: 抽取式/生成式摘要，关键词提取
- **工作汇报**: 自动生成日报/周报/月报
- **文本格式化**: 中英文智能排版、标点符号标准化
- **引用管理**: APA/MLA/Chicago/GB/T 7714 多格式支持
- **待办提取**: 自动识别任务、负责人、截止时间

### 数据分析
- **NL2SQL**: 自然语言转 SQL 查询
- **PDF 解析**: 智能文档解析与检索
- **可视化**: 图表生成与数据分析

## 快速开始

### 环境要求

- Python 3.10+
- pip 或 uv

### 手动安装

```bash
# 安装依赖
pip install -r requirements.txt

# 复制配置模板
cp config/config.example.toml config/config.toml

# 编辑配置文件，填入你的 API Key
# 支持 OpenAI, Anthropic, Google, Ollama 等
```

### 运行

```bash
# Web 模式（唯一入口）
python main.py
# 访问 http://localhost:8000
```

## 项目结构

```
dataagent/
├── main.py          # 统一 Web 应用入口
├── core/            # 核心模块
├── routers/         # API 路由
├── services/        # 业务逻辑
├── static/          # 静态资源
├── templates/       # HTML 模板
├── config/          # 配置文件
└── requirements.txt # 依赖文件
```

## 文档处理模块

| 模块 | 功能 | API 端点 |
|------|------|----------|
| PPT 生成 | 多模板 PPT 生成 | POST /documents/ppt/generate |
| 会议纪要 | 智能议程提取 | POST /documents/meeting-minutes |
| 文档摘要 | 关键词/摘要生成 | POST /documents/summarize |
| 工作报告 | 日报/周报/月报 | POST /documents/report |
| 待办提取 | 任务自动识别 | POST /documents/todos |
| 文本格式化 | 智能排版 | POST /documents/format |
| 引用管理 | 多格式引用 | POST /documents/citations |

## 浏览器自动化（可选）

如需使用浏览器自动化功能，安装 Playwright：

```bash
pip install playwright
playwright install chromium
```

## 许可证

Apache 2.0 License
