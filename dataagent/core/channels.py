"""
DataAgent - Channels 多渠道交互系统
类似于 OpenClaw 的多渠道支持
"""
import asyncio
import json
import time
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from dataclasses import dataclass, field

from core.logging import get_logger
from core.config import config_manager

logger = get_logger("channels")


class ChannelType(str, Enum):
    """渠道类型"""
    WEBSOCKET = "websocket"
    TELEGRAM = "telegram"
    DISCORD = "discord"
    SLACK = "slack"
    EMAIL = "email"
    API = "api"
    CUSTOM = "custom"


class MessageStatus(str, Enum):
    """消息状态"""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"


@dataclass
class Message:
    """消息对象"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    channel_id: str = ""
    channel_type: ChannelType = ChannelType.WEBSOCKET
    user_id: Optional[str] = None
    content: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    status: MessageStatus = MessageStatus.PENDING
    created_at: float = field(default_factory=time.time)
    sent_at: Optional[float] = None


@dataclass
class Channel:
    """渠道配置"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    type: ChannelType = ChannelType.WEBSOCKET
    config: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    created_at: float = field(default_factory=time.time)
    _handler: Optional[Callable] = None


class ChannelsEngine:
    """
    渠道引擎 - 多渠道交互管理
    """
    
    def __init__(self):
        self.channels: Dict[str, Channel] = {}
        self.message_queue: List[Message] = []
        self._data_path: Optional[Path] = None
        self._init_data_path()
        self._init_default_channels()
    
    def _init_data_path(self):
        """初始化数据存储路径"""
        try:
            self._data_path = config_manager.paths.data_dir / "channels"
            self._data_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.warning(f"无法初始化数据存储路径: {e}")
            self._data_path = Path.home() / ".dataagent" / "channels"
            self._data_path.mkdir(parents=True, exist_ok=True)
    
    def _init_default_channels(self):
        """初始化默认渠道"""
        # WebSocket 渠道（默认）
        ws_channel = Channel(
            name="WebSocket",
            type=ChannelType.WEBSOCKET,
            enabled=True
        )
        self.channels[ws_channel.id] = ws_channel
        
        # API 渠道
        api_channel = Channel(
            name="REST API",
            type=ChannelType.API,
            enabled=True
        )
        self.channels[api_channel.id] = api_channel
        
        logger.info(f"初始化了 {len(self.channels)} 个渠道")
    
    def get_channel(self, channel_id: str) -> Optional[Channel]:
        """获取渠道"""
        return self.channels.get(channel_id)
    
    def list_channels(self) -> List[Channel]:
        """列出所有渠道"""
        return list(self.channels.values())
    
    async def send_message(self,
                         channel_id: str,
                         content: str,
                         user_id: Optional[str] = None,
                         metadata: Optional[Dict[str, Any]] = None) -> Optional[Message]:
        """发送消息"""
        channel = self.channels.get(channel_id)
        if not channel or not channel.enabled:
            return None
        
        message = Message(
            channel_id=channel_id,
            channel_type=channel.type,
            user_id=user_id,
            content=content,
            metadata=metadata or {}
        )
        
        self.message_queue.append(message)
        
        # 模拟发送
        message.status = MessageStatus.SENT
        message.sent_at = time.time()
        
        logger.info(f"发送消息到渠道 {channel.name}: {content[:50]}...")
        return message
    
    def receive_message(self,
                       channel_id: str,
                       content: str,
                       user_id: Optional[str] = None,
                       metadata: Optional[Dict[str, Any]] = None) -> Message:
        """接收消息"""
        message = Message(
            channel_id=channel_id,
            content=content,
            user_id=user_id,
            metadata=metadata or {},
            status=MessageStatus.DELIVERED
        )
        
        # 查找渠道类型
        channel = self.channels.get(channel_id)
        if channel:
            message.channel_type = channel.type
        
        self.message_queue.append(message)
        logger.info(f"从渠道接收到消息: {content[:50]}...")
        return message
    
    def register_channel_handler(self, channel_id: str, handler: Callable):
        """注册渠道处理器"""
        if channel_id in self.channels:
            self.channels[channel_id]._handler = handler
    
    def get_message_history(self,
                          channel_id: Optional[str] = None,
                          user_id: Optional[str] = None,
                          limit: int = 100) -> List[Message]:
        """获取消息历史"""
        messages = self.message_queue
        
        if channel_id:
            messages = [m for m in messages if m.channel_id == channel_id]
        
        if user_id:
            messages = [m for m in messages if m.user_id == user_id]
        
        messages.sort(key=lambda m: m.created_at, reverse=True)
        return messages[:limit]


# 全局渠道引擎实例
_channels_engine: Optional[ChannelsEngine] = None


def get_channels_engine() -> ChannelsEngine:
    """获取渠道引擎实例"""
    global _channels_engine
    if _channels_engine is None:
        _channels_engine = ChannelsEngine()
    return _channels_engine


__all__ = [
    "ChannelType",
    "MessageStatus",
    "Message",
    "Channel",
    "ChannelsEngine",
    "get_channels_engine"
]
