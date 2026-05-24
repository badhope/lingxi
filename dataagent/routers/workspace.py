
"""
DataAgent - Workspace & Advanced Features API Routes
实现 SOUL.md、浏览器、工作区管理等高级功能的 API
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import json

from core.auth import get_current_active_user, get_current_active_superuser
from core.soul import (
    get_soul_manager,
    PersonalityConfig,
    PersonalityTrait
)
from core.workspace import (
    get_workspace_manager,
    WorkspaceFileType,
    AgentConfig,
    HeartbeatTask,
    MemoryEntry
)
from core.browser import get_browser_tool, BrowserConfig

router = APIRouter()


# ========== SOUL.md API ==========

@router.get("/soul/current", summary="获取当前 SOUL 配置")
async def get_current_soul():
    """获取当前 SOUL 配置和系统提示词"""
    soul_manager = get_soul_manager()
    personality = soul_manager.get_current_personality()
    system_prompt = soul_manager.get_system_prompt()
    return {
        "success": True,
        "personality": {
            "name": personality.name,
            "description": personality.description,
            "traits": [t.value for t in personality.traits],
            "communication_style": personality.communication_style,
            "brevity": personality.brevity,
            "humor_level": personality.humor_level
        },
        "system_prompt": system_prompt
    }


class UpdateSoulRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    traits: Optional[List[str]] = None
    communication_style: Optional[str] = None
    brevity: Optional[int] = None
    humor_level: Optional[int] = None


@router.put("/soul/current", summary="更新 SOUL 配置")
async def update_soul(request: UpdateSoulRequest):
    """更新当前 SOUL 配置"""
    soul_manager = get_soul_manager()
    personality = soul_manager.get_current_personality()
    
    if request.name:
        personality.name = request.name
    if request.description:
        personality.description = request.description
    if request.traits:
        personality.traits = [PersonalityTrait(t) for t in request.traits]
    if request.communication_style:
        personality.communication_style = request.communication_style
    if request.brevity is not None:
        personality.brevity = request.brevity
    if request.humor_level is not None:
        personality.humor_level = request.humor_level
    
    soul_manager.save_soul(personality)
    
    return {
        "success": True,
        "message": "SOUL 已更新"
    }


@router.get("/soul/templates", summary="获取 SOUL 模板列表")
async def get_soul_templates():
    """获取预定义的 SOUL 模板"""
    return {
        "success": True,
        "templates": [
            "professional",
            "friendly",
            "sassy",
            "minimal"
        ]
    }


class ApplyTemplateRequest(BaseModel):
    template_name: str


@router.post("/soul/templates/apply", summary="应用 SOUL 模板")
async def apply_soul_template(request: ApplyTemplateRequest):
    """应用预定义的 SOUL 模板"""
    soul_manager = get_soul_manager()
    personality = soul_manager.create_soul_template(request.template_name)
    soul_manager.save_soul(personality)
    
    return {
        "success": True,
        "message": f"已应用 {request.template_name} 模板",
        "personality": {
            "name": personality.name,
            "description": personality.description
        }
    }


# ========== Workspace Files API ==========

@router.get("/workspace/files", summary="列出工作区文件")
async def list_workspace_files():
    """列出所有工作区文件"""
    workspace_manager = get_workspace_manager()
    files = workspace_manager.list_workspace_files()
    
    return {
        "success": True,
        "files": files
    }


@router.get("/workspace/files/{file_type}", summary="获取工作区文件内容")
async def get_workspace_file(file_type: str):
    """获取指定工作区文件的内容"""
    try:
        file_enum = WorkspaceFileType(file_type)
    except ValueError:
        raise HTTPException(status_code=404, detail="Invalid file type")
    
    workspace_manager = get_workspace_manager()
    content = workspace_manager.read_file(file_enum)
    
    return {
        "success": True,
        "file_type": file_type,
        "content": content
    }


class WriteFileRequest(BaseModel):
    content: str


@router.put("/workspace/files/{file_type}", summary="更新工作区文件")
async def update_workspace_file(file_type: str, request: WriteFileRequest):
    """更新工作区文件内容"""
    try:
        file_enum = WorkspaceFileType(file_type)
    except ValueError:
        raise HTTPException(status_code=404, detail="Invalid file type")
    
    workspace_manager = get_workspace_manager()
    workspace_manager.write_file(file_enum, request.content)
    
    return {
        "success": True,
        "message": f"{file_type} 已更新"
    }


# ========== AGENTS.md API ==========

@router.get("/workspace/agents", summary="获取 Agent 配置列表")
async def get_agents():
    """获取所有 Agent 配置"""
    workspace_manager = get_workspace_manager()
    agents = workspace_manager.parse_agents_md()
    
    return {
        "success": True,
        "agents": [
            {
                "name": agent.name,
                "description": agent.description,
                "model": agent.model,
                "personality": agent.personality,
                "skills": agent.skills,
                "channels": agent.channels,
                "enabled": agent.enabled
            }
            for agent in agents
        ]
    }


# ========== HEARTBEAT.md API ==========

@router.get("/workspace/heartbeat", summary="获取心跳任务列表")
async def get_heartbeat_tasks():
    """获取所有心跳任务配置"""
    workspace_manager = get_workspace_manager()
    tasks = workspace_manager.parse_heartbeat_md()
    
    return {
        "success": True,
        "tasks": [
            {
                "name": task.name,
                "description": task.description,
                "schedule": task.schedule,
                "time": task.time,
                "enabled": task.enabled,
                "type": task.task_type,
                "message": task.message
            }
            for task in tasks
        ]
    }


# ========== MEMORY.md API ==========

class AddMemoryRequest(BaseModel):
    content: str
    memory_type: str = "note"
    tags: Optional[List[str]] = None
    importance: int = 5


@router.post("/workspace/memory", summary="添加记忆条目")
async def add_memory(request: AddMemoryRequest):
    """添加新的记忆条目"""
    workspace_manager = get_workspace_manager()
    entry = workspace_manager.add_memory(
        content=request.content,
        memory_type=request.memory_type,
        tags=request.tags,
        importance=request.importance
    )
    
    return {
        "success": True,
        "message": "记忆已添加",
        "memory": {
            "id": entry.id,
            "date": entry.date,
            "type": entry.type,
            "content": entry.content,
            "tags": entry.tags,
            "importance": entry.importance
        }
    }


# ========== Browser Automation API ==========

class BrowserNavigateRequest(BaseModel):
    url: str
    wait_until: str = "networkidle"


@router.post("/browser/navigate", summary="浏览器导航")
async def browser_navigate(request: BrowserNavigateRequest):
    """导航到指定 URL"""
    browser = get_browser_tool()
    success = await browser.navigate(request.url, request.wait_until)
    
    return {
        "success": success,
        "url": request.url if success else None,
        "message": "导航成功" if success else "导航失败"
    }


@router.get("/browser/info", summary="获取浏览器状态")
async def browser_info():
    """获取当前浏览器状态"""
    browser = get_browser_tool()
    url = await browser.get_url()
    title = await browser.get_title()
    
    return {
        "success": True,
        "url": url,
        "title": title
    }


class BrowserScreenshotRequest(BaseModel):
    full_page: bool = False
    save_path: Optional[str] = None


@router.post("/browser/screenshot", summary="浏览器截图")
async def browser_screenshot(request: BrowserScreenshotRequest):
    """截取当前页面"""
    browser = get_browser_tool()
    result = await browser.screenshot(request.full_page, request.save_path)
    
    return {
        "success": result.success,
        "image_path": result.image_path,
        "error": result.error
    }


class BrowserExtractRequest(BaseModel):
    selector: Optional[str] = None
    attribute: Optional[str] = None


@router.post("/browser/extract", summary="提取页面内容")
async def browser_extract(request: BrowserExtractRequest):
    """提取页面文本或数据"""
    browser = get_browser_tool()
    
    if request.attribute:
        result = await browser.extract_data(request.selector or "body", request.attribute)
    else:
        result = await browser.extract_text(request.selector)
    
    return {
        "success": result.success,
        "text": result.text,
        "data": result.data,
        "error": result.error
    }


class BrowserClickRequest(BaseModel):
    selector: str


@router.post("/browser/click", summary="点击元素")
async def browser_click(request: BrowserClickRequest):
    """点击指定元素"""
    browser = get_browser_tool()
    success = await browser.click(request.selector)
    
    return {
        "success": success,
        "selector": request.selector
    }


class BrowserFillRequest(BaseModel):
    selector: str
    value: str


@router.post("/browser/fill", summary="填充表单")
async def browser_fill(request: BrowserFillRequest):
    """填充表单字段"""
    browser = get_browser_tool()
    success = await browser.fill(request.selector, request.value)
    
    return {
        "success": success,
        "selector": request.selector
    }


# ========== Dashboard ==========

@router.get("/dashboard", summary="综合仪表盘")
async def dashboard():
    """获取综合仪表盘信息"""
    soul_manager = get_soul_manager()
    workspace_manager = get_workspace_manager()
    
    personality = soul_manager.get_current_personality()
    workspace_files = workspace_manager.list_workspace_files()
    agents = workspace_manager.parse_agents_md()
    heartbeat_tasks = workspace_manager.parse_heartbeat_md()
    
    return {
        "success": True,
        "soul": {
            "name": personality.name,
            "description": personality.description
        },
        "workspace": {
            "file_count": len(workspace_files),
            "files": [{"name": f["name"], "size": f["size"]} for f in workspace_files]
        },
        "agents": {
            "count": len(agents),
            "enabled": sum(1 for a in agents if a.enabled)
        },
        "heartbeat": {
            "count": len(heartbeat_tasks),
            "enabled": sum(1 for t in heartbeat_tasks if t.enabled)
        }
    }

