"""
API 路由 - CrewAI 执行接口
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from agents.base_agent import get_llm
from crews.data_analysis import run_data_analysis
from crews.knowledge_team import run_knowledge_query

router = APIRouter(prefix="/api", tags=["CrewAI 执行"])


class AnalysisRequest(BaseModel):
    """数据分析请求"""
    query: str
    model: Optional[str] = None
    temperature: Optional[float] = None


class KnowledgeRequest(BaseModel):
    """知识库查询请求"""
    question: str
    model: Optional[str] = None


class AnalysisResponse(BaseModel):
    """数据分析响应"""
    success: bool
    result: Optional[str] = None
    error: Optional[str] = None


class KnowledgeResponse(BaseModel):
    """知识库查询响应"""
    success: bool
    result: Optional[str] = None
    sources: Optional[list] = None
    error: Optional[str] = None


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze(request: AnalysisRequest):
    """
    数据分析接口
    
    使用 CrewAI 团队执行数据分析任务
    """
    try:
        llm = get_llm()
        result = run_data_analysis(request.query, llm)
        
        return AnalysisResponse(
            success=True,
            result=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/knowledge/query", response_model=KnowledgeResponse)
async def query_knowledge(request: KnowledgeRequest):
    """
    知识库查询接口
    
    使用 CrewAI 团队执行知识库查询
    """
    try:
        llm = get_llm()
        result = run_knowledge_query(request.question, llm)
        
        return KnowledgeResponse(
            success=True,
            result=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
