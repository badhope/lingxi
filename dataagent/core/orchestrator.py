"""
DataAgent - 多 Agent 编排系统 & LLM 路由故障转移
借鉴 OpenClaw 的多 Agent 协同和 LLM 路由功能
"""
import asyncio
import time
import uuid
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from enum import Enum

from core.logging import get_logger

logger = get_logger("orchestrator")


class LLMProvider(str, Enum):
    """LLM 提供方"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    OLLAMA = "ollama"
    QIANWEN = "qianwen"
    DEEPSEEK = "deepseek"


@dataclass
class LLMConfig:
    """LLM 配置"""
    provider: LLMProvider
    model: str
    api_key: str = ""
    base_url: Optional[str] = None
    priority: int = 0
    enabled: bool = True
    weight: float = 1.0
    max_retries: int = 3
    timeout: int = 30
    temperature: float = 0.7
    max_tokens: int = 2048


@dataclass
class LLMMetrics:
    """LLM 调用指标"""
    requests: int = 0
    successes: int = 0
    failures: int = 0
    total_time: float = 0
    last_success: Optional[float] = None
    last_failure: Optional[float] = None
    error_count: int = 0


class LLMRouter:
    """
    LLM 路由和故障转移管理器
    支持多个 LLM 提供方，智能路由和故障转移
    """
    
    def __init__(self):
        self.providers: Dict[str, LLMConfig] = {}
        self.metrics: Dict[str, LLMMetrics] = {}
        self.routers: List[str] = []
        
        # 路由策略
        self.strategy: str = "priority"  # priority, round_robin, weighted_random
        
        logger.info("LLMRouter 初始化完成")
    
    def add_provider(self, config: LLMConfig) -> str:
        """添加 LLM 提供方"""
        provider_id = f"{config.provider.value}_{uuid.uuid4().hex[:8]}"
        self.providers[provider_id] = config
        self.metrics[provider_id] = LLMMetrics()
        self.routers.append(provider_id)
        logger.info(f"添加 LLM 提供方: {config.provider.value} - {config.model}")
        return provider_id
    
    def remove_provider(self, provider_id: str) -> bool:
        """移除 LLM 提供方"""
        if provider_id in self.providers:
            del self.providers[provider_id]
            del self.metrics[provider_id]
            if provider_id in self.routers:
                self.routers.remove(provider_id)
            logger.info(f"移除 LLM 提供方: {provider_id}")
            return True
        return False
    
    def get_provider(self, provider_id: str) -> Optional[LLMConfig]:
        """获取 LLM 配置"""
        return self.providers.get(provider_id)
    
    def get_next_provider(self) -> Optional[str]:
        """获取下一个可用的 LLM 提供方"""
        enabled_providers = [
            pid for pid in self.routers
            if self.providers[pid].enabled
        ]
        
        if not enabled_providers:
            return None
        
        if self.strategy == "priority":
            # 按优先级排序
            enabled_providers.sort(
                key=lambda pid: (
                    -self.providers[pid].priority,
                    -self.metrics[pid].successes / max(1, self.metrics[pid].requests)
                )
            )
            return enabled_providers[0]
        
        elif self.strategy == "round_robin":
            # 简单的轮询
            if not hasattr(self, '_rr_index'):
                self._rr_index = 0
            provider = enabled_providers[self._rr_index % len(enabled_providers)]
            self._rr_index += 1
            return provider
        
        elif self.strategy == "weighted_random":
            # 加权随机
            total_weight = sum(
                self.providers[pid].weight
                for pid in enabled_providers
            )
            if total_weight <= 0:
                total_weight = len(enabled_providers)
                weights = [1.0 for _ in enabled_providers]
            else:
                weights = [
                    self.providers[pid].weight / total_weight
                    for pid in enabled_providers
                ]
            
            r = random.random()
            cumulative = 0
            for i, provider_id in enumerate(enabled_providers):
                cumulative += weights[i]
                if cumulative >= r:
                    return provider_id
            return enabled_providers[0] if enabled_providers else None
        
        return enabled_providers[0]
    
    def record_success(self, provider_id: str, elapsed: float):
        """记录成功调用"""
        if provider_id in self.metrics:
            metric = self.metrics[provider_id]
            metric.requests += 1
            metric.successes += 1
            metric.total_time += elapsed
            metric.last_success = time.time()
            metric.error_count = max(0, metric.error_count - 1)
    
    def record_failure(self, provider_id: str, elapsed: float):
        """记录失败调用"""
        if provider_id in self.metrics:
            metric = self.metrics[provider_id]
            metric.requests += 1
            metric.failures += 1
            metric.total_time += elapsed
            metric.last_failure = time.time()
            metric.error_count += 1
            
            # 连续失败过多，暂时禁用
            if metric.error_count >= 3:
                self.providers[provider_id].enabled = False
                logger.warning(f"LLM 提供方连续失败过多，暂时禁用: {provider_id}")
    
    async def complete(self, messages: List[Dict], **kwargs) -> Dict[str, Any]:
        """智能调用 LLM，支持故障转移"""
        start_time = time.time()
        
        providers_tried = []
        max_attempts = len(self.providers) + 1
        
        for attempt in range(max_attempts):
            provider_id = self.get_next_provider()
            
            if provider_id is None or provider_id in providers_tried:
                # 没有可用的提供方
                break
            
            providers_tried.append(provider_id)
            config = self.providers[provider_id]
            
            try:
                logger.debug(f"尝试 LLM 提供方 {attempt + 1}/{max_attempts}: {config.provider.value}")
                
                # 实际调用 - 这里可以接入各 LLM SDK
                result = await self._call_llm(config, messages, **kwargs)
                
                elapsed = time.time() - start_time
                self.record_success(provider_id, elapsed)
                
                return {
                    "success": True,
                    "content": result,
                    "provider": config.provider.value,
                    "model": config.model,
                    "provider_id": provider_id,
                    "elapsed": elapsed
                }
                
            except Exception as e:
                elapsed = time.time() - start_time
                self.record_failure(provider_id, elapsed)
                logger.warning(f"LLM 提供方 {config.provider.value} 调用失败: {e}")
                
                if attempt < max_attempts - 1:
                    logger.info("尝试下一个 LLM 提供方...")
        
        # 所有提供方都失败
        return {
            "success": False,
            "error": "所有 LLM 提供方调用失败",
            "providers_tried": providers_tried
        }
    
    async def _call_llm(self, config: LLMConfig, messages: List[Dict], **kwargs) -> str:
        """实际调用 LLM（模拟）"""
        # 这里应该集成各 LLM SDK
        # 模拟调用延迟
        await asyncio.sleep(0.1 + random.random() * 0.5)
        
        # 模拟 10% 失败率
        if random.random() < 0.1:
            raise Exception(f"模拟调用失败: {config.provider.value}")
        
        # 模拟响应
        return f"这是来自 {config.provider.value} {config.model} 的响应。"
    
    def get_status(self) -> Dict[str, Any]:
        """获取路由状态"""
        return {
            "strategy": self.strategy,
            "providers": [
                {
                    "id": pid,
                    "provider": config.provider.value,
                    "model": config.model,
                    "enabled": config.enabled,
                    "priority": config.priority,
                    "weight": config.weight,
                    "metrics": {
                        "requests": self.metrics[pid].requests,
                        "successes": self.metrics[pid].successes,
                        "failures": self.metrics[pid].failures,
                        "success_rate": (self.metrics[pid].successes / max(1, self.metrics[pid].requests)) * 100,
                        "avg_time": self.metrics[pid].total_time / max(1, self.metrics[pid].requests)
                    }
                }
                for pid, config in self.providers.items()
            ],
            "total_providers": len(self.providers),
            "enabled_providers": sum(1 for c in self.providers.values() if c.enabled)
        }


# ========== 多 Agent 编排系统 ==========

class AgentTaskStatus(str, Enum):
    """Agent 任务状态"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class AgentTask:
    """Agent 任务"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    description: str = ""
    assigned_to: Optional[str] = None
    status: AgentTaskStatus = AgentTaskStatus.PENDING
    priority: int = 5
    dependencies: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    result: Optional[Any] = None
    error: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None


class AgentOrchestrator:
    """
    多 Agent 编排器
    管理多个 Agent 的任务分配和协同工作
    """
    
    def __init__(self):
        self.tasks: Dict[str, AgentTask] = {}
        self.agents: Dict[str, Dict[str, Any]] = {}
        self.active_tasks: Dict[str, AgentTask] = {}
        self.completed_tasks: List[str] = []
        
        # 工作队列
        self.task_queue: List[AgentTask] = []
        self.running: bool = False
        self.worker_task: Optional[asyncio.Task] = None
        
        logger.info("AgentOrchestrator 初始化完成")
    
    def register_agent(self, agent_id: str, name: str, capabilities: Optional[List[str]] = None):
        """注册 Agent"""
        self.agents[agent_id] = {
            "id": agent_id,
            "name": name,
            "capabilities": capabilities or [],
            "status": "idle",
            "current_task": None
        }
        logger.info(f"注册 Agent: {name} ({agent_id})")
    
    def create_task(self, description: str, agent_id: Optional[str] = None, priority: int = 5, dependencies: Optional[List[str]] = None) -> str:
        """创建任务"""
        task = AgentTask(
            description=description,
            assigned_to=agent_id,
            priority=priority,
            dependencies=dependencies or []
        )
        self.tasks[task.id] = task
        self.task_queue.append(task)
        
        # 按优先级排序队列
        self.task_queue.sort(key=lambda t: (-t.priority, t.created_at))
        
        logger.info(f"创建任务: {task.id} - {description}")
        return task.id
    
    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        if task_id in self.tasks:
            task = self.tasks[task_id]
            if task.status in [AgentTaskStatus.PENDING, AgentTaskStatus.IN_PROGRESS]:
                task.status = AgentTaskStatus.CANCELLED
                logger.info(f"取消任务: {task_id}")
                return True
        return False
    
    async def start(self):
        """启动编排器"""
        if self.running:
            return
        
        self.running = True
        self.worker_task = asyncio.create_task(self._worker_loop())
        logger.info("AgentOrchestrator 启动")
    
    async def stop(self):
        """停止编排器"""
        self.running = False
        if self.worker_task:
            self.worker_task.cancel()
            try:
                await self.worker_task
            except asyncio.CancelledError:
                pass
        logger.info("AgentOrchestrator 停止")
    
    async def _worker_loop(self):
        """工作循环"""
        while self.running:
            try:
                await self._process_queue()
                await asyncio.sleep(0.5)
            except Exception as e:
                logger.error(f"工作循环错误: {e}")
                await asyncio.sleep(1)
    
    async def _process_queue(self):
        """处理任务队列"""
        for task in list(self.task_queue):
            if task.status != AgentTaskStatus.PENDING:
                continue
            
            # 检查依赖
            deps_ok = True
            for dep_id in task.dependencies:
                if dep_id in self.tasks:
                    dep_task = self.tasks[dep_id]
                    if dep_task.status != AgentTaskStatus.COMPLETED:
                        deps_ok = False
                        break
                else:
                    deps_ok = False
            
            if not deps_ok:
                continue
            
            # 分配任务
            if task.assigned_to:
                agent_id = task.assigned_to
            else:
                agent_id = self._select_agent(task)
            
            if agent_id:
                await self._assign_task(task, agent_id)
    
    def _select_agent(self, task: AgentTask) -> Optional[str]:
        """选择合适的 Agent"""
        # 选择空闲的 Agent
        for agent_id, agent in self.agents.items():
            if agent["status"] == "idle":
                return agent_id
        return None
    
    async def _assign_task(self, task: AgentTask, agent_id: str):
        """分配任务"""
        task.status = AgentTaskStatus.IN_PROGRESS
        task.started_at = time.time()
        task.assigned_to = agent_id
        
        if agent_id in self.agents:
            self.agents[agent_id]["status"] = "busy"
            self.agents[agent_id]["current_task"] = task.id
        
        self.active_tasks[task.id] = task
        
        # 从队列中移除
        if task in self.task_queue:
            self.task_queue.remove(task)
        
        logger.info(f"分配任务 {task.id} 给 Agent {agent_id}")
        
        # 模拟执行
        asyncio.create_task(self._execute_task(task))
    
    async def _execute_task(self, task: AgentTask):
        """执行任务（模拟）"""
        try:
            # 模拟工作
            await asyncio.sleep(1 + random.random() * 3)
            
            # 随机失败
            if random.random() < 0.1:
                raise Exception("模拟任务失败")
            
            # 完成任务
            task.status = AgentTaskStatus.COMPLETED
            task.result = f"任务 '{task.description}' 已完成"
            logger.info(f"任务完成: {task.id}")
        
        except Exception as e:
            task.status = AgentTaskStatus.FAILED
            task.error = str(e)
            logger.warning(f"任务失败: {task.id} - {e}")
        
        finally:
            task.completed_at = time.time()
            
            # 释放 Agent
            if task.assigned_to and task.assigned_to in self.agents:
                self.agents[task.assigned_to]["status"] = "idle"
                self.agents[task.assigned_to]["current_task"] = None
            
            # 从活动任务中移除
            if task.id in self.active_tasks:
                del self.active_tasks[task.id]
            
            self.completed_tasks.append(task.id)
    
    def get_task(self, task_id: str) -> Optional[AgentTask]:
        """获取任务"""
        return self.tasks.get(task_id)
    
    def list_tasks(self, status: Optional[AgentTaskStatus] = None) -> List[Dict]:
        """列出任务"""
        tasks_list = []
        for task in self.tasks.values():
            if status and task.status != status:
                continue
            tasks_list.append({
                "id": task.id,
                "description": task.description,
                "status": task.status.value,
                "priority": task.priority,
                "assigned_to": task.assigned_to,
                "result": task.result,
                "error": task.error,
                "created_at": task.created_at
            })
        return tasks_list
    
    def get_status(self) -> Dict[str, Any]:
        """获取编排器状态"""
        pending = sum(1 for t in self.tasks.values() if t.status == AgentTaskStatus.PENDING)
        in_progress = sum(1 for t in self.tasks.values() if t.status == AgentTaskStatus.IN_PROGRESS)
        completed = sum(1 for t in self.tasks.values() if t.status == AgentTaskStatus.COMPLETED)
        failed = sum(1 for t in self.tasks.values() if t.status == AgentTaskStatus.FAILED)
        
        return {
            "running": self.running,
            "agents": list(self.agents.values()),
            "tasks": {
                "total": len(self.tasks),
                "pending": pending,
                "in_progress": in_progress,
                "completed": completed,
                "failed": failed
            },
            "queue_length": len(self.task_queue)
        }


# 全局实例
_llm_router: Optional[LLMRouter] = None
_agent_orchestrator: Optional[AgentOrchestrator] = None


def get_llm_router() -> LLMRouter:
    """获取 LLM 路由器"""
    global _llm_router
    if _llm_router is None:
        _llm_router = LLMRouter()
    return _llm_router


def get_agent_orchestrator() -> AgentOrchestrator:
    """获取 Agent 编排器"""
    global _agent_orchestrator
    if _agent_orchestrator is None:
        _agent_orchestrator = AgentOrchestrator()
    return _agent_orchestrator
