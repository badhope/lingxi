"""
DataAgent - WebSocket 实时通讯 API 路由
提供聊天、通知、任务进度等实时推送
"""
import json
from typing import Dict, Any, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends, status

from core.logging import get_logger
from core.websocket import (
    get_websocket_manager,
    WebSocketManager,
    MessageType
)
from core.notifications import get_notification_manager

logger = get_logger("websocket_router")

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: Optional[str] = Query(None, description="用户 ID")
):
    """WebSocket 连接端点"""
    ws_manager = get_websocket_manager()
    
    await websocket.accept()
    
    # 注册连接
    connection_id = ws_manager.register_connection(websocket, user_id)
    
    try:
        # 发送连接确认
        connected_msg = ws_manager.create_message(
            MessageType.CONNECTED,
            {
                "connection_id": connection_id,
                "user_id": user_id
            }
        )
        await websocket.send_json(connected_msg)
        
        # 消息处理循环
        while True:
            try:
                data = await websocket.receive_json()
                
                # 处理消息
                await ws_manager.handle_message(connection_id, data)
                
                # 根据消息类型处理
                msg_type = data.get("type")
                action = data.get("action")
                
                # 订阅/取消订阅频道
                if msg_type == "channel":
                    if action == "subscribe" and "channel" in data:
                        ws_manager.subscribe_to_channel(connection_id, data["channel"])
                    elif action == "unsubscribe" and "channel" in data:
                        ws_manager.unsubscribe_from_channel(connection_id, data["channel"])
                
                # 回显确认
                await websocket.send_json({
                    "id": data.get("id"),
                    "type": "ack",
                    "timestamp": __import__("time").time()
                })
                
            except WebSocketDisconnect:
                logger.info(f"WebSocket 断开: {connection_id}")
                break
            except ValueError as e:
                logger.warning(f"WebSocket 接收无效 JSON: {e}")
                error_msg = ws_manager.create_message(
                    MessageType.ERROR,
                    {"error": "Invalid JSON format"}
                )
                await websocket.send_json(error_msg)
            except Exception as e:
                logger.error(f"WebSocket 处理错误: {e}", exc_info=True)
                error_msg = ws_manager.create_message(
                    MessageType.ERROR,
                    {"error": str(e)}
                )
                await websocket.send_json(error_msg)
    
    finally:
        # 清理连接
        await ws_manager.remove_connection(connection_id)


@router.websocket("/ws/notifications")
async def notification_websocket(
    websocket: WebSocket,
    user_id: Optional[str] = Query(None)
):
    """通知专用 WebSocket 端点"""
    ws_manager = get_websocket_manager()
    
    await websocket.accept()
    connection_id = ws_manager.register_connection(websocket, user_id)
    
    try:
        # 订阅通知频道
        ws_manager.subscribe_to_channel(connection_id, "notifications")
        
        # 发送当前未读通知
        notif_manager = get_notification_manager()
        unread_notifs = notif_manager.get(unread_only=True)
        
        if unread_notifs:
            for notif in unread_notifs:
                await websocket.send_json(
                    ws_manager.create_notification(
                        notif["title"],
                        notif["message"],
                        notif["type"]
                    )
                )
        
        # 消息循环
        while True:
            try:
                data = await websocket.receive_json()
                
                # 处理通知标记
                if data.get("type") == "mark_read" and "notification_id" in data:
                    notif_manager.mark_read(data["notification_id"])
                
                await websocket.send_json({"type": "ack"})
                
            except WebSocketDisconnect:
                break
    
    finally:
        await ws_manager.remove_connection(connection_id)


@router.websocket("/ws/tasks/{task_id}")
async def task_websocket(
    websocket: WebSocket,
    task_id: str,
    user_id: Optional[str] = Query(None)
):
    """任务进度专用 WebSocket 端点"""
    ws_manager = get_websocket_manager()
    
    await websocket.accept()
    connection_id = ws_manager.register_connection(websocket, user_id)
    
    try:
        # 订阅任务频道
        channel = f"task_{task_id}"
        ws_manager.subscribe_to_channel(connection_id, channel)
        
        logger.info(f"WebSocket 连接到任务: {task_id}")
        
        # 消息循环
        while True:
            try:
                data = await websocket.receive_json()
                await websocket.send_json({"type": "ack"})
                
            except WebSocketDisconnect:
                break
    
    finally:
        await ws_manager.remove_connection(connection_id)


@router.post("/api/ws/broadcast")
async def broadcast_message(
    message: Dict[str, Any]
):
    """广播消息给所有连接"""
    ws_manager = get_websocket_manager()
    
    msg_type = message.get("type", "notification")
    msg_data = message.get("data", {})
    
    try:
        message_type = MessageType(msg_type)
        msg = ws_manager.create_message(message_type, msg_data)
        
        await ws_manager.broadcast(msg)
        
        return {
            "success": True,
            "connection_count": len(ws_manager.connections)
        }
    except Exception as e:
        logger.error(f"广播消息失败: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@router.post("/api/ws/user/{user_id}/send")
async def send_to_user(
    user_id: str,
    message: Dict[str, Any]
):
    """发送消息给指定用户"""
    ws_manager = get_websocket_manager()
    
    msg_type = message.get("type", "notification")
    msg_data = message.get("data", {})
    
    try:
        message_type = MessageType(msg_type)
        msg = ws_manager.create_message(message_type, msg_data)
        
        sent_count = await ws_manager.send_to_user(user_id, msg)
        
        return {
            "success": True,
            "sent_count": sent_count
        }
    except Exception as e:
        logger.error(f"发送用户消息失败: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@router.post("/api/ws/channel/{channel}/send")
async def send_to_channel(
    channel: str,
    message: Dict[str, Any]
):
    """发送消息给频道订阅者"""
    ws_manager = get_websocket_manager()
    
    msg_type = message.get("type", "notification")
    msg_data = message.get("data", {})
    
    try:
        message_type = MessageType(msg_type)
        msg = ws_manager.create_message(message_type, msg_data)
        
        sent_count = await ws_manager.send_to_channel(channel, msg)
        
        return {
            "success": True,
            "sent_count": sent_count
        }
    except Exception as e:
        logger.error(f"发送频道消息失败: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/api/ws/status")
async def get_websocket_status():
    """获取 WebSocket 状态"""
    ws_manager = get_websocket_manager()
    status = ws_manager.get_status()
    
    return {
        "success": True,
        "data": status
    }
