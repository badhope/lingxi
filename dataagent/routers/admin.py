"""
DataAgent - 综合管理 API
集成所有管理功能的统一接口
"""
from fastapi import APIRouter, HTTPException, Body, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import json

from core.logging import get_logger
from core.plugin_manager import (
    get_enhanced_plugin_manager,
    PluginType
)
from core.config_manager import (
    get_enhanced_config_manager,
    ConfigSource
)
from core.cache import get_cache_manager
from core.notifications import get_notification_manager, NotificationType
from core.docs import get_docs_manager

logger = get_logger("admin_api")

router = APIRouter()


# ========== 配置管理 ==========

class ConfigUpdate(BaseModel):
    """配置更新"""
    key: str
    value: Any
    save: bool = True


@router.get("/config")
async def list_configs(
    prefix: Optional[str] = None,
    include_details: bool = True
):
    """列出配置"""
    try:
        config_manager = get_enhanced_config_manager()
        configs = config_manager.list_configs(prefix)
        
        if include_details:
            result = [
                {
                    'key': c.key,
                    'value': c.value,
                    'source': c.source.value,
                    'default': c.default,
                    'type': c.type_hint,
                    'description': c.description
                }
                for c in configs
            ]
        else:
            result = config_manager.export_dict(prefix)
        
        return {
            'success': True,
            'data': result
        }
        
    except Exception as e:
        logger.error(f"列出配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config/{key}")
async def get_config(key: str):
    """获取单个配置"""
    try:
        config_manager = get_enhanced_config_manager()
        
        if not config_manager.has(key):
            raise HTTPException(status_code=404, detail="配置不存在")
        
        option = config_manager._configs[key]
        
        return {
            'success': True,
            'data': {
                'key': option.key,
                'value': option.value,
                'source': option.source.value,
                'default': option.default,
                'type': option.type_hint
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/config")
async def set_config(update: ConfigUpdate):
    """设置配置"""
    try:
        config_manager = get_enhanced_config_manager()
        config_manager.set(
            update.key,
            update.value,
            source=ConfigSource.FILE,
            save=update.save
        )
        
        return {
            'success': True,
            'message': '配置已更新'
        }
        
    except Exception as e:
        logger.error(f"设置配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/config/reload")
async def reload_config():
    """重新加载配置"""
    try:
        config_manager = get_enhanced_config_manager()
        config_manager.reload()
        
        return {
            'success': True,
            'message': '配置已重新加载'
        }
        
    except Exception as e:
        logger.error(f"重新加载配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config/stats")
async def get_config_stats():
    """获取配置统计"""
    try:
        config_manager = get_enhanced_config_manager()
        
        return {
            'success': True,
            'data': config_manager.get_stats()
        }
        
    except Exception as e:
        logger.error(f"获取配置统计失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== 插件管理 ==========

@router.get("/plugins")
async def list_plugins(
    type: Optional[PluginType] = None,
    loaded_only: bool = False
):
    """列出插件"""
    try:
        plugin_manager = get_enhanced_plugin_manager()
        plugins = plugin_manager.list_plugins(loaded_only)
        
        if type:
            plugins = [p for p in plugins if p.metadata.type == type]
        
        result = [
            {
                'id': p.metadata.id,
                'name': p.metadata.name,
                'description': p.metadata.description,
                'version': p.metadata.version,
                'author': p.metadata.author,
                'type': p.metadata.type.value,
                'loaded': p.loaded,
                'path': p.path,
                'error': p.error_message
            }
            for p in plugins
        ]
        
        return {
            'success': True,
            'data': result
        }
        
    except Exception as e:
        logger.error(f"列出插件失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/plugins/discover")
async def discover_plugins():
    """发现插件"""
    try:
        plugin_manager = get_enhanced_plugin_manager()
        discovered = plugin_manager.discover_plugins()
        
        return {
            'success': True,
            'data': {
                'count': len(discovered),
                'plugins': [
                    {
                        'id': d.id,
                        'name': d.name,
                        'type': d.type.value
                    }
                    for d in discovered
                ]
            }
        }
        
    except Exception as e:
        logger.error(f"发现插件失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/plugins/{plugin_id}/load")
async def load_plugin(plugin_id: str, config: Optional[Dict] = Body(None)):
    """加载插件"""
    try:
        plugin_manager = get_enhanced_plugin_manager()
        success = await plugin_manager.load_plugin(plugin_id, config)
        
        if success:
            return {
                'success': True,
                'message': '插件已加载'
            }
        else:
            raise HTTPException(status_code=400, detail='插件加载失败')
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"加载插件失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/plugins/{plugin_id}/unload")
async def unload_plugin(plugin_id: str):
    """卸载插件"""
    try:
        plugin_manager = get_enhanced_plugin_manager()
        success = await plugin_manager.unload_plugin(plugin_id)
        
        if success:
            return {
                'success': True,
                'message': '插件已卸载'
            }
        else:
            raise HTTPException(status_code=400, detail='插件卸载失败')
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"卸载插件失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/plugins/{plugin_id}/reload")
async def reload_plugin(plugin_id: str):
    """重新加载插件"""
    try:
        plugin_manager = get_enhanced_plugin_manager()
        success = await plugin_manager.reload_plugin(plugin_id)
        
        if success:
            return {
                'success': True,
                'message': '插件已重新加载'
            }
        else:
            raise HTTPException(status_code=400, detail='插件重新加载失败')
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"重新加载插件失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/plugins/load-all")
async def load_all_plugins():
    """加载所有插件"""
    try:
        plugin_manager = get_enhanced_plugin_manager()
        results = await plugin_manager.load_all_plugins()
        
        return {
            'success': True,
            'data': {
                'results': results,
                'success_count': sum(1 for s in results.values() if s),
                'total_count': len(results)
            }
        }
        
    except Exception as e:
        logger.error(f"加载所有插件失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/plugins/stats")
