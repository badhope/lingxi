"""
DataAgent - 内置插件集合
提供丰富的常用功能插件
"""
import asyncio
import base64
import hashlib
import json
import math
import random
import re
import statistics
import time
import urllib.parse
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from core.logging import get_logger
from core.plugins import (
    AgentPlugin,
    AnalyticsPlugin,
    DataSourcePlugin,
    DocumentPlugin,
    IntegrationPlugin,
    PluginMetadata,
    PluginType,
    ToolPlugin,
    VisualizationPlugin,
    plugin_manager,
    plugins_logger,
)


# 内置插件管理器


class MathToolsPlugin(ToolPlugin):
    """数学工具插件"""
    
    def __init__(self):
        super().__init__()
        self.metadata = PluginMetadata(
            id="math_tools",
            name="Math Tools",
            description="数学计算和工具函数",
            version="1.0.0",
            author="DataAgent",
            type=PluginType.TOOL,
            tags=["math", "calculator", "tools"],
        )
        # 安全的数学计算环境
        self._safe_math_env = {
            'abs': abs,
            'round': round,
            'min': min,
            'max': max,
            'sum': sum,
            'pow': pow,
            'sqrt': math.sqrt,
            'exp': math.exp,
            'log': math.log,
            'log10': math.log10,
            'sin': math.sin,
            'cos': math.cos,
            'tan': math.tan,
            'asin': math.asin,
            'acos': math.acos,
            'atan': math.atan,
            'pi': math.pi,
            'e': math.e,
        }
    
    async def initialize(self):
        """初始化插件"""
        # 注册数学工具函数
        self.register_tool("calculate", self._calculate)
        self.register_tool("sum", self._sum)
        self.register_tool("average", self._average)
        self.register_tool("min", self._min)
        self.register_tool("max", self._max)
        self.register_tool("sqrt", self._sqrt)
        self.register_tool("round", self._round)
        self.register_tool("random", self._random)
        self.register_tool("random_range", self._random_range)
        self.register_tool("statistics", self._statistics)
        plugins_logger.info("Math Tools plugin initialized")
    
    async def execute(self, *args, **kwargs) -> Any:
        """执行插件"""
        tool_name = kwargs.get("tool")
        if tool_name:
            return await self.execute_tool(tool_name, *args, **kwargs)
        return {"tools": self.list_tools()}
    
    def _calculate(self, expression: str) -> Dict[str, Any]:
        """计算数学表达式（安全版本）"""
        try:
            # 验证表达式只包含安全字符
            import re
            if not re.match(r'^[\d\s+\-*/().,%^a-zA-Z]*$', expression):
                return {"success": False, "error": "Invalid characters in expression"}
            
            # 使用受限的 eval 环境
            result = eval(expression, {"__builtins__": None}, self._safe_math_env)
            return {"success": True, "expression": expression, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _sum(self, numbers: List[float]) -> Dict[str, Any]:
        """求和"""
        return {"success": True, "result": sum(numbers)}
    
    def _average(self, numbers: List[float]) -> Dict[str, Any]:
        """平均值"""
        return {"success": True, "result": sum(numbers) / len(numbers) if numbers else 0}
    
    def _min(self, numbers: List[float]) -> Dict[str, Any]:
        """最小值"""
        return {"success": True, "result": min(numbers) if numbers else None}
    
    def _max(self, numbers: List[float]) -> Dict[str, Any]:
        """最大值"""
        return {"success": True, "result": max(numbers) if numbers else None}
    
    def _sqrt(self, x: float) -> Dict[str, Any]:
        """平方根"""
        return {"success": True, "result": math.sqrt(x) if x >= 0 else None}
    
    def _round(self, x: float, decimals: int = 2) -> Dict[str, Any]:
        """四舍五入"""
        return {"success": True, "result": round(x, decimals)}
    
    def _random(self) -> Dict[str, Any]:
        """随机数"""
        return {"success": True, "result": random.random()}
    
    def _random_range(self, min_val: float, max_val: float) -> Dict[str, Any]:
        """范围内随机数"""
        return {"success": True, "result": random.uniform(min_val, max_val)}
    
    def _statistics(self, numbers: List[float]) -> Dict[str, Any]:
        """统计信息"""
        if not numbers:
            return {"success": False, "error": "No data"}
        
        return {
            "success": True,
            "sum": sum(numbers),
            "average": sum(numbers) / len(numbers),
            "min": min(numbers),
            "max": max(numbers),
            "median": statistics.median(numbers) if len(numbers) > 1 else numbers[0],
            "stdev": statistics.stdev(numbers) if len(numbers) > 2 else None,
            "count": len(numbers),
        }


class StringToolsPlugin(ToolPlugin):
    """字符串工具插件"""
    
    def __init__(self):
        super().__init__()
        self.metadata = PluginMetadata(
            id="string_tools",
            name="String Tools",
            description="字符串处理工具",
            version="1.0.0",
            author="DataAgent",
            type=PluginType.TOOL,
            tags=["string", "text", "tools"],
        )
    
    async def initialize(self):
        """初始化插件"""
        self.register_tool("uppercase", self._uppercase)
        self.register_tool("lowercase", self._lowercase)
        self.register_tool("capitalize", self._capitalize)
        self.register_tool("trim", self._trim)
        self.register_tool("replace", self._replace)
        self.register_tool("split", self._split)
        self.register_tool("join", self._join)
        self.register_tool("length", self._length)
        self.register_tool("contains", self._contains)
        self.register_tool("extract_numbers", self._extract_numbers)
        plugins_logger.info("String Tools plugin initialized")
    
    async def execute(self, *args, **kwargs) -> Any:
        tool_name = kwargs.get("tool")
        if tool_name:
            return await self.execute_tool(tool_name, *args, **kwargs)
        return {"tools": self.list_tools()}
    
    def _uppercase(self, text: str) -> Dict[str, Any]:
        """转大写"""
        return {"success": True, "result": text.upper()}
    
    def _lowercase(self, text: str) -> Dict[str, Any]:
        """转小写"""
        return {"success": True, "result": text.lower()}
    
    def _capitalize(self, text: str) -> Dict[str, Any]:
        """首字母大写"""
        return {"success": True, "result": text.capitalize()}
    
    def _trim(self, text: str) -> Dict[str, Any]:
        """去除空格"""
        return {"success": True, "result": text.strip()}
    
    def _replace(self, text: str, old: str, new: str) -> Dict[str, Any]:
        """替换"""
        return {"success": True, "result": text.replace(old, new)}
    
    def _split(self, text: str, sep: str = " ") -> Dict[str, Any]:
        """分割"""
        return {"success": True, "result": text.split(sep)}
    
    def _join(self, parts: List[str], sep: str = " ") -> Dict[str, Any]:
        """连接"""
        return {"success": True, "result": sep.join(parts)}
    
    def _length(self, text: str) -> Dict[str, Any]:
        """长度"""
        return {"success": True, "result": len(text)}
    
    def _contains(self, text: str, substr: str) -> Dict[str, Any]:
        """包含"""
        return {"success": True, "result": substr in text}
    
    def _extract_numbers(self, text: str) -> Dict[str, Any]:
        """提取数字"""
        numbers = re.findall(r'\d+\.?\d*', text)
        return {"success": True, "result": [float(num) if '.' in num else int(num) for num in numbers]}


class TimeToolsPlugin(ToolPlugin):
    """时间工具插件"""
    
    def __init__(self):
        super().__init__()
        self.metadata = PluginMetadata(
            id="time_tools",
            name="Time Tools",
            description="时间和日期工具",
            version="1.0.0",
            author="DataAgent",
            type=PluginType.TOOL,
            tags=["time", "date", "tools"],
        )
    
    async def initialize(self):
        """初始化插件"""
        self.register_tool("now", self._now)
        self.register_tool("today", self._today)
        self.register_tool("format", self._format)
        self.register_tool("timestamp", self._timestamp)
        self.register_tool("timestamp_to_date", self._timestamp_to_date)
        self.register_tool("diff", self._diff)
        self.register_tool("add_days", self._add_days)
        self.register_tool("add_hours", self._add_hours)
        self.register_tool("format_relative", self._format_relative)
        plugins_logger.info("Time Tools plugin initialized")
    
    async def execute(self, *args, **kwargs) -> Any:
        tool_name = kwargs.get("tool")
        if tool_name:
            return await self.execute_tool(tool_name, *args, **kwargs)
        return {"tools": self.list_tools()}
    
    def _now(self) -> Dict[str, Any]:
        """当前时间"""
        return {"success": True, "result": datetime.now().isoformat()}
    
    def _today(self) -> Dict[str, Any]:
        """今天日期"""
        return {"success": True, "result": datetime.now().strftime("%Y-%m-%d")}
    
    def _format(self, dt_str: str, fmt: str = "%Y-%m-%d %H:%M:%S") -> Dict[str, Any]:
        """格式化时间"""
        try:
            dt = datetime.fromisoformat(dt_str)
            return {"success": True, "result": dt.strftime(fmt)}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _timestamp(self) -> Dict[str, Any]:
        """时间戳"""
        return {"success": True, "result": time.time()}
    
    def _timestamp_to_date(self, ts: float) -> Dict[str, Any]:
        """时间戳转日期"""
        return {"success": True, "result": datetime.fromtimestamp(ts).isoformat()}
    
    def _diff(self, dt1: str, dt2: str) -> Dict[str, Any]:
        """时间差"""
        try:
            d1 = datetime.fromisoformat(dt1)
            d2 = datetime.fromisoformat(dt2)
            diff = abs((d2 - d1).total_seconds())
            return {
                "success": True,
                "seconds": diff,
                "days": diff / 86400,
                "hours": diff / 3600,
                "minutes": diff / 60,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _add_days(self, dt_str: str, days: int) -> Dict[str, Any]:
        """加天数"""
        try:
            dt = datetime.fromisoformat(dt_str)
            from datetime import timedelta
            result = dt + timedelta(days=days)
            return {"success": True, "result": result.isoformat()}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _add_hours(self, dt_str: str, hours: int) -> Dict[str, Any]:
        """加小时"""
        try:
            dt = datetime.fromisoformat(dt_str)
            from datetime import timedelta
            result = dt + timedelta(hours=hours)
            return {"success": True, "result": result.isoformat()}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _format_relative(self, dt_str: str) -> Dict[str, Any]:
        """相对时间"""
        try:
            dt = datetime.fromisoformat(dt_str)
            now = datetime.now()
            diff = (now - dt).total_seconds()
            
            if diff < 60:
                result = "刚刚"
            elif diff < 3600:
                result = f"{int(diff/60)}分钟前"
            elif diff < 86400:
                result = f"{int(diff/3600)}小时前"
            else:
                result = f"{int(diff/86400)}天前"
            
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}


class FileToolsPlugin(ToolPlugin):
    """文件工具插件"""
    
    def __init__(self):
        super().__init__()
        self.metadata = PluginMetadata(
            id="file_tools",
            name="File Tools",
            description="文件操作工具",
            version="1.0.0",
            author="DataAgent",
            type=PluginType.TOOL,
            tags=["file", "io", "tools"],
        )
    
    async def initialize(self):
        """初始化插件"""
        self.register_tool("read_file", self._read_file)
        self.register_tool("write_file", self._write_file)
        self.register_tool("append_file", self._append_file)
        self.register_tool("file_exists", self._file_exists)
        self.register_tool("list_dir", self._list_dir)
        self.register_tool("delete_file", self._delete_file)
        self.register_tool("get_file_info", self._get_file_info)
        self.register_tool("get_file_extension", self._get_file_extension)
        plugins_logger.info("File Tools plugin initialized")
    
    async def execute(self, *args, **kwargs) -> Any:
        tool_name = kwargs.get("tool")
        if tool_name:
            return await self.execute_tool(tool_name, *args, **kwargs)
        return {"tools": self.list_tools()}
    
    def _read_file(self, file_path: str, encoding: str = "utf-8") -> Dict[str, Any]:
        """读取文件"""
        try:
            with open(file_path, "r", encoding=encoding) as f:
                content = f.read()
            return {"success": True, "content": content}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _write_file(self, file_path: str, content: str, encoding: str = "utf-8") -> Dict[str, Any]:
        """写入文件"""
        try:
            with open(file_path, "w", encoding=encoding) as f:
                f.write(content)
            return {"success": True, "path": file_path}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _append_file(self, file_path: str, content: str, encoding: str = "utf-8") -> Dict[str, Any]:
        """追加文件"""
        try:
            with open(file_path, "a", encoding=encoding) as f:
                f.write(content)
            return {"success": True, "path": file_path}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _file_exists(self, file_path: str) -> Dict[str, Any]:
        """文件是否存在"""
        import os
        return {"success": True, "exists": os.path.exists(file_path)}
    
    def _list_dir(self, dir_path: str) -> Dict[str, Any]:
        """列出目录"""
        import os
        try:
            files = os.listdir(dir_path)
            return {"success": True, "files": files}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _delete_file(self, file_path: str) -> Dict[str, Any]:
        """删除文件"""
        import os
        try:
            os.remove(file_path)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _get_file_info(self, file_path: str) -> Dict[str, Any]:
        """获取文件信息"""
        import os
        try:
            stat = os.stat(file_path)
            return {
                "success": True,
                "size": stat.st_size,
                "created": stat.st_ctime,
                "modified": stat.st_mtime,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _get_file_extension(self, file_path: str) -> Dict[str, Any]:
        """获取文件扩展名"""
        import os
        _, ext = os.path.splitext(file_path)
        return {"success": True, "extension": ext}


class BasicAnalyticsPlugin(AnalyticsPlugin):
    """基础分析插件"""
    
    def __init__(self):
        super().__init__()
        self.metadata = PluginMetadata(
            id="basic_analytics",
            name="Basic Analytics",
            description="基础数据分析功能",
            version="1.0.0",
            author="DataAgent",
            type=PluginType.ANALYTICS,
            tags=["analytics", "statistics", "data"],
        )
    
    async def initialize(self):
        """初始化插件"""
        self.register_analytic("basic_stats", self._basic_stats)
        self.register_analytic("frequency", self._frequency)
        self.register_analytic("correlation", self._correlation)
        self.register_analytic("percentile", self._percentile)
        self.register_analytic("group_by", self._group_by)
        self.register_analytic("top_n", self._top_n)
        self.register_analytic("filter_data", self._filter_data)
        plugins_logger.info("Basic Analytics plugin initialized")
    
    async def execute(self, *args, **kwargs) -> Any:
        analysis_name = kwargs.get("analysis")
        data = kwargs.get("data")
        if analysis_name and data:
            return await self.run_analysis(analysis_name, data, *args, **kwargs)
        return {"analytics": self.list_analytics()}
    
    def _basic_stats(self, data: List[float]) -> Dict[str, Any]:
        """基础统计"""
        if not data:
            return {"success": False, "error": "No data"}
        
        return {
            "success": True,
            "count": len(data),
            "sum": sum(data),
            "mean": sum(data) / len(data),
            "min": min(data),
            "max": max(data),
            "median": statistics.median(data) if len(data) > 1 else data[0],
            "stdev": statistics.stdev(data) if len(data) > 2 else None,
        }
    
    def _frequency(self, data: List[Any]) -> Dict[str, Any]:
        """频率统计"""
        freq = {}
        for item in data:
            freq[item] = freq.get(item, 0) + 1
        return {"success": True, "frequency": freq}
    
    def _correlation(self, data1: List[float], data2: List[float]) -> Dict[str, Any]:
        """相关性"""
        if len(data1) != len(data2) or len(data1) < 2:
            return {"success": False, "error": "Invalid data"}
        
        try:
            import numpy as np
            corr = np.corrcoef(data1, data2)[0, 1]
            return {"success": True, "correlation": float(corr)}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _percentile(self, data: List[float], percentile: float) -> Dict[str, Any]:
        """百分位数"""
        if not data:
            return {"success": False, "error": "No data"}
        
        try:
            sorted_data = sorted(data)
            idx = int(len(sorted_data) * percentile / 100)
            return {"success": True, "value": sorted_data[min(idx, len(sorted_data) - 1)]}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _group_by(self, data: List[Dict], group_key: str, agg_key: str, agg_func: str = "sum") -> Dict[str, Any]:
        """分组聚合"""
        groups = {}
        for item in data:
            key = item.get(group_key)
            val = item.get(agg_key)
            if key not in groups:
                groups[key] = [val]
            else:
                groups[key].append(val)
        
        result = {}
        for key, vals in groups.items():
            if agg_func == "sum":
                result[key] = sum(vals)
            elif agg_func == "mean":
                result[key] = sum(vals) / len(vals)
            elif agg_func == "count":
                result[key] = len(vals)
            elif agg_func == "min":
                result[key] = min(vals)
            elif agg_func == "max":
                result[key] = max(vals)
        
        return {"success": True, "groups": result}
    
    def _top_n(self, data: List[Dict], key: str, n: int = 10, descending: bool = True) -> Dict[str, Any]:
        """Top N"""
        sorted_data = sorted(data, key=lambda x: x.get(key, 0), reverse=descending)
        return {"success": True, "top": sorted_data[:n]}
    
    def _filter_data(self, data: List[Dict], condition: Dict[str, Any]) -> Dict[str, Any]:
        """过滤数据"""
        result = []
        for item in data:
            match = True
            for k, v in condition.items():
                if item.get(k) != v:
                    match = False
                    break
            if match:
                result.append(item)
        return {"success": True, "filtered": result}


class SimpleVisualizationPlugin(VisualizationPlugin):
    """简单可视化插件"""
    
    def __init__(self):
        super().__init__()
        self.metadata = PluginMetadata(
            id="simple_visualization",
            name="Simple Visualization",
            description="简单数据可视化生成",
            version="1.0.0",
            author="DataAgent",
            type=PluginType.VISUALIZATION,
            tags=["visualization", "charts", "plot"],
        )
    
    async def initialize(self):
        """初始化插件"""
        self.register_visualization("bar_chart", self._bar_chart)
        self.register_visualization("pie_chart", self._pie_chart)
        self.register_visualization("line_chart", self._line_chart)
        self.register_visualization("scatter_plot", self._scatter_plot)
        self.register_visualization("histogram", self._histogram)
        self.register_visualization("table", self._table)
        plugins_logger.info("Simple Visualization plugin initialized")
    
    async def execute(self, *args, **kwargs) -> Any:
        viz_name = kwargs.get("visualization")
        data = kwargs.get("data")
        if viz_name and data:
            return await self.generate_visualization(viz_name, data, *args, **kwargs)
        return {"visualizations": self.list_visualizations()}
    
    def _bar_chart(self, data: List[Dict], x_key: str, y_key: str, title: str = "Bar Chart") -> Dict[str, Any]:
        """柱状图"""
        labels = [item.get(x_key) for item in data]
        values = [item.get(y_key) for item in data]
        return {
            "success": True,
            "type": "bar",
            "title": title,
            "labels": labels,
            "data": values,
        }
    
    def _pie_chart(self, data: List[Dict], label_key: str, value_key: str, title: str = "Pie Chart") -> Dict[str, Any]:
        """饼图"""
        labels = [item.get(label_key) for item in data]
        values = [item.get(value_key) for item in data]
        return {
            "success": True,
            "type": "pie",
            "title": title,
            "labels": labels,
            "data": values,
        }
    
    def _line_chart(self, data: List[Dict], x_key: str, y_key: str, title: str = "Line Chart") -> Dict[str, Any]:
        """折线图"""
        labels = [item.get(x_key) for item in data]
        values = [item.get(y_key) for item in data]
        return {
            "success": True,
            "type": "line",
            "title": title,
            "labels": labels,
            "data": values,
        }
    
    def _scatter_plot(self, data: List[Dict], x_key: str, y_key: str, title: str = "Scatter Plot") -> Dict[str, Any]:
        """散点图"""
        points = [{"x": item.get(x_key), "y": item.get(y_key)} for item in data]
        return {
            "success": True,
            "type": "scatter",
            "title": title,
            "points": points,
        }
    
    def _histogram(self, data: List[float], bins: int = 10, title: str = "Histogram") -> Dict[str, Any]:
        """直方图"""
        min_val = min(data)
        max_val = max(data)
        bin_width = (max_val - min_val) / bins
        hist = [0] * bins
        
        for val in data:
            bin_idx = min(int((val - min_val) / bin_width), bins - 1)
            hist[bin_idx] += 1
        
        return {
            "success": True,
            "type": "histogram",
            "title": title,
            "bins": bins,
            "data": hist,
        }
    
    def _table(self, data: List[Dict], columns: List[str] = None) -> Dict[str, Any]:
        """表格"""
        if not data:
            return {"success": False, "error": "No data"}
        
        if not columns:
            columns = list(data[0].keys())
        
        rows = []
        for item in data:
            rows.append({col: item.get(col) for col in columns})
        
        return {
            "success": True,
            "type": "table",
            "columns": columns,
            "rows": rows,
        }


class SampleDataSourcePlugin(DataSourcePlugin):
    """示例数据源插件"""
    
    def __init__(self):
        super().__init__()
        self.metadata = PluginMetadata(
            id="sample_data_source",
            name="Sample Data Source",
            description="示例数据和演示数据源",
            version="1.0.0",
            author="DataAgent",
            type=PluginType.DATA_SOURCE,
            tags=["data", "source", "sample"],
        )
    
    async def initialize(self):
        """初始化插件"""
        self.register_data_source("sales_data", self._sales_data)
        self.register_data_source("weather_data", self._weather_data)
        self.register_data_source("user_data", self._user_data)
        self.register_data_source("product_data", self._product_data)
        self.register_data_source("random_data", self._random_data)
        plugins_logger.info("Sample Data Source plugin initialized")
    
    async def execute(self, *args, **kwargs) -> Any:
        source_name = kwargs.get("source")
        if source_name:
            return await self.fetch_data(source_name, *args, **kwargs)
        return {"sources": self.list_data_sources()}
    
    def _sales_data(self, count: int = 10) -> Dict[str, Any]:
        """销售数据"""
        products = ["产品A", "产品B", "产品C", "产品D"]
        regions = ["华东", "华南", "华北", "西南"]
        data = []
        for i in range(count):
            data.append({
                "id": i + 1,
                "product": random.choice(products),
                "region": random.choice(regions),
                "sales": random.randint(100, 10000),
                "quantity": random.randint(1, 100),
            })
        return {"success": True, "data": data}
    
    def _weather_data(self, days: int = 7) -> Dict[str, Any]:
        """天气数据"""
        data = []
        base_date = datetime.now()
        for i in range(days):
            date = (base_date + timedelta(days=i))
            data.append({
                "date": date.strftime("%Y-%m-%d"),
                "temperature": round(random.uniform(10, 35), 1),
                "humidity": random.randint(30, 90),
                "weather": random.choice(["晴", "多云", "阴", "小雨", "大雨"]),
            })
        return {"success": True, "data": data}
    
    def _user_data(self, count: int = 20) -> Dict[str, Any]:
        """用户数据"""
        names = ["张三", "李四", "王五", "赵六", "孙七", "周八", "吴九", "郑十"]
        data = []
        for i in range(count):
            data.append({
                "id": i + 1,
                "name": random.choice(names) + str(i),
                "age": random.randint(18, 60),
                "city": random.choice(["北京", "上海", "广州", "深圳", "杭州"]),
                "score": round(random.uniform(0, 100), 1),
            })
        return {"success": True, "data": data}
    
    def _product_data(self, count: int = 15) -> Dict[str, Any]:
        """产品数据"""
        categories = ["电子产品", "服装", "食品", "家居", "运动"]
        data = []
        for i in range(count):
            data.append({
                "id": i + 1,
                "name": f"产品{i + 1}",
                "category": random.choice(categories),
                "price": round(random.uniform(10, 5000), 2),
                "stock": random.randint(0, 1000),
                "rating": round(random.uniform(1, 5), 1),
            })
        return {"success": True, "data": data}
    
    def _random_data(self, count: int = 50, min_val: float = 0, max_val: float = 100) -> Dict[str, Any]:
        """随机数据"""
        data = [round(random.uniform(min_val, max_val), 2) for _ in range(count)]
        return {"success": True, "data": data}


class CryptoToolsPlugin(ToolPlugin):
    """加密解密工具插件"""
    
    def __init__(self):
        super().__init__()
        self.metadata = PluginMetadata(
            id="crypto_tools",
            name="Crypto Tools",
            description="加密解密、哈希、编码工具",
            version="1.0.0",
            author="DataAgent",
            type=PluginType.TOOL,
            tags=["crypto", "hash", "encode", "decode"],
        )
    
    async def initialize(self):
        """初始化插件"""
        self.register_tool("md5", self._md5)
        self.register_tool("sha256", self._sha256)
        self.register_tool("sha1", self._sha1)
        self.register_tool("base64_encode", self._base64_encode)
        self.register_tool("base64_decode", self._base64_decode)
        self.register_tool("url_encode", self._url_encode)
        self.register_tool("url_decode", self._url_decode)
        self.register_tool("generate_uuid", self._generate_uuid)
        self.register_tool("generate_password", self._generate_password)
        plugins_logger.info("Crypto Tools plugin initialized")
    
    async def execute(self, *args, **kwargs) -> Any:
        tool_name = kwargs.get("tool")
        if tool_name:
            return await self.execute_tool(tool_name, *args, **kwargs)
        return {"tools": self.list_tools()}
    
    def _md5(self, text: str) -> Dict[str, Any]:
        """MD5哈希"""
        hash_obj = hashlib.md5(text.encode('utf-8'))
        return {"success": True, "result": hash_obj.hexdigest()}
    
    def _sha256(self, text: str) -> Dict[str, Any]:
        """SHA256哈希"""
        hash_obj = hashlib.sha256(text.encode('utf-8'))
        return {"success": True, "result": hash_obj.hexdigest()}
    
    def _sha1(self, text: str) -> Dict[str, Any]:
        """SHA1哈希"""
        hash_obj = hashlib.sha1(text.encode('utf-8'))
        return {"success": True, "result": hash_obj.hexdigest()}
    
    def _base64_encode(self, text: str) -> Dict[str, Any]:
        """Base64编码"""
        encoded = base64.b64encode(text.encode('utf-8')).decode('utf-8')
        return {"success": True, "result": encoded}
    
    def _base64_decode(self, encoded: str) -> Dict[str, Any]:
        """Base64解码"""
        try:
            decoded = base64.b64decode(encoded.encode('utf-8')).decode('utf-8')
            return {"success": True, "result": decoded}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _url_encode(self, text: str) -> Dict[str, Any]:
        """URL编码"""
        encoded = urllib.parse.quote(text)
        return {"success": True, "result": encoded}
    
    def _url_decode(self, encoded: str) -> Dict[str, Any]:
        """URL解码"""
        decoded = urllib.parse.unquote(encoded)
        return {"success": True, "result": decoded}
    
    def _generate_uuid(self) -> Dict[str, Any]:
        """生成UUID"""
        return {"success": True, "result": str(uuid.uuid4())}
    
    def _generate_password(self, length: int = 16, include_symbols: bool = True) -> Dict[str, Any]:
        """生成随机密码"""
        import string
        chars = string.ascii_letters + string.digits
        if include_symbols:
            chars += "!@#$%^&*()"
        password = ''.join(random.choice(chars) for _ in range(length))
        return {"success": True, "result": password}


class DataConverterPlugin(ToolPlugin):
    """数据转换工具插件"""
    
    def __init__(self):
        super().__init__()
        self.metadata = PluginMetadata(
            id="data_converter",
            name="Data Converter",
            description="JSON、CSV、XML等数据格式转换",
            version="1.0.0",
            author="DataAgent",
            type=PluginType.TOOL,
            tags=["convert", "json", "csv", "xml"],
        )
    
    async def initialize(self):
        """初始化插件"""
        self.register_tool("json_pretty", self._json_pretty)
        self.register_tool("json_minify", self._json_minify)
        self.register_tool("json_to_csv", self._json_to_csv)
        self.register_tool("csv_to_json", self._csv_to_json)
        self.register_tool("json_validate", self._json_validate)
        self.register_tool("base64_to_text", self._base64_to_text)
        self.register_tool("text_to_base64", self._text_to_base64)
        plugins_logger.info("Data Converter plugin initialized")
    
    async def execute(self, *args, **kwargs) -> Any:
        tool_name = kwargs.get("tool")
        if tool_name:
            return await self.execute_tool(tool_name, *args, **kwargs)
        return {"tools": self.list_tools()}
    
    def _json_pretty(self, json_str: str, indent: int = 2) -> Dict[str, Any]:
        """JSON格式化"""
        try:
            data = json.loads(json_str)
            pretty = json.dumps(data, indent=indent, ensure_ascii=False)
            return {"success": True, "result": pretty}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _json_minify(self, json_str: str) -> Dict[str, Any]:
        """JSON压缩"""
        try:
            data = json.loads(json_str)
            minified = json.dumps(data, separators=(',', ':'), ensure_ascii=False)
            return {"success": True, "result": minified}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _json_to_csv(self, json_str: str) -> Dict[str, Any]:
        """JSON转CSV"""
        try:
            import csv
            from io import StringIO
            data = json.loads(json_str)
            if not isinstance(data, list) or len(data) == 0:
                return {"success": False, "error": "JSON must be a list of objects"}
            
            output = StringIO()
            writer = csv.DictWriter(output, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
            return {"success": True, "result": output.getvalue()}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _csv_to_json(self, csv_str: str) -> Dict[str, Any]:
        """CSV转JSON"""
        try:
            import csv
            from io import StringIO
            input_file = StringIO(csv_str)
            reader = csv.DictReader(input_file)
            data = list(reader)
            return {"success": True, "result": json.dumps(data, ensure_ascii=False)}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _json_validate(self, json_str: str) -> Dict[str, Any]:
        """验证JSON"""
        try:
            json.loads(json_str)
            return {"success": True, "valid": True}
        except Exception as e:
            return {"success": True, "valid": False, "error": str(e)}
    
    def _base64_to_text(self, b64_str: str) -> Dict[str, Any]:
        """Base64转文本"""
        try:
            decoded = base64.b64decode(b64_str).decode('utf-8')
            return {"success": True, "result": decoded}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _text_to_base64(self, text: str) -> Dict[str, Any]:
        """文本转Base64"""
        try:
            encoded = base64.b64encode(text.encode('utf-8')).decode('utf-8')
            return {"success": True, "result": encoded}
        except Exception as e:
            return {"success": False, "error": str(e)}


class RegexToolsPlugin(ToolPlugin):
    """正则表达式工具插件"""
    
    def __init__(self):
        super().__init__()
        self.metadata = PluginMetadata(
            id="regex_tools",
            name="Regex Tools",
            description="正则表达式匹配、替换、提取",
            version="1.0.0",
            author="DataAgent",
            type=PluginType.TOOL,
            tags=["regex", "pattern", "match"],
        )
    
    async def initialize(self):
        """初始化插件"""
        self.register_tool("match", self._match)
        self.register_tool("find_all", self._find_all)
        self.register_tool("replace", self._replace)
        self.register_tool("split", self._split)
        self.register_tool("test", self._test)
        self.register_tool("extract_emails", self._extract_emails)
        self.register_tool("extract_urls", self._extract_urls)
        self.register_tool("extract_phones", self._extract_phones)
        plugins_logger.info("Regex Tools plugin initialized")
    
    async def execute(self, *args, **kwargs) -> Any:
        tool_name = kwargs.get("tool")
        if tool_name:
            return await self.execute_tool(tool_name, *args, **kwargs)
        return {"tools": self.list_tools()}
    
    def _match(self, pattern: str, text: str) -> Dict[str, Any]:
        """正则匹配"""
        try:
            match = re.match(pattern, text)
            if match:
                return {"success": True, "match": match.group(0), "groups": match.groups()}
            return {"success": True, "match": None}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _find_all(self, pattern: str, text: str) -> Dict[str, Any]:
        """查找所有匹配"""
        try:
            matches = re.findall(pattern, text)
            return {"success": True, "matches": matches}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _replace(self, pattern: str, text: str, replacement: str) -> Dict[str, Any]:
        """替换匹配"""
        try:
            result = re.sub(pattern, replacement, text)
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _split(self, pattern: str, text: str) -> Dict[str, Any]:
        """分割字符串"""
        try:
            parts = re.split(pattern, text)
            return {"success": True, "parts": parts}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _test(self, pattern: str, text: str) -> Dict[str, Any]:
        """测试匹配"""
        try:
            matched = bool(re.search(pattern, text))
            return {"success": True, "matched": matched}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _extract_emails(self, text: str) -> Dict[str, Any]:
        """提取邮箱"""
        pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        emails = re.findall(pattern, text)
        return {"success": True, "emails": emails}
    
    def _extract_urls(self, text: str) -> Dict[str, Any]:
        """提取URL"""
        pattern = r'https?://[^\s<>"]+|www\.[^\s<>"]+'
        urls = re.findall(pattern, text)
        return {"success": True, "urls": urls}
    
    def _extract_phones(self, text: str) -> Dict[str, Any]:
        """提取手机号"""
        pattern = r'1[3-9]\d{9}'
        phones = re.findall(pattern, text)
        return {"success": True, "phones": phones}


class ColorToolsPlugin(ToolPlugin):
    """颜色工具插件"""
    
    def __init__(self):
        super().__init__()
        self.metadata = PluginMetadata(
            id="color_tools",
            name="Color Tools",
            description="颜色格式转换、调色板",
            version="1.0.0",
            author="DataAgent",
            type=PluginType.TOOL,
            tags=["color", "rgb", "hex", "hsl"],
        )
    
    async def initialize(self):
        """初始化插件"""
        self.register_tool("hex_to_rgb", self._hex_to_rgb)
        self.register_tool("rgb_to_hex", self._rgb_to_hex)
        self.register_tool("rgb_to_hsl", self._rgb_to_hsl)
        self.register_tool("hsl_to_rgb", self._hsl_to_rgb)
        self.register_tool("random_color", self._random_color)
        self.register_tool("generate_palette", self._generate_palette)
        plugins_logger.info("Color Tools plugin initialized")
    
    async def execute(self, *args, **kwargs) -> Any:
        tool_name = kwargs.get("tool")
        if tool_name:
            return await self.execute_tool(tool_name, *args, **kwargs)
        return {"tools": self.list_tools()}
    
    def _hex_to_rgb(self, hex_color: str) -> Dict[str, Any]:
        """HEX转RGB"""
        try:
            hex_color = hex_color.lstrip('#')
            if len(hex_color) == 3:
                hex_color = ''.join([c * 2 for c in hex_color])
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            return {"success": True, "r": r, "g": g, "b": b}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _rgb_to_hex(self, r: int, g: int, b: int) -> Dict[str, Any]:
        """RGB转HEX"""
        try:
            hex_str = f"#{r:02x}{g:02x}{b:02x}"
            return {"success": True, "hex": hex_str}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _rgb_to_hsl(self, r: int, g: int, b: int) -> Dict[str, Any]:
        """RGB转HSL"""
        try:
            r_norm, g_norm, b_norm = r / 255, g / 255, b / 255
            max_val = max(r_norm, g_norm, b_norm)
            min_val = min(r_norm, g_norm, b_norm)
            h, s, l = 0, 0, (max_val + min_val) / 2
            
            if max_val != min_val:
                d = max_val - min_val
                s = d / (2 - max_val - min_val) if l > 0.5 else d / (max_val + min_val)
                
                if max_val == r_norm:
                    h = ((g_norm - b_norm) / d + (6 if g_norm < b_norm else 0)) / 6
                elif max_val == g_norm:
                    h = ((b_norm - r_norm) / d + 2) / 6
                else:
                    h = ((r_norm - g_norm) / d + 4) / 6
            
            return {"success": True, "h": round(h * 360), "s": round(s * 100), "l": round(l * 100)}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _hsl_to_rgb(self, h: int, s: int, l: int) -> Dict[str, Any]:
        """HSL转RGB"""
        try:
            h_norm, s_norm, l_norm = h / 360, s / 100, l / 100
            r, g, b = 0, 0, 0
            
            if s_norm == 0:
                r = g = b = l_norm
            else:
                def hue2rgb(p, q, t):
                    if t < 0:
                        t += 1
                    if t > 1:
                        t -= 1
                    if t < 1/6:
                        return p + (q - p) * 6 * t
                    if t < 1/2:
                        return q
                    if t < 2/3:
                        return p + (q - p) * (2/3 - t) * 6
                    return p
                
                q = l_norm * (1 + s_norm) if l_norm < 0.5 else l_norm + s_norm - l_norm * s_norm
                p = 2 * l_norm - q
                r = hue2rgb(p, q, h_norm + 1/3)
                g = hue2rgb(p, q, h_norm)
                b = hue2rgb(p, q, h_norm - 1/3)
            
            return {"success": True, "r": round(r * 255), "g": round(g * 255), "b": round(b * 255)}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _random_color(self) -> Dict[str, Any]:
        """随机颜色"""
        r = random.randint(0, 255)
        g = random.randint(0, 255)
        b = random.randint(0, 255)
        hex_str = f"#{r:02x}{g:02x}{b:02x}"
        return {"success": True, "r": r, "g": g, "b": b, "hex": hex_str}
    
    def _generate_palette(self, base_hex: str, count: int = 5) -> Dict[str, Any]:
        """生成调色板"""
        try:
            rgb = self._hex_to_rgb(base_hex)
            if not rgb["success"]:
                return rgb
            
            palette = []
            for i in range(count):
                factor = 0.3 + (i / (count - 1)) * 0.7 if count > 1 else 1
                r = min(255, int(rgb["r"] * factor))
                g = min(255, int(rgb["g"] * factor))
                b = min(255, int(rgb["b"] * factor))
                hex_str = f"#{r:02x}{g:02x}{b:02x}"
                palette.append({"r": r, "g": g, "b": b, "hex": hex_str})
            
            return {"success": True, "palette": palette}
        except Exception as e:
            return {"success": False, "error": str(e)}


class UnitConverterPlugin(ToolPlugin):
    """单位转换工具插件"""
    
    def __init__(self):
        super().__init__()
        self.metadata = PluginMetadata(
            id="unit_converter",
            name="Unit Converter",
            description="长度、重量、温度等单位转换",
            version="1.0.0",
            author="DataAgent",
            type=PluginType.TOOL,
            tags=["unit", "convert", "length", "weight"],
        )
    
    async def initialize(self):
        """初始化插件"""
        self.register_tool("convert_length", self._convert_length)
        self.register_tool("convert_weight", self._convert_weight)
        self.register_tool("convert_temperature", self._convert_temperature)
        self.register_tool("convert_area", self._convert_area)
        self.register_tool("convert_volume", self._convert_volume)
        self.register_tool("convert_speed", self._convert_speed)
        plugins_logger.info("Unit Converter plugin initialized")
    
    async def execute(self, *args, **kwargs) -> Any:
        tool_name = kwargs.get("tool")
        if tool_name:
            return await self.execute_tool(tool_name, *args, **kwargs)
        return {"tools": self.list_tools()}
    
    def _convert_length(self, value: float, from_unit: str, to_unit: str) -> Dict[str, Any]:
        """长度转换"""
        meters = {
            "mm": 0.001,
            "cm": 0.01,
            "m": 1,
            "km": 1000,
            "in": 0.0254,
            "ft": 0.3048,
            "yd": 0.9144,
            "mi": 1609.344
        }
        if from_unit not in meters or to_unit not in meters:
            return {"success": False, "error": "Invalid unit"}
        
        value_in_meters = value * meters[from_unit]
        result = value_in_meters / meters[to_unit]
        return {"success": True, "result": result, "from": from_unit, "to": to_unit}
    
    def _convert_weight(self, value: float, from_unit: str, to_unit: str) -> Dict[str, Any]:
        """重量转换"""
        kg = {
            "mg": 0.000001,
            "g": 0.001,
            "kg": 1,
            "ton": 1000,
            "oz": 0.0283495,
            "lb": 0.453592
        }
        if from_unit not in kg or to_unit not in kg:
            return {"success": False, "error": "Invalid unit"}
        
        value_in_kg = value * kg[from_unit]
        result = value_in_kg / kg[to_unit]
        return {"success": True, "result": result, "from": from_unit, "to": to_unit}
    
    def _convert_temperature(self, value: float, from_unit: str, to_unit: str) -> Dict[str, Any]:
        """温度转换"""
        celsius = 0
        if from_unit == "c":
            celsius = value
        elif from_unit == "f":
            celsius = (value - 32) * 5 / 9
        elif from_unit == "k":
            celsius = value - 273.15
        else:
            return {"success": False, "error": "Invalid unit"}
        
        result = 0
        if to_unit == "c":
            result = celsius
        elif to_unit == "f":
            result = celsius * 9 / 5 + 32
        elif to_unit == "k":
            result = celsius + 273.15
        else:
            return {"success": False, "error": "Invalid unit"}
        
        return {"success": True, "result": result, "from": from_unit, "to": to_unit}
    
    def _convert_area(self, value: float, from_unit: str, to_unit: str) -> Dict[str, Any]:
        """面积转换"""
        sq_m = {
            "sq_mm": 0.000001,
            "sq_cm": 0.0001,
            "sq_m": 1,
            "sq_km": 1000000,
            "sq_in": 0.00064516,
            "sq_ft": 0.092903,
            "sq_yd": 0.836127,
            "acre": 4046.86,
            "ha": 10000
        }
        if from_unit not in sq_m or to_unit not in sq_m:
            return {"success": False, "error": "Invalid unit"}
        
        value_in_sq_m = value * sq_m[from_unit]
        result = value_in_sq_m / sq_m[to_unit]
        return {"success": True, "result": result, "from": from_unit, "to": to_unit}
    
    def _convert_volume(self, value: float, from_unit: str, to_unit: str) -> Dict[str, Any]:
        """体积转换"""
        liters = {
            "ml": 0.001,
            "l": 1,
            "cu_m": 1000,
            "cu_in": 0.0163871,
            "cu_ft": 28.3168,
            "gal_us": 3.78541,
            "gal_uk": 4.54609,
            "pt_us": 0.473176,
            "pt_uk": 0.568261
        }
        if from_unit not in liters or to_unit not in liters:
            return {"success": False, "error": "Invalid unit"}
        
        value_in_liters = value * liters[from_unit]
        result = value_in_liters / liters[to_unit]
        return {"success": True, "result": result, "from": from_unit, "to": to_unit}
    
    def _convert_speed(self, value: float, from_unit: str, to_unit: str) -> Dict[str, Any]:
        """速度转换"""
        mps = {
            "mps": 1,
            "kmph": 0.277778,
            "mph": 0.44704,
            "knot": 0.514444,
            "fps": 0.3048
        }
        if from_unit not in mps or to_unit not in mps:
            return {"success": False, "error": "Invalid unit"}
        
        value_in_mps = value * mps[from_unit]
        result = value_in_mps / mps[to_unit]
        return {"success": True, "result": result, "from": from_unit, "to": to_unit}


class AdvancedAnalyticsPlugin(AnalyticsPlugin):
    """高级分析插件"""
    
    def __init__(self):
        super().__init__()
        self.metadata = PluginMetadata(
            id="advanced_analytics",
            name="Advanced Analytics",
            description="高级数据分析功能",
            version="1.0.0",
            author="DataAgent",
            type=PluginType.ANALYTICS,
            tags=["analytics", "statistics", "advanced"],
        )
    
    async def initialize(self):
        """初始化插件"""
        self.register_analytic("moving_average", self._moving_average)
        self.register_analytic("linear_regression", self._linear_regression)
        self.register_analytic("normalization", self._normalization)
        self.register_analytic("standardization", self._standardization)
        self.register_analytic("outlier_detection", self._outlier_detection)
        self.register_analytic("histogram_bins", self._histogram_bins)
        self.register_analytic("covariance", self._covariance)
        self.register_analytic("time_series_forecast", self._time_series_forecast)
        plugins_logger.info("Advanced Analytics plugin initialized")
    
    async def execute(self, *args, **kwargs) -> Any:
        analysis_name = kwargs.get("analysis")
        data = kwargs.get("data")
        if analysis_name and data:
            return await self.run_analysis(analysis_name, data, *args, **kwargs)
        return {"analytics": self.list_analytics()}
    
    def _moving_average(self, data: List[float], window: int = 3) -> Dict[str, Any]:
        """移动平均"""
        if len(data) < window:
            return {"success": False, "error": "Data too short"}
        
        ma = []
        for i in range(len(data) - window + 1):
            window_data = data[i:i+window]
            ma.append(sum(window_data) / window)
        
        return {"success": True, "moving_average": ma, "window": window}
    
    def _linear_regression(self, x: List[float], y: List[float]) -> Dict[str, Any]:
        """线性回归"""
        if len(x) != len(y) or len(x) < 2:
            return {"success": False, "error": "Invalid data"}
        
        n = len(x)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(xi * yi for xi, yi in zip(x, y))
        sum_x_sq = sum(xi ** 2 for xi in x)
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x_sq - sum_x ** 2)
        intercept = (sum_y - slope * sum_x) / n
        
        return {"success": True, "slope": slope, "intercept": intercept}
    
    def _normalization(self, data: List[float]) -> Dict[str, Any]:
        """归一化 (0-1)"""
        if not data:
            return {"success": False, "error": "No data"}
        
        min_val = min(data)
        max_val = max(data)
        if max_val == min_val:
            return {"success": True, "normalized": [0.5] * len(data)}
        
        normalized = [(x - min_val) / (max_val - min_val) for x in data]
        return {"success": True, "normalized": normalized, "min": min_val, "max": max_val}
    
    def _standardization(self, data: List[float]) -> Dict[str, Any]:
        """标准化 (Z-score)"""
        if len(data) < 2:
            return {"success": False, "error": "Not enough data"}
        
        mean = sum(data) / len(data)
        variance = sum((x - mean) ** 2 for x in data) / len(data)
        std_dev = math.sqrt(variance) if variance > 0 else 1
        
        standardized = [(x - mean) / std_dev for x in data]
        return {"success": True, "standardized": standardized, "mean": mean, "std_dev": std_dev}
    
    def _outlier_detection(self, data: List[float], threshold: float = 1.5) -> Dict[str, Any]:
        """异常值检测 (IQR方法)"""
        if len(data) < 4:
            return {"success": False, "error": "Not enough data"}
        
        sorted_data = sorted(data)
        q1_index = len(sorted_data) // 4
        q3_index = len(sorted_data) * 3 // 4
        q1 = sorted_data[q1_index]
        q3 = sorted_data[q3_index]
        iqr = q3 - q1
        
        lower_bound = q1 - threshold * iqr
        upper_bound = q3 + threshold * iqr
        
        outliers = [x for x in data if x < lower_bound or x > upper_bound]
        return {
            "success": True,
            "outliers": outliers,
            "lower_bound": lower_bound,
            "upper_bound": upper_bound,
            "q1": q1,
            "q3": q3,
            "iqr": iqr
        }
    
    def _histogram_bins(self, data: List[float], bins: int = 10) -> Dict[str, Any]:
        """直方图分箱"""
        if not data:
            return {"success": False, "error": "No data"}
        
        min_val = min(data)
        max_val = max(data)
        bin_width = (max_val - min_val) / bins if bins > 0 else 1
        
        counts = [0] * bins
        for x in data:
            bin_idx = min(int((x - min_val) / bin_width), bins - 1)
            counts[bin_idx] += 1
        
        bin_edges = [min_val + i * bin_width for i in range(bins + 1)]
        return {"success": True, "counts": counts, "bin_edges": bin_edges, "bins": bins}
    
    def _covariance(self, x: List[float], y: List[float]) -> Dict[str, Any]:
        """协方差"""
        if len(x) != len(y) or len(x) < 2:
            return {"success": False, "error": "Invalid data"}
        
        n = len(x)
        mean_x = sum(x) / n
        mean_y = sum(y) / n
        
        cov = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y)) / n
        return {"success": True, "covariance": cov}
    
    def _time_series_forecast(self, data: List[float], periods: int = 3) -> Dict[str, Any]:
        """简单时间序列预测 (趋势线)"""
        if len(data) < 2:
            return {"success": False, "error": "Not enough data"}
        
        x = list(range(len(data)))
        lr = self._linear_regression(x, data)
        if not lr["success"]:
            return lr
        
        slope = lr["slope"]
        intercept = lr["intercept"]
        
        forecast = []
        for i in range(1, periods + 1):
            forecast_x = len(data) + i - 1
            forecast_y = slope * forecast_x + intercept
            forecast.append(forecast_y)
        
        return {
            "success": True,
            "forecast": forecast,
            "periods": periods,
            "slope": slope,
            "intercept": intercept
        }


