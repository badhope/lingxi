"""
DataAgent - API Framework
统一的API框架，提供路由、错误处理、参数校验等功能
"""
import asyncio
import re
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Callable, Type

from pydantic import BaseModel, Field, ValidationError, field_validator

from .logging import api_logger
from .config import config_manager


# ============================================================
# Response Models
# ============================================================

class APIResponse(BaseModel):
    """统一响应格式"""
    success: bool = True
    data: Any = None
    error: Optional[str] = None
    message: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: time.strftime("%Y-%m-%d %H:%M:%S"))
    
    @classmethod
    def ok(cls, data: Any = None, message: str = "Success"):
        """成功响应"""
        return cls(success=True, data=data, message=message)
    
    @classmethod
    def error(cls, error: str, message: str = "Error"):
        """错误响应"""
        return cls(success=False, error=error, message=message)


class ErrorCode:
    """错误码定义"""
    # 通用错误 (1000-1999)
    SUCCESS = 1000
    UNKNOWN_ERROR = 1001
    VALIDATION_ERROR = 1002
    NOT_FOUND = 1003
    UNAUTHORIZED = 1004
    FORBIDDEN = 1005
    RATE_LIMITED = 1006
    
    # 文件相关错误 (2000-2999)
    FILE_TOO_LARGE = 2001
    INVALID_FILE_TYPE = 2002
    FILE_UPLOAD_FAILED = 2003
    
    # 数据库相关错误 (3000-3999)
    DB_CONNECTION_ERROR = 3001
    DB_QUERY_ERROR = 3002
    DB_NOT_FOUND = 3003
    
    # LLM相关错误 (4000-4999)
    LLM_API_ERROR = 4001
    LLM_TIMEOUT = 4002
    LLM_INVALID_RESPONSE = 4003
    
    # Agent相关错误 (5000-5999)
    AGENT_ERROR = 5001
    AGENT_TIMEOUT = 5002
    AGENT_NOT_FOUND = 5003


class APIError(Exception):
    """API异常类"""
    
    def __init__(self, code: int, message: str, details: Any = None):
        self.code = code
        self.message = message
        self.details = details
        super().__init__(message)
    
    def to_response(self) -> Dict[str, Any]:
        """转换为响应格式"""
        return APIResponse.error(self.message, self.message).model_dump()


# ============================================================
# Request Validation
# ============================================================

class BaseRequest(BaseModel):
    """请求基类"""
    
    @classmethod
    def validate_request(cls, data: Dict[str, Any]) -> 'BaseRequest':
        """验证请求数据"""
        try:
            return cls(**data)
        except ValidationError as e:
            errors = e.errors()
            error_messages = [
                f"{err['loc'][0]}: {err['msg']}" if err['loc'] else err['msg']
                for err in errors
            ]
            raise APIError(ErrorCode.VALIDATION_ERROR, "; ".join(error_messages))


class QueryRequest(BaseRequest):
    """查询请求"""
    query: str = Field(..., min_length=1, max_length=5000, description="查询内容")
    kb_id: Optional[str] = Field(None, description="知识库ID")
    top_k: int = Field(5, ge=1, le=20, description="返回结果数量")
    
    @field_validator('query')
    @classmethod
    def sanitize_query(cls, v):
        """清理查询内容"""
        return v.strip()


class MessageRequest(BaseRequest):
    """消息请求"""
    content: str = Field(..., min_length=1, max_length=100000, description="消息内容")
    session_id: Optional[str] = Field(None, description="会话ID")
    files: List[str] = Field(default_factory=list, description="附加文件")
    settings: Optional[Dict[str, Any]] = Field(None, description="设置")


class SkillRequest(BaseRequest):
    """技能请求"""
    skill_id: Optional[str] = Field(None, description="技能ID")
    name: Optional[str] = Field(None, min_length=1, max_length=50, description="技能名称")
    description: Optional[str] = Field(None, max_length=500, description="技能描述")
    category: Optional[str] = Field(None, description="分类")
    prompts: Optional[Dict[str, str]] = Field(None, description="提示词配置")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if v:
            return v.strip()


