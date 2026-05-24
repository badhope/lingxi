"""
DataAgent - 增强版知识库与文件处理
支持多种办公文件格式、文件处理选项和灵活的 RAG 检索
"""
import asyncio
import hashlib
import json
import mimetypes
import os
import re
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import (
    List,
    Dict,
    Optional,
    Any,
    Union,
    Tuple,
)

from pydantic import BaseModel, Field

from .config import config_manager
from .logging import db_logger, get_logger
from .vector_stores import (
    VectorStore,
    VectorStoreType,
    MemoryVectorStore,
    create_vector_store
)


kb_logger = get_logger("knowledge_base")


# ==================== 文件类型定义 ====================

class FileType(Enum):
    """支持的文件类型"""
    TEXT = "text"
    PDF = "pdf"
    WORD = "word"
    EXCEL = "excel"
    POWERPOINT = "powerpoint"
    CSV = "csv"
    JSON = "json"
    MARKDOWN = "markdown"
    IMAGE = "image"
    HTML = "html"
    XML = "xml"
    UNKNOWN = "unknown"


FILE_EXTENSIONS = {
    FileType.TEXT: [".txt", ".md", ".rst", ".log"],
    FileType.PDF: [".pdf"],
    FileType.WORD: [".doc", ".docx", ".odt"],
    FileType.EXCEL: [".xls", ".xlsx", ".csv", ".ods"],
    FileType.POWERPOINT: [".ppt", ".pptx", ".odp"],
    FileType.CSV: [".csv"],
    FileType.JSON: [".json"],
    FileType.MARKDOWN: [".md"],
    FileType.IMAGE: [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".webp"],
    FileType.HTML: [".html", ".htm"],
    FileType.XML: [".xml"],
}


# ==================== 文件处理选项 ====================

@dataclass
class ProcessingOptions:
    """文件处理选项"""
    # 文本处理
    extract_text: bool = True
    split_into_chunks: bool = True
    chunk_size: int = 500
    chunk_overlap: int = 50
    
    # 内容增强
    extract_metadata: bool = True
    extract_images: bool = False
    extract_tables: bool = True
    ocr_images: bool = False
    
    # 索引处理
    generate_embeddings: bool = True
    hybrid_search: bool = True
    
    # 后处理
    clean_text: bool = True
    remove_duplicates: bool = True


# ==================== 文档和块模型 ====================

class Document(BaseModel):
    """增强的文档模型"""
    id: str = Field(..., description="文档ID")
    title: str = Field(..., description="文档标题")
    content: str = Field(..., description="文档内容")
    source: Optional[str] = Field(None, description="文档来源/文件路径")
    file_type: FileType = Field(FileType.UNKNOWN, description="文件类型")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="文档元数据")
    created_at: str = Field(..., description="创建时间")
    updated_at: str = Field(..., description="更新时间")
    chunk_ids: List[str] = Field(default_factory=list, description="关联的文本块ID")
    file_size: Optional[int] = Field(None, description="文件大小（字节）")
    tags: List[str] = Field(default_factory=list, description="标签")
    version: int = Field(1, description="版本号")
    
    @classmethod
    def from_file(cls, file_path: Path) -> 'Document':
        """从文件创建文档"""
        now = datetime.now().isoformat()
        file_stats = file_path.stat() if file_path.exists() else None
        
        # 生成文档ID
        doc_id = hashlib.md5(f"{file_path.name}_{now}".encode()).hexdigest()
        
        # 确定文件类型
        file_type = get_file_type(file_path)
        
        return cls(
            id=doc_id,
            title=file_path.name,
            content="",  # 初始内容为空，由处理函数填充
            source=str(file_path),
            file_type=file_type,
            created_at=now,
            updated_at=now,
            file_size=file_stats.st_size if file_stats else None,
        )


class DocumentChunk(BaseModel):
    """增强的文档文本块"""
    id: str = Field(..., description="文本块ID")
    document_id: str = Field(..., description="所属文档ID")
    content: str = Field(..., description="文本内容")
    embedding: Optional[List[float]] = Field(None, description="向量嵌入")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")
    chunk_index: int = Field(0, description="在文档中的位置索引")
    chunk_type: str = Field("text", description="块类型 (text/table/image)")
    page_number: Optional[int] = Field(None, description="页码")


