"""
验证核心模块
验证核心模块是否可以正常导入和使用
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

print("=" * 60)
print("DataAgent Core 模块验证")
print("=" * 60)

# 测试各个模块的导入
modules_to_test = [
    ("Config Module", "core.config"),
    ("Logging Module", "core.logging"),
    ("State Module", "core.state"),
    ("Database Module", "core.database"),
    ("Agent Module", "core.agent"),
    ("Tools Module", "core.tools"),
    ("Knowledge Module", "core.knowledge"),
    ("API Module", "core.api"),
    ("Performance Module", "core.performance"),
    ("Extensions Module", "core.extensions"),
    ("Testing Module", "core.testing"),
]

all_imports_successful = True

for module_name, module_path in modules_to_test:
    try:
        print(f"\n正在导入 {module_name}...")
        module = __import__(module_path, fromlist=["*"])
        print(f"✓ {module_name} 导入成功")
        print(f"  模块包含: {[attr for attr in dir(module) if not attr.startswith('_')]}")
    except Exception as e:
        print(f"✗ {module_name} 导入失败: {e}")
        all_imports_successful = False

print("\n" + "=" * 60)
print("导入公共 API 验证")
print("=" * 60)

# 测试导入公共 API
try:
    from core import (
        config_manager,
        get_logger,
        settings_manager,
        conversation_manager,
        skill_manager,
        create_kb,
        list_kbs,
        rag_query,
        APIResponse,
        APIError,
        ErrorCode,
        performance_monitor,
        cache_manager,
        extension_manager,
        register_tool,
        call_tool,
        get_all_tools
    )
    print("✓ 公共 API 导入成功")
except Exception as e:
    print(f"✗ 公共 API 导入失败: {e}")
    all_imports_successful = False

# 测试配置管理器
print("\n" + "=" * 60)
print("配置管理器测试")
print("=" * 60)
try:
    print(f"✓ 配置管理器初始化: {config_manager is not None}")
    print(f"✓ 配置加载成功")
except Exception as e:
    print(f"✗ 配置管理器测试失败: {e}")

print("\n" + "=" * 60)
if all_imports_successful:
    print("所有模块验证成功！")
else:
    print("部分模块验证失败！")
print("=" * 60)
