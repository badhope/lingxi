#!/usr/bin/env python3
"""
插件系统测试脚本
"""
import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.plugins_builtin import (
    MathToolsPlugin,
    StringToolsPlugin,
    TimeToolsPlugin,
    FileToolsPlugin,
    BasicAnalyticsPlugin,
    SimpleVisualizationPlugin,
    SampleDataSourcePlugin,
    CryptoToolsPlugin,
    DataConverterPlugin,
    RegexToolsPlugin,
    ColorToolsPlugin,
    UnitConverterPlugin,
    AdvancedAnalyticsPlugin,
    register_builtin_plugins,
)
from core.logging import get_logger

logger = get_logger("plugin_test")


async def test_plugin_initialization():
    """测试插件初始化"""
    logger.info("=" * 60)
    logger.info("测试 1: 插件初始化")
    logger.info("=" * 60)
    
    plugins = [
        MathToolsPlugin(),
        StringToolsPlugin(),
        TimeToolsPlugin(),
        FileToolsPlugin(),
        BasicAnalyticsPlugin(),
        SimpleVisualizationPlugin(),
        SampleDataSourcePlugin(),
        CryptoToolsPlugin(),
        DataConverterPlugin(),
        RegexToolsPlugin(),
        ColorToolsPlugin(),
        UnitConverterPlugin(),
        AdvancedAnalyticsPlugin(),
    ]
    
    passed = 0
    for plugin in plugins:
        try:
            await plugin.initialize()
            logger.info(f"✅ {plugin.metadata.name} 初始化成功")
            logger.info(f"   ID: {plugin.metadata.id}")
            logger.info(f"   类型: {plugin.metadata.type}")
            logger.info(f"   版本: {plugin.metadata.version}")
            passed += 1
        except Exception as e:
            logger.error(f"❌ {plugin.metadata.name} 初始化失败: {e}")
    
    logger.info(f"\n初始化测试: {passed}/{len(plugins)} 通过")
    return passed == len(plugins)


async def test_math_tools():
    """测试数学工具插件"""
    logger.info("\n" + "=" * 60)
    logger.info("测试 2: 数学工具插件")
    logger.info("=" * 60)
    
    plugin = MathToolsPlugin()
    await plugin.initialize()
    
    tests = [
        ("calculate", {"expression": "2 + 3 * 4"}),
        ("sum", {"numbers": [1, 2, 3, 4, 5]}),
        ("average", {"numbers": [1, 2, 3, 4, 5]}),
        ("min", {"numbers": [5, 3, 9, 1]}),
        ("max", {"numbers": [5, 3, 9, 1]}),
        ("sqrt", {"x": 16}),
        ("random_range", {"min_val": 1, "max_val": 100}),
        ("statistics", {"numbers": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]}),
    ]
    
    passed = 0
    for tool_name, kwargs in tests:
        try:
            result = await plugin.execute_tool(tool_name, **kwargs)
            logger.info(f"✅ {tool_name} 执行成功: {result}")
            passed += 1
        except Exception as e:
            logger.error(f"❌ {tool_name} 执行失败: {e}")
    
    logger.info(f"\n数学工具测试: {passed}/{len(tests)} 通过")
    return passed == len(tests)


async def test_string_tools():
    """测试字符串工具插件"""
    logger.info("\n" + "=" * 60)
    logger.info("测试 3: 字符串工具插件")
    logger.info("=" * 60)
    
    plugin = StringToolsPlugin()
    await plugin.initialize()
    
    tests = [
        ("uppercase", {"text": "hello world"}),
        ("lowercase", {"text": "HELLO WORLD"}),
        ("capitalize", {"text": "hello world"}),
        ("trim", {"text": "  hello world  "}),
        ("length", {"text": "hello world"}),
        ("contains", {"text": "hello world", "substr": "world"}),
        ("extract_numbers", {"text": "abc123def456ghi789"}),
    ]
    
    passed = 0
    for tool_name, kwargs in tests:
        try:
            result = await plugin.execute_tool(tool_name, **kwargs)
            logger.info(f"✅ {tool_name} 执行成功: {result}")
            passed += 1
        except Exception as e:
            logger.error(f"❌ {tool_name} 执行失败: {e}")
    
    logger.info(f"\n字符串工具测试: {passed}/{len(tests)} 通过")
    return passed == len(tests)


