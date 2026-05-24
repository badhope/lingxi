#!/usr/bin/env python3
"""
扩展插件测试脚本
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.plugins_extended_complete import (
    ListToolsPlugin,
    TextGeneratorPlugin,
    DateTimeToolsPlugin,
)
from core.logging import get_logger

logger = get_logger("extended_plugin_test")


async def test_list_tools():
    """测试列表工具插件"""
    logger.info("=" * 60)
    logger.info("测试 1: 列表工具插件")
    logger.info("=" * 60)
    
    plugin = ListToolsPlugin()
    await plugin.initialize()
    
    tests = [
        ("unique", {"items": [1, 2, 2, 3, 3, 3, 4]}),
        ("shuffle", {"items": [1, 2, 3, 4, 5]}),
        ("chunk", {"items": [1, 2, 3, 4, 5, 6, 7], "size": 3}),
        ("flatten", {"nested_list": [[1, 2], [3, [4, 5]], 6]}),
        ("intersection", {"list1": [1, 2, 3, 4], "list2": [3, 4, 5, 6]}),
        ("difference", {"list1": [1, 2, 3, 4], "list2": [3, 4, 5, 6]}),
        ("group_by_length", {"items": ["cat", "dog", "elephant", "lion", "tiger"]}),
    ]
    
    passed = 0
    for tool_name, kwargs in tests:
        try:
            result = await plugin.execute_tool(tool_name, **kwargs)
            logger.info(f"✅ {tool_name} 执行成功: {result}")
            passed += 1
        except Exception as e:
            logger.error(f"❌ {tool_name} 执行失败: {e}")
    
    logger.info(f"\n列表工具测试: {passed}/{len(tests)} 通过")
    return passed == len(tests)


async def test_text_generator():
    """测试文本生成插件"""
    logger.info("\n" + "=" * 60)
    logger.info("测试 2: 文本生成插件")
    logger.info("=" * 60)
    
    plugin = TextGeneratorPlugin()
    await plugin.initialize()
    
    tests = [
        ("generate_lorem_ipsum", {"paragraphs": 2, "sentences_per_paragraph": 3}),
        ("generate_random_words", {"count": 5}),
        ("generate_random_sentences", {"count": 3}),
        ("generate_random_paragraph", {"sentences": 4}),
        ("generate_random_name", {"count": 3}),
    ]
    
    passed = 0
    for tool_name, kwargs in tests:
        try:
            result = await plugin.execute_tool(tool_name, **kwargs)
            logger.info(f"✅ {tool_name} 执行成功: {result}")
            passed += 1
        except Exception as e:
            logger.error(f"❌ {tool_name} 执行失败: {e}")
    
    logger.info(f"\n文本生成测试: {passed}/{len(tests)} 通过")
    return passed == len(tests)


async def test_datetime_tools():
    """测试日期时间工具插件"""
    logger.info("\n" + "=" * 60)
    logger.info("测试 3: 日期时间工具插件")
    logger.info("=" * 60)
    
    plugin = DateTimeToolsPlugin()
    await plugin.initialize()
    
    tests = [
        ("current_datetime", {}),
        ("format_date", {"date_str": "2024-01-15", "input_format": "%Y-%m-%d", "output_format": "%Y年%m月%d日"}),
        ("add_days", {"date_str": "2024-01-15", "days": 10}),
        ("days_between", {"start_date": "2024-01-01", "end_date": "2024-01-31"}),
        ("is_weekend", {"date_str": "2024-01-20"}),
        ("get_week_number", {"date_str": "2024-01-15"}),
        ("get_quarter", {}),
    ]
    
    passed = 0
    for tool_name, kwargs in tests:
        try:
            result = await plugin.execute_tool(tool_name, **kwargs)
            logger.info(f"✅ {tool_name} 执行成功: {result}")
            passed += 1
        except Exception as e:
            logger.error(f"❌ {tool_name} 执行失败: {e}")
    
    logger.info(f"\n日期时间工具测试: {passed}/{len(tests)} 通过")
    return passed == len(tests)


async def main():
    """运行所有测试"""
    logger.info("🚀 开始扩展插件测试")
    
    results = []
    
    try:
        results.append(("列表工具", await test_list_tools()))
        results.append(("文本生成", await test_text_generator()))
        results.append(("日期时间", await test_datetime_tools()))
    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}", exc_info=True)
    
    # 总结
    logger.info("\n" + "=" * 60)
    logger.info("测试总结")
    logger.info("=" * 60)
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        logger.info(f"{name}: {status}")
    
    logger.info(f"\n总计: {passed_count}/{total_count} 测试通过")
    
    return passed_count == total_count


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
