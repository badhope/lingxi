# DATA Agent Platform

<div align="center">

**Build, deploy, and scale production-ready AI agents**

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.x-3178C6.svg)](https://www.typescriptlang.org/)
[![License](https://img.shields.io/badge/License-Apache%202.0-green.svg)](LICENSE)

[Features](#-features) • [Quick Start](#-quick-start) • [Architecture](#️-architecture) • [Deployment](#-deployment) • [Contributing](#-contributing)

</div>

---

## 🚀 Overview

**DATA** is a production-grade LLM application development platform designed for teams building AI-powered products. From simple chatbots to complex multi-agent workflows, DATA provides the visual tools, infrastructure, and runtime to go from prototype to production in hours, not weeks.

### What Makes DATA Different?

- **No-Code to Pro-Code** — Design workflows visually, extend with code when you need more power
- **Production-Ready** — Built-in observability, error handling, and performance monitoring
- **Model Agnostic** — 100+ LLM providers, embed, and rerank models out of the box
- **Enterprise Secure** — RBAC, SSO, audit logs, and data isolation

---

## ✨ Features

### AI Agent Platform
| Feature | Description |
|---------|-------------|
| **Visual Workflow Builder** | Drag-and-drop pipeline design with real-time preview |
| **Multi-Agent Orchestration** | Chain, route, and parallel-execute AI agents |
| **RAG Pipeline** | Built-in document ingestion, chunking, embedding, and retrieval |
| **50+ Built-in Tools** | Web search, code execution, image generation, API connectors |
| **Plugin Ecosystem** | Install community plugins or build your own |
| **Human-in-the-Loop** | Pause workflows for human approval or input |
| **Auto-Scaling** | Horizontal scaling for production workloads |

### Model Management
- **100+ Providers**: OpenAI, Anthropic, Google, AWS Bedrock, Azure, local LLMs (Ollama/Llama.cpp)
- **Model Fallbacks**: Define fallback chains for reliability
- **Load Balancing**: Distribute requests across model instances
- **Usage Tracking**: Monitor token consumption and costs

### Observability
- **Real-time Monitoring**: Live workflow execution traces
- **Logging**: Structured logs with search and filtering
- **Analytics**: Usage patterns, response times, error rates
- **Integration**: OpenTelemetry, Langfuse, custom exporters

### Developer Experience
- **REST API**: Full API access for custom integrations
- **SDKs**: Python, Node.js, and CLI toolkit
- **DSL Export**: Version-controlled app definitions
- **CI/CD Ready**: Docker-based deployment pipeline

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Web Frontend (Next.js)              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │ Workflow │ │  Agent   │ │ Dataset  │ │ Settings │  │
│  │  Studio  │ │  Config  │ │ Manager  │ │   Page   │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘  │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTP/WebSocket
┌──────────────────────▼──────────────────────────────────┐
│                    API Server (FastAPI)                  │
│  ┌─────────────┐  ┌────────────┐  ┌──────────────────┐ │
│  │  Workflow   │  │   Agent    │  │  Model Runtime   │ │
│  │   Engine    │  │  Runner    │  │    Manager       │ │
│  ├─────────────┤  ├────────────┤  ├──────────────────┤ │
│  │ RAG Service │  │ Tool System│  │ Plugin Registry  │ │
│  └─────────────┘  └────────────┘  └──────────────────┘ │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│                    Data & Cache Layer                    │
│  ┌────────────┐ ┌────────────┐ ┌──────────────────┐    │
│  │ PostgreSQL │ │   Redis    │ │  Vector DB       │    │
│  │            │ │            │ │  (multi-engine)  │    │
│  └────────────┘ └────────────┘ └──────────────────┘    │
└──────────────────────────────────────────────────────────┘
```

### Data Flow

```
User Request → API Gateway → Auth Check → Workflow Engine
    ↓
Agent Selection → Context Building → LLM Invocation
    ↓
Tools Execution ← RAG Retrieval ← Knowledge Base
    ↓
Response Assembly → Streaming → User
```

---

## 🚀 Quick Start

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) & [Docker Compose](https://docs.docker.com/compose/install/)
- 4GB+ RAM recommended

### One-Click Launch

```bash
# Clone the repository
git clone https://github.com/your-org/data-agent
cd data-agent

# Start all services
cd docker
docker compose up -d

# Access the platform
# Web UI:    http://localhost:3000
# API:       http://localhost:5001
# Swagger:   http://localhost:5001/docs
```

### Manual Setup (Development)

```bash
# Backend
cd api
cp .env.example .env
uv sync
uv run flask db upgrade
uv run python app.py

# Frontend
cd web
cp .env.example .env.local
pnpm install
pnpm dev
```

---

## 🛠️ Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATA_BIND_ADDRESS` | `0.0.0.0` | API server bind address |
| `DATA_PORT` | `5001` | API server port |
| `SECRET_KEY` | (required) | App encryption key |
| `DB_USERNAME` | `data` | PostgreSQL username |
| `DB_PASSWORD` | `data123456` | PostgreSQL password |
| `DB_HOST` | `localhost` | PostgreSQL host |
| `DB_PORT` | `5432` | PostgreSQL port |
| `REDIS_HOST` | `localhost` | Redis host |
| `REDIS_PORT` | `6379` | Redis port |

---

## 📚 Documentation

- [User Guide](https://docs.data.ai) — Getting started, tutorials, best practices
- [API Reference](https://docs.data.ai/api) — Full REST API documentation  
- [Plugin Development](https://docs.data.ai/plugins) — Building custom plugins
- [Contributor Guide](https://docs.data.ai/contributing) — How to contribute

---

## 🔌 Plugins & Extensions

DATA supports a rich plugin ecosystem:

| Type | Examples |
|------|----------|
| **Model Providers** | OpenAI, Anthropic, Ollama, AWS Bedrock, Azure |
| **Tools** | Web search, Calculator, Code execution, Image gen |
| **Vector Stores** | Qdrant, Milvus, Weaviate, Pinecone |
| **Document Loaders** | PDF, HTML, Notion, Confluence, S3 |
| **Observability** | Langfuse, OpenTelemetry, Sentry |

---

## 🧪 Testing

```bash
# Backend tests
cd api
uv run pytest tests/unit_tests/ -v

# Frontend tests
cd web
pnpm test

# E2E tests
pnpm test:e2e
```

---

## 🤝 Contributing

We welcome contributions! See our [Contributing Guide](CONTRIBUTING.md) for details.

1. Fork the repo
2. Create your feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing`)
5. Open a Pull Request

### Code of Conduct

Please read our [Code of Conduct](CODE_OF_CONDUCT.md).

---

## 📄 License

This project is licensed under the **Apache License 2.0** — see the [LICENSE](LICENSE) file for details.

---

<div align="center">
  <sub>Built with ❤️ by the DATA Team</sub>
</div>
