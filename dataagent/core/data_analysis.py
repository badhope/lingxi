"""
DataAgent - 数据分析模块
提供数据处理、统计分析、可视化等功能
"""
import asyncio
import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Tuple,
    Union
)

from core.config import config_manager
from core.logging import get_logger

analysis_logger = get_logger("data_analysis")


class ChartType(Enum):
    """图表类型"""
    BAR = "bar"
    LINE = "line"
    PIE = "pie"
    SCATTER = "scatter"
    HISTOGRAM = "histogram"
    BOX = "box"
    AREA = "area"
    HEATMAP = "heatmap"
    TREEMAP = "treemap"
    FUNNEL = "funnel"


class AggregationType(Enum):
    """聚合类型"""
    SUM = "sum"
    AVG = "avg"
    COUNT = "count"
    MIN = "min"
    MAX = "max"
    MEDIAN = "median"
    STD = "std"
    VAR = "var"


class FilterOperator(Enum):
    """过滤操作符"""
    EQ = "eq"
    NE = "ne"
    GT = "gt"
    LT = "lt"
    GTE = "gte"
    LTE = "lte"
    CONTAINS = "contains"
    IN = "in"
    NOT_IN = "not_in"
    BETWEEN = "between"


@dataclass
class FilterCondition:
    """过滤条件"""
    field: str
    operator: FilterOperator
    value: Any


@dataclass
class ChartConfig:
    """图表配置"""
    title: str
    chart_type: ChartType
    x_field: str
    y_field: str
    y_aggregation: Optional[AggregationType] = None
    group_by: Optional[str] = None
    filters: List[FilterCondition] = field(default_factory=list)
    sort_by: Optional[str] = None
    sort_ascending: bool = True
    limit: Optional[int] = None
    colors: Optional[List[str]] = None
    width: int = 800
    height: int = 500


@dataclass
class AnalysisResult:
    """分析结果"""
    success: bool
    data: Optional[Any] = None
    chart_config: Optional[ChartConfig] = None
    error: Optional[str] = None
    summary: Optional[str] = None
    insights: List[str] = field(default_factory=list)


