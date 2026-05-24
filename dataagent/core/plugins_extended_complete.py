"""
DataAgent - 扩展插件集合
提供额外的实用插件功能 - 完整版本
"""
import random
import re
import math
from datetime import datetime, timedelta
from typing import Any, Dict, List

from core.logging import get_logger
from core.plugins import (
    PluginMetadata,
    PluginType,
    ToolPlugin,
    AnalyticsPlugin,
    plugin_manager,
    plugins_logger,
)


class ListToolsPlugin(ToolPlugin):
    """列表处理工具插件"""
    
    def __init__(self):
        super().__init__()
        self.metadata = PluginMetadata(
            id="list_tools",
            name="List Tools",
            description="列表处理工具（去重、排序、洗牌等）",
            version="1.0.0",
            author="DataAgent",
            type=PluginType.TOOL,
            tags=["list", "sort", "unique", "shuffle"],
        )
    
    async def initialize(self):
        """初始化插件"""
        self.register_tool("unique", self._unique)
        self.register_tool("shuffle", self._shuffle)
        self.register_tool("chunk", self._chunk)
        self.register_tool("flatten", self._flatten)
        self.register_tool("intersection", self._intersection)
        self.register_tool("difference", self._difference)
        self.register_tool("group_by_length", self._group_by_length)
        plugins_logger.info("List Tools plugin initialized")
    
    async def execute(self, *args, **kwargs) -> Any:
        tool_name = kwargs.get("tool")
        if tool_name:
            return await self.execute_tool(tool_name, *args, **kwargs)
        return {"tools": self.list_tools()}
    
    def _unique(self, items: List[Any]) -> Dict[str, Any]:
        """列表去重"""
        seen = set()
        result = []
        for item in items:
            if item not in seen:
                seen.add(item)
                result.append(item)
        return {
            "success": True,
            "unique": result,
            "original_count": len(items),
            "unique_count": len(result)
        }
    
    def _shuffle(self, items: List[Any], seed: int = None) -> Dict[str, Any]:
        """列表随机打乱"""
        if seed is not None:
            random.seed(seed)
        shuffled = items.copy()
        random.shuffle(shuffled)
        return {
            "success": True,
            "shuffled": shuffled
        }
    
    def _chunk(self, items: List[Any], size: int) -> Dict[str, Any]:
        """列表分块"""
        if size <= 0:
            return {"success": False, "error": "Size must be positive"}
        
        chunks = [items[i:i+size] for i in range(0, len(items), size)]
        return {
            "success": True,
            "chunks": chunks,
            "chunk_count": len(chunks)
        }
    
    def _flatten(self, nested_list: List[Any]) -> Dict[str, Any]:
        """列表扁平化"""
        def flatten(lst):
            result = []
            for item in lst:
                if isinstance(item, list):
                    result.extend(flatten(item))
                else:
                    result.append(item)
            return result
        
        flat = flatten(nested_list)
        return {
            "success": True,
            "flattened": flat,
            "original_depth": self._get_depth(nested_list)
        }
    
    def _get_depth(self, lst, current_depth=0):
        """获取列表嵌套深度"""
        if not isinstance(lst, list) or len(lst) == 0:
            return current_depth
        return max((self._get_depth(item, current_depth + 1) for item in lst if isinstance(item, list)), default=current_depth)
    
    def _intersection(self, list1: List[Any], list2: List[Any]) -> Dict[str, Any]:
        """列表交集"""
        common = list(set(list1) & set(list2))
        return {
            "success": True,
            "intersection": common,
            "count": len(common)
        }
    
    def _difference(self, list1: List[Any], list2: List[Any]) -> Dict[str, Any]:
        """列表差集"""
        diff = list(set(list1) - set(list2))
        return {
            "success": True,
            "difference": diff,
            "count": len(diff)
        }
    
    def _group_by_length(self, items: List[str]) -> Dict[str, Any]:
        """按长度分组"""
        groups = {}
        for item in items:
            length = len(str(item))
            if length not in groups:
                groups[length] = []
            groups[length].append(item)
        return {
            "success": True,
            "groups": groups,
            "group_count": len(groups)
        }