class FileUploadRequest(BaseRequest):
    """文件上传请求"""
    filename: str = Field(..., min_length=1, max_length=255, description="文件名")
    content_type: Optional[str] = Field(None, description="文件类型")
    kb_id: Optional[str] = Field(None, description="关联知识库")
    
    @field_validator('filename')
    @classmethod
    def validate_filename(cls, v):
        """验证文件名"""
        # 检查路径遍历攻击
        if '..' in v or v.startswith('/'):
            raise APIError(ErrorCode.INVALID_FILE_TYPE, "Invalid filename")
        # 检查特殊字符
        if re.search(r'[\<\>\"\'\\\|]', v):
            raise APIError(ErrorCode.INVALID_FILE_TYPE, "Filename contains invalid characters")
        return v


# ============================================================
# Error Handler
# ============================================================

class ErrorHandler:
    """错误处理器"""
    
    @staticmethod
    def handle_validation_error(e: ValidationError) -> Dict[str, Any]:
        """处理验证错误"""
        errors = e.errors()
        messages = [
            f"{'.'.join(str(loc) for loc in err['loc'])}: {err['msg']}"
            for err in errors
        ]
        api_logger.warning(f"Validation error: {messages}")
        return APIResponse.error("; ".join(messages), "Validation failed").model_dump()
    
    @staticmethod
    def handle_api_error(e: APIError) -> Dict[str, Any]:
        """处理API错误"""
        api_logger.error(f"API error [{e.code}]: {e.message}")
        return e.to_response()
    
    @staticmethod
    def handle_generic_error(e: Exception) -> Dict[str, Any]:
        """处理通用错误"""
        api_logger.error(f"Unhandled error: {str(e)}", exc_info=True)
        return APIResponse.error(str(e), "Internal server error").model_dump()
    
    @classmethod
    def handle_error(cls, e: Exception) -> Dict[str, Any]:
        """统一错误处理"""
        if isinstance(e, ValidationError):
            return cls.handle_validation_error(e)
        elif isinstance(e, APIError):
            return cls.handle_api_error(e)
        else:
            return cls.handle_generic_error(e)


# ============================================================
# Rate Limiter
# ============================================================

class RateLimiter:
    """速率限制器"""
    
    def __init__(self):
        self._requests: Dict[str, List[float]] = {}
        self._lock = asyncio.Lock()
        self._max_requests = config_manager.security.rate_limit_max_requests
        self._window = config_manager.security.rate_limit_window
    
    async def check_limit(self, key: str) -> bool:
        """检查是否超过限制"""
        async with self._lock:
            now = time.time()
            window_start = now - self._window
            
            # 清理过期记录
            if key in self._requests:
                self._requests[key] = [
                    t for t in self._requests[key] if t > window_start
                ]
            else:
                self._requests[key] = []
            
            # 检查限制
            if len(self._requests[key]) >= self._max_requests:
                api_logger.warning(f"Rate limit exceeded for key: {key}")
                return False
            
            # 记录请求
            self._requests[key].append(now)
            return True
    
    async def get_remaining(self, key: str) -> int:
        """获取剩余请求次数"""
        async with self._lock:
            now = time.time()
            window_start = now - self._window
            
            if key not in self._requests:
                return self._max_requests
            
            # 清理过期记录
            self._requests[key] = [
                t for t in self._requests[key] if t > window_start
            ]
            
            return max(0, self._max_requests - len(self._requests[key]))
    
    async def reset(self, key: str):
        """重置限制"""
        async with self._lock:
            if key in self._requests:
                del self._requests[key]


# ============================================================
# Middleware
# ============================================================

class RequestMiddleware(ABC):
    """请求中间件基类"""
    
    @abstractmethod
    async def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """处理请求"""
        pass


class SecurityMiddleware(RequestMiddleware):
    """安全中间件"""
    
    async def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """安全检查"""
        # 检查SQL注入
        dangerous_patterns = [
            r'(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)',
            r'(--|#|\/\*|\*\/)',
            r'(\bOR\b.*\b=\b|\bAND\b.*\b=\b)',
        ]
        
        for key, value in request.items():
            if isinstance(value, str):
                for pattern in dangerous_patterns:
                    if re.search(pattern, value, re.IGNORECASE):
                        api_logger.warning(f"Potential SQL injection detected in {key}")
                        raise APIError(
                            ErrorCode.FORBIDDEN,
                            "Request contains potentially dangerous content"
                        )
        
        return request


