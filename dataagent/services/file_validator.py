"""
File Upload Validation Service
用于验证和清理上传的文件
"""
import os
from typing import Tuple, Optional


class FileValidator:
    """文件验证器"""
    
    def __init__(self):
        # 从环境变量获取配置
        self.max_file_size_mb = int(os.getenv('MAX_FILE_SIZE_MB', 10))
        self.max_file_size_bytes = self.max_file_size_mb * 1024 * 1024
        
        allowed_extensions = os.getenv('ALLOWED_FILE_EXTENSIONS', 
                                        '.txt,.pdf,.doc,.docx,.ppt,.pptx,.csv,.json,.md')
        self.allowed_extensions = {ext.strip().lower() for ext in allowed_extensions.split(',')}
    
    def validate_file(self, filename: str, file_size: int) -> Tuple[bool, Optional[str]]:
        """
        验证文件是否符合要求
        
        Returns:
            (is_valid, error_message)
        """
        # 检查文件大小
        if file_size > self.max_file_size_bytes:
            return False, f"文件大小超过限制 (最大 {self.max_file_size_mb} MB)"
        
        # 检查文件扩展名
        file_ext = os.path.splitext(filename)[1].lower()
        if file_ext not in self.allowed_extensions:
            return False, f"不支持的文件类型。支持的类型: {', '.join(self.allowed_extensions)}"
        
        # 检查文件名安全
        if '..' in filename or filename.startswith('/'):
            return False, "文件名包含不安全字符"
        
        return True, None
    
    def sanitize_filename(self, filename: str) -> str:
        """清理文件名，移除不安全字符"""
        import re
        # 只保留安全的字符
        safe_filename = re.sub(r'[^\w\s\-_.]', '', filename)
        # 移除开头的 . 和 ..
        safe_filename = re.sub(r'^\.*', '', safe_filename)
        # 如果文件名空了，生成一个
        if not safe_filename:
            from datetime import datetime
            safe_filename = f"file_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        return safe_filename


# 全局文件验证器实例
file_validator = FileValidator()
