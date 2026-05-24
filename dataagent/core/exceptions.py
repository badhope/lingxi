"""
DataAgent - 统一异常处理模块
提供统一的异常类和错误响应格式化
"""
from enum import Enum
from typing import Optional, Dict, Any
from fastapi import HTTPException, status
from core.logging import get_logger

logger = get_logger("exceptions")


class ErrorCode(Enum):
    """错误代码枚举"""
    # 通用错误 (1xxxx)
    SUCCESS = 20000
    UNKNOWN_ERROR = 10000
    INVALID_REQUEST = 10001
    UNAUTHORIZED = 10002
    FORBIDDEN = 10003
    NOT_FOUND = 10004
    CONFLICT = 10005
    RATE_LIMITED = 10006
    VALIDATION_ERROR = 10007
    
    # 认证错误 (2xxxx)
    AUTH_FAILED = 20001
    TOKEN_EXPIRED = 20002
    TOKEN_INVALID = 20003
    USER_NOT_FOUND = 20004
    USER_DISABLED = 20005
    
    # 资源错误 (3xxxx)
    RESOURCE_NOT_FOUND = 30001
    RESOURCE_EXISTS = 30002
    RESOURCE_INVALID = 30003
    
    # 插件/技能错误 (4xxxx)
    PLUGIN_NOT_FOUND = 40001
    PLUGIN_LOAD_FAILED = 40002
    SKILL_NOT_FOUND = 40003
    SKILL_EXECUTION_FAILED = 40004
    
    # LLM 错误 (5xxxx)
    LLM_PROVIDER_ERROR = 50001
    LLM_TIMEOUT = 50002
    LLM_RATE_LIMIT = 50003
    LLM_INVALID_REQUEST = 50004
    
    # 文件/存储错误 (6xxxx)
    FILE_NOT_FOUND = 60001
    FILE_INVALID = 60002
    FILE_UPLOAD_FAILED = 60003
    
    # 数据错误 (7xxxx)
    DATABASE_ERROR = 70001
    DATA_INVALID = 70002
    
    # WebSocket 错误 (8xxxx)
    WS_CONNECTION_ERROR = 80001
    WS_MESSAGE_ERROR = 80002


class DataAgentException(Exception):
    """DataAgent 基础异常类"""
    
    def __init__(
        self,
        error_code: ErrorCode,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        status_code: int = status.HTTP_400_BAD_REQUEST
    ):
        self.error_code = error_code
        self.message = message
        self.details = details or {}
        self.status_code = status_code
        super().__init__(message)
    
    def to_response(self) -> Dict[str, Any]:
        """转换为 API 响应格式"""
        return {
            "success": False,
            "error": {
                "code": self.error_code.value,
                "message": self.message,
                "details": self.details,
                "timestamp": __import__("time").time()
            }
        }


class ResourceNotFoundException(DataAgentException):
    """资源未找到异常"""
    
    def __init__(self, resource: str, resource_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        message = f"{resource} not found"
        if resource_id:
            message += f" (ID: {resource_id})"
        
        super().__init__(
            error_code=ErrorCode.RESOURCE_NOT_FOUND,
            message=message,
            details=details or {},
            status_code=status.HTTP_404_NOT_FOUND
        )


class InvalidRequestException(DataAgentException):
    """无效请求异常"""
    
    def __init__(self, message: str = "Invalid request", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            error_code=ErrorCode.INVALID_REQUEST,
            message=message,
            details=details or {},
            status_code=status.HTTP_400_BAD_REQUEST
        )


class ValidationException(DataAgentException):
    """验证异常"""
    
    def __init__(self, field: str, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            error_code=ErrorCode.VALIDATION_ERROR,
            message=f"{field}: {message}",
            details=details or {},
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        )


class UnauthorizedException(DataAgentException):
    """未授权异常"""
    
    def __init__(self, message: str = "Unauthorized", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            error_code=ErrorCode.UNAUTHORIZED,
            message=message,
            details=details or {},
            status_code=status.HTTP_401_UNAUTHORIZED
        )


class ForbiddenException(DataAgentException):
    """禁止访问异常"""
    
    def __init__(self, message: str = "Forbidden", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            error_code=ErrorCode.FORBIDDEN,
            message=message,
            details=details or {},
            status_code=status.HTTP_403_FORBIDDEN
        )


class PluginNotFoundException(DataAgentException):
    """插件未找到异常"""
    
    def __init__(self, plugin_id: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            error_code=ErrorCode.PLUGIN_NOT_FOUND,
            message=f"Plugin not found: {plugin_id}",
            details=details or {},
            status_code=status.HTTP_404_NOT_FOUND
        )


class SkillNotFoundException(DataAgentException):
    """技能未找到异常"""
    
    def __init__(self, skill_id: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            error_code=ErrorCode.SKILL_NOT_FOUND,
            message=f"Skill not found: {skill_id}",
            details=details or {},
            status_code=status.HTTP_404_NOT_FOUND
        )


class LLMProviderException(DataAgentException):
    """LLM 提供方异常"""
    
    def __init__(self, provider: str, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            error_code=ErrorCode.LLM_PROVIDER_ERROR,
            message=f"{provider} error: {message}",
            details=details or {},
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )


class FileException(DataAgentException):
    """文件操作异常"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            error_code=ErrorCode.FILE_INVALID,
            message=message,
            details=details or {},
            status_code=status.HTTP_400_BAD_REQUEST
        )


def create_http_exception(exception: DataAgentException) -> HTTPException:
    """将 DataAgent 异常转换为 FastAPI HTTPException"""
    return HTTPException(
        status_code=exception.status_code,
        detail=exception.to_response()
    )


def handle_exception(exc: Exception) -> Dict[str, Any]:
    """通用异常处理函数"""
    if isinstance(exc, DataAgentException):
        logger.error(f"DataAgentException: {exc.error_code.value} - {exc.message}")
        return exc.to_response()
    
    logger.error(f"Unexpected exception: {type(exc).__name__} - {exc}", exc_info=True)
    return {
        "success": False,
        "error": {
            "code": ErrorCode.UNKNOWN_ERROR.value,
            "message": str(exc) or "An unexpected error occurred",
            "details": {},
            "timestamp": __import__("time").time()
        }
    }
