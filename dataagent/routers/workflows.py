"""
DataAgent - 工作流编排 API
提供工作流管理、执行、可视化等功能
"""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Any, Dict, List, Optional

from app.flow.workflow import (
    NodeType,
    NodeStatus,
    Node,
    Edge,
    Workflow,
    WorkflowExecution,
    WorkflowEngine,
    workflow_engine
)
from app.agent.base import BaseAgent
from app.tool import ToolCollection
from core.auth import auth_manager, User, UserRole
from core.logging import get_logger

router = APIRouter(prefix="/api/workflows", tags=["工作流"])
logger = get_logger("workflow_api")


# 请求/响应模型
class CreateWorkflowRequest(BaseModel):
    name: str
    description: str = ""


class UpdateWorkflowRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    variables: Optional[Dict[str, Any]] = None


class AddNodeRequest(BaseModel):
    type: NodeType
    name: str
    description: str = ""
    config: Dict[str, Any] = {}
    metadata: Dict[str, Any] = {}
    dependencies: List[str] = []


class AddEdgeRequest(BaseModel):
    source: str
    target: str
    condition: Optional[str] = None
    label: str = ""


class ExecuteWorkflowRequest(BaseModel):
    inputs: Dict[str, Any] = {}


class WorkflowResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    message: str = ""


def get_current_user(request: Request):
    """获取当前用户（从请求头）"""
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:]
        return auth_manager.verify_session(token)
    return None


