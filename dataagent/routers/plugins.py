"""
DataAgent - 插件系统API路由
提供插件管理和调用的API接口
"""
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from typing import Any, Dict, List, Optional

from core.logging import get_logger
from core.plugins import (
    PluginType,
    PluginStatus,
    plugin_manager,
)

router = APIRouter()
logger = get_logger("plugins_api")


@router.get("/api/plugins")
async def list_plugins(plugin_type: Optional[str] = None):
    """列出所有插件"""
    try:
        type_enum = None
        if plugin_type:
            try:
                type_enum = PluginType(plugin_type)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid plugin type: {plugin_type}")
        
        plugins = plugin_manager.list_plugins(type_enum)
        
        return JSONResponse({
            "success": True,
            "count": len(plugins),
            "plugins": plugins,
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/plugins/{plugin_id}")
async def get_plugin(plugin_id: str):
    """获取插件详情"""
    plugin = plugin_manager.get_plugin(plugin_id)
    
    if not plugin:
        raise HTTPException(status_code=404, detail=f"Plugin not found: {plugin_id}")
    
    return JSONResponse({
        "success": True,
        "plugin": plugin.get_info(),
    })


@router.post("/api/plugins/{plugin_id}/enable")
async def enable_plugin(plugin_id: str):
    """启用插件"""
    plugin = plugin_manager.get_plugin(plugin_id)
    
    if not plugin:
        raise HTTPException(status_code=404, detail=f"Plugin not found: {plugin_id}")
    
    plugin_manager.enable_plugin(plugin_id)
    
    return JSONResponse({
        "success": True,
        "message": f"Plugin enabled: {plugin_id}",
    })


@router.post("/api/plugins/{plugin_id}/disable")
async def disable_plugin(plugin_id: str):
    """禁用插件"""
    plugin = plugin_manager.get_plugin(plugin_id)
    
    if not plugin:
        raise HTTPException(status_code=404, detail=f"Plugin not found: {plugin_id}")
    
    plugin_manager.disable_plugin(plugin_id)
    
    return JSONResponse({
        "success": True,
        "message": f"Plugin disabled: {plugin_id}",
    })


@router.post("/api/plugins/{plugin_id}/execute")
async def execute_plugin(plugin_id: str, request: Request):
    """执行插件功能"""
    plugin = plugin_manager.get_plugin(plugin_id)
    
    if not plugin:
        raise HTTPException(status_code=404, detail=f"Plugin not found: {plugin_id}")
    
    if not plugin.config.enabled:
        raise HTTPException(status_code=400, detail=f"Plugin is disabled: {plugin_id}")
    
    try:
        data = await request.json()
        
        result = await plugin.execute(**data)
        
        return JSONResponse({
            "success": True,
            "plugin_id": plugin_id,
            "result": result,
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/plugins/{plugin_id}/config")
async def set_plugin_config(plugin_id: str, request: Request):
    """设置插件配置"""
    plugin = plugin_manager.get_plugin(plugin_id)
    
    if not plugin:
        raise HTTPException(status_code=404, detail=f"Plugin not found: {plugin_id}")
    
    try:
        data = await request.json()
        
        plugin_manager.set_plugin_config(plugin_id, data.get("settings", {}))
        
        return JSONResponse({
            "success": True,
            "message": f"Plugin config updated: {plugin_id}",
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/plugins/save-state")
async def save_plugin_state():
    """保存插件状态"""
    try:
        plugin_manager.save_state()
        
        return JSONResponse({
            "success": True,
            "message": "Plugin state saved",
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/plugins/load-state")
async def load_plugin_state():
    """加载插件状态"""
    try:
        plugin_manager.load_state()
        
        return JSONResponse({
            "success": True,
            "message": "Plugin state loaded",
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/plugins/{plugin_id}/tools")
async def list_plugin_tools(plugin_id: str):
    """列出工具插件的可用工具"""
    from core.plugins import ToolPlugin
    
    plugin = plugin_manager.get_plugin(plugin_id)
    
    if not plugin:
        raise HTTPException(status_code=404, detail=f"Plugin not found: {plugin_id}")
    
    if not isinstance(plugin, ToolPlugin):
        raise HTTPException(status_code=400, detail=f"Plugin is not a tool plugin: {plugin_id}")
    
    return JSONResponse({
        "success": True,
        "plugin_id": plugin_id,
        "tools": plugin.list_tools(),
    })


@router.post("/api/plugins/{plugin_id}/tools/{tool_name}")
async def execute_tool(plugin_id: str, tool_name: str, request: Request):
    """执行工具插件的特定工具"""
    from core.plugins import ToolPlugin
    
    plugin = plugin_manager.get_plugin(plugin_id)
    
    if not plugin:
        raise HTTPException(status_code=404, detail=f"Plugin not found: {plugin_id}")
    
    if not isinstance(plugin, ToolPlugin):
        raise HTTPException(status_code=400, detail=f"Plugin is not a tool plugin: {plugin_id}")
    
    try:
        data = await request.json()
        
        result = await plugin.execute_tool(tool_name, **data)
        
        return JSONResponse({
            "success": True,
            "plugin_id": plugin_id,
            "tool_name": tool_name,
            "result": result,
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/plugins/{plugin_id}/analytics")
async def list_plugin_analytics(plugin_id: str):
    """列出分析插件的可用分析"""
    from core.plugins import AnalyticsPlugin
    
    plugin = plugin_manager.get_plugin(plugin_id)
    
    if not plugin:
        raise HTTPException(status_code=404, detail=f"Plugin not found: {plugin_id}")
    
    if not isinstance(plugin, AnalyticsPlugin):
        raise HTTPException(status_code=400, detail=f"Plugin is not an analytics plugin: {plugin_id}")
    
    return JSONResponse({
        "success": True,
        "plugin_id": plugin_id,
        "analytics": plugin.list_analytics(),
    })


@router.post("/api/plugins/{plugin_id}/analytics/{analysis_name}")
async def run_analysis(plugin_id: str, analysis_name: str, request: Request):
    """执行分析插件的特定分析"""
    from core.plugins import AnalyticsPlugin
    
    plugin = plugin_manager.get_plugin(plugin_id)
    
    if not plugin:
        raise HTTPException(status_code=404, detail=f"Plugin not found: {plugin_id}")
    
    if not isinstance(plugin, AnalyticsPlugin):
        raise HTTPException(status_code=400, detail=f"Plugin is not an analytics plugin: {plugin_id}")
    
    try:
        data = await request.json()
        
        result = await plugin.run_analysis(analysis_name, data.get("data", []), **data.get("params", {}))
        
        return JSONResponse({
            "success": True,
            "plugin_id": plugin_id,
            "analysis_name": analysis_name,
            "result": result,
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/plugins/{plugin_id}/visualizations")
async def list_plugin_visualizations(plugin_id: str):
    """列出可视化插件的可用可视化"""
    from core.plugins import VisualizationPlugin
    
    plugin = plugin_manager.get_plugin(plugin_id)
    
    if not plugin:
        raise HTTPException(status_code=404, detail=f"Plugin not found: {plugin_id}")
    
    if not isinstance(plugin, VisualizationPlugin):
        raise HTTPException(status_code=400, detail=f"Plugin is not a visualization plugin: {plugin_id}")
    
    return JSONResponse({
        "success": True,
        "plugin_id": plugin_id,
        "visualizations": plugin.list_visualizations(),
    })


@router.post("/api/plugins/{plugin_id}/visualizations/{viz_name}")
async def generate_visualization(plugin_id: str, viz_name: str, request: Request):
    """执行可视化插件的特定可视化"""
    from core.plugins import VisualizationPlugin
    
    plugin = plugin_manager.get_plugin(plugin_id)
    
    if not plugin:
        raise HTTPException(status_code=404, detail=f"Plugin not found: {plugin_id}")
    
    if not isinstance(plugin, VisualizationPlugin):
        raise HTTPException(status_code=400, detail=f"Plugin is not a visualization plugin: {plugin_id}")
    
    try:
        data = await request.json()
        
        result = await plugin.generate_visualization(viz_name, data.get("data", []), **data.get("params", {}))
        
        return JSONResponse({
            "success": True,
            "plugin_id": plugin_id,
            "visualization_name": viz_name,
            "result": result,
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/plugins/{plugin_id}/data-sources")
async def list_plugin_data_sources(plugin_id: str):
    """列出数据源插件的可用数据源"""
    from core.plugins import DataSourcePlugin
    
    plugin = plugin_manager.get_plugin(plugin_id)
    
    if not plugin:
        raise HTTPException(status_code=404, detail=f"Plugin not found: {plugin_id}")
    
    if not isinstance(plugin, DataSourcePlugin):
        raise HTTPException(status_code=400, detail=f"Plugin is not a data source plugin: {plugin_id}")
    
    return JSONResponse({
        "success": True,
        "plugin_id": plugin_id,
        "data_sources": plugin.list_data_sources(),
    })


@router.post("/api/plugins/{plugin_id}/data-sources/{source_name}")
async def fetch_data(plugin_id: str, source_name: str, request: Request):
    """从数据源插件获取数据"""
    from core.plugins import DataSourcePlugin
    
    plugin = plugin_manager.get_plugin(plugin_id)
    
    if not plugin:
        raise HTTPException(status_code=404, detail=f"Plugin not found: {plugin_id}")
    
    if not isinstance(plugin, DataSourcePlugin):
        raise HTTPException(status_code=400, detail=f"Plugin is not a data source plugin: {plugin_id}")
    
    try:
        data = await request.json()
        
        result = await plugin.fetch_data(source_name, **data.get("params", {}))
        
        return JSONResponse({
            "success": True,
            "plugin_id": plugin_id,
            "data_source": source_name,
            "result": result,
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/plugin-types")
async def get_plugin_types():
    """获取所有插件类型"""
    return JSONResponse({
        "success": True,
        "types": [
            {
                "id": t.value,
                "name": t.value.capitalize(),
                "description": f"{t.value} plugin",
            }
            for t in PluginType
        ],
    })


@router.get("/api/plugin-statuses")
async def get_plugin_statuses():
    """获取所有插件状态"""
    return JSONResponse({
        "success": True,
        "statuses": [
            {
                "id": s.value,
                "name": s.value.capitalize(),
            }
            for s in PluginStatus
        ],
    })
