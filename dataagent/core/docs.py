"""
DataAgent - 文档系统
提供使用指南、API 文档、开发文档等
"""
import json
import yaml
import re
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime

from core.logging import get_logger

logger = get_logger("docs")


@dataclass
class DocumentationSection:
    """文档章节"""
    id: str
    title: str
    content: str
    order: int = 0
    category: str = "general"
    tags: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=lambda: datetime.now().timestamp())


@dataclass
class Tutorial:
    """教程"""
    id: str
    title: str
    description: str
    steps: List[Dict[str, str]] = field(default_factory=list)
    category: str = "general"
    difficulty: str = "beginner"
    tags: List[str] = field(default_factory=list)


class DocumentationManager:
    """
    文档管理器
    提供使用指南、API 文档、开发文档
    """
    
    def __init__(self, docs_dir: Optional[Path] = None):
        if docs_dir is None:
            docs_dir = Path.home() / ".dataagent" / "docs"
        
        self.docs_dir = docs_dir
        self.docs_dir.mkdir(parents=True, exist_ok=True)
        
        (self.docs_dir / "guides").mkdir(exist_ok=True)
        (self.docs_dir / "api").mkdir(exist_ok=True)
        (self.docs_dir / "tutorials").mkdir(exist_ok=True)
        (self.docs_dir / "development").mkdir(exist_ok=True)
        
        self._init_default_docs()
        
        logger.info("文档管理器初始化完成")
    
    def _init_default_docs(self):
        """初始化默认文档"""
        
        # 快速开始指南
        quickstart_content = """# 快速开始指南

## 安装

首先确保你已安装 Python 3.9+，然后安装依赖：

```bash
pip install -r requirements.txt
```

## 启动服务

### 方式 1: Web 界面

```bash
cd dataagent
python -m uvicorn web_app:app --host 0.0.0.0 --port 8000
```

然后访问 http://localhost:8000

### 方式 2: 命令行界面

```bash
python cli.py
```

## 基础使用

1. 创建你的第一个对话
2. 尝试使用内置技能
3. 自定义你的 SOUL 配置

## 下一步

- 查看 API 文档了解完整功能
- 阅读教程学习高级用法
"""
        
        quickstart_file = self.docs_dir / "guides" / "quickstart.md"
        if not quickstart_file.exists():
            quickstart_file.write_text(quickstart_content, encoding="utf-8")
        
        # API 文档
        api_content = """# API 文档

## 认证

所有 API 端点（除了 /api/health）需要认证。

### 获取 Token

```bash
POST /api/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "admin"
}
```

### 使用 Token

```
Authorization: Bearer <your_token>
```

## 主要端点

### 对话

- `GET /api/conversations` - 获取对话列表
- `POST /api/conversations` - 创建对话
- `GET /api/conversations/{id}` - 获取对话详情
- `DELETE /api/conversations/{id}` - 删除对话

### 知识

- `GET /api/knowledge` - 获取知识库列表
- `POST /api/knowledge` - 添加知识
- `PUT /api/knowledge/{id}` - 更新知识
- `DELETE /api/knowledge/{id}` - 删除知识

### 技能

- `GET /api/skills` - 获取技能列表
- `POST /api/skills/{id}/execute` - 执行技能

### 工作区

- `GET /api/workspace/files` - 列出工作区文件
- `GET /api/workspace/soul` - 获取 SOUL 配置
- `PUT /api/workspace/soul` - 更新 SOUL 配置

### 媒体

- `POST /api/media/speech-to-text` - 语音识别
- `POST /api/media/text-to-speech` - 语音合成

### 仪表板

- `GET /api/dashboard/overview` - 系统总览
- `GET /api/dashboard/metrics` - 系统指标
- `GET /api/dashboard/health` - 健康检查
"""
        
        api_file = self.docs_dir / "api" / "overview.md"
        if not api_file.exists():
            api_file.write_text(api_content, encoding="utf-8")
        
        # 教程
        tutorial1_content = """# 教程 1: 创建你的第一个 SOUL

## 目标

学习如何自定义 Agent 的性格和行为方式。

## 步骤

### 1. 访问工作区

打开浏览器访问 http://localhost:8000

### 2. 导航到工作区页面

点击侧边栏的 "工作区" 或 "Workspace" 链接。

### 3. 查看当前 SOUL

你会看到一个 Markdown 格式的文档，定义了 Agent 的性格、沟通风格等。

### 4. 修改 SOUL

你可以修改以下部分：
- 名字和描述
- 沟通风格（友好/专业/简洁）
- 禁止使用的短语
- 行为规则

### 5. 保存并测试

点击保存，然后开始新的对话来体验新的 SOUL 配置。

## 提示

- 从小改动开始，逐步调整
- 测试不同的沟通风格，找到最适合你的
"""
        
        tutorial_file = self.docs_dir / "tutorials" / "create-soul.md"
        if not tutorial_file.exists():
            tutorial_file.write_text(tutorial1_content, encoding="utf-8")
        
        # 开发文档
        dev_content = """# 开发文档

## 架构概述

DataAgent 的架构分为以下几层：

```
DataAgent
├── core/        # 核心功能模块
│   ├── soul.py
│   ├── gateway.py
│   ├── skills.py
│   └── ...
├── routers/     # API 路由
│   ├── workspace.py
│   ├── skills.py
│   └── ...
├── services/    # 业务逻辑
├── static/      # 前端资源
└── templates/   # HTML 模板
```

## 核心模块

### SOUL 系统

SOUL（Structured Overview of User Logic）是 Agent 的性格定义系统。

```python
from core.soul import get_soul_manager

manager = get_soul_manager()
soul = manager.get_soul()
```

### 记忆系统

记忆系统提供长期记忆功能。

```python
from core.memory import get_memory_engine

engine = get_memory_engine()
await engine.add_memory(content="这是重要信息")
```

### 技能系统

技能系统允许你扩展 Agent 的能力。

```python
from core.skills import get_skills_engine

engine = get_skills_engine()
await engine.execute_skill("builtin_weather", {"city": "北京"})
```

## 创建插件

1. 在 `plugins/` 目录下创建新的 Python 文件
2. 实现你的插件逻辑
3. 在配置中启用它

## 贡献指南

欢迎提交 Pull Request！
"""
        
        dev_file = self.docs_dir / "development" / "overview.md"
        if not dev_file.exists():
            dev_file.write_text(dev_content, encoding="utf-8")
    
    def list_docs(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """列出文档"""
        docs = []
        
        # 读取所有文档文件
        docs_categories = ["guides", "api", "tutorials", "development"]
        
        for cat in docs_categories:
            if category and category != cat:
                continue
                
            cat_dir = self.docs_dir / cat
            if not cat_dir.exists():
                continue
                
            for file in cat_dir.glob("*.md"):
                docs.append({
                    "id": file.stem,
                    "title": self._title_from_filename(file.stem),
                    "category": cat,
                    "path": str(file),
                    "modified_at": file.stat().st_mtime
                })
        
        return sorted(docs, key=lambda x: (x["category"], x["title"]))
    
    def _title_from_filename(self, filename: str) -> str:
        """从文件名生成标题"""
        return filename.replace("-", " ").replace("_", " ").title()
    
    def get_doc(self, doc_id: str, category: str) -> Optional[Dict[str, Any]]:
        """获取文档内容"""
        doc_file = self.docs_dir / category / f"{doc_id}.md"
        
        if not doc_file.exists():
            return None
        
        content = doc_file.read_text(encoding="utf-8")
        
        # 提取标题（第一行）
        lines = content.split("\n")
        title = self._title_from_filename(doc_id)
        if lines and lines[0].startswith("# "):
            title = lines[0][2:].strip()
        
        return {
            "id": doc_id,
            "title": title,
            "content": content,
            "category": category,
            "path": str(doc_file)
        }
    
    def search_docs(self, query: str) -> List[Dict[str, Any]]:
        """搜索文档"""
        results = []
        query_lower = query.lower()
        
        all_docs = self.list_docs()
        
        for doc in all_docs:
            content = self.get_doc(doc["id"], doc["category"])
            if not content:
                continue
                
            if (query_lower in content["title"].lower() or
                query_lower in content["content"].lower()):
                results.append({
                    **doc,
                    "snippet": content["content"][:200] + "..."
                })
        
        return results
    
    def list_tutorials(self) -> List[Dict[str, Any]]:
        """列出教程"""
        return [
            doc for doc in self.list_docs()
            if doc["category"] == "tutorials"
        ]
    
    def get_quickstart(self) -> Optional[Dict[str, Any]]:
        """获取快速开始指南"""
        return self.get_doc("quickstart", "guides")
    
    def get_api_overview(self) -> Optional[Dict[str, Any]]:
        """获取 API 文档"""
        return self.get_doc("overview", "api")


_docs_manager: Optional[DocumentationManager] = None


def get_docs_manager() -> DocumentationManager:
    """获取文档管理器"""
    global _docs_manager
    if _docs_manager is None:
        _docs_manager = DocumentationManager()
    return _docs_manager
