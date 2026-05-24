"""
DataAgent - 高级功能 API 路由
Gateway、Canvas、多 Agent 编排、LLM 路由
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from core.logging import get_logger
from core.gateway import get_gateway, GatewayStatus
from core.canvas import get_canvas_manager, CanvasElement, CanvasElementType
from core.orchestrator import get_llm_router, get_agent_orchestrator, LLMProvider, LLMConfig

logger = get_logger("advanced_api")

router = APIRouter()


# ========== Gateway API ==========

@router.get("/gateway/status")
async def get_gateway_status():
    """获取 Gateway 状态"""
    gateway = get_gateway()
    return {
        "success": True,
        "status": gateway.status.value,
        "data": gateway.get_status()
    }


@router.post("/gateway/start")
async def start_gateway():
    """启动 Gateway"""
    gateway = get_gateway()
    if gateway.status == GatewayStatus.RUNNING:
        return {"success": True, "message": "Gateway 已在运行"}
    
    await gateway.start()
    return {"success": True, "message": "Gateway 已启动"}


@router.post("/gateway/stop")
async def stop_gateway():
    """停止 Gateway"""
    gateway = get_gateway()
    await gateway.stop()
    return {"success": True, "message": "Gateway 已停止"}


@router.get("/gateway/agents")
async def list_gateway_agents():
    """列出 Gateway 中的 Agent"""
    gateway = get_gateway()
    return {
        "success": True,
        "agents": gateway.list_agents()
    }


# ========== Canvas API ==========

@router.post("/canvas/create")
async def create_canvas(title: Optional[str] = None):
    """创建新 Canvas"""
    manager = get_canvas_manager()
    canvas = manager.create_canvas()
    if title:
        canvas.set_title(title)
    return {
        "success": True,
        "canvas_id": canvas.canvas_id,
        "title": canvas.state.title
    }


@router.get("/canvas/{canvas_id}")
async def get_canvas(canvas_id: str):
    """获取 Canvas 状态"""
    manager = get_canvas_manager()
    canvas = manager.get_canvas(canvas_id)
    
    if not canvas:
        raise HTTPException(status_code=404, detail="Canvas 不存在")
    
    return {
        "success": True,
        "data": canvas.export_json()
    }


@router.get("/canvas")
async def list_canvases():
    """列出所有 Canvas"""
    manager = get_canvas_manager()
    return {
        "success": True,
        "canvases": manager.list_canvases()
    }


@router.post("/canvas/{canvas_id}/text")
async def add_canvas_text(canvas_id: str, text: str, style: Optional[Dict] = None):
    """添加文本元素"""
    manager = get_canvas_manager()
    canvas = manager.get_canvas(canvas_id)
    
    if not canvas:
        raise HTTPException(status_code=404, detail="Canvas 不存在")
    
    element_id = canvas.add_text(text, style)
    return {
        "success": True,
        "element_id": element_id
    }


@router.post("/canvas/{canvas_id}/button")
async def add_canvas_button(canvas_id: str, text: str, action_id: str):
    """添加按钮元素"""
    manager = get_canvas_manager()
    canvas = manager.get_canvas(canvas_id)
    
    if not canvas:
        raise HTTPException(status_code=404, detail="Canvas 不存在")
    
    element_id = canvas.add_button(text, action_id)
    return {
        "success": True,
        "element_id": element_id
    }


@router.post("/canvas/{canvas_id}/card")
async def add_canvas_card(canvas_id: str, title: str, content: str, buttons: Optional[List[Dict]] = None):
    """添加卡片元素"""
    manager = get_canvas_manager()
    canvas = manager.get_canvas(canvas_id)
    
    if not canvas:
        raise HTTPException(status_code=404, detail="Canvas 不存在")
    
    element_id = canvas.add_card(title, content, buttons)
    return {
        "success": True,
        "element_id": element_id
    }


@router.delete("/canvas/{canvas_id}/elements/{element_id}")
async def remove_canvas_element(canvas_id: str, element_id: str):
    """移除元素"""
    manager = get_canvas_manager()
    canvas = manager.get_canvas(canvas_id)
    
    if not canvas:
        raise HTTPException(status_code=404, detail="Canvas 不存在")
    
    success = canvas.remove_element(element_id)
    return {
        "success": success,
        "message": "元素已移除" if success else "元素未找到"
    }


@router.post("/canvas/{canvas_id}/message")
async def show_canvas_message(canvas_id: str, text: str, duration: float = 3.0):
    """显示临时消息"""
    manager = get_canvas_manager()
    canvas = manager.get_canvas(canvas_id)
    
    if not canvas:
        raise HTTPException(status_code=404, detail="Canvas 不存在")
    
    canvas.show_message(text, duration)
    return {"success": True}


@router.post("/canvas/{canvas_id}/action/{action_id}")
async def dispatch_canvas_action(canvas_id: str, action_id: str, data: Optional[Dict] = None):
    """分发 Canvas 动作"""
    manager = get_canvas_manager()
    canvas = manager.get_canvas(canvas_id)
    
    if not canvas:
        raise HTTPException(status_code=404, detail="Canvas 不存在")
    
    result = await canvas.dispatch_action(action_id, data)
    return {
        "success": True,
        "result": result
    }


# ========== LLM Router API ==========

@router.get("/llm-router/status")
async def get_llm_router_status():
    """获取 LLM 路由器状态"""
    router = get_llm_router()
    return {
        "success": True,
        "status": router.get_status()
    }


class AddProviderRequest(BaseModel):
    provider: str
    model: str
    api_key: str = ""
    base_url: Optional[str] = None
    priority: int = 0
    weight: float = 1.0


@router.post("/llm-router/provider")
async def add_llm_provider(request: AddProviderRequest):
    """添加 LLM 提供方"""
    try:
        provider_enum = LLMProvider(request.provider)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"不支持的提供方: {request.provider}")
    
    router = get_llm_router()
    provider_id = router.add_provider(LLMConfig(
        provider=provider_enum,
        model=request.model,
        api_key=request.api_key,
        base_url=request.base_url,
        priority=request.priority,
        weight=request.weight
    ))
    
    return {
        "success": True,
        "provider_id": provider_id,
        "message": "LLM 提供方已添加"
    }


@router.delete("/llm-router/provider/{provider_id}")
async def remove_llm_provider(provider_id: str):
    """移除 LLM 提供方"""
    router = get_llm_router()
    success = router.remove_provider(provider_id)
    
    return {
        "success": success,
        "message": "LLM 提供方已移除" if success else "LLM 提供方未找到"
    }


class LLMCompleteRequest(BaseModel):
    messages: List[Dict]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 2048


@router.post("/llm-router/complete")
async def llm_complete(request: LLMCompleteRequest):
    """智能 LLM 调用（带故障转移）"""
    router = get_llm_router()
    
    if not router.providers:
        # 添加一些默认的提供方用于演示
        router.add_provider(LLMConfig(
            provider=LLMProvider.OPENAI,
            model="gpt-4",
            priority=10
        ))
        router.add_provider(LLMConfig(
            provider=LLMProvider.ANTHROPIC,
            model="claude-3",
            priority=8
        ))
    
    result = await router.complete(
        messages=request.messages,
        temperature=request.temperature,
        max_tokens=request.max_tokens
    )
    
    return result


@router.post("/llm-router/strategy/{strategy}")
async def set_llm_strategy(strategy: str):
    """设置路由策略"""
    if strategy not in ["priority", "round_robin", "weighted_random"]:
        raise HTTPException(status_code=400, detail="无效的策略")
    
    router = get_llm_router()
    router.strategy = strategy
    return {"success": True, "strategy": strategy}


# ========== Agent Orchestrator API ==========

@router.get("/orchestrator/status")
async def get_orchestrator_status():
    """获取编排器状态"""
    orchestrator = get_agent_orchestrator()
    return {
        "success": True,
        "status": orchestrator.get_status()
    }


@router.post("/orchestrator/start")
async def start_orchestrator():
    """启动编排器"""
    orchestrator = get_agent_orchestrator()
    await orchestrator.start()
    return {"success": True, "message": "编排器已启动"}


@router.post("/orchestrator/stop")
async def stop_orchestrator():
    """停止编排器"""
    orchestrator = get_agent_orchestrator()
    await orchestrator.stop()
    return {"success": True, "message": "编排器已停止"}


class RegisterAgentRequest(BaseModel):
    name: str
    capabilities: Optional[List[str]] = None


@router.post("/orchestrator/agent")
async def register_orchestrator_agent(request: RegisterAgentRequest):
    """注册 Agent"""
    orchestrator = get_agent_orchestrator()
    agent_id = f"agent_{request.name.lower()}"
    orchestrator.register_agent(agent_id, request.name, request.capabilities)
    
    return {
        "success": True,
        "agent_id": agent_id
    }


class CreateTaskRequest(BaseModel):
    description: str
    agent_id: Optional[str] = None
    priority: int = 5
    dependencies: Optional[List[str]] = None


@router.post("/orchestrator/task")
async def create_orchestrator_task(request: CreateTaskRequest):
    """创建任务"""
    orchestrator = get_agent_orchestrator()
    task_id = orchestrator.create_task(
        description=request.description,
        agent_id=request.agent_id,
        priority=request.priority,
        dependencies=request.dependencies
    )
    
    return {
        "success": True,
        "task_id": task_id
    }


@router.get("/orchestrator/tasks")
async def list_orchestrator_tasks(status: Optional[str] = None):
    """列出任务"""
    orchestrator = get_agent_orchestrator()
    
    status_enum = None
    if status:
        try:
            from core.orchestrator import AgentTaskStatus
            status_enum = AgentTaskStatus(status)
        except ValueError:
            pass
    
    return {
        "success": True,
        "tasks": orchestrator.list_tasks(status_enum)
    }


@router.get("/orchestrator/task/{task_id}")
async def get_orchestrator_task(task_id: str):
    """获取任务详情"""
    orchestrator = get_agent_orchestrator()
    task = orchestrator.get_task(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="任务未找到")
    
    return {
        "success": True,
        "task": {
            "id": task.id,
            "description": task.description,
            "status": task.status.value,
            "assigned_to": task.assigned_to,
            "result": task.result,
            "error": task.error
        }
    }


@router.delete("/orchestrator/task/{task_id}")
async def cancel_orchestrator_task(task_id: str):
    """取消任务"""
    orchestrator = get_agent_orchestrator()
    success = orchestrator.cancel_task(task_id)
    
    return {
        "success": success,
        "message": "任务已取消" if success else "任务未找到或无法取消"
    }
