"""
DataAgent - Agent 市场路由
提供 Agent 模板管理、分享和用户 Agent 管理功能
"""
from fastapi import APIRouter, HTTPException, Request, Header
from fastapi.responses import JSONResponse
from typing import Optional

from core import (
    AgentCategory,
    AgentVisibility,
    agent_market_manager,
    create_agent_template,
    list_agent_templates,
    get_agent_template,
    create_user_agent,
    list_user_agents,
    get_logger
)

router = APIRouter()
logger = get_logger("agent_market_api")


def get_current_user(authorization: Optional[str] = Header(None)):
    """从请求头中获取当前用户（辅助函数）"""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    return authorization[7:]


@router.get("/api/market/categories")
async def get_agent_categories():
    """获取 Agent 分类列表"""
    return JSONResponse({
        "success": True,
        "categories": [
            {
                "id": cat.value,
                "name": cat.value.capitalize(),
                "description": f"{cat.value} 类 Agent"
            }
            for cat in AgentCategory
        ]
    })


@router.post("/api/market/templates")
async def create_template(request: Request, authorization: Optional[str] = Header(None)):
    """创建 Agent 模板"""
    data = await request.json()
    
    required_fields = ["name", "description", "instructions", "system_prompt"]
    for field in required_fields:
        if field not in data:
            raise HTTPException(status_code=400, detail=f"需要提供 {field} 参数")
    
    try:
        creator_id = get_current_user(authorization) or "anonymous"
        
        template = await agent_market_manager.create_template(
            name=data["name"],
            description=data["description"],
            creator_id=creator_id,
            instructions=data["instructions"],
            system_prompt=data["system_prompt"],
            category=AgentCategory(data.get("category", "general")),
            visibility=AgentVisibility(data.get("visibility", "private")),
            tags=data.get("tags", []),
            version=data.get("version", "1.0.0")
        )
        
        logger.info(f"创建 Agent 模板: {template.name}")
        
        return JSONResponse({
            "success": True,
            "template": template.to_dict()
        })
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建模板失败: {str(e)}")


