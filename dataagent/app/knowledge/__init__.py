"""app.knowledge - 文件加载 + 关键词检索的轻量知识库

RAG 完整能力见 core.knowledge；本目录是 router/knowledge.py 实际接入的版本。
"""

from .knowledge_base import KnowledgeBase, KnowledgeManager
from .qa_engine import ConversationalQAEngine, QAEngine
from .vector_store import DocumentChunk, SimpleVectorStore, VectorStore

__all__ = [
    "KnowledgeBase",
    "KnowledgeManager",
    "QAEngine",
    "ConversationalQAEngine",
    "VectorStore",
    "SimpleVectorStore",
    "DocumentChunk",
]
