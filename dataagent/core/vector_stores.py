"""
DataAgent - 向量存储管理
支持多种向量数据库：内存存储、ChromaDB、Milvus、Pinecone
"""
import asyncio
import json
import threading
from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple
from core.config import config_manager
from core.logging import get_logger


vector_logger = get_logger("vector_stores")


class VectorStoreType(Enum):
    """向量存储类型"""
    MEMORY = "memory"
    CHROMA = "chroma"
    MILVUS = "milvus"
    PINECONE = "pinecone"
    QDRANT = "qdrant"
    WEAVIATE = "weaviate"
    VESPA = "vespa"
    ELASTICSEARCH = "elasticsearch"
    REDIS = "redis"
    FAISS = "faiss"
    LANCEDB = "lancedb"


class VectorStore(ABC):
    """向量存储抽象基类"""
    
    @abstractmethod
    async def add_vectors(self, vectors: List[List[float]], chunk_ids: List[str], metadata: Optional[List[Dict]] = None):
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
    
    @abstractmethod
    def get_info(self) -> Dict[str, Any]:
        """获取存储信息"""
        pass


class MemoryVectorStore(VectorStore):
    """基于内存的向量存储"""
    
    def __init__(self):
        self._vectors: Dict[str, List[float]] = {}
        self._metadata: Dict[str, Dict] = {}
        self._lock = asyncio.Lock()
    
    async def add_vectors(self, vectors: List[List[float]], chunk_ids: List[str], metadata: Optional[List[Dict]] = None):
        async with self._lock:
            for i, (chunk_id, vector) in enumerate(zip(chunk_ids, vectors)):
                self._vectors[chunk_id] = vector
                if metadata and i < len(metadata):
                    self._metadata[chunk_id] = metadata[i]
    
    async def search(self, query_vector: List[float], top_k: int = 5) -> List[Tuple[str, float]]:
        async with self._lock:
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
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot_product / (norm1 * norm2)
    
    async def delete_vectors(self, chunk_ids: List[str]):
        async with self._lock:
            for chunk_id in chunk_ids:
                if chunk_id in self._vectors:
                    del self._vectors[chunk_id]
                if chunk_id in self._metadata:
                    del self._metadata[chunk_id]
    
    async def get_vector(self, chunk_id: str) -> Optional[List[float]]:
        async with self._lock:
            return self._vectors.get(chunk_id)
    
    async def clear(self):
        async with self._lock:
            self._vectors = {}
            self._metadata = {}
    
    def get_info(self) -> Dict[str, Any]:
        return {
            "type": "memory",
            "vector_count": len(self._vectors)
        }


