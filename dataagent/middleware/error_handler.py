"""
DataAgent - 全局异常处理中间件
统一的错误处理、日志记录和响应格式化
"""

import traceback
import time
import logging
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

# 使用标准的 logging 模块
logger = logging.getLogger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """全局异常处理中间件"""

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        request_id = id(request)  # 为请求生成唯一ID

        try:
            # 记录请求开始
            logger.info(
                f"Request [{request_id}] Start: {request.method} {request.url.path}"
            )

            response = await call_next(request)

            # 记录请求完成
            duration = time.time() - start_time
            status_code = response.status_code

            log_msg = f"Request [{request_id}] Complete: {request.method} {request.url.path} -> {status_code} ({duration:.3f}s)"
            
            if status_code >= 500:
                logger.error(log_msg)
            elif status_code >= 400:
                logger.warning(log_msg)
            else:
                logger.info(log_msg)

            return response

        except Exception as e:
            duration = time.time() - start_time
            logger.critical(
                f"Request [{request_id}] Failed: {request.method} {request.url.path} -> UNHANDLED ({duration:.3f}s)",
                exc_info=True
            )

            # 根据错误类型返回不同的响应
            error_detail = str(e)
            
            # 安全地截取错误信息
            if len(error_detail) > 500:
                error_detail = error_detail[:497] + "..."

            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "error": "服务器内部错误",
                    "detail": error_detail,
                    "request_id": str(request_id)
                }
            )
