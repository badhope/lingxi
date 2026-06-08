"""
Knowledge base + RAG framework: document storage, chunking, embedding, search.
Abstract VectorStore + EmbeddingService interfaces; in-memory implementation included.
"""
import asyncio
import hashlib
import json
import threading
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Optional, Any, Union, Tuple

from pydantic import BaseModel, Field

from .config import config_manager
from .logging import db_logger


class Document(BaseModel):
    """文档模型"""
    id: str = Field(..., description="文档ID")
    title: str = Field(..., description="文档标题")
    content: str = Field(..., description="文档内容")
    source: Optional[str] = Field(None, description="文档来源")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="文档元数据")
    created_at: str = Field(..., description="创建时间")
    updated_at: str = Field(..., description="更新时间")
    chunk_ids: List[str] = Field(default_factory=list, description="关联的文本块ID")
    
    @classmethod
    def from_file(cls, file_path: Path) -> 'Document':
        """从文件创建文档"""
        from datetime import datetime
        now = datetime.now().isoformat()
        
        # 读取文件内容
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except:
            content = ""
        
        # 生成文档ID
        doc_id = hashlib.md5(f"{file_path.name}_{now}".encode()).hexdigest()
        
        return cls(
            id=doc_id,
            title=file_path.name,
            content=content,
            source=str(file_path),
            created_at=now,
            updated_at=now
        )


class DocumentChunk(BaseModel):
    """文档文本块"""
    id: str = Field(..., description="文本块ID")
    document_id: str = Field(..., description="所属文档ID")
    content: str = Field(..., description="文本内容")
    embedding: Optional[List[float]] = Field(None, description="向量嵌入")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")
    chunk_index: int = Field(0, description="在文档中的位置索引")


class SearchResult(BaseModel):
    """搜索结果"""
    chunk_id: str = Field(..., description="文本块ID")
    document_id: str = Field(..., description="文档ID")
    content: str = Field(..., description="匹配内容")
    score: float = Field(..., description="匹配分数")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")


class VectorStore(ABC):
    """向量存储抽象基类"""
    
    @abstractmethod
    async def add_vectors(self, vectors: List[List[float]], chunk_ids: List[str]):
        """添加向量"""
        pass
    
    @abstractmethod
    async def search(self, query_vector: List[float], top_k: int = 5) -> List[Tuple[str, float]]:
        """搜索相似向量"""
        pass
    
    @abstractmethod
    async def delete_vectors(self, chunk_ids: List[str]):
        """删除向量"""
        pass
    
    @abstractmethod
    async def get_vector(self, chunk_id: str) -> Optional[List[float]]:
        """获取向量"""
        pass
    
    @abstractmethod
    async def clear(self):
        """清空所有向量"""
        pass