def require_permission(request: Request, permission=None):
    """检查权限"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="未授权")
    return user


@router.get("/")
async def list_workflows(request: Request, include_inactive: bool = False):
    """列出所有工作流"""
    user = require_permission(request)
    
    try:
        workflows = workflow_engine.list_workflows(include_inactive=include_inactive)
        return {
            "success": True,
            "data": [
                {
                    "id": w.id,
                    "name": w.name,
                    "description": w.description,
                    "nodes_count": len(w.nodes),
                    "edges_count": len(w.edges),
                    "created_at": w.created_at,
                    "updated_at": w.updated_at,
                    "is_active": w.is_active
                }
                for w in workflows
            ]
        }
    except Exception as e:
        logger.error(f"列出工作流失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/")
async def create_workflow(request: Request, body: CreateWorkflowRequest):
    """创建新工作流"""
    user = require_permission(request)
    
    try:
        workflow = workflow_engine.create_workflow(body.name, body.description)
        return {
            "success": True,
            "data": {
                "id": workflow.id,
                "name": workflow.name,
                "description": workflow.description
            },
            "message": "工作流创建成功"
        }
    except Exception as e:
        logger.error(f"创建工作流失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{workflow_id}")
async def get_workflow(request: Request, workflow_id: str):
    """获取工作流详情（用于可视化渲染）"""
    user = require_permission(request)
    
    workflow = workflow_engine.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="工作流不存在")
    
    return {
        "success": True,
        "data": workflow_engine.to_dict(workflow)
    }


@router.put("/{workflow_id}")
async def update_workflow(request: Request, workflow_id: str, body: UpdateWorkflowRequest):
    """更新工作流"""
    user = require_permission(request)
    
    workflow = workflow_engine.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="工作流不存在")
    
    if body.name is not None:
        workflow.name = body.name
    if body.description is not None:
        workflow.description = body.description
    if body.is_active is not None:
        workflow.is_active = body.is_active
    if body.variables is not None:
        workflow.variables = body.variables
    
    from datetime import datetime
    workflow.updated_at = datetime.now().isoformat()
    
    return {
        "success": True,
        "data": {"id": workflow.id},
        "message": "工作流更新成功"
    }


@router.delete("/{workflow_id}")
async def delete_workflow(request: Request, workflow_id: str):
    """删除工作流（软删除）"""
    user = require_permission(request)
    
    workflow = workflow_engine.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="工作流不存在")
    
    workflow.is_active = False
    from datetime import datetime
    workflow.updated_at = datetime.now().isoformat()
    
    return {
        "success": True,
        "message": "工作流删除成功"
    }


@router.post("/{workflow_id}/nodes")
async def add_node(request: Request, workflow_id: str, body: AddNodeRequest):
    """添加节点"""
    user = require_permission(request)
    
    try:
        node = Node(
            type=body.type,
            name=body.name,
            description=body.description,
            config=body.config,
            metadata=body.metadata,
            dependencies=body.dependencies
        )
        workflow = workflow_engine.add_node(workflow_id, node)
        return {
            "success": True,
            "data": {"node_id": node.id},
            "message": "节点添加成功"
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"添加节点失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{workflow_id}/nodes/{node_id}")
async def delete_node(request: Request, workflow_id: str, node_id: str):
    """删除节点"""
    user = require_permission(request)
    
    try:
        workflow_engine.delete_node(workflow_id, node_id)
        return {
            "success": True,
            "message": "节点删除成功"
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"删除节点失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{workflow_id}/edges")
async def add_edge(request: Request, workflow_id: str, body: AddEdgeRequest):
    """添加边（节点连接）"""
    user = require_permission(request)
    
    try:
        edge = Edge(
            source=body.source,
            target=body.target,
            condition=body.condition,
            label=body.label
        )
        workflow_engine.add_edge(workflow_id, edge)
        return {
            "success": True,
            "data": {"edge_id": edge.id},
            "message": "边添加成功"
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"添加边失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{workflow_id}/execute")
async def execute_workflow(request: Request, workflow_id: str, body: ExecuteWorkflowRequest):
    """执行工作流"""
    user = require_permission(request)
    
    try:
        # 这里简化处理，实际可以从服务中获取agents和tools
        agents = {}
        tools = None
        
        execution = await workflow_engine.execute_workflow(
            workflow_id,
            inputs=body.inputs,
            agents=agents,
            tools=tools
        )
        
        return {
            "success": True,
            "data": {
                "execution_id": execution.id,
                "status": execution.status,
                "started_at": execution.started_at,
                "completed_at": execution.completed_at
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"执行工作流失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{workflow_id}/executions")
async def list_workflow_executions(request: Request, workflow_id: str):
    """列出工作流执行记录"""
    user = require_permission(request)
    
    # 简化处理，实际需要从存储中查询
    return {
        "success": True,
        "data": []
    }


@router.get("/executions/{execution_id}")
async def get_execution(request: Request, execution_id: str):
    """获取执行详情"""
    user = require_permission(request)
    
    execution = workflow_engine.get_execution(execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="执行记录不存在")
    
    return {
        "success": True,
        "data": {
            "id": execution.id,
            "workflow_id": execution.workflow_id,
            "workflow_name": execution.workflow_name,
            "status": execution.status,
            "started_at": execution.started_at,
            "completed_at": execution.completed_at,
            "inputs": execution.inputs,
            "outputs": execution.outputs,
            "node_executions": execution.node_executions,
            "logs": execution.logs
        }
    }


@router.get("/templates/samples")
async def get_sample_workflows(request: Request):
    """获取示例工作流模板"""
    user = require_permission(request)
    
    # 预定义示例模板
    samples = [
        {
            "id": "data_analysis",
            "name": "数据分析工作流",
            "description": "从数据加载到可视化的完整分析流程",
            "nodes": [
                {"type": "data_transform", "name": "数据清洗", "description": "清洗和预处理数据"},
                {"type": "agent", "name": "数据分析", "description": "AI数据分析Agent", "config": {"agent_key": "data_analyst"}},
                {"type": "tool", "name": "生成图表", "description": "使用图表工具生成可视化", "config": {"tool_name": "generate_chart"}}
            ],
            "tags": ["数据分析", "可视化"]
        },
        {
            "id": "customer_service",
            "name": "客户服务工作流",
            "description": "自动处理客户请求和反馈",
            "nodes": [
                {"type": "start", "name": "接收请求"},
                {"type": "condition", "name": "判断类型", "config": {"condition": "request_type == 'complaint'"}},
                {"type": "agent", "name": "投诉处理", "config": {"agent_key": "complaint_agent"}},
                {"type": "agent", "name": "咨询处理", "config": {"agent_key": "inquiry_agent"}}
            ],
            "tags": ["客服", "自动化"]
        }
    ]
    
    return {
        "success": True,
        "data": samples
    }
