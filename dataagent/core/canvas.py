"""
DataAgent - Canvas 实时交互系统
借鉴 OpenClaw 的 Live Canvas，提供动态可视化和交互式界面
"""
import asyncio
import uuid
import time
import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from enum import Enum

from core.logging import get_logger

logger = get_logger("canvas")


class CanvasElementType(str, Enum):
    """Canvas 元素类型"""
    TEXT = "text"
    BUTTON = "button"
    INPUT = "input"
    SELECT = "select"
    CARD = "card"
    DIVIDER = "divider"
    IMAGE = "image"
    PROGRESS = "progress"
    TABLE = "table"


class CanvasEvent(str, Enum):
    """Canvas 事件类型"""
    CLICK = "click"
    SUBMIT = "submit"
    CHANGE = "change"
    OPEN = "open"
    CLOSE = "close"


@dataclass
class CanvasElement:
    """Canvas 元素"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: CanvasElementType = CanvasElementType.TEXT
    content: str = ""
    style: Dict[str, Any] = field(default_factory=dict)
    props: Dict[str, Any] = field(default_factory=dict)
    actions: List[Dict[str, Any]] = field(default_factory=list)
    children: List["CanvasElement"] = field(default_factory=list)


@dataclass
class CanvasState:
    """Canvas 状态"""
    title: str = "DataAgent Canvas"
    elements: List[CanvasElement] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    version: int = 1
    updated_at: float = field(default_factory=time.time)


@dataclass
class CanvasAction:
    """Canvas 动作记录"""
    id: str
    type: str
    element_id: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    executed: bool = False


class Canvas:
    """
    Live Canvas - 实时交互式界面
    类似 OpenClaw 的 Canvas 功能
    """
    
    def __init__(self, canvas_id: Optional[str] = None):
        self.canvas_id = canvas_id or f"canvas_{uuid.uuid4().hex[:8]}"
        self.state = CanvasState()
        self.history: List[CanvasAction] = []
        self.action_handlers: Dict[str, Callable] = {}
        self.subscribers: List[Callable] = []
        
        logger.info(f"Canvas 初始化完成: {self.canvas_id}")
    
    def reset(self):
        """重置 Canvas"""
        self.state = CanvasState()
        self.history = []
        self._notify_subscribers("reset")
        logger.info("Canvas 已重置")
    
    def set_title(self, title: str):
        """设置标题"""
        self.state.title = title
        self._increment_version()
        self._notify_subscribers("title_change")
    
    def add_element(self, element: CanvasElement, position: Optional[int] = None):
        """添加元素"""
        if position is not None:
            self.state.elements.insert(position, element)
        else:
            self.state.elements.append(element)
        
        self._increment_version()
        self._notify_subscribers("element_added", {"element_id": element.id})
        logger.debug(f"添加元素: {element.id} - {element.type}")
        return element.id
    
    def update_element(self, element_id: str, updates: Dict[str, Any]):
        """更新元素"""
        for element in self.state.elements:
            if element.id == element_id:
                for key, value in updates.items():
                    if key == "content":
                        element.content = value
                    elif key == "style":
                        element.style.update(value)
                    elif key == "props":
                        element.props.update(value)
                
                self._increment_version()
                self._notify_subscribers("element_updated", {"element_id": element_id})
                logger.debug(f"更新元素: {element_id}")
                return True
        return False
    
    def remove_element(self, element_id: str) -> bool:
        """移除元素"""
        for i, element in enumerate(self.state.elements):
            if element.id == element_id:
                del self.state.elements[i]
                self._increment_version()
                self._notify_subscribers("element_removed", {"element_id": element_id})
                logger.debug(f"移除元素: {element_id}")
                return True
        return False
    
    def clear_elements(self):
        """清空所有元素"""
        self.state.elements = []
        self._increment_version()
        self._notify_subscribers("cleared")
    
    def set_context(self, key: str, value: Any):
        """设置上下文数据"""
        self.state.context[key] = value
        self._increment_version()
        self._notify_subscribers("context_updated", {"key": key})
    
    def get_context(self, key: str, default: Any = None) -> Any:
        """获取上下文数据"""
        return self.state.context.get(key, default)
    
    # ========== 快捷方法 - 创建常见 UI ==========
    
    def add_text(self, text: str, style: Optional[Dict] = None) -> str:
        """添加文本元素"""
        element = CanvasElement(
            type=CanvasElementType.TEXT,
            content=text,
            style=style or {}
        )
        return self.add_element(element)
    
    def add_button(self, text: str, action_id: str, style: Optional[Dict] = None) -> str:
        """添加按钮元素"""
        element = CanvasElement(
            type=CanvasElementType.BUTTON,
            content=text,
            style=style or {},
            actions=[{"type": "click", "action": action_id}]
        )
        return self.add_element(element)
    
    def add_card(self, title: str, content: str, buttons: Optional[List[Dict]] = None, style: Optional[Dict] = None) -> str:
        """添加卡片元素"""
        button_elements = []
        if buttons:
            for btn in buttons:
                button_elements.append(
                    CanvasElement(
                        type=CanvasElementType.BUTTON,
                        content=btn.get("text", "按钮"),
                        actions=[{"type": "click", "action": btn.get("action", "")}]
                    )
                )
        
        element = CanvasElement(
            type=CanvasElementType.CARD,
            content=title,
            style=style or {},
            props={"content": content},
            children=button_elements
        )
        return self.add_element(element)
    
    def add_input(self, label: str, placeholder: str = "", action_id: str = "submit", style: Optional[Dict] = None) -> str:
        """添加输入元素"""
        element = CanvasElement(
            type=CanvasElementType.INPUT,
            content=label,
            style=style or {},
            props={"placeholder": placeholder},
            actions=[{"type": "submit", "action": action_id}]
        )
        return self.add_element(element)
    
    def add_divider(self, style: Optional[Dict] = None) -> str:
        """添加分隔线"""
        element = CanvasElement(
            type=CanvasElementType.DIVIDER,
            style=style or {}
        )
        return self.add_element(element)
    
    def add_progress(self, value: float, max_value: float = 100, label: str = "", style: Optional[Dict] = None) -> str:
        """添加进度条"""
        element = CanvasElement(
            type=CanvasElementType.PROGRESS,
            content=label,
            style=style or {},
            props={"value": value, "max": max_value}
        )
        return self.add_element(element)
    
    def show_message(self, text: str, duration: float = 3.0):
        """显示临时消息"""
        msg_id = self.add_text(text, {"class": "message"})
        
        if duration > 0:
            asyncio.create_task(self._remove_after(msg_id, duration))
    
    async def _remove_after(self, element_id: str, delay: float):
        """延迟移除元素"""
        await asyncio.sleep(delay)
        self.remove_element(element_id)
    
    # ========== 事件和订阅 ==========
    
    def on_action(self, action_id: str, handler: Callable):
        """注册动作处理器"""
        self.action_handlers[action_id] = handler
        logger.debug(f"注册动作处理器: {action_id}")
    
    async def dispatch_action(self, action_id: str, data: Optional[Dict] = None) -> Any:
        """分发动作"""
        action = CanvasAction(
            id=str(uuid.uuid4()),
            type=action_id,
            data=data or {}
        )
        self.history.append(action)
        
        if action_id in self.action_handlers:
            try:
                handler = self.action_handlers[action_id]
                if asyncio.iscoroutinefunction(handler):
                    result = await handler(data)
                else:
                    result = handler(data)
                
                action.executed = True
                logger.debug(f"动作执行成功: {action_id}")
                return result
            except Exception as e:
                logger.error(f"动作执行失败 {action_id}: {e}")
        
        return None
    
    def subscribe(self, callback: Callable):
        """订阅状态变更"""
        self.subscribers.append(callback)
    
    def unsubscribe(self, callback: Callable):
        """取消订阅"""
        if callback in self.subscribers:
            self.subscribers.remove(callback)
    
    def _notify_subscribers(self, event_type: str, data: Optional[Dict] = None):
        """通知订阅者"""
        for callback in self.subscribers:
            try:
                if asyncio.iscoroutinefunction(callback):
                    asyncio.create_task(callback(self.state, event_type, data or {}))
                else:
                    callback(self.state, event_type, data or {})
            except Exception as e:
                logger.error(f"通知订阅者失败: {e}")
    
    def _increment_version(self):
        """增加版本号"""
        self.state.version += 1
        self.state.updated_at = time.time()
    
    def export_json(self) -> Dict[str, Any]:
        """导出 Canvas 状态为 JSON"""
        return {
            "canvas_id": self.canvas_id,
            "title": self.state.title,
            "elements": [
                {
                    "id": e.id,
                    "type": e.type.value,
                    "content": e.content,
                    "style": e.style,
                    "props": e.props
                }
                for e in self.state.elements
            ],
            "context": self.state.context,
            "version": self.state.version,
            "updated_at": self.state.updated_at
        }


# Canvas 管理器
class CanvasManager:
    """管理多个 Canvas 实例"""
    
    def __init__(self):
        self.canvases: Dict[str, Canvas] = {}
        logger.info("CanvasManager 初始化完成")
    
    def create_canvas(self, canvas_id: Optional[str] = None) -> Canvas:
        """创建新 Canvas"""
        canvas = Canvas(canvas_id)
        self.canvases[canvas.canvas_id] = canvas
        logger.info(f"创建 Canvas: {canvas.canvas_id}")
        return canvas
    
    def get_canvas(self, canvas_id: str) -> Optional[Canvas]:
        """获取 Canvas"""
        return self.canvases.get(canvas_id)
    
    def list_canvases(self) -> List[Dict[str, Any]]:
        """列出所有 Canvas"""
        return [
            {
                "id": c.canvas_id,
                "title": c.state.title,
                "elements": len(c.state.elements),
                "version": c.state.version
            }
            for c in self.canvases.values()
        ]
    
    def delete_canvas(self, canvas_id: str) -> bool:
        """删除 Canvas"""
        if canvas_id in self.canvases:
            del self.canvases[canvas_id]
            logger.info(f"删除 Canvas: {canvas_id}")
            return True
        return False


# 全局 Canvas 管理器
_canvas_manager: Optional[CanvasManager] = None


def get_canvas_manager() -> CanvasManager:
    """获取 Canvas 管理器"""
    global _canvas_manager
    if _canvas_manager is None:
        _canvas_manager = CanvasManager()
    return _canvas_manager
