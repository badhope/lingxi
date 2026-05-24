"""
DataAgent - 数据分析路由
提供数据处理、统计分析和可视化功能
"""
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from typing import List, Optional

from core import (
    DataAnalyzer,
    ChartType,
    ChartConfig,
    AggregationType,
    FilterOperator,
    FilterCondition,
    create_analyzer,
    analyze_data,
    generate_chart_visualization,
    get_logger
)

router = APIRouter()
logger = get_logger("data_analysis_api")


@router.get("/api/analysis/chart-types")
async def get_chart_types():
    """获取支持的图表类型"""
    return JSONResponse({
        "success": True,
        "chart_types": [
            {
                "id": ct.value,
                "name": ct.value.upper(),
                "description": f"{ct.value} 图表"
            }
            for ct in ChartType
        ]
    })


@router.get("/api/analysis/aggregation-types")
async def get_aggregation_types():
    """获取支持的聚合类型"""
    return JSONResponse({
        "success": True,
        "aggregation_types": [
            {
                "id": at.value,
                "name": at.value.upper(),
                "description": _get_aggregation_description(at)
            }
            for at in AggregationType
        ]
    })


def _get_aggregation_description(at: AggregationType) -> str:
    """获取聚合类型描述"""
    descriptions = {
        AggregationType.SUM: "求和",
        AggregationType.AVG: "平均值",
        AggregationType.COUNT: "计数",
        AggregationType.MIN: "最小值",
        AggregationType.MAX: "最大值",
        AggregationType.MEDIAN: "中位数",
        AggregationType.STD: "标准差",
        AggregationType.VAR: "方差"
    }
    return descriptions.get(at, "未知")


@router.post("/api/analysis/analyze")
async def analyze_field(request: Request):
    """分析指定字段"""
    data = await request.json()
    
    if "data" not in data or "field" not in data:
        raise HTTPException(status_code=400, detail="需要提供 data 和 field 参数")
    
    try:
        analyzer = create_analyzer(data["data"])
        stats = analyzer.get_statistics(data["field"])
        
        return JSONResponse({
            "success": True,
            "statistics": stats
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")


@router.post("/api/analysis/aggregate")
async def aggregate_data(request: Request):
    """聚合数据"""
    data = await request.json()
    
    required_fields = ["data", "field", "aggregation"]
    for field in required_fields:
        if field not in data:
            raise HTTPException(status_code=400, detail=f"需要提供 {field} 参数")
    
    try:
        analyzer = create_analyzer(data["data"])
        
        agg_type = AggregationType(data["aggregation"])
        group_by = data.get("group_by")
        
        result = analyzer.aggregate(
            field=data["field"],
            aggregation_type=agg_type,
            group_by=group_by
        )
        
        return JSONResponse({
            "success": True,
            "result": result
        })
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"参数错误: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"聚合失败: {str(e)}")


@router.post("/api/analysis/chart")
async def create_chart(request: Request):
    """创建图表"""
    data = await request.json()
    
    required_fields = ["title", "chart_type", "x_field", "y_field"]
    for field in required_fields:
        if field not in data:
            raise HTTPException(status_code=400, detail=f"需要提供 {field} 参数")
    
    try:
        analyzer = create_analyzer(data.get("data", []))
        
        chart_config = ChartConfig(
            title=data["title"],
            chart_type=ChartType(data["chart_type"]),
            x_field=data["x_field"],
            y_field=data["y_field"],
            y_aggregation=AggregationType(data["aggregation"]) if data.get("aggregation") else None,
            group_by=data.get("group_by"),
            limit=data.get("limit")
        )
        
        chart_result = analyzer.create_chart(chart_config)
        
        if not chart_result.success:
            raise HTTPException(status_code=400, detail=chart_result.error)
        
        # 生成前端可视化配置
        visualization_config = generate_chart_visualization(chart_result.data)
        
        return JSONResponse({
            "success": True,
            "chart_data": chart_result.data,
            "visualization": visualization_config,
            "insights": chart_result.insights
        })
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"参数错误: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建图表失败: {str(e)}")


@router.post("/api/analysis/pivot")
async def create_pivot_table(request: Request):
    """创建数据透视表"""
    data = await request.json()
    
    required_fields = ["data", "rows", "cols", "values_field"]
    for field in required_fields:
        if field not in data:
            raise HTTPException(status_code=400, detail=f"需要提供 {field} 参数")
    
    try:
        analyzer = create_analyzer(data["data"])
        
        agg_type = AggregationType(data.get("aggregation", "sum"))
        
        pivot_result = analyzer.pivot_table(
            rows=data["rows"],
            cols=data["cols"],
            values_field=data["values_field"],
            aggregation=agg_type
        )
        
        return JSONResponse({
            "success": True,
            "pivot_table": pivot_result
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建透视表失败: {str(e)}")


@router.post("/api/analysis/fields")
async def get_fields(request: Request):
    """获取数据字段信息"""
    data = await request.json()
    
    if "data" not in data:
        raise HTTPException(status_code=400, detail="需要提供 data 参数")
    
    try:
        analyzer = create_analyzer(data["data"])
        fields = analyzer.get_fields()
        
        # 获取每个字段的统计信息
        field_info = []
        for field in fields:
            stats = analyzer.get_statistics(field)
            field_info.append({
                "name": field,
                "type": stats.get("type", "unknown"),
                "statistics": stats
            })
        
        return JSONResponse({
            "success": True,
            "fields": fields,
            "field_info": field_info
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取字段信息失败: {str(e)}")
