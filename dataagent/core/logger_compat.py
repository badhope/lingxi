"""
Logger 兼容性模块
提供向后兼容的 logger 接口
"""
from core.logging import get_logger, core_logger

# 为了兼容旧代码
logger = core_logger

__all__ = ['logger', 'get_logger']
