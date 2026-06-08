"""
WebSocket connection manager with subscriptions, message queue, heartbeat loop,
and helpers to build typed messages (chat / progress / notification).
"""
import json
import asyncio
from typing import Dict, Optional, Any, Set, Callable, List
from datetime import datetime
from enum import Enum
from uuid import uuid4
from core.logging import get_logger

logger = get_logger("websocket")


class MessageType(Enum):
    """消息类型枚举"""
    # 通知消息
    NOTIFICATION = "notification"
    # 聊天消息
    CHAT_MESSAGE = "chat_message"
    # 任务进度
    TASK_PROGRESS = "task_progress"
    # 系统状态
    SYSTEM_STATUS = "system_status"
    # Canvas 界面更新
    CANVAS_UPDATE = "canvas_update"
    # 心跳包
    HEARTBEAT = "heartbeat"
    # 错误
    ERROR = "error"
    # 连接确认
    CONNECTED = "connected"


class MessagePriority(Enum):
    """消息优先级"""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    URGENT = 3


class Connection:
    """WebSocket 连接封装"""
    
    def __init__(self, connection_id: str, user_id: Optional[str] = None):
        self.connection_id = connection_id
        self.user_id = user_id
        self.created_at = datetime.utcnow().timestamp()
        self.last_active = datetime.utcnow().timestamp()
        self.subscribed_channels: Set[str] = set()
        self.metadata: Dict[str, Any] = {}
    
    def touch(self):
        """更新最后活动时间"""
        self.last_active = datetime.utcnow().timestamp()
    
    def subscribe(self, channel: str):
        """订阅频道"""
        self.subscribed_channels.add(channel)
    
    def unsubscribe(self, channel: str):
        """取消订阅"""
        self.subscribed_channels.discard(channel)


