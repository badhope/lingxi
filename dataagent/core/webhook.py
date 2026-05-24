"""
DataAgent - Webhook 和事件系统
支持 Webhook 触发、自定义事件处理、与外部系统集成
"""
import json
import asyncio
import time
import uuid
import hashlib
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from datetime import datetime

import httpx

from core.logging import get_logger

logger = get_logger("webhook")


class EventType(str, Enum):
    """事件类型"""
    MESSAGE_RECEIVED = "message.received"
    MESSAGE_SENT = "message.sent"
    TASK_CREATED = "task.created"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"
    AGENT_ACTIVATED = "agent.activated"
    AGENT_DEACTIVATED = "agent.deactivated"
    SKILL_INSTALLED = "skill.installed"
    SKILL_UNINSTALLED = "skill.uninstalled"
    MEMORY_ADDED = "memory.added"
    MEMORY_SEARCHED = "memory.searched"
    HEARTBEAT_TRIGGERED = "heartbeat.triggered"
    LLM_REQUEST = "llm.request"
    LLM_RESPONSE = "llm.response"
    ERROR_OCCURRED = "error.occurred"
    CUSTOM = "custom"


class WebhookMethod(str, Enum):
    """Webhook HTTP 方法"""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"


@dataclass
class WebhookEvent:
    """Webhook 事件"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: EventType = EventType.CUSTOM
    source: str = "system"
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    retry_count: int = 0
    max_retries: int = 3
    status: str = "pending"


@dataclass
class Webhook:
    """Webhook 配置"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    url: str = ""
    method: WebhookMethod = WebhookMethod.POST
    event_types: List[EventType] = field(default_factory=list)
    headers: Dict[str, str] = field(default_factory=dict)
    secret: str = ""
    enabled: bool = True
    created_at: float = field(default_factory=time.time)
    last_triggered: Optional[float] = None
    success_count: int = 0
    failure_count: int = 0