class ChromaDBVectorStore(VectorStore):
    """ChromaDB 向量存储"""
    
    def __init__(self, collection_name: str = "dataagent"):
        self.collection_name = collection_name
        self._client = None
        self._collection = None
        self._lock = asyncio.Lock()
        self._initialized = False
    
    async def _init_client(self):
        """初始化 ChromaDB 客户端"""
        if self._initialized:
            return
        
        async with self._lock:
            try:
                import chromadb
                from chromadb.utils import embedding_functions
                
                vector_logger.info("正在初始化 ChromaDB 向量存储")
                
                data_dir = config_manager.paths.data_dir / "chroma"
                data_dir.mkdir(parents=True, exist_ok=True)
                
                self._client = chromadb.PersistentClient(path=str(data_dir))
                self._collection = self._client.get_or_create_collection(name=self.collection_name)
                self._initialized = True
                vector_logger.info(f"ChromaDB 初始化成功")
            except ImportError:
                vector_logger.warning("ChromaDB 未安装，将使用内存存储")
                self._initialized = True
                self._fallback = MemoryVectorStore()
            except Exception as e:
                vector_logger.error(f"ChromaDB 初始化失败: {e}")
                self._fallback = MemoryVectorStore()
                self._initialized = True
    
    async def add_vectors(self, vectors: List[List[float]], chunk_ids: List[str], metadata: Optional[List[Dict]] = None):
        await self._init_client()
        
        if hasattr(self, '_fallback'):
            return await self._fallback.add_vectors(vectors, chunk_ids, metadata)
        
        try:
            metadatas = metadata if metadata is not None else [{} for _ in vectors]
            documents = [str(m) for m in metadatas]
            
            self._collection.add(
                embeddings=vectors,
                ids=chunk_ids,
                metadatas=metadatas,
                documents=documents
            )
            vector_logger.debug(f"已添加 {len(vectors)} 个向量到 ChromaDB")
        except Exception as e:
            vector_logger.error(f"添加向量失败: {e}")
    
    async def search(self, query_vector: List[float], top_k: int = 5) -> List[Tuple[str, float]]:
        await self._init_client()
        
        if hasattr(self, '_fallback'):
            return await self._fallback.search(query_vector, top_k)
        
        try:
            results = self._collection.query(
                query_embeddings=[query_vector],
                n_results=top_k
            )
            
            if results and 'ids' in results and results['ids']:
                ids = results['ids'][0]
                distances = results['distances'][0] if 'distances' in results else []
                
                # 转换为相似度分数 (距离越小越相似)
                return list(zip(ids, [1.0 - d for d in distances]))[:top_k]
            return []
        except Exception as e:
            vector_logger.error(f"搜索失败: {e}")
            return []
    
    async def delete_vectors(self, chunk_ids: List[str]):
        await self._init_client()
        
        if hasattr(self, '_fallback'):
            return await self._fallback.delete_vectors(chunk_ids)
        
        try:
            self._collection.delete(ids=chunk_ids)
        except Exception as e:
            vector_logger.error(f"删除向量失败: {e}")
    
    async def get_vector(self, chunk_id: str) -> Optional[List[float]]:
        await self._init_client()
        
        if hasattr(self, '_fallback'):
            return await self._fallback.get_vector(chunk_id)
        
        try:
            results = self._collection.get(ids=[chunk_id])
            if results and 'embeddings' in results and results['embeddings']:
                return results['embeddings'][0]
        except Exception as e:
            vector_logger.error(f"获取向量失败: {e}")
        return None
    
    async def clear(self):
        await self._init_client()
        
        if hasattr(self, '_fallback'):
            return await self._fallback.clear()
        
        try:
            self._collection.delete(where={})
        except Exception as e:
            vector_logger.error(f"清空失败: {e}")
    
    def get_info(self) -> Dict[str, Any]:
        return {
            "type": "chroma",
            "collection_name": self.collection_name
        }


class MilvusVectorStore(VectorStore):
    """Milvus 向量存储"""
    
    def __init__(self, collection_name: str = "dataagent"):
        self.collection_name = collection_name
        self._client = None
        self._collection = None
        self._lock = asyncio.Lock()
        self._initialized = False
    
    async def _init_client(self):
        if self._initialized:
            return
        
        async with self._lock:
            try:
                import pymilvus
                from pymilvus import connections, Collection, CollectionSchema, FieldSchema, DataType
                
                vector_logger.info("正在初始化 Milvus 向量存储")
                
                # 尝试连接本地 Milvus
                connections.connect("default", host="localhost", port="19530")
                
                # 创建集合
                fields = [
                    FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=512),
                    FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=128),
                ]
                schema = CollectionSchema(fields, "DataAgent 知识库向量存储")
                self._collection = Collection(self.collection_name, schema)
                
                # 创建索引
                index_params = {
                    "metric_type": "L2",
                    "index_type": "IVF_FLAT",
                    "params": {"nlist": 128}
                }
                self._collection.create_index("embedding", index_params)
                self._collection.load()
                
                self._initialized = True
                vector_logger.info(f"Milvus 初始化成功")
            except ImportError:
                vector_logger.warning("PyMilvus 未安装，将使用内存存储")
                self._fallback = MemoryVectorStore()
                self._initialized = True
            except Exception as e:
                vector_logger.error(f"Milvus 初始化失败: {e}")
                self._fallback = MemoryVectorStore()
                self._initialized = True
    
    async def add_vectors(self, vectors: List[List[float]], chunk_ids: List[str], metadata: Optional[List[Dict]] = None):
        await self._init_client()
        
        if hasattr(self, '_fallback'):
            return await self._fallback.add_vectors(vectors, chunk_ids, metadata)
        
        try:
            data = [
                chunk_ids,
                vectors
            ]
            
            self._collection.insert(data)
            self._collection.load()
            vector_logger.debug(f"已添加 {len(vectors)} 个向量到 Milvus")
        except Exception as e:
            vector_logger.error(f"添加向量失败: {e}")
    
    async def search(self, query_vector: List[float], top_k: int = 5) -> List[Tuple[str, float]]:
        await self._init_client()
        
        if hasattr(self, '_fallback'):
            return await self._fallback.search(query_vector, top_k)
        
        try:
            search_params = {"metric_type": "L2", "params": {"nprobe": 10}}
            results = self._collection.search(
                [query_vector],
                "embedding", search_params, limit=top_k,
            )
            
            if results and len(results) > 0:
                ids = [h.id for h in results[0]]
                scores = [1.0 / (1.0 + h.distance) for h in results[0]]
                return list(zip(ids, scores))[:top_k]
            return []
        except Exception as e:
            vector_logger.error(f"搜索失败: {e}")
            return []
    
    async def delete_vectors(self, chunk_ids: List[str]):
        await self._init_client()
        
        if hasattr(self, '_fallback'):
            return await self._fallback.delete_vectors(chunk_ids)
        
        try:
            expr = f'id in ["' + '","'.join(chunk_ids) + '"]'
            self._collection.delete(expr)
        except Exception as e:
            vector_logger.error(f"删除向量失败: {e}")
    
    async def get_vector(self, chunk_id: str) -> Optional[List[float]]:
        await self._init_client()
        
        if hasattr(self, '_fallback'):
            return await self._fallback.get_vector(chunk_id)
        
        try:
            results = self._collection.query(f'id == "{chunk_id}"', output_fields=["embedding"])
            if results and len(results) > 0:
                return results[0]["embedding"]
        except Exception as e:
            vector_logger.error(f"获取向量失败: {e}")
        return None
    
    async def clear(self):
        await self._init_client()
        
        if hasattr(self, '_fallback'):
            return await self._fallback.clear()
        
        try:
            expr = 'id like "%"'
            self._collection.delete(expr)
        except Exception as e:
            vector_logger.error(f"清空失败: {e}")
    
    def get_info(self) -> Dict[str, Any]:
        return {
            "type": "milvus",
            "collection_name": self.collection_name
        }


