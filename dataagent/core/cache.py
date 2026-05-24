"""
DataAgent - 缓存系统
提供内存缓存和文件缓存功能
"""
import hashlib
import json
import os
import time
import pickle
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass, field
from functools import wraps
from datetime import datetime, timedelta

from core.logging import get_logger

logger = get_logger("cache")


@dataclass
class CacheEntry:
    """缓存条目"""
    key: str
    value: Any
    created_at: float = field(default_factory=time.time)
    expires_at: Optional[float] = None
    hits: int = 0


class CacheManager:
    """
    缓存管理器
    支持内存缓存和文件缓存
    """
    
    def __init__(
        self,
        cache_dir: Optional[Path] = None,
        default_ttl: int = 3600
    ):
        if cache_dir is None:
            cache_dir = Path.home() / ".dataagent" / "cache"
        
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.default_ttl = default_ttl
        
        # 内存缓存
        self._memory_cache: Dict[str, CacheEntry] = {}
        
        # 统计信息
        self._hits = 0
        self._misses = 0
        self._sets = 0
        self._evictions = 0
        
        logger.info("缓存管理器初始化完成")
    
    def _get_file_path(self, key: str) -> Path:
        """获取缓存文件路径"""
        # 使用 MD5 哈希作为文件名
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"{key_hash}.cache"
    
    def _is_expired(self, entry: CacheEntry) -> bool:
        """检查缓存条目是否过期"""
        if entry.expires_at is None:
            return False
        return time.time() > entry.expires_at
    
    # ========== 内存缓存 ==========
    
    def get(self, key: str) -> Optional[Any]:
        """从内存缓存获取"""
        if key not in self._memory_cache:
            self._misses += 1
            return None
        
        entry = self._memory_cache[key]
        
        if self._is_expired(entry):
            del self._memory_cache[key]
            self._misses += 1
            self._evictions += 1
            return None
        
        entry.hits += 1
        self._hits += 1
        return entry.value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """设置内存缓存"""
        ttl = ttl or self.default_ttl
        expires_at = time.time() + ttl if ttl > 0 else None
        
        self._memory_cache[key] = CacheEntry(
            key=key,
            value=value,
            expires_at=expires_at
        )
        self._sets += 1
    
    def delete(self, key: str) -> bool:
        """删除内存缓存"""
        if key in self._memory_cache:
            del self._memory_cache[key]
            self._evictions += 1
            return True
        return False
    
    def clear_memory(self) -> None:
        """清空内存缓存"""
        count = len(self._memory_cache)
        self._memory_cache = {}
        self._evictions += count
        logger.info(f"清空 {count} 个内存缓存条目")
    
    # ========== 文件缓存 ==========
    
    def get_file(self, key: str) -> Optional[Any]:
        """从文件缓存获取"""
        file_path = self._get_file_path(key)
        
        if not file_path.exists():
            self._misses += 1
            return None
        
        try:
            with open(file_path, 'rb') as f:
                data = pickle.load(f)
            
            entry = CacheEntry(**data)
            
            if self._is_expired(entry):
                file_path.unlink(missing_ok=True)
                self._misses += 1
                self._evictions += 1
                return None
            
            entry.hits += 1
            self._hits += 1
            
            # 更新文件中的 hits 计数
            data['hits'] = entry.hits
            with open(file_path, 'wb') as f:
                pickle.dump(data, f)
            
            return entry.value
            
        except Exception as e:
            logger.error(f"读取文件缓存失败: {e}")
            self._misses += 1
            return None
    
    def set_file(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """设置文件缓存"""
        ttl = ttl or self.default_ttl
        expires_at = time.time() + ttl if ttl > 0 else None
        
        file_path = self._get_file_path(key)
        
        data = {
            'key': key,
            'value': value,
            'created_at': time.time(),
            'expires_at': expires_at,
            'hits': 0
        }
        
        try:
            with open(file_path, 'wb') as f:
                pickle.dump(data, f)
            self._sets += 1
        except Exception as e:
            logger.error(f"写入文件缓存失败: {e}")
    
    def delete_file(self, key: str) -> bool:
        """删除文件缓存"""
        file_path = self._get_file_path(key)
        if file_path.exists():
            file_path.unlink(missing_ok=True)
            self._evictions += 1
            return True
        return False
    
    def clear_files(self) -> int:
        """清空所有文件缓存"""
        count = 0
        for file_path in self.cache_dir.glob("*.cache"):
            try:
                file_path.unlink(missing_ok=True)
                count += 1
            except Exception as e:
                logger.error(f"删除缓存文件失败: {e}")
        
        self._evictions += count
        logger.info(f"清空 {count} 个文件缓存")
        return count
    
    # ========== 混合缓存（先内存后文件） ==========
    
    def get_multi(self, key: str) -> Optional[Any]:
        """先查内存，再查文件"""
        # 先查内存
        value = self.get(key)
        if value is not None:
            return value
        
        # 再查文件
        value = self.get_file(key)
        if value is not None:
            # 加载到内存
            self.set(key, value)
            return value
        
        return None
    
    def set_multi(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """同时设置内存和文件缓存"""
        self.set(key, value, ttl)
        self.set_file(key, value, ttl)
    
    # ========== 装饰器 ==========
    
    def cached(self, ttl: Optional[int] = None, use_file: bool = False):
        """
        缓存装饰器
        :param ttl: 过期时间（秒）
        :param use_file: 是否使用文件缓存
        """
        def decorator(func: Callable):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                # 生成缓存键
                key_parts = [func.__module__, func.__name__]
                key_parts.extend(str(arg) for arg in args)
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                key = ":".join(key_parts)
                
                # 尝试获取缓存
                cache_func = self.get_multi if not use_file else self.get_file
                result = cache_func(key)
                if result is not None:
                    return result
                
                # 执行函数
                result = await func(*args, **kwargs)
                
                # 缓存结果
                set_func = self.set_multi if not use_file else self.set_file
                set_func(key, result, ttl)
                
                return result
            
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                # 生成缓存键
                key_parts = [func.__module__, func.__name__]
                key_parts.extend(str(arg) for arg in args)
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                key = ":".join(key_parts)
                
                # 尝试获取缓存
                cache_func = self.get_multi if not use_file else self.get_file
                result = cache_func(key)
                if result is not None:
                    return result
                
                # 执行函数
                result = func(*args, **kwargs)
                
                # 缓存结果
                set_func = self.set_multi if not use_file else self.set_file
                set_func(key, result, ttl)
                
                return result
            
            if hasattr(func, '__await__'):
                return async_wrapper
            else:
                return sync_wrapper
        
        return decorator
    
    # ========== 统计信息 ==========
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        total_requests = self._hits + self._misses
        hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'hits': self._hits,
            'misses': self._misses,
            'sets': self._sets,
            'evictions': self._evictions,
            'hit_rate': hit_rate,
            'memory_entries': len(self._memory_cache),
            'total_requests': total_requests
        }
    
    def clear_expired(self) -> int:
        """清空过期缓存"""
        # 内存缓存
        expired_keys = [
            key for key, entry in self._memory_cache.items()
            if self._is_expired(entry)
        ]
        for key in expired_keys:
            del self._memory_cache[key]
        
        memory_count = len(expired_keys)
        self._evictions += memory_count
        
        # 文件缓存
        file_count = 0
        for file_path in self.cache_dir.glob("*.cache"):
            try:
                with open(file_path, 'rb') as f:
                    data = pickle.load(f)
                
                if data.get('expires_at') and time.time() > data['expires_at']:
                    file_path.unlink(missing_ok=True)
                    file_count += 1
                    self._evictions += 1
            except Exception:
                pass
        
        logger.info(f"清空 {memory_count} 个过期内存缓存和 {file_count} 个过期文件缓存")
        return memory_count + file_count
    
    def reset_stats(self) -> None:
        """重置统计信息"""
        self._hits = 0
        self._misses = 0
        self._sets = 0
        self._evictions = 0
        logger.info("缓存统计信息已重置")


# 全局缓存管理器
_cache_manager: Optional[CacheManager] = None


def get_cache_manager() -> CacheManager:
    """获取缓存管理器"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager
