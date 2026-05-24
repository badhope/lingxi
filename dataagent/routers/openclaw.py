"""
DataAgent - OpenClaw 综合 API 路由
整合 Heartbeat、Memory、Skills、Channels 等功能的 API
"""
from fastapi import APIRouter, HTTPException, Request, Header, Query
from fastapi.responses import JSONResponse
from typing import Optional, List, Dict, Any
import time

from core import auth_manager, UserRole, Permission
from core.logging import get_logger
from core.heartbeat import (
    get_heartbeat_engine,
    ScheduledTask,
    TaskStatus,
    HeartbeatStatus
)
from core.memory import (
    get_memory_engine,
    MemoryType,
    MemoryItem
)
from core.skills import (
    get_skills_engine,
    Skill,
    SkillStatus,
    SkillParameter
)
from core.channels import (
    get_channels_engine,
    Channel,
    ChannelType,
    Message
)

router = APIRouter()
logger = get_logger("openclaw_api")


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


# ==================== Heartbeat API ====================

@router.get("/openclaw/heartbeat/status")
async def get_heartbeat_status(authorization: Optional[str] = Header(None)):
    """获取心跳状态"""
    require_authenticated(authorization)
    engine = get_heartbeat_engine()
    status = engine.get_status()
    return JSONResponse({
        "success": True,
        "status": status.status.value,
        "active_tasks": status.active_tasks,
        "timestamp": status.timestamp
    })


@router.get("/openclaw/heartbeat/tasks")
async def list_heartbeat_tasks(authorization: Optional[str] = Header(None)):
    """列出所有定时任务"""
    require_authenticated(authorization)
    engine = get_heartbeat_engine()
    tasks = engine.list_tasks()
    return JSONResponse({
        "success": True,
        "tasks": [
            {
                "id": t.id,
                "name": t.name,
                "description": t.description,
                "interval_seconds": t.interval_seconds,
                "enabled": t.enabled,
                "last_run": t.last_run,
                "next_run": t.next_run
            }
            for t in tasks
        ]
    })


@router.post("/openclaw/heartbeat/tasks")
async def create_heartbeat_task(
    request: Request,
    authorization: Optional[str] = Header(None)
):
    """创建定时任务"""
    require_admin(authorization)
    
    try:
        data = await request.json()
        name = data.get("name", "")
        description = data.get("description", "")
        interval_seconds = data.get("interval_seconds", 3600)
        
        if not name:
            raise HTTPException(status_code=400, detail="任务名称不能为空")
        
        engine = get_heartbeat_engine()
        task = ScheduledTask(
            name=name,
            description=description,
            interval_seconds=interval_seconds
        )
        task_id = engine.add_task(task)
        
        return JSONResponse({
            "success": True,
            "task_id": task_id,
            "message": "任务创建成功"
        })
    except Exception as e:
        logger.error(f"创建任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Memory API ====================

@router.post("/openclaw/memory")
async def add_memory(
    request: Request,
    authorization: Optional[str] = Header(None)
):
    """添加记忆"""
    user = require_authenticated(authorization)
    
    try:
        data = await request.json()
        content = data.get("content", "")
        memory_type = MemoryType(data.get("type", "conversation"))
        tags = data.get("tags", [])
        importance = data.get("importance", 0.5)
        
        if not content:
            raise HTTPException(status_code=400, detail="内容不能为空")
        
        engine = get_memory_engine()
        memory_id = engine.add_memory(
            content=content,
            memory_type=memory_type,
            tags=tags,
            importance=importance,
            user_id=user.id
        )
        
        return JSONResponse({
            "success": True,
            "memory_id": memory_id,
            "message": "记忆添加成功"
        })
    except Exception as e:
        logger.error(f"添加记忆失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/openclaw/memory/search")
async def search_memory(
    query: str = Query(""),
    memory_type: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    authorization: Optional[str] = Header(None)
):
    """搜索记忆"""
    user = require_authenticated(authorization)
    
    try:
        engine = get_memory_engine()
        type_enum = MemoryType(memory_type) if memory_type else None
        results = engine.search_memories(
            query=query,
            memory_type=type_enum,
            user_id=user.id,
            limit=limit
        )
        
        return JSONResponse({
            "success": True,
            "results": [
                {
                    "id": r.item.id,
                    "type": r.item.type.value,
                    "content": r.item.content,
                    "tags": r.item.tags,
                    "importance": r.item.importance,
                    "relevance": r.relevance_score,
                    "created_at": r.item.created_at
                }
                for r in results
            ]
        })
    except Exception as e:
        logger.error(f"搜索记忆失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/openclaw/memory/preferences")
async def get_preferences(authorization: Optional[str] = Header(None)):
    """获取用户偏好"""
    user = require_authenticated(authorization)
    
    engine = get_memory_engine()
    preferences = engine.get_all_preferences(user_id=user.id)
    
    return JSONResponse({
        "success": True,
        "preferences": preferences
    })


@router.post("/openclaw/memory/preferences")
async def set_preference(
    request: Request,
    authorization: Optional[str] = Header(None)
):
    """设置用户偏好"""
    user = require_authenticated(authorization)
    
    try:
        data = await request.json()
        key = data.get("key", "")
        value = data.get("value")
        
        if not key:
            raise HTTPException(status_code=400, detail="Key 不能为空")
        
        engine = get_memory_engine()
        engine.set_preference(key, value, user_id=user.id)
        
        return JSONResponse({
            "success": True,
            "message": "偏好设置成功"
        })
    except Exception as e:
        logger.error(f"设置偏好失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/openclaw/memory/export")
async def export_memory(authorization: Optional[str] = Header(None)):
    """导出记忆（类似 Soul.md）"""
    require_admin(authorization)
    
    engine = get_memory_engine()
    exported = engine.export_memories()
    
    return JSONResponse({
        "success": True,
        "data": exported
    })


# ==================== Skills API ====================

@router.get("/openclaw/skills")
async def list_skills(
    category: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None)
):
    """列出所有技能"""
    require_authenticated(authorization)
    
    engine = get_skills_engine()
    skills = engine.list_skills(category=category)
    
    return JSONResponse({
        "success": True,
        "skills": [
            {
                "id": s.id,
                "name": s.name,
                "description": s.description,
                "version": s.version,
                "author": s.author,
                "category": s.category,
                "tags": s.tags,
                "status": s.status.value,
                "enabled": s.enabled,
                "parameters": [
                    {"name": p.name, "type": p.type, "description": p.description, "required": p.required}
                    for p in s.parameters
                ]
            }
            for s in skills
        ],
        "categories": engine.get_categories()
    })