class SearchResult(BaseModel):
    """搜索结果"""
    chunk_id: str = Field(..., description="文本块ID")
    document_id: str = Field(..., description="文档ID")
    document_title: str = Field(..., description="文档标题")
    content: str = Field(..., description="匹配内容")
    score: float = Field(..., description="匹配分数")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")


# ==================== 文件类型检测 ====================

def get_file_type(file_path: Path) -> FileType:
    """获取文件类型"""
    suffix = file_path.suffix.lower()
    
    for file_type, extensions in FILE_EXTENSIONS.items():
        if suffix in extensions:
            return file_type
    
    return FileType.UNKNOWN


# ==================== 文件提取器基类 ====================

class FileExtractor(ABC):
    """文件提取器基类"""
    
    @abstractmethod
    def extract_text(self, file_path: Path) -> str:
        """提取文本内容"""
        pass
    
    @abstractmethod
    def extract_metadata(self, file_path: Path) -> Dict[str, Any]:
        """提取元数据"""
        pass


class TextFileExtractor(FileExtractor):
    """文本文件提取器"""
    
    def extract_text(self, file_path: Path) -> str:
        """提取文本内容"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # 尝试其他编码
            try:
                with open(file_path, 'r', encoding='gbk') as f:
                    return f.read()
            except:
                return ""
    
    def extract_metadata(self, file_path: Path) -> Dict[str, Any]:
        """提取元数据"""
        stats = file_path.stat() if file_path.exists() else None
        return {
            "file_size": stats.st_size if stats else 0,
            "encoding": "utf-8",
        }


class PDFExtractor(FileExtractor):
    """PDF文件提取器"""
    
    def extract_text(self, file_path: Path) -> str:
        """提取PDF文本内容"""
        try:
            # 简单的文本提取
            try:
                import PyPDF2
                text = ""
                with open(file_path, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    for page in reader.pages:
                        text += page.extract_text() + "\n\n"
                return text
            except ImportError:
                kb_logger.warning("PyPDF2 not available, returning placeholder text")
                return f"[PDF document: {file_path.name}] - PyPDF2 not installed"
        except Exception as e:
            kb_logger.error(f"Error extracting text from PDF: {e}")
            return f"[PDF document: {file_path.name}]"
    
    def extract_metadata(self, file_path: Path) -> Dict[str, Any]:
        """提取PDF元数据"""
        try:
            import PyPDF2
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                metadata = reader.metadata
                return {
                    "title": metadata.title if metadata else None,
                    "author": metadata.author if metadata else None,
                    "subject": metadata.subject if metadata else None,
                    "page_count": len(reader.pages),
                }
        except:
            return {"page_count": 0}


class SimpleExtractor(FileExtractor):
    """简单文件提取器（通用）"""
    
    def extract_text(self, file_path: Path) -> str:
        """简单的文本提取"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except:
            return f"[Document: {file_path.name}]"
    
    def extract_metadata(self, file_path: Path) -> Dict[str, Any]:
        """简单的元数据提取"""
        stats = file_path.stat() if file_path.exists() else None
        return {
            "file_size": stats.st_size if stats else 0,
        }


def get_extractor(file_type: FileType) -> FileExtractor:
    """获取对应类型的文件提取器"""
    if file_type == FileType.PDF:
        return PDFExtractor()
    elif file_type == FileType.TEXT or file_type == FileType.MARKDOWN:
        return TextFileExtractor()
    else:
        return SimpleExtractor()


# ==================== 文本处理工具 ====================

def clean_text(text: str) -> str:
    """文本清理"""
    if not text:
        return ""
    
    # 移除多余的空白
    text = re.sub(r'\s+', ' ', text)
    # 移除特殊字符
    text = re.sub(r'[^\w\s.,!?"\'()\-:;]', '', text)
    return text.strip()