class TextGeneratorPlugin(ToolPlugin):
    """文本生成工具插件"""
    
    def __init__(self):
        super().__init__()
        self.metadata = PluginMetadata(
            id="text_generator",
            name="Text Generator",
            description="文本生成工具（随机文本、Lorem ipsum等）",
            version="1.0.0",
            author="DataAgent",
            type=PluginType.TOOL,
            tags=["text", "generator", "lorem", "random"],
        )
    
    async def initialize(self):
        """初始化插件"""
        self.register_tool("generate_lorem_ipsum", self._generate_lorem_ipsum)
        self.register_tool("generate_random_words", self._generate_random_words)
        self.register_tool("generate_random_sentences", self._generate_random_sentences)
        self.register_tool("generate_random_paragraph", self._generate_random_paragraph)
        self.register_tool("generate_random_name", self._generate_random_name)
        plugins_logger.info("Text Generator plugin initialized")
    
    async def execute(self, *args, **kwargs) -> Any:
        tool_name = kwargs.get("tool")
        if tool_name:
            return await self.execute_tool(tool_name, *args, **kwargs)
        return {"tools": self.list_tools()}
    
    def _generate_lorem_ipsum(self, paragraphs: int = 3, sentences_per_paragraph: int = 4) -> Dict[str, Any]:
        """生成Lorem ipsum文本"""
        words = [
            'lorem', 'ipsum', 'dolor', 'sit', 'amet', 'consectetur', 'adipiscing', 'elit',
            'sed', 'do', 'eiusmod', 'tempor', 'incididunt', 'ut', 'labore', 'et', 'dolore',
            'magna', 'aliqua', 'enim', 'ad', 'minim', 'veniam', 'quis', 'nostrud',
            'exercitation', 'ullamco', 'laboris', 'nisi', 'aliquip', 'ex', 'ea', 'commodo',
            'consequat', 'duis', 'aute', 'irure', 'in', 'reprehenderit', 'voluptate',
            'velit', 'esse', 'cillum', 'fugiat', 'nulla', 'pariatur', 'excepteur', 'sint',
            'occaecat', 'cupidatat', 'non', 'proident', 'sunt', 'culpa', 'qui', 'officia',
            'deserunt', 'mollit', 'anim', 'id', 'est', 'laborum'
        ]
        
        result = []
        for _ in range(paragraphs):
            sentences = []
            for _ in range(sentences_per_paragraph):
                word_count = random.randint(8, 15)
                sentence_words = [random.choice(words) for _ in range(word_count)]
                sentence = ' '.join(sentence_words).capitalize() + '.'
                sentences.append(sentence)
            result.append(' '.join(sentences))
        
        return {
            "success": True,
            "paragraphs": result,
            "paragraph_count": paragraphs
        }
    
    def _generate_random_words(self, count: int = 10) -> Dict[str, Any]:
        """生成随机单词"""
        words = [
            'apple', 'banana', 'cherry', 'dragon', 'elephant', 'forest', 'garden',
            'horizon', 'island', 'journey', 'kingdom', 'lantern', 'mountain', 'nature',
            'ocean', 'paradise', 'quartz', 'rainbow', 'sunset', 'thunder', 'universe',
            'valley', 'wonder', 'xylophone', 'yellow', 'zenith'
        ]
        
        result = [random.choice(words) for _ in range(count)]
        return {
            "success": True,
            "words": result,
            "count": len(result)
        }
    
    def _generate_random_sentences(self, count: int = 5) -> Dict[str, Any]:
        """生成随机句子"""
        subjects = ['The cat', 'A bird', 'The dog', 'Someone', 'Everyone', 'Nobody']
        verbs = ['runs', 'jumps', 'sings', 'dances', 'writes', 'reads']
        objects = ['quickly', 'slowly', 'happily', 'quietly', 'loudly', 'easily']
        
        sentences = []
        for _ in range(count):
            sentence = f"{random.choice(subjects)} {random.choice(verbs)} {random.choice(objects)}."
            sentences.append(sentence)
        
        return {
            "success": True,
            "sentences": sentences,
            "count": len(sentences)
        }
    
    def _generate_random_paragraph(self, sentences: int = 5) -> Dict[str, Any]:
        """生成随机段落"""
        result = self._generate_random_sentences(sentences)
        paragraph = ' '.join(result['sentences'])
        return {
            "success": True,
            "paragraph": paragraph,
            "sentence_count": sentences
        }
    
    def _generate_random_name(self, count: int = 1, gender: str = "any") -> Dict[str, Any]:
        """生成随机姓名"""
        first_names_male = ['张', '王', '李', '刘', '陈', '杨', '赵', '黄', '周', '吴']
        first_names_female = ['王', '李', '刘', '陈', '杨', '赵', '黄', '周', '吴', '徐']
        last_names = ['伟', '芳', '娜', '秀英', '敏', '静', '丽', '强', '磊', '军', '洋', '勇', '艳', '杰', '涛']
        
        names = []
        for _ in range(count):
            if gender == 'male':
                first = random.choice(first_names_male)
            elif gender == 'female':
                first = random.choice(first_names_female)
            else:
                first = random.choice(first_names_male + first_names_female)
            
            last = random.choice(last_names)
            names.append(f"{first}{last}")
        
        return {
            "success": True,
            "names": names,
            "count": len(names)
        }