class PineconeVectorStore(VectorStore):
    """Pinecone 向量存储 (云端)"""
    
    def __init__(self, index_name: str = "dataagent", api_key: Optional[str] = None, environment: str = "us-west1-gcp"):
        self.index_name = index_name
        self.api_key = api_key or os.getenv("PINECONE_API_KEY") or config_manager.get_secret("pinecone_api_key") if hasattr(config_manager, 'get_secret') else None
        self.environment = environment
        self._index = None
        self._lock = asyncio.Lock()
        self._initialized = False
    
    async def _init_client(self):
        if self._initialized:
            return
        
        async with self._lock:
            try:
                import pinecone
                
                vector_logger.info("正在初始化 Pinecone 向量存储")
                
                if not self.api_key:
                    raise ValueError("需要配置 Pinecone API 密钥")
                
                pinecone.init(api_key=self.api_key, environment=self.environment)
                
                if self.index_name not in pinecone.list_indexes():
                    pinecone.create_index(
                        name=self.index_name,
                        dimension=128,
                        metric="cosine"
                    )
                
                self._index = pinecone.Index(self.index_name)
                self._initialized = True
                vector_logger.info("Pinecone 初始化成功")
            except ImportError:
                vector_logger.warning("Pinecone 未安装，将使用内存存储")
                self._fallback = MemoryVectorStore()
                self._initialized = True
            except Exception as e:
                vector_logger.error(f"Pinecone 初始化失败: {e}")
                self._fallback = MemoryVectorStore()
                self._initialized = True
    
    async def add_vectors(self, vectors: List[List[float]], chunk_ids: List[str], metadata: Optional[List[Dict]] = None):
        await self._init_client()
        
        if hasattr(self, '_fallback'):
            return await self._fallback.add_vectors(vectors, chunk_ids, metadata)
        
        try:
            items = []
            for i, (chunk_id, vector) in enumerate(zip(chunk_ids, vectors)):
                item = (chunk_id, vector)
                if metadata and i < len(metadata):
                    items.append(item + (metadata[i],))
                else:
                    items.append(item)
            
            self._index.upsert(items)
            vector_logger.debug(f"已添加 {len(vectors)} 个向量到 Pinecone")
        except Exception as e:
            vector_logger.error(f"添加向量失败: {e}")
    
    async def search(self, query_vector: List[float], top_k: int = 5) -> List[Tuple[str, float]]:
        await self._init_client()
        
        if hasattr(self, '_fallback'):
            return await self._fallback.search(query_vector, top_k)
        
        try:
            results = self._index.query(vector=query_vector, top_k=top_k, include_values=True)
            
            if results and 'matches' in results:
                matches = results['matches']
                return [(m['id'], m['score']) for m in matches]
            return []
        except Exception as e:
            vector_logger.error(f"搜索失败: {e}")
            return []
    
    async def delete_vectors(self, chunk_ids: List[str]):
        await self._init_client()
        
        if hasattr(self, '_fallback'):
            return await self._fallback.delete_vectors(chunk_ids)
        
        try:
            self._index.delete(ids=chunk_ids)
        except Exception as e:
            vector_logger.error(f"删除向量失败: {e}")
    
    async def get_vector(self, chunk_id: str) -> Optional[List[float]]:
        await self._init_client()
        
        if hasattr(self, '_fallback'):
            return await self._fallback.get_vector(chunk_id)
        
        try:
            results = self._index.fetch(ids=[chunk_id])
            if results and 'vectors' in results and chunk_id in results['vectors']:
                return results['vectors'][chunk_id]['values']
        except Exception as e:
            vector_logger.error(f"获取向量失败: {e}")
        return None
    
    async def clear(self):
        await self._init_client()
        
        if hasattr(self, '_fallback'):
            return await self._fallback.clear()
        
        try:
            self._index.delete(delete_all=True)
        except Exception as e:
            vector_logger.error(f"清空失败: {e}")
    
    def get_info(self) -> Dict[str, Any]:
        return {
            "type": "pinecone",
            "index_name": self.index_name
        }


