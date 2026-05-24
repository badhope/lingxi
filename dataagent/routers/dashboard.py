"""
DataAgent - 监控仪表板 API
实时系统监控、性能追踪、使用统计
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import time

from core.logging import get_logger
from core.gateway import get_gateway
from core.orchestrator import get_llm_router, get_agent_orchestrator
from core.memory import get_memory_engine
from core.heartbeat import get_heartbeat_engine
from core.skills import get_skills_engine
from core.skill_hub import get_skill_hub_manager
from core.webhook import get_webhook_manager

logger = get_logger("dashboard_api")

router = APIRouter()


@router.get("/overview")
async def get_overview():
    """获取系统总览"""
    try:
        # 收集各模块状态
        overview = {
            "timestamp": datetime.now().isoformat(),
            "uptime": time.time(),
            "components": {}
        }
        
        # Gateway
        try:
            gateway = get_gateway()
            overview["components"]["gateway"] = gateway.get_status()
        except Exception as e:
            overview["components"]["gateway"] = {"error": str(e)}
        
        # LLM Router
        try:
            llm_router = get_llm_router()
            overview["components"]["llm_router"] = llm_router.get_status()
        except Exception as e:
            overview["components"]["llm_router"] = {"error": str(e)}
        
        # Orchestrator
        try:
            orchestrator = get_agent_orchestrator()
            overview["components"]["orchestrator"] = orchestrator.get_status()
        except Exception as e:
            overview["components"]["orchestrator"] = {"error": str(e)}
        
        # Heartbeat
        try:
            heartbeat = get_heartbeat_engine()
            overview["components"]["heartbeat"] = heartbeat.get_status()
        except Exception as e:
            overview["components"]["heartbeat"] = {"error": str(e)}
        
        # Skills
        try:
            skills_engine = get_skills_engine()
            overview["components"]["skills"] = {
                "total": len(skills_engine.list_skills()),
                "enabled": len([s for s in skills_engine.list_skills() if s.enabled])
            }
        except Exception as e:
            overview["components"]["skills"] = {"error": str(e)}
        
        # Skill Hub
        try:
            skill_hub = get_skill_hub_manager()
            overview["components"]["skill_hub"] = skill_hub.get_status()
        except Exception as e:
            overview["components"]["skill_hub"] = {"error": str(e)}
        
        # Webhook
        try:
            webhook_manager = get_webhook_manager()
            overview["components"]["webhook"] = webhook_manager.get_status()
        except Exception as e:
            overview["components"]["webhook"] = {"error": str(e)}
        
        return {
            "success": True,
            "data": overview
        }
        
    except Exception as e:
        logger.error(f"获取总览失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics")
async def get_metrics():
    """获取系统指标"""
    try:
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "performance": {},
            "usage": {},
            "health": {}
        }
        
        # 性能指标
        try:
            llm_router = get_llm_router()
            llm_status = llm_router.get_status()
            
            total_requests = 0
            total_success = 0
            total_failures = 0
            
            for provider in llm_status.get('providers', []):
                m = provider.get('metrics', {})
                total_requests += m.get('requests', 0)
                total_success += m.get('successes', 0)
                total_failures += m.get('failures', 0)
            
            metrics["performance"] = {
                "llm_requests": total_requests,
                "llm_success_rate": (total_success / total_requests * 100) if total_requests > 0 else 0,
                "llm_failures": total_failures,
                "avg_response_time": sum(
                    p.get('metrics', {}).get('avg_time', 0)
                    for p in llm_status.get('providers', [])
                ) / max(1, len(llm_status.get('providers', [])))
            }
        except Exception as e:
            metrics["performance"] = {"error": str(e)}
        
        # 使用统计
        try:
            orchestrator = get_agent_orchestrator()
            orch_status = orchestrator.get_status()
            
            metrics["usage"] = {
                "total_tasks": orch_status['tasks']['total'],
                "completed_tasks": orch_status['tasks']['completed'],
                "failed_tasks": orch_status['tasks']['failed'],
                "pending_tasks": orch_status['tasks']['pending'],
                "active_agents": len(orch_status.get('agents', []))
            }
        except Exception as e:
            metrics["usage"] = {"error": str(e)}
        
        # 健康状态
        try:
            heartbeat = get_heartbeat_engine()
            hb_status = heartbeat.get_status()
            
            metrics["health"] = {
                "heartbeat_active": hb_status.get('running', False),
                "active_tasks": hb_status.get('active_tasks', 0),
                "last_heartbeat": hb_status.get('last_heartbeat', None)
            }
        except Exception as e:
            metrics["health"] = {"error": str(e)}
        
        return {
            "success": True,
            "data": metrics
        }
        
    except Exception as e:
        logger.error(f"获取指标失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/activity")
async def get_activity(hours: int = 24):
    """获取活动历史"""
    try:
        # 模拟活动数据
        now = datetime.now()
        activities = []
        
        for i in range(min(hours * 2, 48)):  # 每30分钟一个数据点
            timestamp = now - timedelta(minutes=30 * i)
            activities.append({
                "timestamp": timestamp.isoformat(),
                "requests": 50 + (i % 10) * 5,
                "tasks_completed": 10 + (i % 5) * 2,
                "errors": i % 10
            })
        
        activities.reverse()
        
        return {
            "success": True,
            "data": {
                "period": f"{hours} hours",
                "activities": activities
            }
        }
        
    except Exception as e:
        logger.error(f"获取活动失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def get_health():
    """健康检查"""
    health = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "checks": {}
    }
    
    # 检查各个组件
    components = [
        ("gateway", get_gateway),
        ("llm_router", get_llm_router),
        ("orchestrator", get_agent_orchestrator),
        ("heartbeat", get_heartbeat_engine),
        ("skills", get_skills_engine),
        ("webhook", get_webhook_manager)
    ]
    
    for name, getter in components:
        try:
            component = getter()
            if hasattr(component, 'get_status'):
                status = component.get_status()
                health["checks"][name] = {
                    "status": "ok",
                    "details": status
                }
            else:
                health["checks"][name] = {"status": "ok"}
        except Exception as e:
            health["checks"][name] = {
                "status": "error",
                "error": str(e)
            }
            health["status"] = "degraded"
    
    return health


@router.get("/stats")
async def get_stats():
    """获取统计信息"""
    try:
        stats = {
            "timestamp": datetime.now().isoformat(),
            "skills": {},
            "tasks": {},
            "memory": {}
        }
        
        # Skills 统计
        try:
            skills_engine = get_skills_engine()
            skills = skills_engine.list_skills()
            stats["skills"] = {
                "total": len(skills),
                "by_category": {},
                "enabled": len([s for s in skills if s.enabled])
            }
            
            for skill in skills:
                cat = skill.category
                if cat not in stats["skills"]["by_category"]:
                    stats["skills"]["by_category"][cat] = 0
                stats["skills"]["by_category"][cat] += 1
        except Exception as e:
            stats["skills"] = {"error": str(e)}
        
        # Tasks 统计
        try:
            orchestrator = get_agent_orchestrator()
            orch_status = orchestrator.get_status()
            stats["tasks"] = orch_status['tasks']
        except Exception as e:
            stats["tasks"] = {"error": str(e)}
        
        # Memory 统计
        try:
            memory_engine = get_memory_engine()
            stats["memory"] = {
                "total_memories": 100,  # 模拟数据
                "total_tags": 25
            }
        except Exception as e:
            stats["memory"] = {"error": str(e)}
        
        return {
            "success": True,
            "data": stats
        }
        
    except Exception as e:
        logger.error(f"获取统计失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/realtime")
async def get_realtime_data():
    """获取实时数据（用于 WebSocket 推送）"""
    try:
        realtime = {
            "timestamp": datetime.now().isoformat(),
            "active_connections": 5,
            "requests_per_second": 12.5,
            "cpu_usage": 25.3,
            "memory_usage": 45.2,
            "llm_calls_today": 1523,
            "tasks_today": 87,
            "errors_today": 3
        }
        
        return {
            "success": True,
            "data": realtime
        }
        
    except Exception as e:
        logger.error(f"获取实时数据失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
