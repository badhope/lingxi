# DATA-Agent

> Multi-Agent Intelligent Data Assistant powered by CrewAI Framework

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![CrewAI](https://img.shields.io/badge/CrewAI-0.30+-green.svg)](https://github.com/joaomdmoura/crewAI)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-red.svg)](https://fastapi.tiangolo.com/)

**[English](./README.md)** | 
**[中文](./README_zh.md)**

</div>

---

## 🌟 Introduction

DATA-Agent is a powerful intelligent data assistant built on the **CrewAI** framework. It implements a role-driven multi-agent collaboration pattern that breaks down complex tasks into collaborative workflows between specialized agents.

### Key Features

- 🤖 **Multi-Agent Collaboration System** - Each agent has unique roles, goals, and specialized skills
- 📊 **Intelligent Data Analysis** - Automatically research, analyze, and report on data
- 📚 **Knowledge Base Q&A** - Intelligent retrieval and answering of knowledge base questions
- 🔌 **RESTful API** - Complete HTTP API interface
- 💻 **CLI Tool** - User-friendly interactive command-line interface
- 📄 **Document Processing** - Support for PDF, PPT, DOC, and other formats

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- OpenAI API Key (or compatible API)
- Support for Anthropic, Azure OpenAI, and other providers

### Installation

#### 1. Clone the Repository

```bash
git clone https://github.com/badhope/DATA-Agent.git
cd DATA-Agent/dataagent
```

#### 2. Install Dependencies

```bash
# Full dependencies
pip install -r requirements.txt

# Or minimal dependencies
pip install -r requirements-minimal.txt
```

#### 3. Configure Environment Variables

Copy the example configuration:

```bash
cp .env.example .env
```

Edit the `.env` file with your API credentials:

```env
# OpenAI API Key (Required)
OPENAI_API_KEY=sk-your-actual-api-key-here

# Model Configuration
DEFAULT_MODEL=gpt-4-turbo
DEFAULT_TEMPERATURE=0.7

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Logging Configuration
LOG_LEVEL=INFO

# Debug Mode
DEBUG=true
```

#### 4. Start the Application

**Option 1: Start API Service**

```bash
python main.py
```

Then access:
- API Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/health
- Homepage: http://localhost:8000

**Option 2: Use CLI Tool**

```bash
python cli.py
```

**Option 3: Programmatic Usage**

```python
from crews.data_analysis import run_data_analysis
from agents.base_agent import get_llm

llm = get_llm()
result = run_data_analysis("How to improve sales performance", llm)
print(result)
```

---

## 🏗️ Project Structure

```
DATA-Agent/
├── dataagent/                        # Main application directory
│   ├── agents/                       # Agent definitions
│   │   ├── __init__.py
│   │   └── base_agent.py           # Base agent creation utilities
│   │
│   ├── crews/                       # Crew configurations
│   │   ├── __init__.py
│   │   ├── data_analysis.py        # Data analysis crew
│   │   └── knowledge_team.py       # Knowledge base crew
│   │
│   ├── tools/                       # Tool collections (extensible)
│   │   └── __init__.py
│   │
│   ├── app/                         # Core functionality
│   │   ├── document/              # Document processing
│   │   ├── knowledge/             # Knowledge base system
│   │   └── utils/                 # Utility functions
│   │
│   ├── core/                        # Core services (simplified)
│   │   ├── config.py              # Configuration management
│   │   ├── database.py            # Database operations
│   │   └── ...
│   │
│   ├── routers/                     # API routes
│   │   ├── api.py                 # CrewAI execution API
│   │   ├── auth.py                # Authentication
│   │   ├── conversations.py       # Conversations
│   │   └── ...
│   │
│   ├── services/                   # Business services
│   │   ├── document_service.py
│   │   └── polish_service.py
│   │
│   ├── config/                     # Configuration files
│   ├── data/                       # Data directory
│   ├── static/                     # Static assets
│   ├── templates/                  # Template files
│   │
│   ├── config.py                  # Unified configuration
│   ├── main.py                    # API entry point
│   ├── cli.py                     # CLI entry point
│   ├── requirements.txt           # Dependencies
│   └── README.md                  # This file
│
├── .gitignore                     # Git ignore rules
├── LICENSE                        # MIT License
├── README.md                      # English README
├── README_zh.md                  # Chinese README
└── pyproject.toml               # Python project configuration
```

---

## 💡 Core Features

### 1. Data Analysis Crew

Three specialized agents collaborate to complete analysis:

**Workflow:**
```
User Query → Researcher Agent → Analyst Agent → Writer Agent → Complete Report
```

**Agent Roles:**

- 📚 **Researcher**
  - Goal: Research the problem deeply and collect relevant data
  - Skills: Search, data organization, case collection

- 📊 **Analyst**
  - Goal: Analyze data and discover insights
  - Skills: Statistical analysis, trend identification, visualization recommendations

- ✍️ **Writer**
  - Goal: Transform analysis results into professional reports
  - Skills: Copywriting, structure design, chart descriptions

**Usage Example:**
```python
from crews.data_analysis import create_data_analysis_crew

crew = create_data_analysis_crew()
result = crew.kickoff(inputs={"query": "Analyze e-commerce trends in 2024"})
print(result)
```

### 2. Knowledge Base Q&A Crew

**Agent Roles:**

- 📖 **Knowledge Manager**
  - Goal: Quickly retrieve relevant knowledge and provide accurate answers
  - Skills: Document retrieval, knowledge organization, answer generation

**Usage Example:**
```python
from crews.knowledge_team import create_knowledge_crew

crew = create_knowledge_crew()
result = crew.kickoff(inputs={"question": "How to clean data with Python?"})
print(result)
```

---

## 🔧 API Usage

### Data Analysis Endpoint

```bash
POST /api/analyze
Content-Type: application/json

{
  "query": "How to improve business growth",
  "model": "gpt-4-turbo",
  "temperature": 0.7
}
```

**Response:**
```json
{
  "success": true,
  "result": "# Business Growth Analysis Report\n\n## Executive Summary\n..."
}
```

### Knowledge Base Query Endpoint

```bash
POST /api/knowledge/query
Content-Type: application/json

{
  "question": "How to perform data analysis with Python",
  "model": "gpt-4-turbo"
}
```

**Response:**
```json
{
  "success": true,
  "result": "# Python Data Analysis Guide\n\n## Recommended Core Libraries\n..."
}
```

### Health Check

```bash
GET /health
GET /api/health
```

---

## 🛠️ Tech Stack

| Category | Technology |
|----------|------------|
| **Web Framework** | FastAPI |
| **AI Framework** | CrewAI, LangChain |
| **LLM** | OpenAI GPT, Anthropic Claude |
| **Vector Database** | FAISS |
| **Knowledge Base** | LlamaIndex |
| **Document Processing** | pdfplumber, python-pptx, python-docx |
| **CLI Interface** | Rich |
| **Data Processing** | Pandas, NumPy |
| **Web Server** | Uvicorn |

---

## 📖 Configuration

### Multi-Model Support

DATA-Agent supports multiple LLM providers:

- OpenAI GPT-4 / GPT-3.5
- Anthropic Claude
- Azure OpenAI
- And more (through configuration)

### Configuration File

Detailed configuration can be done in `config/config.toml`:

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

## 🎯 Use Cases

### 1. Business Analysis
- Market trend analysis
- Competitive intelligence gathering
- Business data insights
- Investment suggestion generation

### 2. Knowledge Management
- Intelligent document Q&A
- Knowledge base construction
- Information extraction and organization
- Knowledge graph applications

### 3. Document Processing
- Meeting minutes generation
- Automatic report writing
- Document format conversion
- Data analysis visualization

### 4. Software Development (Optional Extension)
- Code analysis and refactoring
- Automatic documentation generation
- Bug analysis and fix suggestions

---

## 🔄 Project History

### v2.0 (Current Version)
- ✅ Refactored to CrewAI-based architecture
- ✅ Removed redundant code and experimental features
- ✅ Simplified project structure for better maintainability
- ✅ Preserved core document processing and knowledge base features
- ✅ Added CLI interactive tool

### v1.x (Legacy Version)
- Old architecture, feature-rich but complex
- Included Docker sandbox and other extended features
- Multi-agent system prototype
- Archived for reference

---

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

Please read [CONTRIBUTING.md](./CONTRIBUTING.md) for details on our code of conduct and the submission process.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.

---

## 💬 Support & Feedback

For questions or suggestions:

- Submit an Issue
- Send a Pull Request
- Join the Discussion

---

## 🙏 Acknowledgments

Special thanks to these open source projects:

- [CrewAI](https://github.com/joaomdmoura/crewAI) - Excellent multi-agent collaboration framework
- [FastAPI](https://fastapi.tiangolo.com/) - High-performance web framework
- [LangChain](https://langchain.com/) - LLM application framework
- [FAISS](https://github.com/facebookresearch/faiss) - Efficient vector search library

---

<div align="center">

**Built with ❤️ by DATA-Agent Team**

</div>
