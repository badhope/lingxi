"""
DataAgent - Heartbeat 心跳机制
类似于 OpenClaw 的 Heartbeat 系统，提供后台任务监控、定时任务和健康检查
"""
import asyncio
import threading
import time
import uuid
from datetime import datetime, timedelta
from typing import Callable, Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass, field
from pathlib import Path
import json

from core.logging import get_logger
from core.config import config_manager

logger = get_logger("heartbeat")


class TaskStatus(str, Enum):
    """任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class HeartbeatStatus(str, Enum):
    """心跳状态"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class ScheduledTask:
    """定时任务定义"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str = ""
    cron_expression: str = ""  # "*/5 * * * *" 格式
    interval_seconds: int = 0  # 或者使用秒级间隔
    enabled: bool = True
    last_run: Optional[float] = None
    next_run: Optional[float] = None
    task_func: Optional[Callable] = None
    task_type: str = "generic"
    config: Dict[str, Any] = field(default_factory=dict)
    max_retries: int = 3
    retry_count: int = 0
    error_message: Optional[str] = None


@dataclass
class HeartbeatRecord:
    """心跳记录"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)
    status: HeartbeatStatus = HeartbeatStatus.HEALTHY
    active_tasks: int = 0
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    tasks: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


class HeartbeatEngine:
    """
    心跳引擎 - 核心调度器
    类似于 OpenClaw 的 Heartbeat 系统
    """
    
    def __init__(self):
        self.tasks: Dict[str, ScheduledTask] = {}
        self.heartbeat_records: List[HeartbeatRecord] = []
        self._running: bool = False
        self._thread: Optional[threading.Thread] = None
        self._event_loop: Optional[asyncio.AbstractEventLoop] = None
        self._heartbeat_interval: float = 10.0  # 10秒心跳
        self._max_records: int = 1000  # 最多保留1000条记录
        self._callbacks: List[Callable] = []
        self._data_path: Optional[Path] = None
        self._init_data_path()
    
    def _init_data_path(self):
        """初始化数据存储路径"""
        try:
            self._data_path = config_manager.paths.data_dir / "heartbeat"
            self._data_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.warning(f"无法初始化数据存储路径: {e}")
            self._data_path = Path.home() / ".dataagent" / "heartbeat"
            self._data_path.mkdir(parents=True, exist_ok=True)
    
    def start(self):
        """启动心跳引擎"""
        if self._running:
            logger.warning("心跳引擎已经在运行")
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._run_heartbeat_loop, daemon=True)
        self._thread.start()
        logger.info("心跳引擎已启动")
        
        # 加载保存的任务
        self._load_tasks()
    
    def stop(self):
        """停止心跳引擎"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5.0)
        logger.info("心跳引擎已停止")
        
        # 保存任务
        self._save_tasks()
    
    def _run_heartbeat_loop(self):
        """运行心跳循环（在独立线程中）"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self._event_loop = loop
        
        try:
            loop.run_until_complete(self._async_heartbeat_loop())
        except Exception as e:
            logger.error(f"心跳循环异常: {e}", exc_info=True)
        finally:
            loop.close()
    
    async def _async_heartbeat_loop(self):
        """异步心跳循环"""
        while self._running:
            try:
                await self._tick()
                await asyncio.sleep(self._heartbeat_interval)
            except Exception as e:
                logger.error(f"心跳 tick 异常: {e}")
    
    async def _tick(self):
        """执行一次心跳"""
        # 创建心跳记录
        record = HeartbeatRecord(
            status=HeartbeatStatus.HEALTHY,
            active_tasks=len([t for t in self.tasks.values() if t.enabled])
        )
        
        # 检查任务执行
        for task_id, task in self.tasks.items():
            if not task.enabled:
                continue
            
            if task.next_run and time.time() >= task.next_run:
                await self._execute_task(task)
        
        # 记录心跳
        self.heartbeat_records.append(record)
        if len(self.heartbeat_records) > self._max_records:
            self.heartbeat_records = self.heartbeat_records[-self._max_records:]
        
        # 触发回调
        for callback in self._callbacks:
            try:
                callback(record)
            except Exception as e:
                logger.error(f"心跳回调异常: {e}")
    
    async def _execute_task(self, task: ScheduledTask):
        """执行定时任务"""
        task.last_run = time.time()
        task.retry_count += 1
        
        try:
            if task.task_func:
                logger.info(f"执行定时任务: {task.name}")
                if asyncio.iscoroutinefunction(task.task_func):
                    await task.task_func(task.config)
                else:
                    task.task_func(task.config)
                task.status = TaskStatus.COMPLETED
                task.error_message = None
                task.retry_count = 0
            else:
                logger.warning(f"任务 {task.name} 没有配置执行函数")
        except Exception as e:
            logger.error(f"任务执行失败: {task.name}, 错误: {e}")
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            
            # 重试逻辑
            if task.retry_count < task.max_retries:
                task.next_run = time.time() + 60  # 1分钟后重试
                logger.info(f"任务 {task.name} 将在1分钟后重试 ({task.retry_count}/{task.max_retries})")
        
        # 计算下次执行时间
        self._schedule_next_run(task)
    
    def _schedule_next_run(self, task: ScheduledTask):
        """计算下次执行时间"""
        if task.interval_seconds > 0:
            task.next_run = time.time() + task.interval_seconds
        elif task.cron_expression:
            # 简单的cron解析 - 这里可以使用 croniter 库增强
            task.next_run = time.time() + 3600  # 默认1小时后
        else:
            task.next_run = None
    
    def add_task(self, task: ScheduledTask) -> str:
        """添加定时任务"""
        self.tasks[task.id] = task
        self._schedule_next_run(task)
        logger.info(f"添加定时任务: {task.name}")
        self._save_tasks()
        return task.id
    
    def remove_task(self, task_id: str) -> bool:
        """移除定时任务"""
        if task_id in self.tasks:
            del self.tasks[task_id]
            logger.info(f"移除定时任务: {task_id}")
            self._save_tasks()
            return True
        return False
    
    def get_task(self, task_id: str) -> Optional[ScheduledTask]:
        """获取任务"""
        return self.tasks.get(task_id)
    
    def list_tasks(self) -> List[ScheduledTask]:
        """列出所有任务"""
        return list(self.tasks.values())
    
    def enable_task(self, task_id: str) -> bool:
        """启用任务"""
        if task_id in self.tasks:
            self.tasks[task_id].enabled = True
            self._save_tasks()
            return True
        return False
    
    def disable_task(self, task_id: str) -> bool:
        """禁用任务"""
        if task_id in self.tasks:
            self.tasks[task_id].enabled = False
            self._save_tasks()
            return True
        return False
    
    def register_callback(self, callback: Callable):
        """注册心跳回调"""
        self._callbacks.append(callback)
    
    def get_status(self) -> HeartbeatRecord:
        """获取当前状态"""
        if self.heartbeat_records:
            return self.heartbeat_records[-1]
        return HeartbeatRecord(status=HeartbeatStatus.UNHEALTHY)
    
    def _save_tasks(self):
        """保存任务到文件"""
        if not self._data_path:
            return
        
        try:
            tasks_data = []
            for task in self.tasks.values():
                tasks_data.append({
                    "id": task.id,
                    "name": task.name,
                    "description": task.description,
                    "cron_expression": task.cron_expression,
                    "interval_seconds": task.interval_seconds,
                    "enabled": task.enabled,
                    "task_type": task.task_type,
                    "config": task.config,
                    "max_retries": task.max_retries
                })
            
            tasks_file = self._data_path / "tasks.json"
            with open(tasks_file, "w", encoding="utf-8") as f:
                json.dump(tasks_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存任务失败: {e}")
    
    def _load_tasks(self):
        """从文件加载任务"""
        if not self._data_path:
            return
        
        try:
            tasks_file = self._data_path / "tasks.json"
            if tasks_file.exists():
                with open(tasks_file, "r", encoding="utf-8") as f:
                    tasks_data = json.load(f)
                
                for task_data in tasks_data:
                    task = ScheduledTask(
                        id=task_data["id"],
                        name=task_data["name"],
                        description=task_data.get("description", ""),
                        cron_expression=task_data.get("cron_expression", ""),
                        interval_seconds=task_data.get("interval_seconds", 0),
                        enabled=task_data.get("enabled", True),
                        task_type=task_data.get("task_type", "generic"),
                        config=task_data.get("config", {}),
                        max_retries=task_data.get("max_retries", 3)
                    )
                    self.tasks[task.id] = task
                    self._schedule_next_run(task)
                
                logger.info(f"加载了 {len(self.tasks)} 个定时任务")
        except Exception as e:
            logger.error(f"加载任务失败: {e}")


# 全局心跳引擎实例
_heartbeat_engine: Optional[HeartbeatEngine] = None


def get_heartbeat_engine() -> HeartbeatEngine:
    """获取心跳引擎实例"""
    global _heartbeat_engine
    if _heartbeat_engine is None:
        _heartbeat_engine = HeartbeatEngine()
    return _heartbeat_engine


def start_heartbeat():
    """启动心跳引擎（全局函数）"""
    get_heartbeat_engine().start()


def stop_heartbeat():
    """停止心跳引擎（全局函数）"""
    get_heartbeat_engine().stop()


__all__ = [
    "TaskStatus",
    "HeartbeatStatus",
    "ScheduledTask",
    "HeartbeatRecord",
    "HeartbeatEngine",
    "get_heartbeat_engine",
    "start_heartbeat",
    "stop_heartbeat"
]