async def get_plugin_stats():
    """获取插件统计"""
    try:
        plugin_manager = get_enhanced_plugin_manager()
        
        return {
            'success': True,
            'data': plugin_manager.get_stats()
        }
        
    except Exception as e:
        logger.error(f"获取插件统计失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== 缓存管理 ==========

@router.get("/cache")
async def get_cache_stats():
    """获取缓存统计"""
    try:
        cache_manager = get_cache_manager()
        
        return {
            'success': True,
            'data': cache_manager.get_stats()
        }
        
    except Exception as e:
        logger.error(f"获取缓存统计失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/cache/memory")
async def clear_memory_cache():
    """清空内存缓存"""
    try:
        cache_manager = get_cache_manager()
        cache_manager.clear_memory()
        
        return {
            'success': True,
            'message': '内存缓存已清空'
        }
        
    except Exception as e:
        logger.error(f"清空内存缓存失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/cache/files")
async def clear_file_cache():
    """清空文件缓存"""
    try:
        cache_manager = get_cache_manager()
        count = cache_manager.clear_files()
        
        return {
            'success': True,
            'message': f'已清空 {count} 个文件缓存'
        }
        
    except Exception as e:
        logger.error(f"清空文件缓存失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/cache/expired")
async def clear_expired_cache():
    """清空过期缓存"""
    try:
        cache_manager = get_cache_manager()
        count = cache_manager.clear_expired()
        
        return {
            'success': True,
            'message': f'已清空 {count} 个过期缓存'
        }
        
    except Exception as e:
        logger.error(f"清空过期缓存失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cache/{key}")
async def get_cache_value(key: str):
    """获取缓存值"""
    try:
        cache_manager = get_cache_manager()
        value = cache_manager.get_multi(key)
        
        return {
            'success': True,
            'data': {
                'key': key,
                'value': value
            }
        }
        
    except Exception as e:
        logger.error(f"获取缓存值失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== 通知管理 ==========

@router.get("/notifications")
async def list_notifications(
    unread_only: bool = False,
    limit: int = 50
):
    """列出通知"""
    try:
        notif_manager = get_notification_manager()
        notifs = notif_manager.get(
            unread_only=unread_only,
            limit=limit
        )
        
        return {
            'success': True,
            'data': notifs
        }
        
    except Exception as e:
        logger.error(f"列出通知失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/notifications/unread/count")
async def get_unread_count():
    """获取未读通知数量"""
    try:
        notif_manager = get_notification_manager()
        
        return {
            'success': True,
            'data': {
                'count': notif_manager.get_unread_count()
            }
        }
        
    except Exception as e:
        logger.error(f"获取未读通知数量失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: str):
    """标记通知为已读"""
    try:
        notif_manager = get_notification_manager()
        success = notif_manager.mark_read(notification_id)
        
        if success:
            return {
                'success': True,
                'message': '通知已标记为已读'
            }
        else:
            raise HTTPException(status_code=404, detail='通知不存在')
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"标记通知为已读失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/notifications/read-all")
async def mark_all_read():
    """标记所有通知为已读"""
    try:
        notif_manager = get_notification_manager()
        notif_manager.mark_all_read()
        
        return {
            'success': True,
            'message': '所有通知已标记为已读'
        }
        
    except Exception as e:
        logger.error(f"标记所有通知为已读失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/notifications/{notification_id}")
async def delete_notification(notification_id: str):
    """删除通知"""
    try:
        notif_manager = get_notification_manager()
        success = notif_manager.delete(notification_id)
        
        if success:
            return {
                'success': True,
                'message': '通知已删除'
            }
        else:
            raise HTTPException(status_code=404, detail='通知不存在')
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除通知失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/notifications")
async def clear_all_notifications():
    """清空所有通知"""
    try:
        notif_manager = get_notification_manager()
        notif_manager.clear_all()
        
        return {
            'success': True,
            'message': '所有通知已清空'
        }
        
    except Exception as e:
        logger.error(f"清空所有通知失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class SimpleNotification(BaseModel):
    """简单通知"""
    title: str
    message: str


@router.post("/notifications/{type}")
async def send_notification(type: NotificationType, notification: SimpleNotification):
    """发送通知"""
    try:
        notif_manager = get_notification_manager()
        
        if type == NotificationType.INFO:
            notif_id = notif_manager.info(notification.title, notification.message)
        elif type == NotificationType.SUCCESS:
            notif_id = notif_manager.success(notification.title, notification.message)
        elif type == NotificationType.WARNING:
            notif_id = notif_manager.warning(notification.title, notification.message)
        elif type == NotificationType.ERROR:
            notif_id = notif_manager.error(notification.title, notification.message)
        else:
            notif_id = notif_manager.send(
                notification.title,
                notification.message,
                type=type
            )
        
        return {
            'success': True,
            'data': {
                'notification_id': notif_id
            }
        }
        
    except Exception as e:
        logger.error(f"发送通知失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== 文档管理 ==========

@router.get("/docs")
async def list_docs(category: Optional[str] = None):
    """列出文档"""
    try:
        docs_manager = get_docs_manager()
        docs = docs_manager.list_docs(category)
        
        return {
            'success': True,
            'data': docs
        }
        
    except Exception as e:
        logger.error(f"列出文档失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/docs/search")
async def search_docs(query: str):
    """搜索文档"""
    try:
        docs_manager = get_docs_manager()
        results = docs_manager.search_docs(query)
        
        return {
            'success': True,
            'data': results
        }
        
    except Exception as e:
        logger.error(f"搜索文档失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/docs/{category}/{doc_id}")
async def get_doc(category: str, doc_id: str):
    """获取文档内容"""
    try:
        docs_manager = get_docs_manager()
        doc = docs_manager.get_doc(doc_id, category)
        
        if not doc:
            raise HTTPException(status_code=404, detail='文档不存在')
        
        return {
            'success': True,
            'data': doc
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取文档失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/docs/quickstart")
async def get_quickstart():
    """获取快速开始指南"""
    try:
        docs_manager = get_docs_manager()
        doc = docs_manager.get_quickstart()
        
        if not doc:
            raise HTTPException(status_code=404, detail='快速开始指南不存在')
        
        return {
            'success': True,
            'data': doc
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取快速开始指南失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== 综合状态 ==========

@router.get("/status")
async def get_system_status():
    """获取系统综合状态"""
    try:
        config_manager = get_enhanced_config_manager()
        plugin_manager = get_enhanced_plugin_manager()
        cache_manager = get_cache_manager()
        notif_manager = get_notification_manager()
        
        return {
            'success': True,
            'data': {
                'config': config_manager.get_stats(),
                'plugins': plugin_manager.get_stats(),
                'cache': cache_manager.get_stats(),
                'notifications': {
                    'unread_count': notif_manager.get_unread_count()
                }
            }
        }
        
    except Exception as e:
        logger.error(f"获取系统状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