class QdrantVectorStore(VectorStore):
    """Qdrant 向量存储"""
    
    def __init__(self, collection_name: str = "dataagent", host: str = "localhost", port: int = 6333):
        self.collection_name = collection_name
        self.host = host
        self.port = port
        self._client = None
        self._lock = asyncio.Lock()
        self._initialized = False
    
    async def _init_client(self):
        if self._initialized:
            return
        
        async with self._lock:
            try:
                from qdrant_client import QdrantClient
                from qdrant_client.models import Distance, VectorParams
                
                vector_logger.info("正在初始化 Qdrant 向量存储")
                self._client = QdrantClient(host=self.host, port=self.port)
                
                collections = self._client.get_collections().collections
                collection_names = [c.name for c in collections]
                
                if self.collection_name not in collection_names:
                    self._client.create_collection(
                        collection_name=self.collection_name,
                        vectors_config=VectorParams(size=128, distance=Distance.COSINE)
                    )
                
                self._initialized = True
                vector_logger.info(f"Qdrant 初始化成功")
            except ImportError:
                vector_logger.warning("Qdrant 客户端未安装，将使用内存存储")
                self._fallback = MemoryVectorStore()
                self._initialized = True
            except Exception as e:
                vector_logger.error(f"Qdrant 初始化失败: {e}")
                self._fallback = MemoryVectorStore()
                self._initialized = True
    
    async def add_vectors(self, vectors: List[List[float]], chunk_ids: List[str], metadata: Optional[List[Dict]] = None):
        await self._init_client()
        
        if hasattr(self, '_fallback'):
            return await self._fallback.add_vectors(vectors, chunk_ids, metadata)
        
        try:
            from qdrant_client.models import PointStruct
            
            points = []
            for i, (chunk_id, vector) in enumerate(zip(chunk_ids, vectors)):
                meta = metadata[i] if metadata and i < len(metadata) else {}
                points.append(PointStruct(id=chunk_id, vector=vector, payload=meta))
            
            self._client.upsert(collection_name=self.collection_name, points=points)
            vector_logger.debug(f"已添加 {len(vectors)} 个向量到 Qdrant")
        except Exception as e:
            vector_logger.error(f"添加向量失败: {e}")
    
    async def search(self, query_vector: List[float], top_k: int = 5) -> List[Tuple[str, float]]:
        await self._init_client()
        
        if hasattr(self, '_fallback'):
            return await self._fallback.search(query_vector, top_k)
        
        try:
            results = self._client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=top_k
            )
            return [(h.id, h.score) for h in results]
        except Exception as e:
            vector_logger.error(f"搜索失败: {e}")
            return []
    
    async def delete_vectors(self, chunk_ids: List[str]):
        await self._init_client()
        
        if hasattr(self, '_fallback'):
            return await self._fallback.delete_vectors(chunk_ids)
        
        try:
            self._client.delete(collection_name=self.collection_name, points_selector=chunk_ids)
        except Exception as e:
            vector_logger.error(f"删除向量失败: {e}")
    
    async def get_vector(self, chunk_id: str) -> Optional[List[float]]:
        await self._init_client()
        
        if hasattr(self, '_fallback'):
            return await self._fallback.get_vector(chunk_id)
        
        try:
            result = self._client.retrieve(collection_name=self.collection_name, ids=[chunk_id])
            if result and len(result) > 0:
                return result[0].vector
        except Exception as e:
            vector_logger.error(f"获取向量失败: {e}")
        return None
    
    async def clear(self):
        await self._init_client()
        
        if hasattr(self, '_fallback'):
            return await self._fallback.clear()
        
        try:
            self._client.delete_collection(collection_name=self.collection_name)
        except Exception as e:
            vector_logger.error(f"清空失败: {e}")
    
    def get_info(self) -> Dict[str, Any]:
        return {"type": "qdrant", "collection_name": self.collection_name, "host": self.host}


