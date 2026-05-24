
"""
DataAgent - 技能仓库 API 路由
ClawHub 风格的完整技能管理 API
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from core.logging import get_logger
from core.skill_hub import get_skill_hub_manager

logger = get_logger("skillhub_api")

router = APIRouter()


@router.get("/status")
async def get_hub_status():
    """获取技能仓库状态"""
    hub = get_skill_hub_manager()
    return {
        "success": True,
        "status": hub.get_status()
    }


@router.get("/categories")
async def get_categories():
    """获取所有技能分类"""
    hub = get_skill_hub_manager()
    return {
        "success": True,
        "categories": hub.get_categories()
    }


@router.get("/search")
async def search_skills(
    query: str = "",
    category: Optional[str] = None,
    tags: Optional[str] = None,
    page: int = 1,
    limit: int = 20
):
    """搜索技能仓库"""
    tag_list = None
    if tags:
        tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
    
    hub = get_skill_hub_manager()
    result = hub.search_skills(
        query=query,
        category=category,
        tags=tag_list,
        page=page,
        limit=limit
    )
    return result


@router.get("/installed")
async def list_installed_skills():
    """列出已安装的技能"""
    hub = get_skill_hub_manager()
    return {
        "success": True,
        "skills": hub.list_installed()
    }


class InstallRequest(BaseModel):
    skill_id: str


@router.post("/install")
async def install_skill(request: InstallRequest):
    """安装技能"""
    hub = get_skill_hub_manager()
    result = await hub.install_skill(request.skill_id)
    return result


@router.post("/uninstall")
async def uninstall_skill(request: InstallRequest):
    """卸载技能"""
    hub = get_skill_hub_manager()
    result = await hub.uninstall_skill(request.skill_id)
    return result


@router.get("/featured")
async def get_featured_skills():
    """获取精选技能"""
    hub = get_skill_hub_manager()
    result = hub.search_skills(limit=10)
    
    # 简单排序
    sorted_skills = sorted(
        result["skills"],
        key=lambda s: (-s["downloads"], -s["rating"])
    )
    
    return {
        "success": True,
        "total": len(sorted_skills),
        "skills": sorted_skills[:10]
    }