class WebSocketManager:
    """
    WebSocket 管理器
    管理连接、消息广播、频道订阅
    """
    
    def __init__(self):
        # 活跃连接
        self.connections: Dict[str, Connection] = {}
        # 用户连接映射
        self.user_connections: Dict[str, Set[str]] = {}
        # 频道订阅
        self.channel_subscribers: Dict[str, Set[str]] = {}
        # 消息队列
        self.message_queue: asyncio.Queue = asyncio.Queue()
        # 运行状态
        self._running: bool = False
        # 消息处理器
        self._message_handlers: Dict[MessageType, List[Callable]] = {}
        # 心跳任务
        self._heartbeat_task: Optional[asyncio.Task] = None
        
        logger.info("WebSocket 管理器初始化完成")
    
    def register_connection(self, websocket, user_id: Optional[str] = None) -> str:
        """
        注册新连接
        返回 connection_id
        """
        connection_id = str(uuid4())
        
        connection = Connection(
            connection_id=connection_id,
            user_id=user_id
        )
        
        self.connections[connection_id] = connection
        
        if user_id:
            if user_id not in self.user_connections:
                self.user_connections[user_id] = set()
            self.user_connections[user_id].add(connection_id)
        
        logger.info(f"WebSocket 连接建立: {connection_id} (user: {user_id})")
        return connection_id
    
    async def remove_connection(self, connection_id: str):
        """移除连接"""
        if connection_id not in self.connections:
            return
        
        connection = self.connections[connection_id]
        
        # 清理用户映射
        if connection.user_id and connection.user_id in self.user_connections:
            self.user_connections[connection.user_id].discard(connection_id)
            if not self.user_connections[connection.user_id]:
                del self.user_connections[connection.user_id]
        
        # 清理频道订阅
        for channel in connection.subscribed_channels:
            if channel in self.channel_subscribers:
                self.channel_subscribers[channel].discard(connection_id)
                if not self.channel_subscribers[channel]:
                    del self.channel_subscribers[channel]
        
        del self.connections[connection_id]
        logger.info(f"WebSocket 连接关闭: {connection_id}")
    
    def get_connection(self, connection_id: str) -> Optional[Connection]:
        """获取连接"""
        return self.connections.get(connection_id)
    
    async def send_to_connection(
        self,
        connection_id: str,
        message: Dict[str, Any]
    ) -> bool:
        """
        发送消息到指定连接
        这里是占位符，实际 WebSocket 发送在路由层处理
        消息会被放入队列等待发送
        """
        if connection_id not in self.connections:
            return False
        
        await self.message_queue.put({
            "connection_id": connection_id,
            "message": message
        })
        
        self.connections[connection_id].touch()
        return True
    
    async def send_to_user(
        self,
        user_id: str,
        message: Dict[str, Any]
    ) -> int:
        """发送消息给指定用户的所有连接"""
        if user_id not in self.user_connections:
            return 0
        
        sent_count = 0
        for connection_id in self.user_connections[user_id]:
            if await self.send_to_connection(connection_id, message):
                sent_count += 1
        
        return sent_count
    
    async def send_to_channel(
        self,
        channel: str,
        message: Dict[str, Any]
    ) -> int:
        """发送消息到频道所有订阅者"""
        if channel not in self.channel_subscribers:
            return 0
        
        sent_count = 0
        for connection_id in self.channel_subscribers[channel]:
            if await self.send_to_connection(connection_id, message):
                sent_count += 1
        
        return sent_count
    
    async def broadcast(self, message: Dict[str, Any]) -> int:
        """广播消息给所有连接"""
        sent_count = 0
        for connection_id in list(self.connections.keys()):
            if await self.send_to_connection(connection_id, message):
                sent_count += 1
        
        return sent_count
    
    def subscribe_to_channel(self, connection_id: str, channel: str):
        """订阅频道"""
        if connection_id not in self.connections:
            return
        
        connection = self.connections[connection_id]
        connection.subscribe(channel)
        
        if channel not in self.channel_subscribers:
            self.channel_subscribers[channel] = set()
        
        self.channel_subscribers[channel].add(connection_id)
        logger.debug(f"连接 {connection_id} 订阅频道 {channel}")
    
    def unsubscribe_from_channel(self, connection_id: str, channel: str):
        """取消订阅频道"""
        if connection_id not in self.connections:
            return
        
        connection = self.connections[connection_id]
        connection.unsubscribe(channel)
        
        if channel in self.channel_subscribers:
            self.channel_subscribers[channel].discard(connection_id)
            if not self.channel_subscribers[channel]:
                del self.channel_subscribers[channel]
        
        logger.debug(f"连接 {connection_id} 取消订阅频道 {channel}")
    
    def register_message_handler(self, message_type: MessageType, handler: Callable):
        """注册消息处理器"""
        if message_type not in self._message_handlers:
            self._message_handlers[message_type] = []
        
        self._message_handlers[message_type].append(handler)
        logger.debug(f"注册了 {message_type.value} 消息处理器")
    
    async def handle_message(self, connection_id: str, message: Dict[str, Any]):
        """处理收到的消息"""
        try:
            msg_type_str = message.get("type")
            if not msg_type_str:
                logger.warning(f"收到无效消息: {message}")
                return
            
            msg_type = MessageType(msg_type_str)
            
            if connection_id in self.connections:
                self.connections[connection_id].touch()
            
            if msg_type in self._message_handlers:
                for handler in self._message_handlers[msg_type]:
                    try:
                        await handler(connection_id, message)
                    except Exception as e:
                        logger.error(f"消息处理器异常: {e}")
        
        except ValueError as e:
            logger.warning(f"无效消息类型: {e}")
        except Exception as e:
            logger.error(f"处理消息异常: {e}")
    
    @staticmethod
    def create_message(
        message_type: MessageType,
        data: Optional[Dict[str, Any]] = None,
        priority: MessagePriority = MessagePriority.NORMAL
    ) -> Dict[str, Any]:
        """创建标准格式的消息"""
        return {
            "id": str(uuid4()),
            "type": message_type.value,
            "timestamp": datetime.utcnow().timestamp(),
            "priority": priority.value,
            "data": data or {}
        }
    
    @staticmethod
    def create_chat_message(
        content: str,
        sender: str = "system",
        conversation_id: Optional[str] = None,
        priority: MessagePriority = MessagePriority.NORMAL
    ) -> Dict[str, Any]:
        """创建聊天消息"""
        return WebSocketManager.create_message(
            message_type=MessageType.CHAT_MESSAGE,
            data={
                "content": content,
                "sender": sender,
                "conversation_id": conversation_id
            },
            priority=priority
        )
    
    @staticmethod
    def create_task_progress(
        task_id: str,
        status: str,
        progress: float = 0.0,
        message: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """创建任务进度消息"""
        return WebSocketManager.create_message(
            message_type=MessageType.TASK_PROGRESS,
            data={
                "task_id": task_id,
                "status": status,
                "progress": progress,
                "message": message,
                "data": data
            }
        )
    
    @staticmethod
    def create_notification(
        title: str,
        content: str,
        notification_type: str = "info",
        priority: MessagePriority = MessagePriority.NORMAL
    ) -> Dict[str, Any]:
        """创建通知消息"""
        return WebSocketManager.create_message(
            message_type=MessageType.NOTIFICATION,
            data={
                "title": title,
                "content": content,
                "type": notification_type
            },
            priority=priority
        )
    
    async def start(self):
        """启动 WebSocket 管理器"""
        if self._running:
            return
        
        self._running = True
        
        # 启动心跳任务
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        
        logger.info("WebSocket 管理器已启动")
    
    async def stop(self):
        """停止 WebSocket 管理器"""
        self._running = False
        
        if self._heartbeat_task and not self._heartbeat_task.done():
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
        
        # 清理所有连接
        self.connections.clear()
        self.user_connections.clear()
        self.channel_subscribers.clear()
        
        logger.info("WebSocket 管理器已停止")
    
    async def _heartbeat_loop(self):
        """心跳循环"""
        while self._running:
            try:
                # 发送心跳给所有连接
                heartbeat_msg = self.create_message(MessageType.HEARTBEAT, {
                    "server_time": datetime.utcnow().timestamp()
                })
                await self.broadcast(heartbeat_msg)
                
                # 清理不活跃连接
                now = datetime.utcnow().timestamp()
                inactive_threshold = 5 * 60  # 5 分钟
                
                # 创建字典副本，避免迭代时修改
                inactive_connections = []
                for conn_id, conn in list(self.connections.items()):
                    if now - conn.last_active > inactive_threshold:
                        inactive_connections.append(conn_id)
                
                for conn_id in inactive_connections:
                    await self.remove_connection(conn_id)
                
                await asyncio.sleep(30)  # 每 30 秒发送一次心跳
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat loop error: {e}")
                await asyncio.sleep(30)
    
    def get_status(self) -> Dict[str, Any]:
        """获取管理器状态"""
        return {
            "connections_count": len(self.connections),
            "users_count": len(self.user_connections),
            "channels_count": len(self.channel_subscribers),
            "running": self._running
        }


# 全局 WebSocket 管理器
_websocket_manager: Optional[WebSocketManager] = None


def get_websocket_manager() -> WebSocketManager:
    """获取 WebSocket 管理器"""
    global _websocket_manager
    if _websocket_manager is None:
        _websocket_manager = WebSocketManager()
    return _websocket_manager
