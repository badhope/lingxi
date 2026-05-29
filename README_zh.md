# DATA-Agent

> 基于 CrewAI 框架的多Agent智能数据助手

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![CrewAI](https://img.shields.io/badge/CrewAI-0.30+-green.svg)](https://github.com/joaomdmoura/crewAI)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-red.svg)](https://fastapi.tiangolo.com/)

**[English](./README.md)** | 
**[中文](./README_zh.md)**

</div>

---

## 🌟 项目简介

DATA-Agent 是一个功能强大的智能数据助手，基于 **CrewAI** 框架构建。它采用角色驱动的多Agent协作模式，将复杂任务分解为多个专业化Agent之间的协作工作流程。

### 核心特点

- 🤖 **多Agent协作系统** - 每个Agent都有独特的角色、目标和专业技能
- 📊 **智能数据分析** - 自动完成数据研究、分析和报告撰写
- 📚 **知识库问答** - 智能检索和回答知识库问题
- 🔌 **RESTful API** - 提供完整的HTTP API接口
- 💻 **命令行工具** - 友好的交互式命令行界面
- 📄 **文档处理** - 支持PDF、PPT、DOC等多种格式文档处理

---

## 🚀 快速开始

### 环境要求

- Python 3.10 或更高版本
- OpenAI API Key（或兼容的API）
- 支持 Anthropic、Azure OpenAI 等多种提供商

### 安装步骤

#### 1. 克隆项目

```bash
git clone https://github.com/badhope/DATA-Agent.git
cd DATA-Agent/dataagent
```

#### 2. 安装依赖

```bash
# 完整依赖
pip install -r requirements.txt

# 最小依赖
pip install -r requirements-minimal.txt
```

#### 3. 配置环境变量

复制配置示例：

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入你的API密钥：

```env
# OpenAI API Key（必需）
OPENAI_API_KEY=sk-your-actual-api-key-here

# 模型配置
DEFAULT_MODEL=gpt-4-turbo
DEFAULT_TEMPERATURE=0.7

# API 配置
API_HOST=0.0.0.0
API_PORT=8000

# 日志配置
LOG_LEVEL=INFO

# 调试模式
DEBUG=true
```

#### 4. 启动项目

**方式一：启动API服务**

```bash
python main.py
```

然后访问：
- API 文档：http://localhost:8000/docs
- 健康检查：http://localhost:8000/health
- 主页：http://localhost:8000

**方式二：使用命令行工具**

```bash
python cli.py
```

**方式三：编程使用**

```python
from crews.data_analysis import run_data_analysis
from agents.base_agent import get_llm

llm = get_llm()
result = run_data_analysis("如何提升销售业绩", llm)
print(result)
```

---

## 🏗️ 项目结构

```
DATA-Agent/
├── dataagent/                        # 主应用目录
│   ├── agents/                       # Agent 定义
│   │   ├── __init__.py
│   │   └── base_agent.py           # 基础Agent创建工具
│   │
│   ├── crews/                       # Crew 配置
│   │   ├── __init__.py
│   │   ├── data_analysis.py        # 数据分析团队
│   │   └── knowledge_team.py       # 知识库团队
│   │
│   ├── tools/                       # 工具集（可扩展）
│   │   └── __init__.py
│   │
│   ├── app/                         # 核心功能
│   │   ├── document/              # 文档处理
│   │   ├── knowledge/             # 知识库系统
│   │   └── utils/                 # 工具函数
│   │
│   ├── core/                        # 核心服务（精简）
│   │   ├── config.py              # 配置管理
│   │   ├── database.py            # 数据库操作
│   │   └── ...
│   │
│   ├── routers/                     # API 路由
│   │   ├── api.py                 # CrewAI执行API
│   │   ├── auth.py                # 认证
│   │   ├── conversations.py       # 对话
│   │   └── ...
│   │
│   ├── services/                   # 业务服务
│   │   ├── document_service.py
│   │   └── polish_service.py
│   │
│   ├── config/                     # 配置文件
│   ├── data/                       # 数据目录
│   ├── static/                     # 静态资源
│   ├── templates/                  # 模板文件
│   │
│   ├── config.py                  # 统一配置
│   ├── main.py                    # API入口
│   ├── cli.py                     # CLI入口
│   ├── requirements.txt           # 依赖列表
│   └── README.md                  # 项目文档
│
├── .gitignore                     # Git忽略规则
├── LICENSE                        # MIT许可证
├── README.md                      # 英文文档
├── README_zh.md                  # 中文文档
└── pyproject.toml                # Python项目配置
```

---

## 💡 核心功能

### 1. 数据分析团队

三个专业Agent协作完成分析：

**工作流程：**
```
用户问题 → 研究员Agent → 分析师Agent → 报告作家Agent → 完整报告
```

**Agent 角色：**

- 📚 **研究员 (Researcher)**
  - 目标：深入研究问题，收集相关数据
  - 技能：搜索、数据整理、案例收集

- 📊 **分析师 (Analyst)**
  - 目标：分析数据，发现洞见
  - 技能：统计分析、趋势识别、可视化建议

- ✍️ **报告作家 (Writer)**
  - 目标：将分析结果转化为专业报告
  - 技能：文案写作、结构设计、图表描述

**使用示例：**
```python
from crews.data_analysis import create_data_analysis_crew

crew = create_data_analysis_crew()
result = crew.kickoff(inputs={"query": "分析2024年电商行业趋势"})
print(result)
```

### 2. 知识库问答团队

**Agent 角色：**

- 📖 **知识库管理员 (Knowledge Manager)**
  - 目标：快速检索相关知识，提供准确答案
  - 技能：文档检索、知识组织、答案生成

**使用示例：**
```python
from crews.knowledge_team import create_knowledge_crew

crew = create_knowledge_crew()
result = crew.kickoff(inputs={"question": "如何使用Python进行数据清洗？"})
print(result)
```

---

## 🔧 API 使用说明

### 数据分析接口

```bash
POST /api/analyze
Content-Type: application/json

{
  "query": "如何提升业务增长",
  "model": "gpt-4-turbo",
  "temperature": 0.7
}
```

**响应：**
```json
{
  "success": true,
  "result": "# 业务增长分析报告\n\n## 执行摘要\n..."
}
```

### 知识库查询接口

```bash
POST /api/knowledge/query
Content-Type: application/json

{
  "question": "如何使用Python进行数据分析",
  "model": "gpt-4-turbo"
}
```

**响应：**
```json
{
  "success": true,
  "result": "# Python数据分析指南\n\n## 核心库推荐\n..."
}
```

### 健康检查

```bash
GET /health
GET /api/health
```

---

## 🛠️ 技术栈

| 类别 | 技术 |
|------|------|
| **Web框架** | FastAPI |
| **AI框架** | CrewAI, LangChain |
| **LLM** | OpenAI GPT, Anthropic Claude |
| **向量数据库** | FAISS |
| **知识库** | LlamaIndex |
| **文档处理** | pdfplumber, python-pptx, python-docx |
| **CLI界面** | Rich |
| **数据处理** | Pandas, NumPy |
| **Web服务器** | Uvicorn |

---

## 📖 配置说明

### 多模型支持

DATA-Agent 支持多种LLM提供商：

- OpenAI GPT-4 / GPT-3.5
- Anthropic Claude
- Azure OpenAI
- 更多（通过配置）

### 配置文件

在 `config/config.toml` 中可以进行详细配置：

```toml
[core]
name = "DATA-Agent"
version = "2.0.0"

[llm]
provider = "openai"
model = "gpt-4-turbo"
temperature = 0.7
```

---

## 🎯 使用场景

### 1. 商业分析
- 市场趋势分析
- 竞争情报收集
- 业务数据洞察
- 投资建议生成

### 2. 知识管理
- 文档智能问答
- 知识库构建
- 信息抽取与整理
- 知识图谱应用

### 3. 文档处理
- 会议纪要生成
- 报告自动撰写
- 文档格式转换
- 数据分析可视化

### 4. 软件开发（可选扩展）
- 代码分析与重构
- 文档自动生成
- Bug分析与修复建议

---

## 🔄 项目历史

### v2.0（当前版本）
- ✅ 重构为基于 CrewAI 的架构
- ✅ 删除冗余代码和实验性功能
- ✅ 简化项目结构，提升可维护性
- ✅ 保留核心文档处理和知识库功能
- ✅ 新增 CLI 交互式工具

### v1.x（旧版本）
- 旧架构，功能丰富但复杂
- 包含 Docker 沙箱等扩展功能
- 多 Agent 系统原型
- 已归档参考

---

## 🤝 贡献指南

我们欢迎贡献！请遵循以下步骤：

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

请阅读 [CONTRIBUTING.md](./CONTRIBUTING.md) 了解我们的行为准则和提交流程。

---

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](./LICENSE) 文件。

---

## 💬 支持与反馈

如有问题或建议：

- 提交 Issue
- 发送 Pull Request
- 加入讨论

---

## 🙏 致谢

特别感谢以下开源项目：

- [CrewAI](https://github.com/joaomdmoura/crewAI) - 优秀的多Agent协作框架
- [FastAPI](https://fastapi.tiangolo.com/) - 高性能Web框架
- [LangChain](https://langchain.com/) - LLM应用框架
- [FAISS](https://github.com/facebookresearch/faiss) - 高效向量检索库

---

<div align="center">

**由 DATA-Agent 团队用 ❤️ 构建**

</div>
