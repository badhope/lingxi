"""
DataAgent - 通知系统
支持多种通知方式（邮件、浏览器、控制台、Webhook）
"""
import json
import asyncio
import time
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from datetime import datetime

from core.logging import get_logger

logger = get_logger("notifications")


class NotificationType(str, Enum):
    """通知类型"""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    NEW_MESSAGE = "new_message"
    REMINDER = "reminder"
    SYSTEM = "system"


class NotificationChannel(str, Enum):
    """通知渠道"""
    CONSOLE = "console"
    BROWSER = "browser"
    EMAIL = "email"
    WEBHOOK = "webhook"


@dataclass
class Notification:
    """通知"""
    id: str = field(default_factory=lambda: f"notif_{int(time.time() * 1000)}")
    type: NotificationType = NotificationType.INFO
    title: str = ""
    message: str = ""
    channel: NotificationChannel = NotificationChannel.CONSOLE
    priority: int = 0  # 0-10, higher is more important
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    read: bool = False
    sent: bool = False


class NotificationManager:
    """
    通知管理器
    管理各种通知渠道和通知发送
    """
    
    def __init__(self, notif_dir: Optional[Path] = None):
        if notif_dir is None:
            notif_dir = Path.home() / ".dataagent" / "notifications"
        
        self.notif_dir = notif_dir
        self.notif_dir.mkdir(parents=True, exist_ok=True)
        
        self.notifications: Dict[str, Notification] = {}
        self.subscribers: List[Callable] = []
        self._load_notifications()
        
        logger.info("通知管理器初始化完成")
    
    def _load_notifications(self):
        """加载保存的通知"""
        notif_file = self.notif_dir / "notifications.json"
        
        if notif_file.exists():
            try:
                with open(notif_file, 'r', encoding='utf-8') as f:
                    notif_data = json.load(f)
                
                for data in notif_data:
                    try:
                        notif = Notification(
                            id=data['id'],
                            type=NotificationType(data.get('type', 'info')),
                            title=data.get('title', ''),
                            message=data.get('message', ''),
                            channel=NotificationChannel(data.get('channel', 'console')),
                            priority=data.get('priority', 0),
                            data=data.get('data', {}),
                            timestamp=data.get('timestamp', time.time()),
                            read=data.get('read', False),
                            sent=data.get('sent', False)
                        )
                        self.notifications[notif.id] = notif
                    except Exception as e:
                        logger.error(f"加载通知失败: {e}")
                        
            except Exception as e:
                logger.error(f"读取通知文件失败: {e}")
    
    def _save_notifications(self):
        """保存通知"""
        notif_file = self.notif_dir / "notifications.json"
        
        try:
            notif_data = []
            for notif in self.notifications.values():
                notif_data.append({
                    "id": notif.id,
                    "type": notif.type.value,
                    "title": notif.title,
                    "message": notif.message,
                    "channel": notif.channel.value,
                    "priority": notif.priority,
                    "data": notif.data,
                    "timestamp": notif.timestamp,
                    "read": notif.read,
                    "sent": notif.sent
                })
            
            with open(notif_file, 'w', encoding='utf-8') as f:
                json.dump(notif_data[-100:], f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存通知失败: {e}")
    
    def send(
        self,
        title: str,
        message: str,
        type: NotificationType = NotificationType.INFO,
        channel: NotificationChannel = NotificationChannel.CONSOLE,
        priority: int = 0,
        data: Optional[Dict[str, Any]] = None
    ) -> str:
        """发送通知"""
        
        notification = Notification(
            type=type,
            title=title,
            message=message,
            channel=channel,
            priority=priority,
            data=data or {}
        )
        
        self.notifications[notification.id] = notification
        
        # 发送到指定渠道
        asyncio.create_task(self._send_notification(notification))
        
        # 通知订阅者
        for subscriber in self.subscribers:
            try:
                if asyncio.iscoroutinefunction(subscriber):
                    asyncio.create_task(subscriber(notification))
                else:
                    subscriber(notification)
            except Exception as e:
                logger.error(f"通知订阅者失败: {e}")
        
        self._save_notifications()
        
        logger.info(f"发送通知: {title}")
        return notification.id
    
    async def _send_notification(self, notification: Notification):
        """实际发送通知"""
        try:
            # 根据渠道发送
            if notification.channel == NotificationChannel.CONSOLE:
                await self._send_console(notification)
            elif notification.channel == NotificationChannel.BROWSER:
                await self._send_browser(notification)
            elif notification.channel == NotificationChannel.EMAIL:
                await self._send_email(notification)
            elif notification.channel == NotificationChannel.WEBHOOK:
                await self._send_webhook(notification)
            
            notification.sent = True
            self._save_notifications()
            
        except Exception as e:
            logger.error(f"发送通知失败: {e}", exc_info=True)
    
    async def _send_console(self, notification: Notification):
        """发送到控制台"""
        # 颜色编码
        color_codes = {
            NotificationType.INFO: "\033[94m",
            NotificationType.SUCCESS: "\033[92m",
            NotificationType.WARNING: "\033[93m",
            NotificationType.ERROR: "\033[91m",
            NotificationType.TASK_COMPLETED: "\033[92m",
            NotificationType.TASK_FAILED: "\033[91m",
            NotificationType.NEW_MESSAGE: "\033[96m",
            NotificationType.REMINDER: "\033[93m",
            NotificationType.SYSTEM: "\033[95m"
        }
        
        color = color_codes.get(notification.type, "")
        reset = "\033[0m"
        
        print(f"\n{color}═" * 60)
        print(f"  {notification.title}")
        print(f"  {datetime.fromtimestamp(notification.timestamp).strftime('%Y-%m-%d %H:%M:%S')}")
        print("─" * 60)
        print(f"  {notification.message}")
        print(f"═" * 60 + f"{reset}\n")
    
    async def _send_browser(self, notification: Notification):
        """发送到浏览器（通过 WebSocket）"""
        # 这里会通过 WebSocket 发送到前端
        pass
    
    async def _send_email(self, notification: Notification):
        """发送邮件（需要配置）"""
        logger.info(f"邮件通知功能需要配置: {notification.title}")
    
    async def _send_webhook(self, notification: Notification):
        """发送到 Webhook"""
        try:
            from core.webhook import get_webhook_manager
            webhook_manager = get_webhook_manager()
            
            await webhook_manager.emit_event(
                NotificationType.NEW_MESSAGE,
                {
                    "notification": {
                        "id": notification.id,
                        "title": notification.title,
                        "message": notification.message,
                        "type": notification.type.value
                    }
                }
            )
        except Exception as e:
            logger.warning(f"Webhook 通知失败: {e}")
    
    def get(
        self,
        notification_id: Optional[str] = None,
        unread_only: bool = False,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """获取通知"""
        
        if notification_id:
            if notification_id in self.notifications:
                notif = self.notifications[notification_id]
                return [{
                    "id": notif.id,
                    "type": notif.type.value,
                    "title": notif.title,
                    "message": notif.message,
                    "channel": notif.channel.value,
                    "priority": notif.priority,
                    "data": notif.data,
                    "timestamp": notif.timestamp,
                    "read": notif.read,
                    "sent": notif.sent
                }]
            return []
        
        # 获取所有通知
        notifs = list(self.notifications.values())
        
        # 过滤
        if unread_only:
            notifs = [n for n in notifs if not n.read]
        
        # 排序（最新的在前）
        notifs.sort(key=lambda x: -x.timestamp)
        
        # 限制数量
        notifs = notifs[:limit]
        
        return [
            {
                "id": n.id,
                "type": n.type.value,
                "title": n.title,
                "message": n.message,
                "channel": n.channel.value,
                "priority": n.priority,
                "data": n.data,
                "timestamp": n.timestamp,
                "read": n.read,
                "sent": n.sent
            }
            for n in notifs
        ]
    
    def mark_read(self, notification_id: str) -> bool:
        """标记通知为已读"""
        if notification_id in self.notifications:
            self.notifications[notification_id].read = True
            self._save_notifications()
            return True
        return False
    
    def mark_all_read(self):
        """标记所有通知为已读"""
        for notif in self.notifications.values():
            notif.read = True
        self._save_notifications()
    
    def delete(self, notification_id: str) -> bool:
        """删除通知"""
        if notification_id in self.notifications:
            del self.notifications[notification_id]
            self._save_notifications()
            return True
        return False
    
    def clear_all(self):
        """清除所有通知"""
        self.notifications = {}
        self._save_notifications()
    
    def subscribe(self, callback: Callable):
        """订阅通知"""
        self.subscribers.append(callback)
    
    def unsubscribe(self, callback: Callable):
        """取消订阅"""
        if callback in self.subscribers:
            self.subscribers.remove(callback)
    
    def get_unread_count(self) -> int:
        """获取未读通知数"""
        return sum(1 for n in self.notifications.values() if not n.read)
    
    # 快捷方法
    def info(self, title: str, message: str, **kwargs):
        """发送信息通知"""
        return self.send(title, message, NotificationType.INFO, **kwargs)
    
    def success(self, title: str, message: str, **kwargs):
        """发送成功通知"""
        return self.send(title, message, NotificationType.SUCCESS, **kwargs)
    
    def warning(self, title: str, message: str, **kwargs):
        """发送警告通知"""
        return self.send(title, message, NotificationType.WARNING, **kwargs)
    
    def error(self, title: str, message: str, **kwargs):
        """发送错误通知"""
        return self.send(title, message, NotificationType.ERROR, **kwargs)
    
    def task_completed(self, task_name: str, result: Optional[str] = None):
        """任务完成通知"""
        message = f"任务 '{task_name}' 已完成"
        if result:
            message += f": {result}"
        return self.send(
            "任务完成",
            message,
            NotificationType.TASK_COMPLETED
        )
    
    def task_failed(self, task_name: str, error: Optional[str] = None):
        """任务失败通知"""
        message = f"任务 '{task_name}' 失败"
        if error:
            message += f": {error}"
        return self.send(
            "任务失败",
            message,
            NotificationType.TASK_FAILED,
            priority=5
        )
    
    def reminder(self, title: str, message: str, **kwargs):
        """提醒通知"""
        return self.send(title, message, NotificationType.REMINDER, priority=3, **kwargs)


_notification_manager: Optional[NotificationManager] = None


def get_notification_manager() -> NotificationManager:
    """获取通知管理器"""
    global _notification_manager
    if _notification_manager is None:
        _notification_manager = NotificationManager()
    return _notification_manager