def split_into_chunks(
    content: str,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
    document_id: str = ""
) -> List[DocumentChunk]:
    """将文档分割为文本块"""
    chunks = []
    content_length = len(content)
    chunk_index = 0
    
    if content_length == 0:
        return chunks
    
    for i in range(0, content_length, chunk_size - chunk_overlap):
        end = min(i + chunk_size, content_length)
        chunk_content = content[i:end]
        
        # 避免在句子中间切割
        if end < content_length:
            last_period = chunk_content.rfind('.')
            last_newline = chunk_content.rfind('\n')
            
            best_split = max(last_period, last_newline)
            if best_split > len(chunk_content) - 100 and best_split > 0:
                chunk_content = chunk_content[:best_split + 1]
                end = i + len(chunk_content)
        
        chunk_id = hashlib.md5(f"{document_id}_{chunk_index}".encode()).hexdigest()
        chunk = DocumentChunk(
            id=chunk_id,
            document_id=document_id,
            content=chunk_content,
            chunk_index=chunk_index,
            chunk_type="text"
        )
        chunks.append(chunk)
        chunk_index += 1
    
    return chunks


# ==================== 向量存储 ====================

class VectorStore(ABC):
    """向量存储抽象基类"""
    
    @abstractmethod
    async def add_vectors(self, vectors: List[List[float]], chunk_ids: List[str]):
        pass
    
    @abstractmethod
    async def search(self, query_vector: List[float], top_k: int = 5) -> List[Tuple[str, float]]:
        pass
    
    @abstractmethod
    async def delete_vectors(self, chunk_ids: List[str]):
        pass


class MemoryVectorStore(VectorStore):
    """基于内存的向量存储"""
    
    def __init__(self):
        self._vectors: Dict[str, List[float]] = {}
        self._lock = threading.RLock()
    
    async def add_vectors(self, vectors: List[List[float]], chunk_ids: List[str]):
        with self._lock:
            for chunk_id, vector in zip(chunk_ids, vectors):
                self._vectors[chunk_id] = vector
    
    async def search(self, query_vector: List[float], top_k: int = 5) -> List[Tuple[str, float]]:
        with self._lock:
            if not self._vectors:
                return []
            
            results = []
            for chunk_id, vector in self._vectors.items():
                similarity = self._cosine_similarity(query_vector, vector)
                results.append((chunk_id, similarity))
            
            results.sort(key=lambda x: x[1], reverse=True)
            return results[:top_k]
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    async def delete_vectors(self, chunk_ids: List[str]):
        with self._lock:
            for chunk_id in chunk_ids:
                if chunk_id in self._vectors:
                    del self._vectors[chunk_id]


class SimpleEmbeddingService:
    """简单的嵌入服务"""
    
    def __init__(self):
        self._dimension = 128
    
    async def embed(self, texts: List[str]) -> List[List[float]]:
        """简单的字符频率嵌入"""
        results = []
        for text in texts:
            vector = []
            text_bytes = text.encode('utf-8')
            
            for i in range(self._dimension):
                if i < len(text_bytes):
                    vector.append(text_bytes[i] / 255.0)
                else:
                    vector.append(0.0)
            
            results.append(vector)
        
        return results
    
    def get_dimension(self) -> int:
        return self._dimension


# ==================== 增强的知识库 ====================