class DateTimeToolsPlugin(ToolPlugin):
    """日期时间工具插件"""
    
    def __init__(self):
        super().__init__()
        self.metadata = PluginMetadata(
            id="datetime_tools",
            name="DateTime Tools",
            description="日期时间处理工具（格式化、计算、工作日等）",
            version="1.0.0",
            author="DataAgent",
            type=PluginType.TOOL,
            tags=["datetime", "date", "time", "calendar"],
        )
    
    async def initialize(self):
        """初始化插件"""
        self.register_tool("current_datetime", self._current_datetime)
        self.register_tool("format_date", self._format_date)
        self.register_tool("add_days", self._add_days)
        self.register_tool("days_between", self._days_between)
        self.register_tool("is_weekend", self._is_weekend)
        self.register_tool("get_week_number", self._get_week_number)
        self.register_tool("get_quarter", self._get_quarter)
        plugins_logger.info("DateTime Tools plugin initialized")
    
    async def execute(self, *args, **kwargs) -> Any:
        tool_name = kwargs.get("tool")
        if tool_name:
            return await self.execute_tool(tool_name, *args, **kwargs)
        return {"tools": self.list_tools()}
    
    def _current_datetime(self, timezone: str = "Asia/Shanghai") -> Dict[str, Any]:
        """获取当前日期时间"""
        now = datetime.now()
        return {
            "success": True,
            "datetime": now.isoformat(),
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
            "timestamp": now.timestamp(),
            "weekday": now.strftime("%A"),
            "weekday_cn": ['星期一', '星期二', '星期三', '星期四', '星期五', '星期六', '星期日'][now.weekday()]
        }
    
    def _format_date(self, date_str: str, input_format: str = "%Y-%m-%d", output_format: str = "%Y年%m月%d日") -> Dict[str, Any]:
        """日期格式化"""
        try:
            dt = datetime.strptime(date_str, input_format)
            formatted = dt.strftime(output_format)
            return {
                "success": True,
                "original": date_str,
                "formatted": formatted,
                "weekday": dt.strftime("%A"),
                "weekday_cn": ['星期一', '星期二', '星期三', '星期四', '星期五', '星期六', '星期日'][dt.weekday()]
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _add_days(self, date_str: str, days: int, format_str: str = "%Y-%m-%d") -> Dict[str, Any]:
        """日期加减天数"""
        try:
            dt = datetime.strptime(date_str, format_str)
            new_dt = dt + timedelta(days=days)
            return {
                "success": True,
                "original": date_str,
                "days_added": days,
                "result": new_dt.strftime(format_str),
                "weekday": new_dt.strftime("%A"),
                "weekday_cn": ['星期一', '星期二', '星期三', '星期四', '星期五', '星期六', '星期日'][new_dt.weekday()]
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _days_between(self, start_date: str, end_date: str, format_str: str = "%Y-%m-%d") -> Dict[str, Any]:
        """计算日期差"""
        try:
            start = datetime.strptime(start_date, format_str)
            end = datetime.strptime(end_date, format_str)
            diff = abs((end - start).days)
            return {
                "success": True,
                "start_date": start_date,
                "end_date": end_date,
                "days": diff,
                "weeks": diff / 7,
                "months": diff / 30
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _is_weekend(self, date_str: str, format_str: str = "%Y-%m-%d") -> Dict[str, Any]:
        """判断是否周末"""
        try:
            dt = datetime.strptime(date_str, format_str)
            is_weekend = dt.weekday() >= 5
            return {
                "success": True,
                "date": date_str,
                "is_weekend": is_weekend,
                "is_workday": not is_weekend,
                "weekday": ['星期一', '星期二', '星期三', '星期四', '星期五', '星期六', '星期日'][dt.weekday()]
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _get_week_number(self, date_str: str, format_str: str = "%Y-%m-%d") -> Dict[str, Any]:
        """获取周数"""
        try:
            dt = datetime.strptime(date_str, format_str)
            week_num = dt.isocalendar()[1]
            return {
                "success": True,
                "date": date_str,
                "year": dt.year,
                "week_number": week_num,
                "day_of_week": dt.weekday() + 1
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _get_quarter(self, date_str: str = None, format_str: str = "%Y-%m-%d") -> Dict[str, Any]:
        """获取季度"""
        try:
            if date_str:
                dt = datetime.strptime(date_str, format_str)
            else:
                dt = datetime.now()
            
            quarter = (dt.month - 1) // 3 + 1
            quarter_months = {
                1: ['01', '02', '03'],
                2: ['04', '05', '06'],
                3: ['07', '08', '09'],
                4: ['10', '11', '12']
            }
            
            return {
                "success": True,
                "date": dt.strftime(format_str),
                "quarter": quarter,
                "quarter_name": f"Q{quarter}",
                "months": quarter_months[quarter]
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


__all__ = [
    "ListToolsPlugin",
    "TextGeneratorPlugin",
    "DateTimeToolsPlugin",
]