@router.post("/openclaw/skills/{skill_id}/execute")
async def execute_skill(
    skill_id: str,
    request: Request,
    authorization: Optional[str] = Header(None)
):
    """执行技能"""
    user = require_authenticated(authorization)
    
    try:
        data = await request.json()
        params = data.get("params", {})
        
        engine = get_skills_engine()
        result = await engine.execute_skill(skill_id, params)
        
        return JSONResponse(result)
    except Exception as e:
        logger.error(f"执行技能失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Channels API ====================

@router.get("/openclaw/channels")
async def list_channels(authorization: Optional[str] = Header(None)):
    """列出所有渠道"""
    require_authenticated(authorization)
    
    engine = get_channels_engine()
    channels = engine.list_channels()
    
    return JSONResponse({
        "success": True,
        "channels": [
            {
                "id": c.id,
                "name": c.name,
                "type": c.type.value,
                "enabled": c.enabled,
                "created_at": c.created_at
            }
            for c in channels
        ]
    })


@router.get("/openclaw/channels/messages")
async def get_channel_messages(
    channel_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    authorization: Optional[str] = Header(None)
):
    """获取消息历史"""
    user = require_authenticated(authorization)
    
    engine = get_channels_engine()
    messages = engine.get_message_history(
        channel_id=channel_id,
        user_id=user.id,
        limit=limit
    )
    
    return JSONResponse({
        "success": True,
        "messages": [
            {
                "id": m.id,
                "channel_type": m.channel_type.value,
                "content": m.content,
                "status": m.status.value,
                "created_at": m.created_at
            }
            for m in messages
        ]
    })


# ==================== 综合 Dashboard API ====================

@router.get("/openclaw/dashboard")
async def get_dashboard(authorization: Optional[str] = Header(None)):
    """获取综合仪表盘"""
    require_authenticated(authorization)
    
    try:
        # 获取各模块状态
        heartbeat_engine = get_heartbeat_engine()
        memory_engine = get_memory_engine()
        skills_engine = get_skills_engine()
        channels_engine = get_channels_engine()
        
        # 统计数据
        recent_memories = memory_engine.get_recent_memories(limit=10)
        all_skills = skills_engine.list_skills()
        active_tasks = [t for t in heartbeat_engine.list_tasks() if t.enabled]
        
        return JSONResponse({
            "success": True,
            "dashboard": {
                "heartbeat": {
                    "status": heartbeat_engine.get_status().status.value,
                    "active_tasks": len(active_tasks)
                },
                "memory": {
                    "total_memories": len(memory_engine.memories),
                    "recent_count": len(recent_memories)
                },
                "skills": {
                    "total_skills": len(all_skills),
                    "enabled_skills": len([s for s in all_skills if s.enabled])
                },
                "channels": {
                    "total_channels": len(channels_engine.channels),
                    "enabled_channels": len([c for c in channels_engine.list_channels() if c.enabled])
                }
            }
        })
    except Exception as e:
        logger.error(f"获取仪表盘失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