async def test_crypto_tools():
    """测试加密解密工具插件"""
    logger.info("\n" + "=" * 60)
    logger.info("测试 4: 加密解密工具插件")
    logger.info("=" * 60)
    
    plugin = CryptoToolsPlugin()
    await plugin.initialize()
    
    tests = [
        ("md5", {"text": "hello world"}),
        ("sha256", {"text": "hello world"}),
        ("sha1", {"text": "hello world"}),
        ("base64_encode", {"text": "hello world"}),
        ("url_encode", {"text": "hello world!@#$%"}),
        ("generate_uuid", {}),
        ("generate_password", {"length": 16}),
    ]
    
    passed = 0
    for tool_name, kwargs in tests:
        try:
            result = await plugin.execute_tool(tool_name, **kwargs)
            logger.info(f"✅ {tool_name} 执行成功: {result}")
            passed += 1
        except Exception as e:
            logger.error(f"❌ {tool_name} 执行失败: {e}")
    
    # 测试 Base64 解码
    try:
        encoded = await plugin.execute_tool("base64_encode", text="test message")
        if encoded.get("success"):
            decoded = await plugin.execute_tool("base64_decode", encoded=encoded["result"])
            logger.info(f"✅ base64_decode 执行成功: {decoded}")
            passed += 1
    except Exception as e:
        logger.error(f"❌ base64_decode 执行失败: {e}")
    
    logger.info(f"\n加密工具测试: {passed}/{len(tests) + 1} 通过")
    return passed >= len(tests)


async def test_data_converter():
    """测试数据转换工具插件"""
    logger.info("\n" + "=" * 60)
    logger.info("测试 5: 数据转换工具插件")
    logger.info("=" * 60)
    
    plugin = DataConverterPlugin()
    await plugin.initialize()
    
    tests = [
        ("json_pretty", {"json_str": '{"name":"test","value":123}'}),
        ("json_minify", {"json_str": '{  "name":  "test"  }'}),
        ("json_validate", {"json_str": '{"valid":true}'}),
        ("text_to_base64", {"text": "test data"}),
    ]
    
    passed = 0
    for tool_name, kwargs in tests:
        try:
            result = await plugin.execute_tool(tool_name, **kwargs)
            logger.info(f"✅ {tool_name} 执行成功: {result}")
            passed += 1
        except Exception as e:
            logger.error(f"❌ {tool_name} 执行失败: {e}")
    
    logger.info(f"\n数据转换测试: {passed}/{len(tests)} 通过")
    return passed == len(tests)


async def test_basic_analytics():
    """测试基础分析插件"""
    logger.info("\n" + "=" * 60)
    logger.info("测试 6: 基础分析插件")
    logger.info("=" * 60)
    
    plugin = BasicAnalyticsPlugin()
    await plugin.initialize()
    
    tests = [
        ("basic_stats", [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], {}),
        ("frequency", ["a", "b", "a", "c", "b", "a"], {}),
        ("percentile", [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], {"percentile": 50}),
    ]
    
    passed = 0
    for analysis_name, data, params in tests:
        try:
            kwargs = params.copy()
            result = await plugin.run_analysis(analysis_name, data, **kwargs)
            logger.info(f"✅ {analysis_name} 执行成功: {result}")
            passed += 1
        except Exception as e:
            logger.error(f"❌ {analysis_name} 执行失败: {e}")
    
    logger.info(f"\n基础分析测试: {passed}/{len(tests)} 通过")
    return passed >= len(tests)


async def test_advanced_analytics():
    """测试高级分析插件"""
    logger.info("\n" + "=" * 60)
    logger.info("测试 7: 高级分析插件")
    logger.info("=" * 60)
    
    plugin = AdvancedAnalyticsPlugin()
    await plugin.initialize()
    
    tests = [
        ("moving_average", [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], {"window": 3}),
        ("normalization", [1, 2, 3, 4, 5], {}),
        ("standardization", [1, 2, 3, 4, 5], {}),
        ("histogram_bins", [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], {"bins": 5}),
        ("time_series_forecast", [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], {"periods": 3}),
    ]
    
    passed = 0
    for analysis_name, data, params in tests:
        try:
            kwargs = params.copy()
            result = await plugin.run_analysis(analysis_name, data, **kwargs)
            logger.info(f"✅ {analysis_name} 执行成功: {result}")
            passed += 1
        except Exception as e:
            logger.error(f"❌ {analysis_name} 执行失败: {e}")
    
    logger.info(f"\n高级分析测试: {passed}/{len(tests)} 通过")
    return passed >= len(tests)


