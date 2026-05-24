"""
DataAgent - 完整的工作流编排系统
支持可视化拖拽、节点连接、条件分支等功能
"""
import asyncio
import json
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union, Callable
from pydantic import BaseModel, Field

from app.agent.base import BaseAgent
from app.flow.base import BaseFlow
from app.llm import LLM
from app.logger import logger
from app.tool import ToolCollection


class NodeType(str, Enum):
    """节点类型"""
    START = "start"
    END = "end"
    AGENT = "agent"
    TOOL = "tool"
    CONDITION = "condition"
    PARALLEL = "parallel"
    LOOP = "loop"
    DATA_TRANSFORM = "data_transform"


class NodeStatus(str, Enum):
    """节点执行状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class Node(BaseModel):
    """工作流节点"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: NodeType
    name: str
    description: str = ""
    config: Dict[str, Any] = Field(default_factory=dict)
    status: NodeStatus = NodeStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    dependencies: List[str] = Field(default_factory=list)


class Edge(BaseModel):
    """工作流边（节点连接）"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source: str  # 源节点ID
    target: str  # 目标节点ID
    condition: Optional[str] = None  # 条件表达式（仅用于条件分支）
    label: str = ""


class Workflow(BaseModel):
    """工作流定义"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    nodes: List[Node] = Field(default_factory=list)
    edges: List[Edge] = Field(default_factory=list)
    variables: Dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    is_active: bool = True
    tags: List[str] = Field(default_factory=list)