class DataAnalyzer:
    """数据分析器"""
    
    def __init__(self, data: Optional[List[Dict]] = None):
        self.data: List[Dict] = data or []
        self.cache: Dict[str, Any] = {}
    
    def load_data(self, data: List[Dict]):
        """加载数据"""
        self.data = data
        self.cache = {}
        analysis_logger.info(f"已加载 {len(data)} 条数据")
    
    def load_from_file(self, file_path: Path):
        """从文件加载数据（支持 JSON、CSV 等）"""
        try:
            if file_path.suffix == '.json':
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        self.load_data(data)
                    elif isinstance(data, dict) and 'data' in data:
                        self.load_data(data['data'])
                    else:
                        raise ValueError("JSON 格式不正确")
            elif file_path.suffix == '.csv':
                self._load_csv(file_path)
            else:
                raise ValueError(f"不支持的文件格式: {file_path.suffix}")
        except Exception as e:
            analysis_logger.error(f"加载文件失败: {e}")
            raise
    
    def _load_csv(self, file_path: Path):
        """加载 CSV 数据"""
        try:
            import csv
            data = []
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    data.append(row)
            self.load_data(data)
        except ImportError:
            analysis_logger.warning("CSV 加载功能需要 csv 模块（已内置）")
            raise
    
    def get_fields(self) -> List[str]:
        """获取所有字段"""
        if not self.data:
            return []
        return list(self.data[0].keys())
    
    def get_statistics(self, field: str) -> Dict[str, Any]:
        """获取字段的统计信息"""
        values = []
        for row in self.data:
            if field in row:
                values.append(row[field])
        
        if not values:
            return {}
        
        try:
            numeric_values = [float(v) for v in values if v not in [None, '']]
            
            if not numeric_values:
                return {
                    "field": field,
                    "type": "non-numeric",
                    "count": len(values),
                    "unique_count": len(set(values))
                }
            
            import statistics
            
            return {
                "field": field,
                "type": "numeric",
                "count": len(numeric_values),
                "min": min(numeric_values),
                "max": max(numeric_values),
                "sum": sum(numeric_values),
                "avg": sum(numeric_values) / len(numeric_values),
                "median": statistics.median(numeric_values) if len(numeric_values) > 1 else numeric_values[0],
                "std": statistics.stdev(numeric_values) if len(numeric_values) > 2 else None,
                "var": statistics.variance(numeric_values) if len(numeric_values) > 2 else None
            }
        except Exception as e:
            analysis_logger.error(f"计算统计信息失败: {e}")
            return {
                "field": field,
                "error": str(e)
            }
    
    def aggregate(
        self,
        field: str,
        aggregation_type: AggregationType = AggregationType.SUM,
        group_by: Optional[str] = None,
        filters: Optional[List[FilterCondition]] = None
    ) -> Dict[str, Any]:
        """聚合数据"""
        filtered_data = self._apply_filters(filters or [])
        
        if group_by:
            groups = {}
            for row in filtered_data:
                group_key = row.get(group_by, 'unknown')
                if group_key not in groups:
                    groups[group_key] = []
                if field in row:
                    groups[group_key].append(row[field])
            
            results = {}
            for group_name, group_values in groups.items():
                results[group_name] = self._compute_aggregation(group_values, aggregation_type)
            
            return {
                "type": "grouped",
                "group_by": group_by,
                "results": results
            }
        else:
            values = [row[field] for row in filtered_data if field in row]
            return {
                "type": "single",
                "result": self._compute_aggregation(values, aggregation_type)
            }
    
    def _compute_aggregation(self, values: List[Any], agg_type: AggregationType) -> Any:
        """计算聚合值"""
        try:
            numeric_values = [float(v) for v in values if v not in [None, '']]
            
            if not numeric_values:
                return None
            
            if agg_type == AggregationType.SUM:
                return sum(numeric_values)
            elif agg_type == AggregationType.AVG:
                return sum(numeric_values) / len(numeric_values)
            elif agg_type == AggregationType.COUNT:
                return len(numeric_values)
            elif agg_type == AggregationType.MIN:
                return min(numeric_values)
            elif agg_type == AggregationType.MAX:
                return max(numeric_values)
            elif agg_type == AggregationType.MEDIAN:
                import statistics
                return statistics.median(numeric_values)
            elif agg_type == AggregationType.STD:
                import statistics
                return statistics.stdev(numeric_values) if len(numeric_values) > 2 else None
            elif agg_type == AggregationType.VAR:
                import statistics
                return statistics.variance(numeric_values) if len(numeric_values) > 2 else None
        except Exception as e:
            analysis_logger.error(f"聚合计算失败: {e}")
            return None
    
    def _apply_filters(self, filters: List[FilterCondition]) -> List[Dict]:
        """应用过滤条件"""
        filtered_data = list(self.data)
        
        for filter_cond in filters:
            filtered_data = [
                row for row in filtered_data
                if self._check_condition(row, filter_cond)
            ]
        
        return filtered_data
    
    def _check_condition(self, row: Dict, condition: FilterCondition) -> bool:
        """检查行是否满足条件"""
        field_value = row.get(condition.field)
        target_value = condition.value
        operator = condition.operator
        
        if operator == FilterOperator.EQ:
            return str(field_value) == str(target_value)
        elif operator == FilterOperator.NE:
            return str(field_value) != str(target_value)
        elif operator == FilterOperator.GT:
            try:
                return float(field_value) > float(target_value)
            except:
                return False
        elif operator == FilterOperator.LT:
            try:
                return float(field_value) < float(target_value)
            except:
                return False
        elif operator == FilterOperator.GTE:
            try:
                return float(field_value) >= float(target_value)
            except:
                return False
        elif operator == FilterOperator.LTE:
            try:
                return float(field_value) <= float(target_value)
            except:
                return False
        elif operator == FilterOperator.CONTAINS:
            return str(target_value) in str(field_value)
        elif operator == FilterOperator.IN:
            return field_value in target_value
        elif operator == FilterOperator.NOT_IN:
            return field_value not in target_value
        elif operator == FilterOperator.BETWEEN:
            try:
                min_val, max_val = target_value
                return float(min_val) <= float(field_value) <= float(max_val)
            except:
                return False
        
        return False
    
    def create_chart(self, config: ChartConfig) -> AnalysisResult:
        """创建图表数据（不实际渲染，只是准备数据）"""
        try:
            filtered_data = self._apply_filters(config.filters)
            
            if not filtered_data:
                return AnalysisResult(success=False, error="没有符合条件的数据")
            
            chart_data = self._prepare_chart_data(filtered_data, config)
            
            insights = self._generate_insights(filtered_data, config)
            
            return AnalysisResult(
                success=True,
                data=chart_data,
                chart_config=config,
                insights=insights
            )
        except Exception as e:
            analysis_logger.error(f"创建图表失败: {e}")
            return AnalysisResult(success=False, error=str(e))
    
    def _prepare_chart_data(self, data: List[Dict], config: ChartConfig) -> Dict[str, Any]:
        """准备图表数据"""
        x_values = []
        y_values = []
        
        if config.group_by:
            return self._prepare_grouped_data(data, config)
        
        for row in data:
            x_values.append(row.get(config.x_field))
            
            if config.y_aggregation:
                y_values.append(row.get(config.y_field))
            else:
                y_values.append(row.get(config.y_field))
        
        if config.y_aggregation:
            y_values = [self._compute_aggregation(y_values, config.y_aggregation)]
            x_values = [config.y_field]
        
        if config.sort_by:
            combined = list(zip(x_values, y_values))
            reverse = not config.sort_ascending
            combined.sort(key=lambda x: x[0] if config.sort_by == config.x_field else x[1], reverse=reverse)
            x_values = [c[0] for c in combined]
            y_values = [c[1] for c in combined]
        
        if config.limit:
            x_values = x_values[:config.limit]
            y_values = y_values[:config.limit]
        
        return {
            "chart_type": config.chart_type.value,
            "x": x_values,
            "y": y_values,
            "title": config.title
        }
    
    def _prepare_grouped_data(self, data: List[Dict], config: ChartConfig) -> Dict[str, Any]:
        """准备分组数据"""
        groups = {}
        
        for row in data:
            group_key = row.get(config.group_by, 'unknown')
            if group_key not in groups:
                groups[group_key] = []
            
            x_val = row.get(config.x_field)
            y_val = row.get(config.y_field)
            groups[group_key].append((x_val, y_val))
        
        series_data = {}
        for group_name, values in groups.items():
            x_vals = [v[0] for v in values]
            y_vals = [v[1] for v in values]
            
            if config.y_aggregation:
                y_vals = [self._compute_aggregation(y_vals, config.y_aggregation)]
            
            series_data[group_name] = {
                "x": x_vals,
                "y": y_vals
            }
        
        return {
            "chart_type": config.chart_type.value,
            "grouped": True,
            "series": series_data,
            "title": config.title
        }
    
    def _generate_insights(self, data: List[Dict], config: ChartConfig) -> List[str]:
        """生成数据洞察"""
        insights = []
        
        try:
            insights.append(f"分析数据量: {len(data)} 条")
            
            if len(data) > 0:
                fields = list(data[0].keys())
                insights.append(f"可用字段: {', '.join(fields[:5])}{'...' if len(fields) > 5 else ''}")
            
            if config.y_field:
                stats = self.get_statistics(config.y_field)
                if stats.get('type') == 'numeric':
                    insights.append(f"{config.y_field} 平均值: {stats.get('avg', '-'):.2f}")
                    insights.append(f"{config.y_field} 最小值: {stats.get('min', '-')}")
                    insights.append(f"{config.y_field} 最大值: {stats.get('max', '-')}")
            
            if config.group_by:
                groups = set([row.get(config.group_by, 'unknown') for row in data])
                insights.append(f"分组数: {len(groups)} 个")
        
        except Exception as e:
            analysis_logger.debug(f"生成洞察失败: {e}")
        
        return insights
    
    def pivot_table(
        self,
        rows: List[str],
        cols: List[str],
        values_field: str,
        aggregation: AggregationType = AggregationType.SUM,
        filters: Optional[List[FilterCondition]] = None
    ) -> Dict[str, Any]:
        """创建数据透视表"""
        filtered_data = self._apply_filters(filters or [])
        
        pivot_data = {}
        
        for row in filtered_data:
            row_key = tuple([str(row.get(r, '')) for r in rows])
            col_key = tuple([str(row.get(c, '')) for c in cols])
            
            if row_key not in pivot_data:
                pivot_data[row_key] = {}
            
            if col_key not in pivot_data[row_key]:
                pivot_data[row_key][col_key] = []
            
            if values_field in row:
                pivot_data[row_key][col_key].append(row[values_field])
        
        result = {}
        for row_key, cols_data in pivot_data.items():
            result[row_key] = {}
            for col_key, values in cols_data.items():
                result[row_key][col_key] = self._compute_aggregation(values, aggregation)
        
        return {
            "rows": rows,
            "cols": cols,
            "values": values_field,
            "data": result
        }