async def test_sample_data_source():
    """测试数据源插件"""
    logger.info("\n" + "=" * 60)
    logger.info("测试 8: 数据源插件")
    logger.info("=" * 60)
    
    plugin = SampleDataSourcePlugin()
    await plugin.initialize()
    
    tests = [
        ("sales_data", {"count": 5}),
        ("weather_data", {"days": 7}),
        ("user_data", {"count": 10}),
        ("product_data", {"count": 5}),
        ("random_data", {"count": 10, "min_val": 0, "max_val": 100}),
    ]
    
    passed = 0
    for source_name, params in tests:
        try:
            result = await plugin.fetch_data(source_name, **params)
            logger.info(f"✅ {source_name} 获取成功: {len(result.get('data', []))} 条数据")
            passed += 1
        except Exception as e:
            logger.error(f"❌ {source_name} 获取失败: {e}")
    
    logger.info(f"\n数据源测试: {passed}/{len(tests)} 通过")
    return passed == len(tests)


async def test_unit_converter():
    """测试单位转换工具插件"""
    logger.info("\n" + "=" * 60)
    logger.info("测试 9: 单位转换工具插件")
    logger.info("=" * 60)
    
    plugin = UnitConverterPlugin()
    await plugin.initialize()
    
    tests = [
        ("convert_length", {"value": 100, "from_unit": "cm", "to_unit": "m"}),
        ("convert_weight", {"value": 1, "from_unit": "kg", "to_unit": "g"}),
        ("convert_temperature", {"value": 0, "from_unit": "c", "to_unit": "f"}),
        ("convert_area", {"value": 1, "from_unit": "sq_m", "to_unit": "sq_cm"}),
        ("convert_speed", {"value": 100, "from_unit": "kmph", "to_unit": "mps"}),
    ]
    
    passed = 0
    for tool_name, kwargs in tests:
        try:
            result = await plugin.execute_tool(tool_name, **kwargs)
            logger.info(f"✅ {tool_name} 执行成功: {result}")
            passed += 1
        except Exception as e:
            logger.error(f"❌ {tool_name} 执行失败: {e}")
    
    logger.info(f"\n单位转换测试: {passed}/{len(tests)} 通过")
    return passed == len(tests)


async def test_color_tools():
    """测试颜色工具插件"""
    logger.info("\n" + "=" * 60)
    logger.info("测试 10: 颜色工具插件")
    logger.info("=" * 60)
    
    plugin = ColorToolsPlugin()
    await plugin.initialize()
    
    tests = [
        ("hex_to_rgb", {"hex_color": "#FF5733"}),
        ("rgb_to_hex", {"r": 255, "g": 87, "b": 51}),
        ("rgb_to_hsl", {"r": 255, "g": 87, "b": 51}),
        ("random_color", {}),
        ("generate_palette", {"base_hex": "#FF5733", "count": 5}),
    ]
    
    passed = 0
    for tool_name, kwargs in tests:
        try:
            result = await plugin.execute_tool(tool_name, **kwargs)
            logger.info(f"✅ {tool_name} 执行成功: {result}")
            passed += 1
        except Exception as e:
            logger.error(f"❌ {tool_name} 执行失败: {e}")
    
    logger.info(f"\n颜色工具测试: {passed}/{len(tests)} 通过")
    return passed == len(tests)


async def main():
    """运行所有测试"""
    logger.info("🚀 开始插件系统测试")
    logger.info("项目目录: %s", project_root)
    
    results = []
    
    try:
        results.append(("插件初始化", await test_plugin_initialization()))
        results.append(("数学工具", await test_math_tools()))
        results.append(("字符串工具", await test_string_tools()))
        results.append(("加密工具", await test_crypto_tools()))
        results.append(("数据转换", await test_data_converter()))
        results.append(("基础分析", await test_basic_analytics()))
        results.append(("高级分析", await test_advanced_analytics()))
        results.append(("数据源", await test_sample_data_source()))
        results.append(("单位转换", await test_unit_converter()))
        results.append(("颜色工具", await test_color_tools()))
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
