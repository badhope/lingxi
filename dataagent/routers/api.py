"""API routes for the two CrewAI flows."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from agents.base_agent import get_llm
from crews.data_analysis import run_data_analysis
from crews.knowledge_team import run_knowledge_query

router = APIRouter(prefix="/api")


class AnalysisRequest(BaseModel):
    """Request body for the analysis flow."""
    query: str
    model: Optional[str] = None
    temperature: Optional[float] = None


class KnowledgeRequest(BaseModel):
    """Request body for the KB query flow."""
    question: str
    model: Optional[str] = None


class AnalysisResponse(BaseModel):
    """Data analysis response."""
    success: bool
    result: Optional[str] = None
    error: Optional[str] = None


class KnowledgeResponse(BaseModel):
    """Knowledge query response."""
    success: bool
    result: Optional[str] = None
    sources: Optional[list] = None
    error: Optional[str] = None


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze(request: AnalysisRequest):
    """Run data analysis via CrewAI crew."""
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
    """Run knowledge query via CrewAI crew."""
    try:
        llm = get_llm()
        result = run_knowledge_query(request.question, llm)

        return KnowledgeResponse(
            success=True,
            result=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