@dataclass
class EventSubscription:
    """事件订阅"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    event_types: List[EventType] = field(default_factory=list)
    handler: Callable = field(default=None)
    filter_func: Optional[Callable] = None
    enabled: bool = True


class WebhookManager:
    """
    Webhook 管理器
    支持事件触发、Webhook 注册、HTTP 回调
    """
    
    def __init__(self, webhook_dir: Optional[Path] = None):
        if webhook_dir is None:
            webhook_dir = Path.home() / ".dataagent" / "webhooks"
        
        self.webhook_dir = webhook_dir
        self.webhook_dir.mkdir(parents=True, exist_ok=True)
        
        self.webhooks: Dict[str, Webhook] = {}
        self.subscriptions: Dict[str, EventSubscription] = {}
        self.event_queue: List[WebhookEvent] = []
        
        self._running = False
        self._worker_task: Optional[asyncio.Task] = None
        
        self._load_webhooks()
        
        logger.info("Webhook 管理器初始化完成")
    
    def _load_webhooks(self):
        """加载 Webhook 配置"""
        config_file = self.webhook_dir / "webhooks.json"
        
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for webhook_data in data.get('webhooks', []):
                    webhook = Webhook(
                        id=webhook_data['id'],
                        name=webhook_data['name'],
                        url=webhook_data['url'],
                        method=WebhookMethod(webhook_data.get('method', 'POST')),
                        event_types=[EventType(et) for et in webhook_data.get('event_types', [])],
                        headers=webhook_data.get('headers', {}),
                        secret=webhook_data.get('secret', ''),
                        enabled=webhook_data.get('enabled', True)
                    )
                    self.webhooks[webhook.id] = webhook
                
                logger.info(f"加载了 {len(self.webhooks)} 个 Webhook")
                
            except Exception as e:
                logger.error(f"加载 Webhook 配置失败: {e}")
    
    def _save_webhooks(self):
        """保存 Webhook 配置"""
        config_file = self.webhook_dir / "webhooks.json"
        
        data = {
            'webhooks': [
                {
                    'id': w.id,
                    'name': w.name,
                    'url': w.url,
                    'method': w.method.value,
                    'event_types': [et.value for et in w.event_types],
                    'headers': w.headers,
                    'secret': w.secret,
                    'enabled': w.enabled
                }
                for w in self.webhooks.values()
            ]
        }
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def register_webhook(
        self,
        name: str,
        url: str,
        event_types: List[EventType],
        method: WebhookMethod = WebhookMethod.POST,
        headers: Optional[Dict[str, str]] = None,
        secret: str = ""
    ) -> str:
        """注册 Webhook"""
        webhook = Webhook(
            name=name,
            url=url,
            event_types=event_types,
            method=method,
            headers=headers or {},
            secret=secret
        )
        
        self.webhooks[webhook.id] = webhook
        self._save_webhooks()
        
        logger.info(f"注册 Webhook: {name} -> {url}")
        return webhook.id
    
    def unregister_webhook(self, webhook_id: str) -> bool:
        """取消注册 Webhook"""
        if webhook_id in self.webhooks:
            del self.webhooks[webhook_id]
            self._save_webhooks()
            logger.info(f"取消注册 Webhook: {webhook_id}")
            return True
        return False
    
    def list_webhooks(self) -> List[Dict[str, Any]]:
        """列出所有 Webhook"""
        return [
            {
                'id': w.id,
                'name': w.name,
                'url': w.url,
                'method': w.method.value,
                'event_types': [et.value for et in w.event_types],
                'enabled': w.enabled,
                'last_triggered': w.last_triggered,
                'success_count': w.success_count,
                'failure_count': w.failure_count
            }
            for w in self.webhooks.values()
        ]
    
    def subscribe(
        self,
        name: str,
        event_types: List[EventType],
        handler: Callable,
        filter_func: Optional[Callable] = None
    ) -> str:
        """订阅事件"""
        subscription = EventSubscription(
            name=name,
            event_types=event_types,
            handler=handler,
            filter_func=filter_func
        )
        
        self.subscriptions[subscription.id] = subscription
        logger.info(f"订阅事件: {name}")
        return subscription.id
    
    def unsubscribe(self, subscription_id: str) -> bool:
        """取消订阅"""
        if subscription_id in self.subscriptions:
            del self.subscriptions[subscription_id]
            logger.info(f"取消订阅: {subscription_id}")
            return True
        return False
    
    async def emit_event(
        self,
        event_type: EventType,
        data: Dict[str, Any],
        source: str = "system"
    ):
        """触发事件"""
        event = WebhookEvent(
            type=event_type,
            source=source,
            data=data
        )
        
        self.event_queue.append(event)
        logger.debug(f"事件触发: {event_type.value}")
        
        await self._process_subscriptions(event)
    
    async def _process_subscriptions(self, event: WebhookEvent):
        """处理事件订阅"""
        for subscription in self.subscriptions.values():
            if not subscription.enabled:
                continue
            
            if event.type not in subscription.event_types:
                continue
            
            if subscription.filter_func:
                try:
                    if not subscription.filter_func(event):
                        continue
                except Exception as e:
                    logger.error(f"事件过滤器错误: {e}")
                    continue
            
            try:
                handler = subscription.handler
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
                
                logger.debug(f"事件处理器执行: {subscription.name}")
                
            except Exception as e:
                logger.error(f"事件处理错误: {e}")
    
    async def trigger_webhooks(self, event: WebhookEvent):
        """触发匹配的 Webhook"""
        for webhook in self.webhooks.values():
            if not webhook.enabled:
                continue
            
            if event.type not in webhook.event_types:
                continue
            
            asyncio.create_task(self._send_webhook(webhook, event))
    
    async def _send_webhook(self, webhook: Webhook, event: WebhookEvent):
        """发送 Webhook 请求"""
        try:
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'DataAgent-Webhook/1.0',
                'X-Event-Type': event.type.value,
                'X-Event-ID': event.id,
                'X-Timestamp': str(event.timestamp),
                **webhook.headers
            }
            
            if webhook.secret:
                payload = json.dumps(event.data, ensure_ascii=False)
                signature = hashlib.sha256(
                    f"{webhook.secret}{payload}".encode()
                ).hexdigest()
                headers['X-Signature'] = signature
            
            body = {
                'event': event.type.value,
                'event_id': event.id,
                'timestamp': event.timestamp,
                'source': event.source,
                'data': event.data
            }
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                if webhook.method == WebhookMethod.GET:
                    response = await client.get(webhook.url, headers=headers)
                elif webhook.method == WebhookMethod.POST:
                    response = await client.post(webhook.url, headers=headers, json=body)
                elif webhook.method == WebhookMethod.PUT:
                    response = await client.put(webhook.url, headers=headers, json=body)
                elif webhook.method == WebhookMethod.DELETE:
                    response = await client.delete(webhook.url, headers=headers)
                else:
                    response = await client.post(webhook.url, headers=headers, json=body)
                
                if response.status_code < 400:
                    webhook.success_count += 1
                    webhook.last_triggered = time.time()
                    logger.info(f"Webhook 发送成功: {webhook.name}")
                else:
                    webhook.failure_count += 1
                    logger.warning(f"Webhook 返回错误: {webhook.name} - {response.status_code}")
            
            self._save_webhooks()
            
        except Exception as e:
            webhook.failure_count += 1
            logger.error(f"Webhook 发送失败: {webhook.name} - {e}")
            self._save_webhooks()
            
            if event.retry_count < event.max_retries:
                event.retry_count += 1
                await asyncio.sleep(2 ** event.retry_count)
                asyncio.create_task(self._send_webhook(webhook, event))
    
    async def start(self):
        """启动 Webhook 处理"""
        if self._running:
            return
        
        self._running = True
        self._worker_task = asyncio.create_task(self._process_loop())
        logger.info("Webhook 管理器已启动")
    
    async def stop(self):
        """停止 Webhook 处理"""
        self._running = False
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        logger.info("Webhook 管理器已停止")
    
    async def _process_loop(self):
        """事件处理循环"""
        while self._running:
            try:
                while self.event_queue:
                    event = self.event_queue.pop(0)
                    await self.trigger_webhooks(event)
                
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"事件处理循环错误: {e}")
                await asyncio.sleep(1)
    
    def get_status(self) -> Dict[str, Any]:
        """获取状态"""
        return {
            'webhooks': len(self.webhooks),
            'subscriptions': len(self.subscriptions),
            'queue_length': len(self.event_queue),
            'running': self._running
        }


_webhook_manager: Optional[WebhookManager] = None


def get_webhook_manager() -> WebhookManager:
    """获取 Webhook 管理器"""
    global _webhook_manager
    if _webhook_manager is None:
        _webhook_manager = WebhookManager()
    return _webhook_manager
