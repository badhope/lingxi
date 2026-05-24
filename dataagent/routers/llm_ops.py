"""
DataAgent - LLMOps API 路由
提供LLM调用追踪、性能监控、成本分析等API端点
"""

from fastapi import APIRouter, HTTPException, Request, Header, Query
from fastapi.responses import JSONResponse
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import time

from core.llm_ops import (
    llm_ops,
    prompt_manager,
    ab_test_manager,
    LLMProvider,
    LLMTraceStatus,
    LLMCallTrace,
    ModelMetrics,
    PromptVersion,
    ABTest
)
from core import auth_manager, UserRole, Permission
from core.logging import get_logger

router = APIRouter()
logger = get_logger("llm_ops_api")


def get_current_user(authorization: Optional[str] = Header(None)):
    """从请求头中获取当前用户"""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization[7:]
    return auth_manager.verify_session(token)


def require_admin(authorization: Optional[str] = Header(None)):
    """要求管理员权限"""
    user = get_current_user(authorization)
    if not user or user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="权限不足")
    return user


def require_authenticated(authorization: Optional[str] = Header(None)):
    """要求认证用户"""
    user = get_current_user(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="未授权")
    return user


# ==================== 追踪相关 API ====================

@router.get("/api/llm_ops/traces")
async def get_traces(
    provider: Optional[str] = Query(None, description="LLM提供商"),
    model: Optional[str] = Query(None, description="模型名称"),
    user_id: Optional[str] = Query(None, description="用户ID"),
    status: Optional[str] = Query(None, description="状态: pending|running|success|failed|cached"),
    days: Optional[int] = Query(None, description="最近几天的数据"),
    limit: int = Query(100, ge=1, le=1000, description="返回数量限制"),
    authorization: Optional[str] = Header(None)
):
    """获取LLM调用追踪记录"""
    require_admin(authorization)
    
    try:
        status_enum = LLMTraceStatus(status) if status else None
        start_time = None
        if days:
            start_time = time.time() - (days * 24 * 3600)
        
        traces = llm_ops.get_traces(
            provider=provider,
            model=model,
            user_id=user_id,
            status=status_enum,
            start_time=start_time,
            limit=limit
        )
        
        return JSONResponse({
            "success": True,
            "traces": [t.dict() for t in traces],
            "total": len(traces)
        })
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/api/llm_ops/traces/{trace_id}")
async def get_trace_detail(
    trace_id: str,
    authorization: Optional[str] = Header(None)
):
    """获取单个追踪详情"""
    require_admin(authorization)
    
    trace = llm_ops.traces_by_id.get(trace_id)
    if not trace:
        raise HTTPException(status_code=404, detail="追踪记录不存在")
    
    return JSONResponse({
        "success": True,
        "trace": trace.dict()
    })


@router.delete("/api/llm_ops/traces")
async def clear_traces(
    days: Optional[int] = Query(None, description="清除N天前的数据，不指定则全部清除"),
    authorization: Optional[str] = Header(None)
):
    """清除追踪记录"""
    require_admin(authorization)
    
    if days:
        cutoff = time.time() - (days * 24 * 3600)
        llm_ops.traces = [t for t in llm_ops.traces if t.start_time >= cutoff]
        llm_ops.traces_by_id = {t.id: t for t in llm_ops.traces}
    else:
        llm_ops.traces = []
        llm_ops.traces_by_id = {}
    
    logger.info(f"清除追踪记录: {days if days else '全部'}天前")
    return JSONResponse({"success": True, "message": "追踪记录已清除"})


# ==================== 指标相关 API ====================

@router.get("/api/llm_ops/metrics")
async def get_all_metrics(
    authorization: Optional[str] = Header(None)
):
    """获取所有模型指标"""
    require_authenticated(authorization)
    
    metrics = llm_ops.get_all_metrics()
    return JSONResponse({
        "success": True,
        "metrics": [m.dict() for m in metrics]
    })


@router.get("/api/llm_ops/metrics/{provider}/{model}")
async def get_model_metrics(
    provider: str,
    model: str,
    authorization: Optional[str] = Header(None)
):
    """获取特定模型的指标"""
    require_authenticated(authorization)
    
    metrics = llm_ops.get_model_metrics(provider, model)
    if not metrics:
        raise HTTPException(status_code=404, detail="模型指标不存在")
    
    return JSONResponse({
        "success": True,
        "metrics": metrics.dict()
    })


# ==================== 成本相关 API ====================

@router.get("/api/llm_ops/costs")
async def get_cost_summary(
    days: int = Query(30, ge=1, le=365, description="统计天数"),
    authorization: Optional[str] = Header(None)
):
    """获取成本汇总"""
    require_authenticated(authorization)
    
    summary = llm_ops.get_cost_summary(days=days)
    return JSONResponse({
        "success": True,
        "summary": summary
    })


@router.get("/api/llm_ops/costs/export")
async def export_costs(
    days: int = Query(30, ge=1, le=365, description="导出天数"),
    format: str = Query("json", description="导出格式: json"),
    authorization: Optional[str] = Header(None)
):
    """导出成本数据"""
    require_admin(authorization)
    
    data = llm_ops.export_traces(format=format)
    return JSONResponse({
        "success": True,
        "data": data,
        "format": format
    })


# ==================== 提示词管理 API ====================

@router.get("/api/llm_ops/prompts")
async def list_prompts(
    authorization: Optional[str] = Header(None)
):
    """列出所有提示词"""
    require_authenticated(authorization)
    
    prompts = prompt_manager.list_prompts()
    return JSONResponse({
        "success": True,
        "prompts": [p.dict() for p in prompts]
    })