class WeaviateVectorStore(VectorStore):
    """Weaviate 向量存储"""
    
    def __init__(self, class_name: str = "DataAgent", host: str = "http://localhost:8080"):
        self.class_name = class_name
        self.host = host
        self._client = None
        self._lock = asyncio.Lock()
        self._initialized = False
    
    async def _init_client(self):
        if self._initialized:
            return
        
        async with self._lock:
            try:
                import weaviate
                from weaviate.classes.init import AdditionalConfig, Timeout
                
                vector_logger.info("正在初始化 Weaviate 向量存储")
                self._client = weaviate.connect_to_local(
                    host=self.host,
                    additional_config=AdditionalConfig(timeout=Timeout(init=10))
                )
                
                if not self._client.collections.exists(self.class_name):
                    self._client.collections.create(self.class_name)
                
                self._initialized = True
                vector_logger.info(f"Weaviate 初始化成功")
            except ImportError:
                vector_logger.warning("Weaviate 客户端未安装，将使用内存存储")
                self._fallback = MemoryVectorStore()
                self._initialized = True
            except Exception as e:
                vector_logger.error(f"Weaviate 初始化失败: {e}")
                self._fallback = MemoryVectorStore()
                self._initialized = True
    
    async def add_vectors(self, vectors: List[List[float]], chunk_ids: List[str], metadata: Optional[List[Dict]] = None):
        await self._init_client()
        
        if hasattr(self, '_fallback'):
            return await self._fallback.add_vectors(vectors, chunk_ids, metadata)
        
        try:
            collection = self._client.collections.get(self.class_name)
            with collection.batch.fixed_size(batch_size=100) as batch:
                for i, (chunk_id, vector) in enumerate(zip(chunk_ids, vectors)):
                    props = metadata[i] if metadata and i < len(metadata) else {}
                    props["chunk_id"] = chunk_id
                    batch.add_object(properties=props, vector=vector)
            vector_logger.debug(f"已添加 {len(vectors)} 个向量到 Weaviate")
        except Exception as e:
            vector_logger.error(f"添加向量失败: {e}")
    
    async def search(self, query_vector: List[float], top_k: int = 5) -> List[Tuple[str, float]]:
        await self._init_client()
        
        if hasattr(self, '_fallback'):
            return await self._fallback.search(query_vector, top_k)
        
        try:
            collection = self._client.collections.get(self.class_name)
            results = collection.query.near_vector(near_vector=query_vector, limit=top_k)
            return [(h.properties["chunk_id"], h.score) for h in results.objects]
        except Exception as e:
            vector_logger.error(f"搜索失败: {e}")
            return []
    
    async def delete_vectors(self, chunk_ids: List[str]):
        await self._init_client()
        
        if hasattr(self, '_fallback'):
            return await self._fallback.delete_vectors(chunk_ids)
        
        try:
            collection = self._client.collections.get(self.class_name)
            collection.data.delete_many(where={"chunk_id": chunk_ids})
        except Exception as e:
            vector_logger.error(f"删除向量失败: {e}")
    
    async def get_vector(self, chunk_id: str) -> Optional[List[float]]:
        await self._init_client()
        
        if hasattr(self, '_fallback'):
            return await self._fallback.get_vector(chunk_id)
        
        try:
            collection = self._client.collections.get(self.class_name)
            result = collection.query.fetch_objects(where={"chunk_id": chunk_id}, include_vector=True)
            if result.objects:
                return result.objects[0].vector
        except Exception as e:
            vector_logger.error(f"获取向量失败: {e}")
        return None
    
    async def clear(self):
        await self._init_client()
        
        if hasattr(self, '_fallback'):
            return await self._fallback.clear()
        
        try:
            self._client.collections.delete(self.class_name)
        except Exception as e:
            vector_logger.error(f"清空失败: {e}")
    
    def get_info(self) -> Dict[str, Any]:
        return {"type": "weaviate", "class_name": self.class_name, "host": self.host}