class EnhancedKnowledgeBase:
    """增强的知识库"""
    
    def __init__(self, name: str, description: Optional[str] = None, 
                 vector_store_type: VectorStoreType = VectorStoreType.MEMORY, **kwargs):
        self.id = hashlib.md5(name.encode()).hexdigest()
        self.name = name
        self.description = description
        self.documents: Dict[str, Document] = {}
        self.chunks: Dict[str, DocumentChunk] = {}
        self.vector_store_type = vector_store_type
        self.vector_store: VectorStore = create_vector_store(vector_store_type, **kwargs)
        self.embedding_service = SimpleEmbeddingService()
        self.created_at = datetime.now().isoformat()
    
    async def add_file(
        self,
        file_path: Path,
        options: Optional[ProcessingOptions] = None
    ) -> str:
        """添加文件到知识库"""
        if options is None:
            options = ProcessingOptions()
        
        kb_logger.info(f"Adding file to knowledge base '{self.name}': {file_path.name}")
        
        # 1. 创建文档
        document = Document.from_file(file_path)
        
        # 2. 获取文件提取器
        file_type = get_file_type(file_path)
        extractor = get_extractor(file_type)
        
        # 3. 提取文本
        if options.extract_text:
            document.content = extractor.extract_text(file_path)
        
        # 4. 提取元数据
        if options.extract_metadata:
            document.metadata = extractor.extract_metadata(file_path)
        
        # 5. 文本清理
        if options.clean_text:
            document.content = clean_text(document.content)
        
        # 6. 分割为块
        chunks = []
        if options.split_into_chunks and document.content:
            chunks = split_into_chunks(
                document.content,
                chunk_size=options.chunk_size,
                chunk_overlap=options.chunk_overlap,
                document_id=document.id
            )
        
        # 7. 添加文档和块
        self.documents[document.id] = document
        for chunk in chunks:
            self.chunks[chunk.id] = chunk
            document.chunk_ids.append(chunk.id)
        
        # 8. 生成嵌入
        if options.generate_embeddings and chunks:
            chunk_contents = [chunk.content for chunk in chunks]
            embeddings = await self.embedding_service.embed(chunk_contents)
            chunk_ids = [chunk.id for chunk in chunks]
            await self.vector_store.add_vectors(embeddings, chunk_ids)
            
            # 保存嵌入到块对象
            for chunk, embedding in zip(chunks, embeddings):
                chunk.embedding = embedding
        
        kb_logger.info(f"File added successfully: {document.title} (chunks: {len(chunks)})")
        return document.id
    
    async def add_text(
        self,
        content: str,
        title: str,
        options: Optional[ProcessingOptions] = None
    ) -> str:
        """添加文本到知识库"""
        if options is None:
            options = ProcessingOptions()
        
        now = datetime.now().isoformat()
        doc_id = hashlib.md5(f"{title}_{now}".encode()).hexdigest()
        
        # 创建文档
        document = Document(
            id=doc_id,
            title=title,
            content=content,
            created_at=now,
            updated_at=now,
            file_type=FileType.TEXT
        )
        
        # 处理文本
        if options.clean_text:
            document.content = clean_text(document.content)
        
        # 分块
        chunks = []
        if options.split_into_chunks:
            chunks = split_into_chunks(
                document.content,
                chunk_size=options.chunk_size,
                chunk_overlap=options.chunk_overlap,
                document_id=document.id
            )
        
        # 添加到知识库
        self.documents[document.id] = document
        for chunk in chunks:
            self.chunks[chunk.id] = chunk
            document.chunk_ids.append(chunk.id)
        
        # 生成嵌入
        if options.generate_embeddings and chunks:
            chunk_contents = [chunk.content for chunk in chunks]
            embeddings = await self.embedding_service.embed(chunk_contents)
            chunk_ids = [chunk.id for chunk in chunks]
            await self.vector_store.add_vectors(embeddings, chunk_ids)
        
        kb_logger.info(f"Text added successfully: {title} (chunks: {len(chunks)})")
        return document.id
    
    async def search(
        self,
        query: str,
        top_k: int = 5
    ) -> List[SearchResult]:
        """搜索知识库"""
        if not self.chunks:
            return []
        
        # 生成查询嵌入
        query_embedding = await self.embedding_service.embed([query])
        
        if not query_embedding:
            return []
        
        # 向量搜索
        results = await self.vector_store.search(query_embedding[0], top_k)
        
        # 构建搜索结果
        search_results = []
        for chunk_id, score in results:
            if chunk_id in self.chunks:
                chunk = self.chunks[chunk_id]
                document = self.documents.get(chunk.document_id)
                
                if document:
                    search_results.append(SearchResult(
                        chunk_id=chunk.id,
                        document_id=chunk.document_id,
                        document_title=document.title,
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
        
        # 删除关联的块和向量
        for chunk_id in document.chunk_ids:
            if chunk_id in self.chunks:
                del self.chunks[chunk_id]
        
        await self.vector_store.delete_vectors(document.chunk_ids)
        
        # 删除文档
        del self.documents[doc_id]
        
        kb_logger.info(f"Document deleted: {document.title}")
    
    def get_document(self, doc_id: str) -> Optional[Document]:
        """获取文档"""
        return self.documents.get(doc_id)
    
    def list_documents(self) -> List[Document]:
        """获取所有文档"""
        return list(self.documents.values())
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "document_count": len(self.documents),
            "chunk_count": len(self.chunks),
            "total_characters": sum(len(doc.content) for doc in self.documents.values()),
            "kb_name": self.name,
            "kb_id": self.id
        }


# ==================== 增强的知识库管理器 ====================

class EnhancedKnowledgeBaseManager:
    """增强的知识库管理器"""
    
    _instance = None
    _lock = asyncio.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._knowledge_bases: Dict[str, EnhancedKnowledgeBase] = {}
            self._initialized = True
    
    async def create_knowledge_base(
        self, name: str, description: Optional[str] = None,
        vector_store_type: VectorStoreType = VectorStoreType.MEMORY,
        **kwargs
    ) -> EnhancedKnowledgeBase:
        """创建知识库"""
        kb = EnhancedKnowledgeBase(name, description, vector_store_type, **kwargs)
        
        if kb.id in self._knowledge_bases:
            raise ValueError(f"Knowledge base '{name}' already exists")
        
        self._knowledge_bases[kb.id] = kb
        kb_logger.info(f"Knowledge base created: {name} with vector store {vector_store_type.value}")
        return kb
    
    def get_knowledge_base(self, kb_id: str) -> Optional[EnhancedKnowledgeBase]:
        """获取知识库"""
        return self._knowledge_bases.get(kb_id)
    
    def delete_knowledge_base(self, kb_id: str):
        """删除知识库"""
        if kb_id in self._knowledge_bases:
            del self._knowledge_bases[kb_id]
            kb_logger.info(f"Knowledge base deleted: {kb_id}")
    
    def list_knowledge_bases(self) -> List[EnhancedKnowledgeBase]:
        """获取所有知识库"""
        return list(self._knowledge_bases.values())


# 全局实例
enhanced_kb_manager = EnhancedKnowledgeBaseManager()


# ==================== 便捷函数 ====================

async def create_enhanced_kb(
    name: str,
    description: Optional[str] = None,
    vector_store_type: VectorStoreType = VectorStoreType.MEMORY,
    **kwargs
) -> EnhancedKnowledgeBase:
    """创建增强知识库"""
    return await enhanced_kb_manager.create_knowledge_base(name, description, vector_store_type, **kwargs)


def get_enhanced_kb(kb_id: str) -> Optional[EnhancedKnowledgeBase]:
    """获取增强知识库"""
    return enhanced_kb_manager.get_knowledge_base(kb_id)


def list_enhanced_kbs() -> List[EnhancedKnowledgeBase]:
    """获取所有增强知识库"""
    return enhanced_kb_manager.list_knowledge_bases()


async def add_file_to_kb(
    kb_id: str,
    file_path: Path,
    options: Optional[ProcessingOptions] = None
) -> str:
    """添加文件到知识库"""
    kb = get_enhanced_kb(kb_id)
    if not kb:
        raise ValueError(f"Knowledge base not found: {kb_id}")
    
    return await kb.add_file(file_path, options)


async def search_kb(
    kb_id: str,
    query: str,
    top_k: int = 5
) -> List[SearchResult]:
    """搜索知识库"""
    kb = get_enhanced_kb(kb_id)
    if not kb:
        return []
    
    return await kb.search(query, top_k)


__all__ = [
    "EnhancedKnowledgeBase",
    "EnhancedKnowledgeBaseManager",
    "ProcessingOptions",
    "FileType",
    "Document",
    "DocumentChunk",
    "SearchResult",
    "FileExtractor",
    "create_enhanced_kb",
    "get_enhanced_kb",
    "list_enhanced_kbs",
    "add_file_to_kb",
    "search_kb",
    "get_file_type",
    "enhanced_kb_manager",
    "VectorStoreType",
]