@router.get("/api/llm_ops/prompts/{name}")
async def get_prompt(
    name: str,
    version: Optional[str] = Query(None, description="版本号，不指定则返回最新版本"),
    authorization: Optional[str] = Header(None)
):
    """获取提示词"""
    require_authenticated(authorization)
    
    prompt = prompt_manager.get_prompt(name, version=version)
    if not prompt:
        raise HTTPException(status_code=404, detail="提示词不存在")
    
    return JSONResponse({
        "success": True,
        "prompt": prompt.dict()
    })


@router.post("/api/llm_ops/prompts")
async def create_prompt(
    request: Request,
    authorization: Optional[str] = Header(None)
):
    """创建提示词"""
    user = require_authenticated(authorization)
    
    data = await request.json()
    name = data.get("name", "")
    prompt_text = data.get("prompt", "")
    description = data.get("description", "")
    variables = data.get("variables", [])
    tags = data.get("tags", [])
    
    if not name or not prompt_text:
        raise HTTPException(status_code=400, detail="名称和提示词内容不能为空")
    
    prompt = prompt_manager.create_prompt(
        name=name,
        prompt=prompt_text,
        description=description,
        variables=variables,
        created_by=user.id,
        tags=tags
    )
    
    return JSONResponse({
        "success": True,
        "prompt": prompt.dict(),
        "message": "提示词创建成功"
    })


# ==================== A/B测试 API ====================

@router.get("/api/llm_ops/ab_tests")
async def list_ab_tests(
    authorization: Optional[str] = Header(None)
):
    """列出所有A/B测试"""
    require_authenticated(authorization)
    
    tests = list(ab_test_manager.tests.values())
    return JSONResponse({
        "success": True,
        "tests": [t.dict() for t in tests]
    })


@router.get("/api/llm_ops/ab_tests/{test_id}")
async def get_ab_test(
    test_id: str,
    authorization: Optional[str] = Header(None)
):
    """获取A/B测试详情"""
    require_authenticated(authorization)
    
    test = ab_test_manager.tests.get(test_id)
    if not test:
        raise HTTPException(status_code=404, detail="测试不存在")
    
    return JSONResponse({
        "success": True,
        "test": test.dict()
    })


@router.get("/api/llm_ops/ab_tests/{test_id}/results")
async def get_ab_test_results(
    test_id: str,
    authorization: Optional[str] = Header(None)
):
    """获取A/B测试结果"""
    require_authenticated(authorization)
    
    results = ab_test_manager.get_test_results(test_id)
    if not results:
        raise HTTPException(status_code=404, detail="测试不存在")
    
    return JSONResponse({
        "success": True,
        "results": results
    })


@router.post("/api/llm_ops/ab_tests")
async def create_ab_test(
    request: Request,
    authorization: Optional[str] = Header(None)
):
    """创建A/B测试"""
    require_admin(authorization)
    
    data = await request.json()
    name = data.get("name", "")
    variants = data.get("variants", {})
    traffic_split = data.get("traffic_split", {})
    metric = data.get("metric", "user_satisfaction")
    description = data.get("description", "")
    
    if not name or not variants or not traffic_split:
        raise HTTPException(status_code=400, detail="名称、变体和流量分配不能为空")
    
    try:
        test = ab_test_manager.create_test(
            name=name,
            variants=variants,
            traffic_split=traffic_split,
            metric=metric
        )
        test.description = description
        
        return JSONResponse({
            "success": True,
            "test": test.dict(),
            "message": "A/B测试创建成功"
        })
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/api/llm_ops/ab_tests/{test_id}/conversion")
async def record_conversion(
    test_id: str,
    request: Request,
    authorization: Optional[str] = Header(None)
):
    """记录转化"""
    require_authenticated(authorization)
    
    data = await request.json()
    variant_id = data.get("variant_id", "")
    revenue = data.get("revenue", 0.0)
    
    if not variant_id:
        raise HTTPException(status_code=400, detail="变体ID不能为空")
    
    ab_test_manager.record_conversion(test_id, variant_id, revenue)
    
    return JSONResponse({
        "success": True,
        "message": "转化记录成功"
    })


# ==================== 缓存管理 API ====================

@router.get("/api/llm_ops/cache")
async def get_cache_stats(
    authorization: Optional[str] = Header(None)
):
    """获取缓存统计"""
    require_admin(authorization)
    
    return JSONResponse({
        "success": True,
        "cache": {
            "size": len(llm_ops.cache),
            "max_size": llm_ops.max_cache_size,
            "usage": len(llm_ops.cache) / llm_ops.max_cache_size
        }
    })


@router.delete("/api/llm_ops/cache")
async def clear_cache(
    authorization: Optional[str] = Header(None)
):
    """清除缓存"""
    require_admin(authorization)
    
    llm_ops.cache = {}
    
    return JSONResponse({
        "success": True,
        "message": "缓存已清除"
    })


# ==================== 仪表盘 API ====================

@router.get("/api/llm_ops/dashboard")
async def get_dashboard(
    authorization: Optional[str] = Header(None)
):
    """获取仪表盘数据"""
    require_authenticated(authorization)
    
    # 获取24小时和30天的数据
    day_summary = llm_ops.get_cost_summary(days=1)
    month_summary = llm_ops.get_cost_summary(days=30)
    
    # 获取所有模型指标
    metrics = llm_ops.get_all_metrics()
    
    # 获取最近调用
    recent_traces = llm_ops.get_traces(limit=10)
    
    return JSONResponse({
        "success": True,
        "dashboard": {
            "day_summary": day_summary,
            "month_summary": month_summary,
            "metrics": [m.dict() for m in metrics],
            "recent_traces": [t.dict() for t in recent_traces]
        }
    })
