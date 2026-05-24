"""
DataAgent Core Integration Tests
核心模块集成测试
"""
import asyncio
import sys
import os
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "dataagent"))

from core import (
    config_manager,
    get_logger,
    core_logger,
    api_logger,
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

from core.tools import BaseTool, ToolResult
from core.knowledge import Document, KnowledgeBase

# 初始化测试日志
test_logger = get_logger("test_core_integration")


class SimpleTool(BaseTool):
    """简单的测试工具"""
    name: str = "simple_tool"
    description: str = "简单测试工具"

    async def execute(self, input: str = "") -> ToolResult:
        test_logger.info(f"Simple tool executed with input: {input}")
        return ToolResult.success(f"Processed: {input}")


async def test_config_manager():
    """测试配置管理器"""
    test_logger.info("=" * 60)
    test_logger.info("Testing Config Manager")
    test_logger.info("=" * 60)
    
    try:
        assert config_manager is not None
        assert config_manager.config is not None
        assert config_manager.config.llm is not None
        assert config_manager.config.paths is not None
        
        test_logger.info("✓ Config Manager initialization successful")
        
        test_logger.info(f"  LLM provider: {config_manager.config.llm.get('default', {}).get('provider', 'unknown')}")
        test_logger.info(f"  LLM model: {config_manager.config.llm.get('default', {}).get('model', 'unknown')}")
        
        return True
    except Exception as e:
        test_logger.error(f"✗ Config manager test failed: {e}")
        return False


async def test_state_managers():
    """测试状态管理器"""
    test_logger.info("=" * 60)
    test_logger.info("Testing State Managers")
    test_logger.info("=" * 60)
    
    try:
        # 测试设置管理器
        assert settings_manager is not None
        assert settings_manager.settings is not None
        test_logger.info("✓ Settings manager initialized")
        
        # 测试会话管理器
        assert conversation_manager is not None
        test_logger.info("✓ Conversation manager initialized")
        
        # 测试技能管理器
        assert skill_manager is not None
        assert skill_manager.skills is not None
        test_logger.info("✓ Skills manager initialized")
        
        return True
    except Exception as e:
        test_logger.error(f"✗ State managers test failed: {e}")
        return False


async def test_knowledge_base():
    """测试知识库"""
    test_logger.info("=" * 60)
    test_logger.info("Testing Knowledge Base")
    test_logger.info("=" * 60)
    
    try:
        # 创建知识库
        kb = await create_kb("test_kb", "测试知识库")
        assert kb is not None
        test_logger.info("✓ Created knowledge base: test_kb")
        
        # 添加文档
        doc_id = await kb.add_document(
            content="这是一个测试文档。DataAgent 是一个强大的 AI 助手。",
            title="测试文档"
        )
        assert doc_id is not None
        test_logger.info("✓ Added document to knowledge base")
        
        # 搜索
        search_results = await kb.search("测试文档")
        assert search_results is not None
        test_logger.info(f"✓ Search returned {len(search_results)} results")
        
        # 列出所有知识库
        all_kbs = await list_kbs()
        assert len(all_kbs) >= 1
        test_logger.info(f"✓ Listed knowledge bases: {len(all_kbs)}")
        
        # 清理
        await kb.delete_document(doc_id)
        
        return True
    except Exception as e:
        test_logger.error(f"✗ Knowledge base test failed: {e}")
        return False


async def test_api_responses():
    """测试 API 响应"""
    test_logger.info("=" * 60)
    test_logger.info("Testing API Responses")
    test_logger.info("=" * 60)
    
    try:
        # 测试成功响应
        ok_response = APIResponse.ok(data={"key": "value"}, message="Test success")
        assert ok_response.success is True
        assert ok_response.message == "Test success"
        test_logger.info("✓ OK response created successfully")
        
        # 测试错误响应
        error_response = APIResponse.error(message="Test error")
        assert error_response.success is False
        test_logger.info("✓ Error response created successfully")
        
        # 测试 API 异常
        api_error = APIError(ErrorCode.VALIDATION_ERROR, "Validation failed")
        assert api_error.code == ErrorCode.VALIDATION_ERROR
        assert api_error.message == "Validation failed"
        test_logger.info("✓ API error created successfully")
        
        return True
    except Exception as e:
        test_logger.error(f"✗ API responses test failed: {e}")
        return False


async def test_performance_monitoring():
    """测试性能监控"""
    test_logger.info("=" * 60)
    test_logger.info("Testing Performance Monitoring")
    test_logger.info("=" * 60)
    
    try:
        assert performance_monitor is not None
        test_logger.info("✓ Performance monitor initialized")
        
        # 记录请求
        start_time = datetime.now()
        performance_monitor.record_request(
            endpoint="/test",
            duration=0.05,
            success=True
        )
        test_logger.info("✓ Request recorded")
        
        # 获取指标
        metrics = performance_monitor.get_metrics()
        assert metrics is not None
        assert "total_requests" in metrics
        test_logger.info(f"✓ Performance metrics: {metrics['total_requests']} requests")
        
        # 获取系统指标
        system_metrics = performance_monitor.get_system_metrics()
        assert system_metrics is not None
        test_logger.info("✓ System metrics obtained")
        
        return True
    except Exception as e:
        test_logger.error(f"✗ Performance monitoring test failed: {e}")
        return False


async def test_cache_manager():
    """测试缓存管理"""
    test_logger.info("=" * 60)
    test_logger.info("Testing Cache Management")
    test_logger.info("=" * 60)
    
    try:
        assert cache_manager is not None
        test_logger.info("✓ Cache manager initialized")
        
        # 设置缓存
        cache_manager.set("test_key", "test_value")
        assert cache_manager.get("test_key") == "test_value"
        test_logger.info("✓ Cache set and retrieved successfully")
        
        # 获取统计
        stats = cache_manager.get_stats()
        assert stats is not None
        test_logger.info(f"✓ Cache stats: {stats['size']} items")
        
        # 清空缓存
        cache_manager.clear()
        assert cache_manager.get("test_key") is None
        test_logger.info("✓ Cache cleared successfully")
        
        return True
    except Exception as e:
        test_logger.error(f"✗ Cache manager test failed: {e}")
        return False


async def test_extensions():
    """测试扩展系统"""
    test_logger.info("=" * 60)
    test_logger.info("Testing Extensions")
    test_logger.info("=" * 60)
    
    try:
        assert extension_manager is not None
        test_logger.info("✓ Extension manager initialized")
        
        # 列出扩展
        extensions = extension_manager.list_extensions()
        assert extensions is not None
        test_logger.info(f"✓ {len(extensions)} extensions found")
        
        # 检查核心扩展
        extension_names = [ext["name"] for ext in extensions]
        assert "MCP Client" in extension_names
        assert "MultiModal Processor" in extension_names
        assert "Workflow Engine" in extension_names
        test_logger.info("✓ All core extensions registered")
        
        return True
    except Exception as e:
        test_logger.error(f"✗ Extensions test failed: {e}")
        return False


async def test_tools():
    """测试工具系统"""
    test_logger.info("=" * 60)
    test_logger.info("Testing Tools System")
    test_logger.info("=" * 60)
    
    try:
        # 创建工具
        simple_tool = SimpleTool()
        test_logger.info("✓ Created test tool")
        
        # 注册工具
        await register_tool(simple_tool)
        
        # 获取工具列表
        tools = await get_all_tools()
        test_logger.info(f"✓ {len(tools)} tools registered")
        
        # 执行工具
        result = await call_tool("simple_tool")
        test_logger.info(f"✓ Tool executed with result: {result}")
        
        return True
    except Exception as e:
        test_logger.error(f"✗ Tools test failed: {e}")
        return False


async def run_all_tests():
    """运行所有集成测试"""
    test_logger.info("=" * 60)
    test_logger.info("DATA AGENT CORE INTEGRATION TESTS")
    test_logger.info("=" * 60)
    
    tests = [
        test_config_manager,
        test_state_managers,
        test_knowledge_base,
        test_api_responses,
        test_performance_monitoring,
        test_cache_manager,
        test_extensions,
        test_tools
    ]
    
    results = []
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test_name = test.__name__
            test_logger.info(f"\nRunning {test_name}")
            test_logger.info("-" * 40)
            
            if asyncio.iscoroutinefunction(test):
                result = await test()
            else:
                result = test()
            
            results.append((test_name, result))
            
            if result:
                passed += 1
            else:
                failed += 1
        except Exception as e:
            test_logger.error(f"Test {test.__name__} error: {e}")
            results.append((test.__name__, False))
            failed += 1
    
    test_logger.info("=" * 60)
    test_logger.info(f"TEST RESULTS")
    test_logger.info("=" * 60)
    test_logger.info(f"Total: {len(results)}")
    test_logger.info(f"Passed: {passed}")
    test_logger.info(f"Failed: {failed}")
    test_logger.info("=" * 60)
    
    for test_name, result in results:
        status = "✓" if result else "✗"
        test_logger.info(f"{status} {test_name}")
    
    test_logger.info("=" * 60)
    
    return passed == len(tests)


if __name__ == "__main__":
    print("=" * 60)
    print("DataAgent Core Integration Tests")
    print("=" * 60)
    print("Starting test suite...")
    print()
    
    success = asyncio.run(run_all_tests())
    
    print()
    print("=" * 60)
    if success:
        print("All tests passed!")
    else:
        print("Some tests failed!")
    print("=" * 60)
