"""
DataAgent - Testing Framework
测试框架，提供单元测试和集成测试工具
"""
import asyncio
import time
from typing import Any, Dict, List, Optional, Callable

from .logging import get_logger

logger = get_logger('dataagent.testing')


class TestCase:
    """测试用例"""
    
    def __init__(self, name: str, func: Callable):
        self.name = name
        self.func = func
        self.passed = False
        self.error: Optional[str] = None
        self.duration: float = 0
    
    async def run(self) -> bool:
        """运行测试"""
        start_time = time.time()
        try:
            if asyncio.iscoroutinefunction(self.func):
                await self.func()
            else:
                self.func()
            self.passed = True
            self.error = None
        except Exception as e:
            self.passed = False
            self.error = str(e)
        finally:
            self.duration = time.time() - start_time
        return self.passed


class TestSuite:
    """测试套件"""
    
    def __init__(self, name: str):
        self.name = name
        self.tests: List[TestCase] = []
        self.results: Dict[str, bool] = {}
    
    def add_test(self, name: str, func: Callable):
        """添加测试"""
        test = TestCase(name, func)
        self.tests.append(test)
    
    async def run(self, verbose: bool = True) -> Dict[str, Any]:
        """运行所有测试"""
        start_time = time.time()
        passed = 0
        failed = 0
        
        for test in self.tests:
            if verbose:
                logger.info(f"Running: {test.name}")
            
            result = await test.run()
            self.results[test.name] = result
            
            if result:
                passed += 1
                if verbose:
                    logger.info(f"  ✓ Passed ({test.duration:.3f}s)")
            else:
                failed += 1
                if verbose:
                    logger.error(f"  ✗ Failed: {test.error}")
        
        total_time = time.time() - start_time
        
        summary = {
            "suite": self.name,
            "total": len(self.tests),
            "passed": passed,
            "failed": failed,
            "duration": total_time,
            "success_rate": (passed / len(self.tests) * 100) if self.tests else 0
        }
        
        return summary


class TestRunner:
    """测试运行器"""
    
    def __init__(self):
        self.suites: Dict[str, TestSuite] = {}
    
    def create_suite(self, name: str) -> TestSuite:
        """创建测试套件"""
        suite = TestSuite(name)
        self.suites[name] = suite
        return suite
    
    def get_suite(self, name: str) -> Optional[TestSuite]:
        """获取测试套件"""
        return self.suites.get(name)
    
    async def run_all(self, verbose: bool = True) -> List[Dict[str, Any]]:
        """运行所有测试套件"""
        results = []
        
        for name, suite in self.suites.items():
            logger.info(f"\n{'='*60}")
            logger.info(f"Running Test Suite: {name}")
            logger.info(f"{'='*60}")
            
            result = await suite.run(verbose)
            results.append(result)
        
        return results
    
    async def run_suite(self, name: str, verbose: bool = True) -> Optional[Dict[str, Any]]:
        """运行指定测试套件"""
        suite = self.get_suite(name)
        if not suite:
            logger.error(f"Test suite not found: {name}")
            return None
        
        return await suite.run(verbose)


# 全局测试运行器
test_runner = TestRunner()


# 辅助装饰器
def test(name: str, suite_name: str = "default"):
    """测试装饰器"""
    def decorator(func: Callable) -> Callable:
        suite = test_runner.create_suite(suite_name)
        suite.add_test(name, func)
        return func
    return decorator


# 内置测试示例
async def run_config_tests():
    """运行配置测试"""
    suite = test_runner.create_suite("Config")
    
    def test_config_loading():
        """测试配置加载"""
        from core.config import config_manager
        assert config_manager is not None
        assert config_manager.config is not None
    
    def test_path_config():
        """测试路径配置"""
        from core.config import config_manager
        assert config_manager.paths is not None
        assert config_manager.paths.base_dir is not None
    
    suite.add_test("Config Loading", test_config_loading)
    suite.add_test("Path Config", test_path_config)
    
    return await suite.run()


async def run_logging_tests():
    """运行日志测试"""
    suite = test_runner.create_suite("Logging")
    
    def test_logger_creation():
        """测试日志器创建"""
        from core.logging import get_logger
        logger = get_logger("test")
        assert logger is not None
    
    def test_log_levels():
        """测试日志级别"""
        from core.logging import get_logger
        logger = get_logger("test.levels")
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
    
    suite.add_test("Logger Creation", test_logger_creation)
    suite.add_test("Log Levels", test_log_levels)
    
    return await suite.run()


async def run_state_tests():
    """运行状态管理测试"""
    suite = test_runner.create_suite("State")
    
    def test_state_manager():
        """测试状态管理器"""
        from core.state import state_manager
        assert state_manager is not None
    
    def test_settings_manager():
        """测试设置管理器"""
        from core.state import settings_manager
        assert settings_manager is not None
    
    suite.add_test("State Manager", test_state_manager)
    suite.add_test("Settings Manager", test_settings_manager)
    
    return await suite.run()


async def run_knowledge_tests():
    """运行知识库测试"""
    suite = test_runner.create_suite("Knowledge")
    
    async def test_kb_creation():
        """测试知识库创建"""
        from core.knowledge import create_kb
        kb = await create_kb("test_kb", "Test Knowledge Base")
        assert kb is not None
        assert kb.name == "test_kb"
    
    async def test_document_add():
        """测试文档添加"""
        from core.knowledge import create_kb
        kb = await create_kb("test_kb_2", "Test")
        doc_id = await kb.add_document("Test content", "Test Doc")
        assert doc_id is not None
    
    suite.add_test("KB Creation", test_kb_creation)
    suite.add_test("Document Add", test_document_add)
    
    return await suite.run()


async def run_tools_tests():
    """运行工具测试"""
    suite = test_runner.create_suite("Tools")
    
    async def test_tool_registry():
        """测试工具注册"""
        from core.tools import tool_registry
        assert tool_registry is not None
    
    suite.add_test("Tool Registry", test_tool_registry)
    
    return await suite.run()


async def run_api_tests():
    """运行API测试"""
    suite = test_runner.create_suite("API")
    
    def test_error_handler():
        """测试错误处理器"""
        from core.api import ErrorHandler, APIError, ErrorCode
        error = APIError(ErrorCode.VALIDATION_ERROR, "Test error")
        response = ErrorHandler.handle_api_error(error)
        assert response is not None
        assert response["success"] is False
    
    def test_rate_limiter():
        """测试速率限制器"""
        from core.api import rate_limiter
        assert rate_limiter is not None
    
    suite.add_test("Error Handler", test_error_handler)
    suite.add_test("Rate Limiter", test_rate_limiter)
    
    return await suite.run()


async def run_all_tests(verbose: bool = True):
    """运行所有测试"""
    logger.info("Starting DataAgent Test Suite")
    logger.info("="*60)
    
    results = []
    
    results.append(await run_config_tests())
    results.append(await run_logging_tests())
    results.append(await run_state_tests())
    results.append(await run_knowledge_tests())
    results.append(await run_tools_tests())
    results.append(await run_api_tests())
    
    total_tests = sum(r["total"] for r in results)
    total_passed = sum(r["passed"] for r in results)
    total_failed = sum(r["failed"] for r in results)
    
    logger.info("="*60)
    logger.info("Test Summary")
    logger.info("="*60)
    logger.info(f"Total Tests: {total_tests}")
    logger.info(f"Passed: {total_passed}")
    logger.info(f"Failed: {total_failed}")
    logger.info(f"Success Rate: {(total_passed/total_tests*100) if total_tests else 0:.2f}%")
    
    return results
