"""
DataAgent - Gateway 守护进程系统
借鉴 OpenClaw 的 Gateway 概念，提供长期运行的守护进程、多 Agent 协调、事件总线
"""
import asyncio
import threading
import time
import json
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from pathlib import Path
from datetime import datetime

from core.logging import get_logger
from core.heartbeat import HeartbeatEngine
from core.memory import MemoryEngine
from core.workspace import get_workspace_manager

logger = get_logger("gateway")


class GatewayStatus(str, Enum):
    """Gateway 状态"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"


@dataclass
class GatewayEvent:
    """Gateway 事件"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: str
    source: str
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    processed: bool = False


@dataclass
class AgentInstance:
    """运行中的 Agent 实例"""
    id: str
    name: str
    personality: str = "default"
    status: str = "idle"
    channel: str = "console"
    last_active: float = field(default_factory=time.time)
    config: Dict[str, Any] = field(default_factory=dict)
    session_id: Optional[str] = None


class Gateway:
    """
    DataAgent Gateway - 中央协调守护进程
    类似 OpenClaw 的 Gateway 架构
    """
    
    def __init__(self, workspace_path: Optional[Path] = None):
        self.status = GatewayStatus.STOPPED
        self.workspace_path = workspace_path
        self.workspace_manager = get_workspace_manager(workspace_path)
        
        # 组件
        self.heartbeat_engine: Optional[HeartbeatEngine] = None
        self.memory_engine: Optional[MemoryEngine] = None
        
        # Agent 管理
        self.agents: Dict[str, AgentInstance] = {}
        self.main_agent: Optional[AgentInstance] = None
        
        # 事件总线
        self.event_queue: List[GatewayEvent] = []
        self.event_handlers: Dict[str, List[Callable]] = {}
        self.event_lock = asyncio.Lock()
        
        # 后台任务
        self._main_loop_task: Optional[asyncio.Task] = None
        self._monitor_task: Optional[asyncio.Task] = None
        
        # 配置
        self.config = {
            "auto_start_heartbeat": True,
            "auto_save_memory": True,
            "log_events": True,
            "event_queue_max": 1000
        }
        
        logger.info("Gateway 初始化完成")
    
    async def start(self):
        """启动 Gateway"""
        if self.status == GatewayStatus.RUNNING:
            logger.warning("Gateway 已在运行")
            return
        
        logger.info("Gateway 启动中...")
        self.status = GatewayStatus.STARTING
        
        try:
            # 初始化组件
            from core.heartbeat import get_heartbeat_engine
            from core.memory import get_memory_engine
            
            self.heartbeat_engine = get_heartbeat_engine()
            self.memory_engine = get_memory_engine()
            
            # 创建主 Agent
            self._initialize_agents()
            
            # 启动后台任务
            self._main_loop_task = asyncio.create_task(self._main_loop())
            self._monitor_task = asyncio.create_task(self._monitor_loop())
            
            # 启动心跳引擎
            if self.config["auto_start_heartbeat"]:
                await self.heartbeat_engine.start()
            
            self.status = GatewayStatus.RUNNING
            logger.info("Gateway 启动成功！")
            
            # 发送启动事件
            await self.emit_event("gateway.started", {"timestamp": time.time()})
            
        except Exception as e:
            logger.error(f"Gateway 启动失败: {e}", exc_info=True)
            self.status = GatewayStatus.ERROR
            raise
    
    async def stop(self):
        """停止 Gateway"""
        if self.status == GatewayStatus.STOPPED:
            return
        
        logger.info("Gateway 停止中...")
        self.status = GatewayStatus.STOPPING
        
        # 发送停止事件
        await self.emit_event("gateway.stopping", {"timestamp": time.time()})
        
        try:
            # 停止心跳
            if self.heartbeat_engine:
                await self.heartbeat_engine.stop()
            
            # 取消任务
            if self._main_loop_task:
                self._main_loop_task.cancel()
            if self._monitor_task:
                self._monitor_task.cancel()
            
            # 等待任务结束
            if self._main_loop_task:
                try:
                    await self._main_loop_task
                except asyncio.CancelledError:
                    pass
            
            if self._monitor_task:
                try:
                    await self._monitor_task
                except asyncio.CancelledError:
                    pass
            
            self.status = GatewayStatus.STOPPED
            logger.info("Gateway 已停止")
            
        except Exception as e:
            logger.error(f"Gateway 停止失败: {e}", exc_info=True)
            self.status = GatewayStatus.ERROR
    
    def _initialize_agents(self):
        """初始化 Agent 配置"""
        agents_config = self.workspace_manager.parse_agents_md()
        
        for agent_config in agents_config:
            if agent_config.enabled:
                agent = AgentInstance(
                    id=f"agent_{agent_config.name}",
                    name=agent_config.name,
                    personality=agent_config.personality,
                    channel="console",
                    config={
                        "model": agent_config.model,
                        "skills": agent_config.skills,
                        "description": agent_config.description
                    }
                )
                self.agents[agent.id] = agent
                
                # 设置主 Agent
                if agent_config.name == "main":
                    self.main_agent = agent
                    logger.info(f"主 Agent 已设置: {agent.name}")
        
        if not self.main_agent and self.agents:
            # 使用第一个 Agent 作为主 Agent
            self.main_agent = next(iter(self.agents.values()))
            logger.info(f"使用首个 Agent 作为主 Agent: {self.main_agent.name}")
    
    async def _main_loop(self):
        """主事件循环"""
        logger.info("主事件循环启动")
        
        while self.status in [GatewayStatus.STARTING, GatewayStatus.RUNNING]:
            try:
                # 处理事件队列
                await self._process_events()
                
                # 短延迟，避免 CPU 占用
                await asyncio.sleep(0.1)
                
            except asyncio.CancelledError:
                logger.info("主事件循环已取消")
                break
            except Exception as e:
                logger.error(f"主事件循环错误: {e}", exc_info=True)
                await asyncio.sleep(1)
    
    async def _monitor_loop(self):
        """监控循环"""
        logger.info("监控循环启动")
        
        while self.status in [GatewayStatus.STARTING, GatewayStatus.RUNNING]:
            try:
                # 更新 Agent 活跃时间
                for agent in self.agents.values():
                    if agent.status == "active":
                        agent.last_active = time.time()
                
                # 定期清理事件队列
                async with self.event_lock:
                    if len(self.event_queue) > self.config["event_queue_max"]:
                        self.event_queue = self.event_queue[-self.config["event_queue_max"]:]
                
                await asyncio.sleep(5)
                
            except asyncio.CancelledError:
                logger.info("监控循环已取消")
                break
            except Exception as e:
                logger.error(f"监控循环错误: {e}", exc_info=True)
                await asyncio.sleep(5)
    
    async def _process_events(self):
        """处理事件队列"""
        async with self.event_lock:
            events_to_process = [e for e in self.event_queue if not e.processed]
            
            for event in events_to_process:
                try:
                    # 调用事件处理器
                    if event.type in self.event_handlers:
                        for handler in self.event_handlers[event.type]:
                            try:
                                if asyncio.iscoroutinefunction(handler):
                                    await handler(event)
                                else:
                                    handler(event)
                            except Exception as e:
                                logger.error(f"事件处理器错误 {event.type}: {e}")
                    
                    # 记录事件
                    if self.config["log_events"]:
                        logger.debug(f"处理事件: {event.type} - {event.source}")
                    
                    event.processed = True
                    
                except Exception as e:
                    logger.error(f"事件处理错误: {e}")
    
    async def emit_event(self, event_type: str, data: Dict[str, Any], source: str = "gateway"):
        """发送事件"""
        event = GatewayEvent(
            type=event_type,
            source=source,
            data=data
        )
        
        async with self.event_lock:
            self.event_queue.append(event)
        
        return event
    
    def on_event(self, event_type: str, handler: Callable):
        """注册事件监听器"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        
        self.event_handlers[event_type].append(handler)
        logger.debug(f"事件监听器已注册: {event_type}")
    
    def get_agent(self, agent_id: str) -> Optional[AgentInstance]:
        """获取 Agent 实例"""
        return self.agents.get(agent_id)
    
    def list_agents(self) -> List[Dict[str, Any]]:
        """列出所有 Agent"""
        return [
            {
                "id": a.id,
                "name": a.name,
                "personality": a.personality,
                "status": a.status,
                "last_active": a.last_active,
                "channel": a.channel
            }
            for a in self.agents.values()
        ]
    
    def get_status(self) -> Dict[str, Any]:
        """获取 Gateway 状态"""
        return {
            "status": self.status.value,
            "uptime": time.time() - self.workspace_manager.workspace_path.stat().st_ctime if self.workspace_path else 0,
            "agents": len(self.agents),
            "events_in_queue": len([e for e in self.event_queue if not e.processed]),
            "heartbeat": self.heartbeat_engine.get_status() if self.heartbeat_engine else None,
            "timestamp": time.time()
        }


# 全局 Gateway 实例
_gateway_instance: Optional[Gateway] = None


def get_gateway(workspace_path: Optional[Path] = None) -> Gateway:
    """获取 Gateway 单例"""
    global _gateway_instance
    if _gateway_instance is None:
        _gateway_instance = Gateway(workspace_path)
    return _gateway_instance