class MemoryVectorStore(VectorStore):
    """基于内存的向量存储"""
    
    def __init__(self):
        self._vectors: Dict[str, List[float]] = {}
        self._lock = threading.RLock()
    
    async def add_vectors(self, vectors: List[List[float]], chunk_ids: List[str]):
        """添加向量"""
        with self._lock:
            for chunk_id, vector in zip(chunk_ids, vectors):
                self._vectors[chunk_id] = vector
    
    async def search(self, query_vector: List[float], top_k: int = 5) -> List[Tuple[str, float]]:
        """搜索相似向量（使用余弦相似度）"""
        with self._lock:
            if not self._vectors:
                return []
            
            # 计算余弦相似度
            results = []
            for chunk_id, vector in self._vectors.items():
                similarity = self._cosine_similarity(query_vector, vector)
                results.append((chunk_id, similarity))
            
            # 按相似度排序并取前k个
            results.sort(key=lambda x: x[1], reverse=True)
            return results[:top_k]
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算余弦相似度"""
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    async def delete_vectors(self, chunk_ids: List[str]):
        """删除向量"""
        with self._lock:
            for chunk_id in chunk_ids:
                if chunk_id in self._vectors:
                    del self._vectors[chunk_id]
    
    async def get_vector(self, chunk_id: str) -> Optional[List[float]]:
        """获取向量"""
        with self._lock:
            return self._vectors.get(chunk_id)
    
    async def clear(self):
        """清空所有向量"""
        with self._lock:
            self._vectors = {}


class EmbeddingService(ABC):
    """嵌入服务抽象基类"""
    
    @abstractmethod
    async def embed(self, texts: List[str]) -> List[List[float]]:
        """将文本转换为向量嵌入"""
        pass
    
    @abstractmethod
    def get_dimension(self) -> int:
        """获取嵌入向量维度"""
        pass


class SimpleEmbeddingService(EmbeddingService):
    """简单的嵌入服务（用于演示）"""
    
    def __init__(self):
        self._dimension = 384  # 默认维度
    
    async def embed(self, texts: List[str]) -> List[List[float]]:
        """简单的字符频率嵌入（仅用于演示）"""
        results = []
        for text in texts:
            # 创建简单的字符频率向量
            vector = []
            for i in range(self._dimension):
                if i < len(text):
                    vector.append(ord(text[i]) / 255)
                else:
                    vector.append(0.0)
            results.append(vector)
        return results
    
    def get_dimension(self) -> int:
        """获取嵌入向量维度"""
        return self._dimension


class KnowledgeBase(BaseModel):
    """知识库"""
    
    id: str = Field(..., description="知识库ID")
    name: str = Field(..., description="知识库名称")
    description: Optional[str] = Field(None, description="知识库描述")
    documents: Dict[str, Document] = Field(default_factory=dict, description="文档集合")
    chunks: Dict[str, DocumentChunk] = Field(default_factory=dict, description="文本块集合")
    vector_store: VectorStore = Field(default_factory=MemoryVectorStore, description="向量存储")
    embedding_service: EmbeddingService = Field(default_factory=SimpleEmbeddingService, description="嵌入服务")
    chunk_size: int = Field(500, description="文本块大小")
    chunk_overlap: int = Field(50, description="文本块重叠大小")
    
    class Config:
        arbitrary_types_allowed = True
    
    async def add_document(self, content: str, title: str, source: Optional[str] = None) -> str:
        """添加文档"""
        from datetime import datetime
        now = datetime.now().isoformat()
        
        # 创建文档
        doc_id = hashlib.md5(f"{title}_{now}".encode()).hexdigest()
        document = Document(
            id=doc_id,
            title=title,
            content=content,
            source=source,
            created_at=now,
            updated_at=now
        )
        
        # 分割文档为文本块
        chunks = self._split_into_chunks(content, doc_id)
        
        # 添加到知识库
        self.documents[doc_id] = document
        
        for chunk in chunks:
            self.chunks[chunk.id] = chunk
            document.chunk_ids.append(chunk.id)
        
        # 生成嵌入并添加到向量存储
        chunk_contents = [chunk.content for chunk in chunks]
        embeddings = await self.embedding_service.embed(chunk_contents)
        chunk_ids = [chunk.id for chunk in chunks]
        await self.vector_store.add_vectors(embeddings, chunk_ids)
        
        db_logger.info(f"Document added to knowledge base '{self.name}': {title}")
        return doc_id
    
    async def add_file(self, file_path: Path) -> str:
        """从文件添加文档"""
        document = Document.from_file(file_path)
        return await self.add_document(document.content, document.title, str(file_path))
    
    def _split_into_chunks(self, content: str, document_id: str) -> List[DocumentChunk]:
        """将文档分割为文本块"""
        chunks = []
        content_length = len(content)
        chunk_index = 0
        
        for i in range(0, content_length, self.chunk_size - self.chunk_overlap):
            end = min(i + self.chunk_size, content_length)
            chunk_content = content[i:end]
            
            # 避免在句子中间切割（简单实现）
            if end < content_length:
                last_period = chunk_content.rfind('.')
                if last_period > len(chunk_content) - 50:
                    chunk_content = chunk_content[:last_period + 1]
                    end = i + len(chunk_content)
            
            chunk_id = hashlib.md5(f"{document_id}_{chunk_index}".encode()).hexdigest()
            chunk = DocumentChunk(
                id=chunk_id,
                document_id=document_id,
                content=chunk_content,
                chunk_index=chunk_index
            )
            chunks.append(chunk)
            chunk_index += 1
        
        return chunks
    
    async def search(self, query: str, top_k: int = 5) -> List[SearchResult]:
        """搜索知识库"""
        # 生成查询向量
        query_embedding = await self.embedding_service.embed([query])
        
        if not query_embedding:
            return []
        
        # 在向量存储中搜索
        results = await self.vector_store.search(query_embedding[0], top_k)
        
        # 构建搜索结果
        search_results = []
        for chunk_id, score in results:
            if chunk_id in self.chunks:
                chunk = self.chunks[chunk_id]
                search_results.append(SearchResult(
                    chunk_id=chunk.id,
                    document_id=chunk.document_id,
                    content=chunk.content,
                    score=score,
                    metadata=chunk.metadata
                ))
        
        return search_results
    
    async def delete_document(self, doc_id: str):
        """删除文档"""
        if doc_id not in self.documents:
            return
        
        document = self.documents[doc_id]
        
        # 删除关联的文本块和向量
        for chunk_id in document.chunk_ids:
            if chunk_id in self.chunks:
                del self.chunks[chunk_id]
            await self.vector_store.delete_vectors([chunk_id])
        
        # 删除文档
        del self.documents[doc_id]
        
        db_logger.info(f"Document deleted from knowledge base '{self.name}': {doc_id}")
    
    async def get_document(self, doc_id: str) -> Optional[Document]:
        """获取文档"""
        return self.documents.get(doc_id)
    
    async def list_documents(self) -> List[Document]:
        """获取所有文档列表"""
        return list(self.documents.values())
    
    async def get_statistics(self) -> Dict[str, Any]:
        """获取知识库统计信息"""
        return {
            "document_count": len(self.documents),
            "chunk_count": len(self.chunks),
            "total_characters": sum(len(doc.content) for doc in self.documents.values()),
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap
        }


class KnowledgeBaseManager:
    """知识库管理器"""
    
    _instance = None
    _lock = asyncio.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._knowledge_bases: Dict[str, KnowledgeBase] = {}
            self._initialized = True
    
    async def create_knowledge_base(self, name: str, description: Optional[str] = None) -> KnowledgeBase:
        """创建知识库"""
        kb_id = hashlib.md5(name.encode()).hexdigest()
        
        if kb_id in self._knowledge_bases:
            raise ValueError(f"Knowledge base '{name}' already exists")
        
        kb = KnowledgeBase(
            id=kb_id,
            name=name,
            description=description
        )
        
        self._knowledge_bases[kb_id] = kb
        db_logger.info(f"Knowledge base created: {name}")
        return kb
    
    async def get_knowledge_base(self, kb_id: str) -> Optional[KnowledgeBase]:
        """获取知识库"""
        return self._knowledge_bases.get(kb_id)
    
    async def delete_knowledge_base(self, kb_id: str):
        """删除知识库"""
        if kb_id in self._knowledge_bases:
            del self._knowledge_bases[kb_id]
            db_logger.info(f"Knowledge base deleted: {kb_id}")
    
    async def list_knowledge_bases(self) -> List[KnowledgeBase]:
        """获取所有知识库列表"""
        return list(self._knowledge_bases.values())


class RAGEngine:
    """RAG引擎"""
    
    def __init__(self, knowledge_base: KnowledgeBase):
        self._kb = knowledge_base
    
    async def retrieve(self, query: str, top_k: int = 5) -> List[SearchResult]:
        """检索相关文档"""
        return await self._kb.search(query, top_k)
    
    async def generate(self, query: str, context: str, llm_service) -> str:
        """使用LLM生成回答"""
        prompt = f"""根据以下上下文信息回答问题：

