"""
DataAgent - Performance & Security Module
性能优化和安全加固模块
"""
import asyncio
import hashlib
import hmac
import time
import psutil
import os
from typing import Dict, Any, Optional

from .logging import get_logger

logger = get_logger('dataagent.performance')


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self._start_time = time.time()
        self._metrics: Dict[str, Any] = {}
        self._request_count = 0
        self._error_count = 0
    
    def record_request(self, endpoint: str, duration: float, success: bool = True):
        """记录请求"""
        self._request_count += 1
        if not success:
            self._error_count += 1
        
        if endpoint not in self._metrics:
            self._metrics[endpoint] = {
                "count": 0,
                "total_duration": 0,
                "avg_duration": 0,
                "min_duration": float('inf'),
                "max_duration": 0,
                "errors": 0
            }
        
        m = self._metrics[endpoint]
        m["count"] += 1
        m["total_duration"] += duration
        m["avg_duration"] = m["total_duration"] / m["count"]
        m["min_duration"] = min(m["min_duration"], duration)
        m["max_duration"] = max(m["max_duration"], duration)
        if not success:
            m["errors"] += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        return {
            "uptime": time.time() - self._start_time,
            "total_requests": self._request_count,
            "total_errors": self._error_count,
            "error_rate": self._error_count / self._request_count if self._request_count > 0 else 0,
            "endpoints": self._metrics
        }
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """获取系统指标"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_used_mb": memory.used / (1024 * 1024),
                "memory_available_mb": memory.available / (1024 * 1024),
                "disk_percent": disk.percent,
                "disk_used_gb": disk.used / (1024 * 1024 * 1024),
                "disk_free_gb": disk.free / (1024 * 1024 * 1024)
            }
        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            return {}
    
    def reset(self):
        """重置指标"""
        self._metrics = {}
        self._request_count = 0
        self._error_count = 0


class SecurityManager:
    """安全管理器"""
    
    def __init__(self):
        self._failed_attempts: Dict[str, int] = {}
        self._blocked_ips: Dict[str, float] = {}
        self._max_attempts = 5
        self._block_duration = 3600  # 1小时
    
    def check_ip(self, ip: str) -> bool:
        """检查IP是否被阻止"""
        if ip in self._blocked_ips:
            if time.time() - self._blocked_ips[ip] < self._block_duration:
                return False
            else:
                del self._blocked_ips[ip]
        return True
    
    def record_failed_attempt(self, ip: str):
        """记录失败尝试"""
        if ip not in self._failed_attempts:
            self._failed_attempts[ip] = 0
        
        self._failed_attempts[ip] += 1
        
        if self._failed_attempts[ip] >= self._max_attempts:
            self._blocked_ips[ip] = time.time()
            logger.warning(f"IP blocked due to too many failed attempts: {ip}")
    
    def reset_attempts(self, ip: str):
        """重置失败尝试"""
        if ip in self._failed_attempts:
            del self._failed_attempts[ip]
    
    def generate_token(self, length: int = 32) -> str:
        """生成安全令牌"""
        import secrets
        return secrets.token_urlsafe(length)
    
    def hash_password(self, password: str) -> str:
        """密码哈希"""
        salt = hashlib.sha256(str(time.time()).encode()).hexdigest()[:16]
        pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return f"{salt}${pwd_hash.hex()}"
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """验证密码"""
        try:
            salt, pwd_hash = hashed.split('$')
            new_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
            return hmac.compare_digest(new_hash.hex(), pwd_hash)
        except:
            return False


class CacheManager:
    """缓存管理器"""
    
    def __init__(self, max_size: int = 1000):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._max_size = max_size
        self._access_times: Dict[str, float] = {}
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        if key in self._cache:
            entry = self._cache[key]
            if time.time() - entry["timestamp"] < entry["ttl"]:
                self._access_times[key] = time.time()
                return entry["value"]
            else:
                del self._cache[key]
                if key in self._access_times:
                    del self._access_times[key]
        return None
    
    def set(self, key: str, value: Any, ttl: int = 3600):
        """设置缓存"""
        if len(self._cache) >= self._max_size:
            self._evict_oldest()
        
        self._cache[key] = {
            "value": value,
            "timestamp": time.time(),
            "ttl": ttl
        }
        self._access_times[key] = time.time()
    
    def delete(self, key: str):
        """删除缓存"""
        if key in self._cache:
            del self._cache[key]
        if key in self._access_times:
            del self._access_times[key]
    
    def clear(self):
        """清空缓存"""
        self._cache = {}
        self._access_times = {}
    
    def _evict_oldest(self):
        """驱逐最旧的条目"""
        if not self._access_times:
            return
        
        oldest_key = min(self._access_times.items(), key=lambda x: x[1])[0]
        self.delete(oldest_key)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        return {
            "size": len(self._cache),
            "max_size": self._max_size,
            "utilization": len(self._cache) / self._max_size if self._max_size > 0 else 0
        }


class ConnectionPool:
    """连接池"""
    
    def __init__(self, factory, max_connections: int = 10):
        self._factory = factory
        self._max_connections = max_connections
        self._pool: asyncio.Queue = asyncio.Queue(max_connections)
        self._size = 0
        self._lock = asyncio.Lock()
    
    async def initialize(self):
        """初始化连接池"""
        for _ in range(self._max_connections // 2):
            await self.add_connection()
    
    async def add_connection(self):
        """添加连接"""
        async with self._lock:
            if self._size < self._max_connections:
                conn = await self._factory()
                await self._pool.put(conn)
                self._size += 1
    
    async def get_connection(self):
        """获取连接"""
        try:
            conn = await asyncio.wait_for(self._pool.get(), timeout=5.0)
            return conn
        except asyncio.TimeoutError:
            await self.add_connection()
            return await self._pool.get()
    
    async def return_connection(self, conn):
        """归还连接"""
        await self._pool.put(conn)
    
    async def close_all(self):
        """关闭所有连接"""
        while not self._pool.empty():
            try:
                conn = self._pool.get_nowait()
                if hasattr(conn, 'close'):
                    await conn.close()
            except:
                pass
        self._size = 0


# 全局实例
performance_monitor = PerformanceMonitor()
security_manager = SecurityManager()
cache_manager = CacheManager()


# 便捷函数
def monitor_performance(func):
    """性能监控装饰器"""
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        success = True
        try:
            result = await func(*args, **kwargs)
            return result
        except Exception as e:
            success = False
            raise
        finally:
            duration = time.time() - start_time
            performance_monitor.record_request(
                func.__name__,
                duration,
                success
            )
    return wrapper


def rate_limit(max_calls: int, period: float):
    """速率限制装饰器"""
    calls = []
    
    def decorator(func):
        async def wrapper(*args, **kwargs):
            now = time.time()
            calls[:] = [t for t in calls if now - t < period]
            
            if len(calls) >= max_calls:
                raise Exception(f"Rate limit exceeded: {max_calls} calls per {period}s")
            
            calls.append(now)
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_auth(func):
    """认证要求装饰器"""
    async def wrapper(*args, **kwargs):
        # 检查认证逻辑
        # 这里简化处理，实际应该检查token等
        return await func(*args, **kwargs)
    return wrapper