class WorkflowExecution(BaseModel):
    """工作流执行记录"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workflow_id: str
    workflow_name: str
    started_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None
    status: NodeStatus = NodeStatus.PENDING
    node_executions: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    inputs: Dict[str, Any] = Field(default_factory=dict)
    outputs: Dict[str, Any] = Field(default_factory=dict)
    logs: List[Dict[str, Any]] = Field(default_factory=list)


class WorkflowEngine:
    """工作流引擎"""
    
    def __init__(self):
        self.workflows: Dict[str, Workflow] = {}
        self.executions: Dict[str, WorkflowExecution] = {}
        self.llm = LLM()
        self._node_registry: Dict[NodeType, Callable] = {}
        self._register_default_nodes()
    
    def _register_default_nodes(self):
        """注册默认节点处理器"""
        self._node_registry = {
            NodeType.START: self._handle_start_node,
            NodeType.END: self._handle_end_node,
            NodeType.AGENT: self._handle_agent_node,
            NodeType.TOOL: self._handle_tool_node,
            NodeType.CONDITION: self._handle_condition_node,
            NodeType.PARALLEL: self._handle_parallel_node,
            NodeType.LOOP: self._handle_loop_node,
            NodeType.DATA_TRANSFORM: self._handle_data_transform_node,
        }
    
    def create_workflow(self, name: str, description: str = "") -> Workflow:
        """创建新工作流"""
        workflow = Workflow(
            name=name,
            description=description
        )
        # 添加默认的开始和结束节点
        start_node = Node(type=NodeType.START, name="开始", description="工作流开始")
        end_node = Node(type=NodeType.END, name="结束", description="工作流结束")
        workflow.nodes.extend([start_node, end_node])
        workflow.edges.append(Edge(source=start_node.id, target=end_node.id, label="默认流程"))
        
        self.workflows[workflow.id] = workflow
        logger.info(f"创建工作流: {name} (ID: {workflow.id})")
        return workflow
    
    def add_node(self, workflow_id: str, node: Node) -> Workflow:
        """添加节点到工作流"""
        if workflow_id not in self.workflows:
            raise ValueError(f"工作流不存在: {workflow_id}")
        
        workflow = self.workflows[workflow_id]
        workflow.nodes.append(node)
        workflow.updated_at = datetime.now().isoformat()
        logger.info(f"添加节点: {node.name} 到工作流: {workflow.name}")
        return workflow
    
    def add_edge(self, workflow_id: str, edge: Edge) -> Workflow:
        """添加边（节点连接）"""
        if workflow_id not in self.workflows:
            raise ValueError(f"工作流不存在: {workflow_id}")
        
        workflow = self.workflows[workflow_id]
        workflow.edges.append(edge)
        workflow.updated_at = datetime.now().isoformat()
        logger.info(f"添加边: {edge.source} -> {edge.target}")
        return workflow
    
    def delete_node(self, workflow_id: str, node_id: str) -> Workflow:
        """删除节点"""
        if workflow_id not in self.workflows:
            raise ValueError(f"工作流不存在: {workflow_id}")
        
        workflow = self.workflows[workflow_id]
        workflow.nodes = [n for n in workflow.nodes if n.id != node_id]
        # 删除相关边
        workflow.edges = [e for e in workflow.edges if e.source != node_id and e.target != node_id]
        workflow.updated_at = datetime.now().isoformat()
        logger.info(f"删除节点: {node_id}")
        return workflow
    
    def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """获取工作流"""
        return self.workflows.get(workflow_id)
    
    def list_workflows(self, include_inactive: bool = False) -> List[Workflow]:
        """列出所有工作流"""
        return [
            w for w in self.workflows.values() if include_inactive or w.is_active]
    
    async def execute_workflow(
        self,
        workflow_id: str,
        inputs: Dict[str, Any] = None,
        agents: Optional[Dict[str, BaseAgent]] = None,
        tools: Optional[ToolCollection] = None
    ) -> WorkflowExecution:
        """执行工作流"""
        if workflow_id not in self.workflows:
            raise ValueError(f"工作流不存在: {workflow_id}")
        
        workflow = self.workflows[workflow_id]
        execution = WorkflowExecution(
            workflow_id=workflow_id,
            workflow_name=workflow.name,
            inputs=inputs or {},
            status=NodeStatus.RUNNING
        )
        self.executions[execution.id] = execution
        
        logger.info(f"开始执行工作流: {workflow.name} (ID: {execution.id})")
        
        try:
            await self._execute_workflow_nodes(
                workflow,
                execution,
                agents or {},
                tools
            )
            execution.status = NodeStatus.COMPLETED
        except Exception as e:
            execution.status = NodeStatus.FAILED
            execution.logs.append({
                "timestamp": datetime.now().isoformat(),
                "level": "error",
                "message": str(e)
            })
            logger.error(f"工作流执行失败: {str(e)}")
        
        execution.completed_at = datetime.now().isoformat()
        return execution
    
    async def _execute_workflow_nodes(
        self,
        workflow: Workflow,
        execution: WorkflowExecution,
        agents: Dict[str, BaseAgent],
        tools: Optional[ToolCollection]
    ):
        """执行工作流节点"""
        # 查找开始节点
        start_node = next((n for n in workflow.nodes if n.type == NodeType.START), None)
        if not start_node:
            raise ValueError("工作流缺少开始节点")
        
        # 构建执行顺序（拓扑排序）
        execution_order = self._get_execution_order(workflow)
        
        # 执行上下文
        context = {
            "workflow": workflow,
            "execution": execution,
            "agents": agents,
            "tools": tools,
            "variables": workflow.variables.copy()
        }
        
        # 依次执行节点
        for node_id in execution_order:
            node = next((n for n in workflow.nodes if n.id == node_id), None)
            if not node:
                continue
            
            await self._execute_node(node, context, execution)
    
    def _get_execution_order(self, workflow: Workflow) -> List[str]:
        """获取节点执行顺序（拓扑排序）"""
        visited = set()
        order = []
        
        def visit(node_id: str):
            if node_id in visited:
                return
            visited.add(node_id)
            
            # 找到所有依赖此节点的目标节点
            target_nodes = [e.target for e in workflow.edges if e.source == node_id]
            
            for target in target_nodes:
                visit(target)
            
            order.insert(0, node_id)
        
        # 从开始节点开始
        start_node = next((n for n in workflow.nodes if n.type == NodeType.START), None)
        if start_node:
            visit(start_node.id)
        
        return order
    
    async def _execute_node(
        self,
        node: Node,
        context: Dict[str, Any],
        execution: WorkflowExecution
    ):
        """执行单个节点"""
        logger.info(f"执行节点: {node.name} ({node.type})")
        
        node_execution = {
            "node_id": node.id,
            "node_name": node.name,
            "node_type": node.type,
            "started_at": datetime.now().isoformat(),
            "status": NodeStatus.RUNNING
        }
        execution.node_executions[node.id] = node_execution
        
        try:
            node.status = NodeStatus.RUNNING
            node.started_at = datetime.now().isoformat()
            
            # 根据节点类型处理
            handler = self._node_registry.get(node.type)
            if handler:
                result = await handler(node, context, execution)
                node.result = result
                node.status = NodeStatus.COMPLETED
            else:
                node.result = {"success": True, "message": "节点执行完成"}
                node.status = NodeStatus.COMPLETED
            
            node.completed_at = datetime.now().isoformat()
            
            node_execution["status"] = node.status
            node_execution["result"] = node.result
            node_execution["completed_at"] = node.completed_at
            
            execution.logs.append({
                "timestamp": datetime.now().isoformat(),
                "level": "info",
                "message": f"节点 {node.name} 执行完成"
            })
            
        except Exception as e:
            node.status = NodeStatus.FAILED
            node.error = str(e)
            node.completed_at = datetime.now().isoformat()
            
            node_execution["status"] = node.status
            node_execution["error"] = str(e)
            node_execution["completed_at"] = node.completed_at
            
            execution.logs.append({
                "timestamp": datetime.now().isoformat(),
                "level": "error",
                "message": f"节点 {node.name} 执行失败: {str(e)}"
            })
            
            raise
    
    async def _handle_start_node(self, node: Node, context: Dict, execution: WorkflowExecution) -> Dict[str, Any]:
        """处理开始节点"""
        return {"success": True, "inputs": execution.inputs}
    
    async def _handle_end_node(self, node: Node, context: Dict, execution: WorkflowExecution) -> Dict[str, Any]:
        """处理结束节点"""
        return {"success": True, "outputs": execution.outputs}
    
    async def _handle_agent_node(self, node: Node, context: Dict, execution: WorkflowExecution) -> Dict[str, Any]:
        """处理Agent节点"""
        agent_key = node.config.get("agent_key")
        prompt = node.config.get("prompt", "")
        agents = context.get("agents", {})
        
        if agent_key not in agents:
            raise ValueError(f"Agent '{agent_key}' 不存在")
        
        agent = agents[agent_key]
        
        # 构建prompt，可用上下文变量
        prompt = self._interpolate_variables(prompt, execution)
        
        result = await agent.run(prompt)
        return {"success": True, "result": result}
    
    async def _handle_tool_node(self, node: Node, context: Dict, execution: WorkflowExecution) -> Dict[str, Any]:
        """处理工具节点"""
        tool_name = node.config.get("tool_name")
        tool_params = node.config.get("params", {})
        tools = context.get("tools")
        
        if not tools:
            raise ValueError("没有可用的工具")
        
        # 插值参数
        interpolated_params = {
            k: self._interpolate_variables(str(v), execution)
            for k, v in tool_params.items()
        }
        
        result = await tools.execute_tool(tool_name, **interpolated_params)
        return {"success": True, "result": result}
    
    async def _handle_condition_node(self, node: Node, context: Dict, execution: WorkflowExecution) -> Dict[str, Any]:
        """处理条件节点"""
        condition = node.config.get("condition", "")
        condition = self._interpolate_variables(condition, execution)
        
        # 简单的条件评估
        try:
            result = eval(condition)
            return {"success": True, "result": bool(result)}
        except Exception as e:
            return {"success": True, "result": False, "error": str(e)}
    
    async def _handle_parallel_node(self, node: Node, context: Dict, execution: WorkflowExecution) -> Dict[str, Any]:
        """处理并行节点"""
        parallel_tasks = node.config.get("tasks", [])
        results = []
        
        async def execute_task(task_config):
            # 这里简化处理，实际可以执行子任务
            return {"task": task_config}
        
        tasks = [execute_task(task) for task in parallel_tasks]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return {"success": True, "results": results}
    
    async def _handle_loop_node(self, node: Node, context: Dict, execution: WorkflowExecution) -> Dict[str, Any]:
        """处理循环节点"""
        loop_var = node.config.get("loop_var", "items")
        max_iterations = node.config.get("max_iterations", 100)
        
        items = execution.outputs.get(loop_var, [])
        results = []
        
        for i, item in enumerate(items[:max_iterations]):
            results.append({"index": i, "item": item})
        
        return {"success": True, "results": results}
    
    async def _handle_data_transform_node(self, node: Node, context: Dict, execution: WorkflowExecution) -> Dict[str, Any]:
        """处理数据转换节点"""
        transform_type = node.config.get("transform_type", "map")
        mapping = node.config.get("mapping", {})
        
        result = {}
        for src, dest in mapping.items():
            dest = dest or src
            if src in execution.outputs:
                result[dest] = execution.outputs[src]
        
        return {"success": True, "transformed": result}
    
    def _interpolate_variables(self, text: str, execution: WorkflowExecution) -> str:
        """插值变量"""
        import re
        
        result = text
        pattern = r'\$\{([^}]+)\}'
        
        def replace(match):
            var_name = match.group(1)
            # 尝试从不同位置查找变量
            value = execution.outputs.get(var_name) or execution.inputs.get(var_name) or ''
            return str(value)
        
        return re.sub(pattern, replace, result)
    
    def get_execution(self, execution_id: str) -> Optional[WorkflowExecution]:
        """获取执行记录"""
        return self.executions.get(execution_id)
    
    def to_dict(self, workflow: Workflow) -> Dict[str, Any]:
        """工作流转为字典（用于前端渲染）"""
        return {
            "id": workflow.id,
            "name": workflow.name,
            "description": workflow.description,
            "nodes": [
                {
                    "id": n.id,
                    "type": n.type,
                    "name": n.name,
                    "description": n.description,
                    "config": n.config,
                    "status": n.status,
                    "metadata": n.metadata
                }
                for n in workflow.nodes
            ],
            "edges": [
                {
                    "id": e.id,
                    "source": e.source,
                    "target": e.target,
                    "condition": e.condition,
                    "label": e.label
                }
                for e in workflow.edges
            ],
            "variables": workflow.variables
        }
    
    def from_dict(self, data: Dict[str, Any]) -> Workflow:
        """从字典加载工作流"""
        workflow = Workflow(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", ""),
            description=data.get("description", ""),
            variables=data.get("variables", {})
        )
        
        for node_data in data.get("nodes", []):
            node = Node(**node_data)
            workflow.nodes.append(node)
        
        for edge_data in data.get("edges", []):
            edge = Edge(**edge_data)
            workflow.edges.append(edge)
        
        return workflow


# 全局工作流引擎实例
workflow_engine = WorkflowEngine()


__all__ = [
    "NodeType",
    "NodeStatus",
    "Node",
    "Edge",
    "Workflow",
    "WorkflowExecution",
    "WorkflowEngine",
    "workflow_engine"
]
