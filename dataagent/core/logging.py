"""
DataAgent - Unified Logging System
统一日志管理模块
"""
import logging
import logging.handlers
import os
import sys
from pathlib import Path
from typing import Optional

from .config import config_manager


class ColoredFormatter(logging.Formatter):
    """带颜色的日志格式化器"""
    
    COLORS = {
        'DEBUG': '\033[0;34m',      # Blue
        'INFO': '\033[0;32m',       # Green
        'WARNING': '\033[0;33m',    # Yellow
        'ERROR': '\033[0;31m',      # Red
        'CRITICAL': '\033[1;31m',   # Bold Red
        'RESET': '\033[0m'          # Reset
    }
    
    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.COLORS['INFO'])
        record.levelname = f"{log_color}{record.levelname}{self.COLORS['RESET']}"
        record.msg = f"{log_color}{record.msg}{self.COLORS['RESET']}"
        return super().format(record)


class StructuredFormatter(logging.Formatter):
    """结构化日志格式化器 - 支持JSON输出"""
    
    def format(self, record):
        # 获取额外的上下文信息
        extra = record.__dict__.get('extra', {})
        log_entry = {
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            **extra
        }
        
        # 添加异常信息
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        return str(log_entry)


class LoggerManager:
    """日志管理器"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._configure_logging()
            self._initialized = True
    
    def _configure_logging(self):
        """配置日志系统"""
        # 获取配置
        log_config = config_manager.logging
        paths = config_manager.paths
        
        # 创建日志目录
        log_dir = paths.data_dir / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # 设置根日志级别
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, log_config.level))
        
        # 移除默认处理器
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # 创建格式化器
        console_formatter = ColoredFormatter(log_config.format)
        file_formatter = logging.Formatter(log_config.format)
        
        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
        
        # 文件处理器（带轮换）
        if log_config.file_path:
            log_file = Path(log_config.file_path)
        else:
            log_file = log_dir / "dataagent.log"
        
        max_bytes = log_config.max_file_size_mb * 1024 * 1024
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=log_config.backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
    
    def get_logger(self, name: str) -> logging.Logger:
        """获取指定名称的日志记录器"""
        return logging.getLogger(name)
    
    def configure_for_module(self, module_name: str, level: Optional[int] = None) -> logging.Logger:
        """为特定模块配置日志记录器"""
        logger = logging.getLogger(module_name)
        if level:
            logger.setLevel(level)
        return logger


# 创建全局日志管理器实例
logger_manager = LoggerManager()


def get_logger(name: str) -> logging.Logger:
    """获取日志记录器的便捷函数"""
    return logger_manager.get_logger(name)


class LogContext:
    """日志上下文管理器 - 用于添加请求上下文信息"""
    
    def __init__(self, logger: logging.Logger, **context):
        self.logger = logger
        self.context = context
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
    
    def info(self, message: str, **kwargs):
        self.logger.info(message, extra={'extra': {**self.context, **kwargs}})
    
    def debug(self, message: str, **kwargs):
        self.logger.debug(message, extra={'extra': {**self.context, **kwargs}})
    
    def warning(self, message: str, **kwargs):
        self.logger.warning(message, extra={'extra': {**self.context, **kwargs}})
    
    def error(self, message: str, **kwargs):
        self.logger.error(message, extra={'extra': {**self.context, **kwargs}})
    
    def critical(self, message: str, **kwargs):
        self.logger.critical(message, extra={'extra': {**self.context, **kwargs}})


# 为主要模块创建预配置的日志记录器
core_logger = get_logger('dataagent.core')
api_logger = get_logger('dataagent.api')
agent_logger = get_logger('dataagent.agent')
tool_logger = get_logger('dataagent.tool')
llm_logger = get_logger('dataagent.llm')
db_logger = get_logger('dataagent.db')
security_logger = get_logger('dataagent.security')