@router.get("/api/market/templates")
async def list_templates(
    category: Optional[str] = None,
    tag: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = "download_count"
):
    """列出 Agent 模板"""
    try:
        cat_enum = AgentCategory(category) if category else None
        
        templates = await agent_market_manager.list_templates(
            category=cat_enum,
            tag=tag,
            only_public=True,
            search_query=search,
            sort_by=sort_by
        )
        
        return JSONResponse({
            "success": True,
            "templates": [t.to_dict() for t in templates]
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取模板列表失败: {str(e)}")


@router.get("/api/market/templates/{template_id}")
async def get_template(template_id: str):
    """获取模板详情"""
    template = await agent_market_manager.get_template(template_id)
    
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    # 增加查看次数
    await agent_market_manager.view_template(template_id)
    
    return JSONResponse({
        "success": True,
        "template": template.to_dict()
    })


@router.post("/api/market/templates/{template_id}/rate")
async def rate_template(
    template_id: str,
    request: Request,
    authorization: Optional[str] = Header(None)
):
    """评分模板"""
    data = await request.json()
    
    if "score" not in data:
        raise HTTPException(status_code=400, detail="需要提供 score 参数")
    
    user_id = get_current_user(authorization) or "anonymous"
    
    try:
        template = await agent_market_manager.rate_template(
            template_id=template_id,
            user_id=user_id,
            score=float(data["score"]),
            comment=data.get("comment")
        )
        
        if not template:
            raise HTTPException(status_code=404, detail="模板不存在")
        
        return JSONResponse({
            "success": True,
            "template": template.to_dict()
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"评分失败: {str(e)}")


@router.post("/api/market/templates/{template_id}/download")
async def download_template(
    template_id: str,
    authorization: Optional[str] = Header(None)
):
    """下载模板（保存到用户账户）"""
    user_id = get_current_user(authorization)
    
    if not user_id:
        raise HTTPException(status_code=401, detail="需要登录才能下载")
    
    try:
        template = await agent_market_manager.download_template(template_id)
        
        if not template:
            raise HTTPException(status_code=404, detail="模板不存在")
        
        # 自动创建用户 Agent
        user_agent = await agent_market_manager.create_user_agent(
            user_id=user_id,
            name=f"{template.name} (副本)",
            system_prompt=template.system_prompt,
            instructions=template.instructions,
            template_id=template_id
        )
        
        return JSONResponse({
            "success": True,
            "message": "模板已保存到您的 Agent 列表",
            "user_agent": user_agent.to_dict()
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"下载失败: {str(e)}")


# 用户 Agent 管理
@router.get("/api/agents")
async def get_user_agents(authorization: Optional[str] = Header(None)):
    """获取当前用户的 Agent 列表"""
    user_id = get_current_user(authorization)
    
    if not user_id:
        return JSONResponse({
            "success": True,
            "agents": []
        })
    
    try:
        agents = await agent_market_manager.list_user_agents(user_id)
        
        return JSONResponse({
            "success": True,
            "agents": [a.to_dict() for a in agents]
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取 Agent 列表失败: {str(e)}")


@router.post("/api/agents")
async def create_user_agent_route(
    request: Request,
    authorization: Optional[str] = Header(None)
):
    """创建用户 Agent"""
    data = await request.json()
    user_id = get_current_user(authorization) or "anonymous"
    
    required_fields = ["name", "system_prompt", "instructions"]
    for field in required_fields:
        if field not in data:
            raise HTTPException(status_code=400, detail=f"需要提供 {field} 参数")
    
    try:
        agent = await agent_market_manager.create_user_agent(
            user_id=user_id,
            name=data["name"],
            system_prompt=data["system_prompt"],
            instructions=data["instructions"],
            template_id=data.get("template_id"),
            is_public=data.get("is_public", False),
            tags=data.get("tags", [])
        )
        
        logger.info(f"创建用户 Agent: {agent.name}")
        
        return JSONResponse({
            "success": True,
            "agent": agent.to_dict()
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建 Agent 失败: {str(e)}")


@router.put("/api/agents/{agent_id}")
async def update_user_agent(
    agent_id: str,
    request: Request,
    authorization: Optional[str] = Header(None)
):
    """更新用户 Agent"""
    data = await request.json()
    user_id = get_current_user(authorization) or "anonymous"
    
    try:
        agent = await agent_market_manager.update_user_agent(
            user_id=user_id,
            agent_id=agent_id,
            **data
        )
        
        if not agent:
            raise HTTPException(status_code=404, detail="Agent 不存在")
        
        return JSONResponse({
            "success": True,
            "agent": agent.to_dict()
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新 Agent 失败: {str(e)}")


@router.delete("/api/agents/{agent_id}")
async def delete_user_agent(
    agent_id: str,
    authorization: Optional[str] = Header(None)
):
    """删除用户 Agent"""
    user_id = get_current_user(authorization) or "anonymous"
    
    success = await agent_market_manager.delete_user_agent(user_id, agent_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Agent 不存在")
    
    return JSONResponse({
        "success": True,
        "message": "Agent 已删除"
    })


@router.post("/api/agents/{agent_id}/publish")
async def publish_agent_to_market(
    agent_id: str,
    request: Request,
    authorization: Optional[str] = Header(None)
):
    """将用户 Agent 发布到市场"""
    data = await request.json()
    user_id = get_current_user(authorization)
    
    if not user_id:
        raise HTTPException(status_code=401, detail="需要登录才能发布")
    
    try:
        template = await agent_market_manager.publish_agent_to_market(
            user_id=user_id,
            agent_id=agent_id,
            name=data.get("name"),
            description=data.get("description"),
            category=AgentCategory(data.get("category", "general")),
            tags=data.get("tags", [])
        )
        
        if not template:
            raise HTTPException(status_code=404, detail="Agent 不存在")
        
        logger.info(f"发布 Agent 到市场: {template.name}")
        
        return JSONResponse({
            "success": True,
            "message": "Agent 已发布到市场",
            "template": template.to_dict()
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"发布失败: {str(e)}")