class ValidationMiddleware(RequestMiddleware):
    """验证中间件"""
    
    def __init__(self, schema: Type[BaseRequest]):
        self.schema = schema
    
    async def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """验证请求"""
        try:
            validated = self.schema.validate_request(request)
            return validated.model_dump()
        except APIError:
            raise
        except Exception as e:
            raise APIError(ErrorCode.VALIDATION_ERROR, str(e))


# ============================================================
# Router
# ============================================================

class APIMethod:
    """API方法定义"""
    
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"


class APIEndpoint:
    """API端点"""
    
    def __init__(
        self,
        path: str,
        method: str,
        handler: Callable,
        request_schema: Optional[Type[BaseRequest]] = None,
        middlewares: Optional[List[RequestMiddleware]] = None,
        tags: Optional[List[str]] = None,
        summary: Optional[str] = None,
        description: Optional[str] = None,
        rate_limit: bool = True,
    ):
        self.path = path
        self.method = method
        self.handler = handler
        self.request_schema = request_schema
        self.middlewares = middlewares or []
        self.tags = tags or []
        self.summary = summary
        self.description = description
        self.rate_limit = rate_limit


class APICollector:
    """API收集器 - 用于收集所有API端点"""
    
    def __init__(self):
        self._endpoints: Dict[str, List[APIEndpoint]] = {}
    
    def add_endpoint(self, endpoint: APIEndpoint):
        """添加端点"""
        key = f"{endpoint.method}:{endpoint.path}"
        if key not in self._endpoints:
            self._endpoints[key] = []
        self._endpoints[key].append(endpoint)
    
    def get_endpoint(self, method: str, path: str) -> Optional[APIEndpoint]:
        """获取端点"""
        key = f"{method}:{path}"
        endpoints = self._endpoints.get(key, [])
        return endpoints[0] if endpoints else None
    
    def list_endpoints(self) -> List[APIEndpoint]:
        """列出所有端点"""
        endpoints = []
        for endpoint_list in self._endpoints.values():
            endpoints.extend(endpoint_list)
        return endpoints
    
    def get_openapi_spec(self) -> Dict[str, Any]:
        """生成OpenAPI规范"""
        paths = {}
        
        for endpoint in self.list_endpoints():
            if endpoint.path not in paths:
                paths[endpoint.path] = {}
            
            method_lower = endpoint.method.lower()
            paths[endpoint.path][method_lower] = {
                "summary": endpoint.summary or endpoint.path,
                "description": endpoint.description or "",
                "tags": endpoint.tags,
                "responses": {
                    "200": {"description": "Success"},
                    "400": {"description": "Validation error"},
                    "500": {"description": "Internal server error"},
                },
            }
        
        return {
            "openapi": "3.0.0",
            "info": {
                "title": "DataAgent API",
                "version": "1.0.0",
                "description": "DataAgent API Documentation",
            },
            "paths": paths,
        }


# 全局实例
rate_limiter = RateLimiter()
api_collector = APICollector()
security_middleware = SecurityMiddleware()


# 便捷函数
async def check_rate_limit(key: str) -> bool:
    """检查速率限制"""
    return await rate_limiter.check_limit(key)


async def get_rate_limit_remaining(key: str) -> int:
    """获取剩余请求次数"""
    return await rate_limiter.get_remaining(key)


def validate_request(schema: Type[BaseRequest]):
    """验证请求装饰器"""
    def decorator(func: Callable) -> Callable:
        async def wrapper(*args, **kwargs):
            request_data = kwargs.get('request') or args[0] if args else {}
            validated = schema.validate_request(request_data)
            kwargs['request'] = validated.model_dump()
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def api_endpoint(
    path: str,
    method: str = APIMethod.POST,
    request_schema: Optional[Type[BaseRequest]] = None,
    tags: Optional[List[str]] = None,
    summary: Optional[str] = None,
    rate_limit: bool = True,
):
    """API端点装饰器"""
    def decorator(func: Callable) -> Callable:
        endpoint = APIEndpoint(
            path=path,
            method=method,
            handler=func,
            request_schema=request_schema,
            tags=tags,
            summary=summary,
            rate_limit=rate_limit,
        )
        api_collector.add_endpoint(endpoint)
        return func
    return decorator