class FAISSVectorStore(VectorStore):
    """FAISS 向量存储（本地，快速）"""
    
    def __init__(self, index_path: Optional[Path] = None):
        self.index_path = index_path or config_manager.paths.data_dir / "faiss_index"
        self._index = None
        self._doc_ids = []
        self._vectors = []
        self._metadata = {}
        self._lock = asyncio.Lock()
        self._initialized = False
    
    async def _init_client(self):
        if self._initialized:
            return
        
        async with self._lock:
            try:
                import faiss
                import numpy as np
                
                vector_logger.info("正在初始化 FAISS 向量存储")
                
                if self.index_path.exists():
                    try:
                        self._index = faiss.read_index(str(self.index_path))
                        with open(self.index_path.with_suffix('.ids'), 'r') as f:
                            self._doc_ids = json.load(f)
                        with open(self.index_path.with_suffix('.meta'), 'r') as f:
                            self._metadata = json.load(f)
                        vector_logger.info("已加载 FAISS 索引")
                    except Exception as e:
                        vector_logger.warning(f"加载索引失败，将创建新索引: {e}")
                
                if self._index is None:
                    self._index = faiss.IndexFlatL2(128)
                
                self._initialized = True
            except ImportError:
                vector_logger.warning("FAISS 未安装，将使用内存存储")
                self._fallback = MemoryVectorStore()
                self._initialized = True
            except Exception as e:
                vector_logger.error(f"FAISS 初始化失败: {e}")
                self._fallback = MemoryVectorStore()
                self._initialized = True
    
    async def add_vectors(self, vectors: List[List[float]], chunk_ids: List[str], metadata: Optional[List[Dict]] = None):
        await self._init_client()
        
        if hasattr(self, '_fallback'):
            return await self._fallback.add_vectors(vectors, chunk_ids, metadata)
        
        try:
            import numpy as np
            
            async with self._lock:
                vectors_np = np.array(vectors).astype(np.float32)
                self._index.add(vectors_np)
                
                self._doc_ids.extend(chunk_ids)
                self._vectors.extend(vectors)
                
                if metadata:
                    for i, chunk_id in enumerate(chunk_ids):
                        self._metadata[chunk_id] = metadata[i]
                
                self._save_index()
                vector_logger.debug(f"已添加 {len(vectors)} 个向量到 FAISS")
        except Exception as e:
            vector_logger.error(f"添加向量失败: {e}")
    
    def _save_index(self):
        try:
            import faiss
            if self._index:
                faiss.write_index(self._index, str(self.index_path))
                with open(self.index_path.with_suffix('.ids'), 'w') as f:
                    json.dump(self._doc_ids, f)
                with open(self.index_path.with_suffix('.meta'), 'w') as f:
                    json.dump(self._metadata, f)
        except Exception as e:
            vector_logger.error(f"保存索引失败: {e}")
    
    async def search(self, query_vector: List[float], top_k: int = 5) -> List[Tuple[str, float]]:
        await self._init_client()
        
        if hasattr(self, '_fallback'):
            return await self._fallback.search(query_vector, top_k)
        
        try:
            import numpy as np
            
            async with self._lock:
                query_np = np.array([query_vector]).astype(np.float32)
                distances, indices = self._index.search(query_np, top_k)
                
                results = []
                for i, idx in enumerate(indices[0]):
                    if idx < len(self._doc_ids):
                        doc_id = self._doc_ids[idx]
                        distance = distances[0][i]
                        score = 1.0 / (1.0 + distance)
                        results.append((doc_id, score))
                
                return results
        except Exception as e:
            vector_logger.error(f"搜索失败: {e}")
            return []
    
    async def delete_vectors(self, chunk_ids: List[str]):
        await self._init_client()
        
        if hasattr(self, '_fallback'):
            return await self._fallback.delete_vectors(chunk_ids)
        
        try:
            async with self._lock:
                delete_indices = [i for i, doc_id in enumerate(self._doc_ids) if doc_id in chunk_ids]
                
                # 创建新索引，排除删除的向量
                import faiss
                import numpy as np
                
                new_index = faiss.IndexFlatL2(128)
                new_doc_ids = []
                new_vectors = []
                
                for i, doc_id in enumerate(self._doc_ids):
                    if i not in delete_indices:
                        new_doc_ids.append(doc_id)
                        new_vectors.append(self._vectors[i])
                
                if new_vectors:
                    new_index.add(np.array(new_vectors).astype(np.float32))
                
                self._index = new_index
                self._doc_ids = new_doc_ids
                self._vectors = new_vectors
                
                for doc_id in chunk_ids:
                    if doc_id in self._metadata:
                        del self._metadata[doc_id]
                
                self._save_index()
        except Exception as e:
            vector_logger.error(f"删除向量失败: {e}")
    
    async def get_vector(self, chunk_id: str) -> Optional[List[float]]:
        await self._init_client()
        
        if hasattr(self, '_fallback'):
            return await self._fallback.get_vector(chunk_id)
        
        async with self._lock:
            if chunk_id in self._doc_ids:
                idx = self._doc_ids.index(chunk_id)
                return self._vectors[idx]
        return None
    
    async def clear(self):
        await self._init_client()
        
        if hasattr(self, '_fallback'):
            return await self._fallback.clear()
        
        try:
            import faiss
            
            async with self._lock:
                self._index = faiss.IndexFlatL2(128)
                self._doc_ids = []
                self._vectors = []
                self._metadata = {}
                
                if self.index_path.exists():
                    import os
                    os.remove(self.index_path)
                    os.remove(self.index_path.with_suffix('.ids'))
                    os.remove(self.index_path.with_suffix('.meta'))
        except Exception as e:
            vector_logger.error(f"清空失败: {e}")
    
    def get_info(self) -> Dict[str, Any]:
        return {
            "type": "faiss",
            "index_path": str(self.index_path),
            "vector_count": len(self._doc_ids) if self._doc_ids else 0
        }