def generate_chart_visualization(chart_data: Dict[str, Any]) -> Dict[str, Any]:
    """生成图表可视化配置（可用于前端渲染）"""
    chart_type = chart_data.get("chart_type", "bar")
    
    config = {
        "type": chart_type,
        "data": {},
        "options": {}
    }
    
    if chart_data.get("grouped", False):
        datasets = []
        colors = ['#3498db', '#2ecc71', '#e74c3c', '#f39c12', '#9b59b6', '#1abc9c']
        
        for i, (series_name, series) in enumerate(chart_data.get("series", {}).items()):
            datasets.append({
                "label": str(series_name),
                "data": series.get("y", []),
                "backgroundColor": colors[i % len(colors)],
                "borderColor": colors[i % len(colors)],
                "borderWidth": 1
            })
        
        config["data"] = {
            "labels": list(chart_data.get("series", {}).values())[0].get("x", []) if chart_data.get("series") else [],
            "datasets": datasets
        }
    else:
        config["data"] = {
            "labels": chart_data.get("x", []),
            "datasets": [{
                "label": chart_data.get("title", "Data"),
                "data": chart_data.get("y", []),
                "backgroundColor": "#3498db",
                "borderColor": "#3498db",
                "borderWidth": 1
            }]
        }
    
    config["options"] = {
        "responsive": True,
        "plugins": {
            "title": {
                "display": True,
                "text": chart_data.get("title", "Data Analysis")
            },
            "legend": {
                "display": len(config["data"].get("datasets", [])) > 1
            }
        }
    }
    
    return config


# 便捷函数
def create_analyzer(data: Optional[List[Dict]] = None) -> DataAnalyzer:
    """创建分析器"""
    return DataAnalyzer(data)


def analyze_data(data: List[Dict], field: str) -> Dict[str, Any]:
    """快速分析数据"""
    analyzer = create_analyzer(data)
    return analyzer.get_statistics(field)


__all__ = [
    "ChartType",
    "AggregationType",
    "FilterOperator",
    "FilterCondition",
    "ChartConfig",
    "AnalysisResult",
    "DataAnalyzer",
    "create_analyzer",
    "analyze_data",
    "generate_chart_visualization"
]
