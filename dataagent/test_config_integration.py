"""
测试核心配置系统整合
"""
import sys
from pathlib import Path

# 添加项目根目录
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("=" * 60)
print("测试核心配置系统整合")
print("=" * 60)

try:
    from core import config_manager, get_logger
    print("✓ 成功导入核心模块")
    
    # 测试配置加载
    print(f"\n配置路径: {config_manager.paths.base_dir}")
    print(f"✓ 配置加载成功")
    
    # 测试 LLM 配置
    default_llm = config_manager.llm.get('default', {})
    print(f"\n默认 LLM 配置:")
    if hasattr(default_llm, 'provider'):
        print(f"  Provider: {default_llm.provider}")
    if hasattr(default_llm, 'model'):
        print(f"  Model: {default_llm.model}")
    print("✓ LLM 配置访问正常")
    
    # 测试安全配置
    print(f"\n安全配置:")
    print(f"  CORS Origins: {config_manager.security.cors_origins}")
    print(f"  Rate Limit: {config_manager.security.rate_limit_max_requests}/{config_manager.security.rate_limit_window}s")
    print("✓ 安全配置访问正常")
    
    # 测试日志系统
    logger = get_logger('test')
    logger.info("测试日志记录")
    print("✓ 日志系统正常")
    
    print("\n" + "=" * 60)
    print("所有测试通过！✓")
    print("=" * 60)
    
except Exception as e:
    print(f"\n✗ 测试失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
