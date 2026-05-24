"""
DataAgent - Memory 持久化记忆系统
类似于 OpenClaw 的 Soul.md 系统，提供跨会话记忆、用户偏好存储和语义搜索
"""
import json
import time
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime

from core.logging import get_logger
from core.config import config_manager

logger = get_logger("memory")


class MemoryType(str, Enum):
    """记忆类型"""
    CONVERSATION = "conversation"  # 对话记忆
    PREFERENCE = "preference"  # 用户偏好
    FACT = "fact"  # 事实信息
    TASK = "task"  # 任务记录
    NOTE = "note"  # 笔记
    SKILL = "skill"  # 技能记忆
    CUSTOM = "custom"  # 自定义类型


@dataclass
class MemoryItem:
    """单个记忆条目"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: MemoryType = MemoryType.CONVERSATION
    content: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    importance: float = 0.5  # 重要性 0-1
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    accessed_at: float = field(default_factory=time.time)
    access_count: int = 0
    user_id: Optional[str] = None


@dataclass
class MemorySearchResult:
    """记忆搜索结果"""
    item: MemoryItem
    relevance_score: float = 0.0


class MemoryEngine:
    """
    记忆引擎 - 核心存储管理器
    类似于 OpenClaw 的 Soul.md 系统
    """
    
    def __init__(self):
        self.memories: Dict[str, MemoryItem] = {}
        self._data_path: Optional[Path] = None
        self._init_data_path()
        self._load_memories()
    
    def _init_data_path(self):
        """初始化数据存储路径"""
        try:
            self._data_path = config_manager.paths.data_dir / "memory"
            self._data_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.warning(f"无法初始化数据存储路径: {e}")
            self._data_path = Path.home() / ".dataagent" / "memory"
            self._data_path.mkdir(parents=True, exist_ok=True)
    
    def add_memory(self,
                   content: str,
                   memory_type: MemoryType = MemoryType.CONVERSATION,
                   metadata: Optional[Dict[str, Any]] = None,
                   tags: Optional[List[str]] = None,
                   importance: float = 0.5,
                   user_id: Optional[str] = None) -> str:
        """添加新记忆"""
        item = MemoryItem(
            type=memory_type,
            content=content,
            metadata=metadata or {},
            tags=tags or [],
            importance=importance,
            user_id=user_id
        )
        
        self.memories[item.id] = item
        self._save_memories()
        logger.info(f"添加记忆: {item.type} - {len(content)} 字符")
        return item.id
    
    def get_memory(self, memory_id: str) -> Optional[MemoryItem]:
        """获取单个记忆"""
        item = self.memories.get(memory_id)
        if item:
            item.accessed_at = time.time()
            item.access_count += 1
            self._save_memories()
        return item
    
    def update_memory(self, memory_id: str, **kwargs) -> bool:
        """更新记忆"""
        item = self.memories.get(memory_id)
        if not item:
            return False
        
        allowed_fields = ["content", "metadata", "tags", "importance", "type"]
        for key, value in kwargs.items():
            if key in allowed_fields and hasattr(item, key):
                setattr(item, key, value)
        
        item.updated_at = time.time()
        self._save_memories()
        logger.info(f"更新记忆: {memory_id}")
        return True
    
    def delete_memory(self, memory_id: str) -> bool:
        """删除记忆"""
        if memory_id in self.memories:
            del self.memories[memory_id]
            self._save_memories()
            logger.info(f"删除记忆: {memory_id}")
            return True
        return False
    
    def search_memories(self,
                        query: str = "",
                        memory_type: Optional[MemoryType] = None,
                        tags: Optional[List[str]] = None,
                        user_id: Optional[str] = None,
                        limit: int = 20,
                        min_importance: float = 0.0) -> List[MemorySearchResult]:
        """
        搜索记忆
        
        支持关键词搜索、类型过滤、标签过滤
        """
        results = []
        
        for item in self.memories.values():
            # 基本过滤
            if item.importance < min_importance:
                continue
            
            if user_id and item.user_id != user_id:
                continue
            
            if memory_type and item.type != memory_type:
                continue
            
            if tags:
                # 至少匹配一个标签
                if not any(tag in item.tags for tag in tags):
                    continue
            
            # 简单的相关性评分
            relevance_score = self._calculate_relevance(item, query)
            results.append(MemorySearchResult(item=item, relevance_score=relevance_score))
        
        # 按相关性、重要性和时间排序
        results.sort(
            key=lambda r: (
                r.relevance_score,
                r.item.importance,
                r.item.access_count,
                r.item.created_at
            ),
            reverse=True
        )
        
        return results[:limit]
    
    def _calculate_relevance(self, item: MemoryItem, query: str) -> float:
        """简单的相关性计算"""
        if not query:
            return item.importance
        
        score = 0.0
        query_lower = query.lower()
        content_lower = item.content.lower()
        
        # 关键词匹配
        if query_lower in content_lower:
            score += 1.0
        
        # 标签匹配
        for tag in item.tags:
            if tag.lower() in query_lower:
                score += 0.5
        
        # 时间衰减 - 新内容权重更高
        age_days = (time.time() - item.created_at) / (24 * 3600)
        time_factor = max(0.1, 1.0 - (age_days / 30))  # 30天衰减
        
        # 访问频率
        access_factor = min(1.0, item.access_count / 10.0)
        
        return (score + item.importance) * time_factor * (1 + access_factor * 0.2)
    
    def get_recent_memories(self,
                            limit: int = 50,
                            memory_type: Optional[MemoryType] = None,
                            user_id: Optional[str] = None) -> List[MemoryItem]:
        """获取最近的记忆"""
        memories = list(self.memories.values())
        
        if memory_type:
            memories = [m for m in memories if m.type == memory_type]
        
        if user_id:
            memories = [m for m in memories if m.user_id == user_id]
        
        memories.sort(key=lambda m: m.created_at, reverse=True)
        return memories[:limit]
    
    def get_memories_by_type(self, memory_type: MemoryType, limit: int = 100) -> List[MemoryItem]:
        """按类型获取记忆"""
        memories = [m for m in self.memories.values() if m.type == memory_type]
        memories.sort(key=lambda m: m.created_at, reverse=True)
        return memories[:limit]
    
    def get_all_tags(self) -> List[str]:
        """获取所有标签"""
        tag_set = set()
        for item in self.memories.values():
            tag_set.update(item.tags)
        return sorted(list(tag_set))
    
    def set_preference(self, key: str, value: Any, user_id: Optional[str] = None):
        """设置用户偏好"""
        # 检查是否已有此偏好
        existing = None
        for item in self.memories.values():
            if (item.type == MemoryType.PREFERENCE and
                item.metadata.get("key") == key and
                item.user_id == user_id):
                existing = item
                break
        
        if existing:
            existing.content = str(value)
            existing.metadata["value"] = value
            existing.updated_at = time.time()
        else:
            self.add_memory(
                content=f"{key} = {value}",
                memory_type=MemoryType.PREFERENCE,
                metadata={"key": key, "value": value},
                tags=["preference", key],
                importance=0.6,
                user_id=user_id
            )
        
        self._save_memories()
    
    def get_preference(self, key: str, default: Any = None, user_id: Optional[str] = None) -> Any:
        """获取用户偏好"""
        for item in self.memories.values():
            if (item.type == MemoryType.PREFERENCE and
                item.metadata.get("key") == key and
                item.user_id == user_id):
                return item.metadata.get("value", default)
        return default
    
    def get_all_preferences(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """获取所有偏好"""
        preferences = {}
        for item in self.memories.values():
            if item.type == MemoryType.PREFERENCE and item.user_id == user_id:
                key = item.metadata.get("key")
                if key:
                    preferences[key] = item.metadata.get("value")
        return preferences
    
    def export_memories(self, output_path: Optional[Path] = None) -> str:
        """导出所有记忆（类似 Soul.md）"""
        if output_path is None:
            output_path = self._data_path / "soul.md"
        
        # 生成 Markdown 格式的记忆导出
        markdown_lines = ["# DataAgent - Soul Memory", ""]
        
        # 按类型分组
        memories_by_type = {}
        for item in self.memories.values():
            if item.type not in memories_by_type:
                memories_by_type[item.type] = []
            memories_by_type[item.type].append(item)
        
        for mem_type, items in memories_by_type.items():
            markdown_lines.append(f"## {mem_type.value}", "")
            
            for item in sorted(items, key=lambda x: x.created_at, reverse=True):
                created_str = datetime.fromtimestamp(item.created_at).strftime("%Y-%m-%d %H:%M:%S")
                markdown_lines.append(f"### [{created_str}] {item.type}", "")
                markdown_lines.append(item.content)
                markdown_lines.append("")
                
                if item.tags:
                    markdown_lines.append(f"Tags: {', '.join(item.tags)}")
                markdown_lines.append(f"Importance: {item.importance:.2f}")
                markdown_lines.append("---")
                markdown_lines.append("")
        
        content = "\n".join(markdown_lines)
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        logger.info(f"记忆导出到: {output_path}")
        return content
    
    def clear_old_memories(self, days: int = 90, min_importance: float = 0.3):
        """清理旧的、不重要的记忆"""
        cutoff_time = time.time() - (days * 24 * 3600)
        to_delete = []
        
        for item in self.memories.values():
            if (item.created_at < cutoff_time and
                item.importance < min_importance and
                item.access_count < 3):
                to_delete.append(item.id)
        
        for mem_id in to_delete:
            del self.memories[mem_id]
        
        if to_delete:
            logger.info(f"清理了 {len(to_delete)} 条旧记忆")
            self._save_memories()
    
    def _save_memories(self):
        """保存记忆到文件"""
        if not self._data_path:
            return
        
        try:
            memories_data = []
            for item in self.memories.values():
                memories_data.append({
                    "id": item.id,
                    "type": item.type.value,
                    "content": item.content,
                    "metadata": item.metadata,
                    "tags": item.tags,
                    "importance": item.importance,
                    "created_at": item.created_at,
                    "updated_at": item.updated_at,
                    "accessed_at": item.accessed_at,
                    "access_count": item.access_count,
                    "user_id": item.user_id
                })
            
            memories_file = self._data_path / "memories.json"
            with open(memories_file, "w", encoding="utf-8") as f:
                json.dump(memories_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存记忆失败: {e}")
    
    def _load_memories(self):
        """从文件加载记忆"""
        if not self._data_path:
            return
        
        try:
            memories_file = self._data_path / "memories.json"
            if memories_file.exists():
                with open(memories_file, "r", encoding="utf-8") as f:
                    memories_data = json.load(f)
                
                for item_data in memories_data:
                    item = MemoryItem(
                        id=item_data["id"],
                        type=MemoryType(item_data["type"]),
                        content=item_data["content"],
                        metadata=item_data.get("metadata", {}),
                        tags=item_data.get("tags", []),
                        importance=item_data.get("importance", 0.5),
                        created_at=item_data.get("created_at", time.time()),
                        updated_at=item_data.get("updated_at", time.time()),
                        accessed_at=item_data.get("accessed_at", time.time()),
                        access_count=item_data.get("access_count", 0),
                        user_id=item_data.get("user_id")
                    )
                    self.memories[item.id] = item
                
                logger.info(f"加载了 {len(self.memories)} 条记忆")
        except Exception as e:
            logger.error(f"加载记忆失败: {e}")


# 全局记忆引擎实例
_memory_engine: Optional[MemoryEngine] = None


def get_memory_engine() -> MemoryEngine:
    """获取记忆引擎实例"""
    global _memory_engine
    if _memory_engine is None:
        _memory_engine = MemoryEngine()
    return _memory_engine


__all__ = [
    "MemoryType",
    "MemoryItem",
    "MemorySearchResult",
    "MemoryEngine",
    "get_memory_engine"
]