# 注册所有内置插件
async def register_builtin_plugins():
    """注册所有内置插件"""
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
    
    # 添加扩展插件
    if EXTENDED_PLUGINS_AVAILABLE:
        if ListToolsPlugin:
            plugins.append(ListToolsPlugin())
        if TextGeneratorPlugin:
            plugins.append(TextGeneratorPlugin())
        if DateTimeToolsPlugin:
            plugins.append(DateTimeToolsPlugin())
    
    for plugin in plugins:
        await plugin_manager.register_plugin(plugin)
        await plugin_manager.initialize_plugin(plugin.metadata.id)
    
    plugins_logger.info(f"Registered {len(plugins)} built-in plugins")


__all__ = [
    "MathToolsPlugin",
    "StringToolsPlugin",
    "TimeToolsPlugin",
    "FileToolsPlugin",
    "BasicAnalyticsPlugin",
    "SimpleVisualizationPlugin",
    "SampleDataSourcePlugin",
    "CryptoToolsPlugin",
    "DataConverterPlugin",
    "RegexToolsPlugin",
    "ColorToolsPlugin",
    "UnitConverterPlugin",
    "AdvancedAnalyticsPlugin",
    "register_builtin_plugins",
    "EXTENDED_PLUGINS_AVAILABLE",
]


# 从扩展模块导入额外的插件
try:
    from core.plugins_extended_complete import (
        ListToolsPlugin,
        TextGeneratorPlugin,
        DateTimeToolsPlugin,
    )
    EXTENDED_PLUGINS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"部分扩展插件导入失败: {e}")
    ListToolsPlugin = None
    TextGeneratorPlugin = None
    DateTimeToolsPlugin = None
    EXTENDED_PLUGINS_AVAILABLE = False