上下文：
{context}

问题：{query}

请根据上下文信息回答问题，如果上下文没有相关信息，请说明。"""
        
        # 这里应该调用实际的LLM服务
        # 目前返回一个简单的响应
        return f"基于检索到的信息，关于'{query}'的回答如下...\n\n参考内容摘要：\n{context[:200]}..."
    
    async def query(self, query: str, llm_service=None, top_k: int = 5) -> Dict[str, Any]:
        """执行完整的RAG查询"""
        # 1. 检索相关文档
        search_results = await self.retrieve(query, top_k)
        
        # 2. 构建上下文
        context = "\n\n".join([result.content for result in search_results])
        
        # 3. 生成回答
        answer = await self.generate(query, context, llm_service)
        
        # 4. 返回结果
        return {
            "query": query,
            "answer": answer,
            "sources": [
                {
                    "chunk_id": result.chunk_id,
                    "document_id": result.document_id,
                    "score": result.score,
                    "content": result.content[:100] + "..." if len(result.content) > 100 else result.content
                } for result in search_results
            ],
            "context_length": len(context)
        }


# 全局实例
kb_manager = KnowledgeBaseManager()


# 便捷函数
async def create_kb(name: str, description: Optional[str] = None) -> KnowledgeBase:
    """创建知识库"""
    return await kb_manager.create_knowledge_base(name, description)


async def get_kb(kb_id: str) -> Optional[KnowledgeBase]:
    """获取知识库"""
    return await kb_manager.get_knowledge_base(kb_id)


async def list_kbs() -> List[KnowledgeBase]:
    """获取所有知识库"""
    return await kb_manager.list_knowledge_bases()


async def rag_query(kb_id: str, query: str, llm_service=None) -> Dict[str, Any]:
    """执行RAG查询"""
    kb = await kb_manager.get_knowledge_base(kb_id)
    if not kb:
        raise ValueError(f"Knowledge base not found: {kb_id}")
    
    engine = RAGEngine(kb)
    return await engine.query(query, llm_service)



