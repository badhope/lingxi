"""
DataAgent - 向量数据库路由
提供向量存储的创建、管理和搜索功能
"""
import asyncio
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from typing import Optional

from core import (
    VectorStoreType,
    create_vector_store,
    enhanced_kb_manager,
    get_logger
)

router = APIRouter()
logger = get_logger("vector_stores_api")


@router.get("/api/vector-stores/types")
async def get_vector_store_types():
    """获取支持的向量存储类型"""
    return JSONResponse({
        "success": True,
        "types": [
            {
                "id": vst.value,
                "name": vst.value.upper(),
                "description": _get_vector_store_description(vst)
            }
            for vst in VectorStoreType
        ]
    })


def _get_vector_store_description(vst: VectorStoreType) -> str:
    """获取向量存储类型的描述"""
    descriptions = {
        VectorStoreType.MEMORY: "内存存储，最快速但不持久化",
        VectorStoreType.CHROMA: "ChromaDB，本地向量数据库，适合中小规模数据",
        VectorStoreType.MILVUS: "Milvus，企业级向量数据库，适合大规模数据",
        VectorStoreType.PINECONE: "Pinecone，云端向量服务，无需部署",
        VectorStoreType.QDRANT: "Qdrant，高性能向量搜索引擎",
        VectorStoreType.WEAVIATE: "Weaviate，开源向量搜索引擎",
        VectorStoreType.FAISS: "FAISS，Facebook AI 相似度搜索，本地高性能",
        VectorStoreType.ELASTICSEARCH: "Elasticsearch，企业级搜索引擎",
        VectorStoreType.REDIS: "Redis，内存数据库，支持向量",
        VectorStoreType.VESPA: "Vespa，Yahoo 开源向量搜索",
        VectorStoreType.LANCEDB: "LanceDB，现代化向量数据库"
    }
    return descriptions.get(vst, "未知类型")


@router.get("/api/vector-stores/health")
async def check_vector_stores_health():
    """检查各向量存储的健康状态"""
    health_status = {}
    
    for vst in VectorStoreType:
        try:
            store = create_vector_store(vst)
            info = store.get_info()
            health_status[vst.value] = {
                "available": True,
                "type": info.get("type", vst.value),
                "status": "healthy"
            }
        except Exception as e:
            health_status[vst.value] = {
                "available": False,
                "error": str(e),
                "status": "unhealthy"
            }
    
    return JSONResponse({
        "success": True,
        "health": health_status
    })


@router.get("/api/vector-stores/info/{store_type}")
async def get_vector_store_info(store_type: str):
    """获取特定向量存储的详细信息"""
    try:
        vst = VectorStoreType(store_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"未知的向量存储类型: {store_type}")
    
    try:
        store = create_vector_store(vst)
        info = store.get_info()
        
        return JSONResponse({
            "success": True,
            "type": vst.value,
            "info": info
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取信息失败: {str(e)}")