def create_vector_store(store_type: VectorStoreType = VectorStoreType.MEMORY, **kwargs) -> VectorStore:
    """创建向量存储实例"""
    
    if store_type == VectorStoreType.MEMORY:
        vector_logger.info("使用内存向量存储")
        return MemoryVectorStore()
    
    elif store_type == VectorStoreType.CHROMA:
        vector_logger.info("使用 ChromaDB 向量存储")
        return ChromaDBVectorStore(**kwargs)
    
    elif store_type == VectorStoreType.MILVUS:
        vector_logger.info("使用 Milvus 向量存储")
        return MilvusVectorStore(**kwargs)
    
    elif store_type == VectorStoreType.PINECONE:
        vector_logger.info("使用 Pinecone 向量存储")
        return PineconeVectorStore(**kwargs)
    
    elif store_type == VectorStoreType.QDRANT:
        vector_logger.info("使用 Qdrant 向量存储")
        return QdrantVectorStore(**kwargs)
    
    elif store_type == VectorStoreType.WEAVIATE:
        vector_logger.info("使用 Weaviate 向量存储")
        return WeaviateVectorStore(**kwargs)
    
    elif store_type == VectorStoreType.FAISS:
        vector_logger.info("使用 FAISS 向量存储")
        return FAISSVectorStore(**kwargs)
    
    else:
        vector_logger.warning(f"未知存储类型 {store_type}，使用默认内存存储")
        return MemoryVectorStore()


__all__ = [
    "VectorStoreType",
    "VectorStore",
    "MemoryVectorStore",
    "ChromaDBVectorStore",
    "MilvusVectorStore",
    "PineconeVectorStore",
    "QdrantVectorStore",
    "WeaviateVectorStore",
    "FAISSVectorStore",
    "create_vector_store"
]
