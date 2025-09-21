"""
WebSocket 事件管理器 - 用於即時狀態更新
"""
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging

logger = logging.getLogger(__name__)

socketio = SocketIO(cors_allowed_origins="*", logger=True, engineio_logger=True)

# 存儲用戶連線和訂閱
user_connections = {}  # user_id -> set of session_ids
requisition_subscribers = {}  # requisition_id -> set of session_ids

@socketio.on('connect')
def handle_connect():
    """處理客戶端連線"""
    try:
        logger.info(f'Client connected: {request.sid}')
        emit('connection_status', {'status': 'connected', 'message': '已連接到即時更新服務'})
    except Exception as e:
        logger.error(f'Connection error: {e}')

@socketio.on('disconnect')
def handle_disconnect():
    """處理客戶端斷線"""
    try:
        logger.info(f'Client disconnected: {request.sid}')
        # 清理訂閱
        cleanup_subscriptions(request.sid)
    except Exception as e:
        logger.error(f'Disconnect error: {e}')

@socketio.on('authenticate')
@jwt_required()
def handle_authenticate(data):
    """處理用戶身份驗證"""
    try:
        user_id = get_jwt_identity()
        
        if user_id not in user_connections:
            user_connections[user_id] = set()
        user_connections[user_id].add(request.sid)
        
        join_room(f'user_{user_id}')
        logger.info(f'User {user_id} authenticated with session {request.sid}')
        
        emit('auth_status', {
            'authenticated': True, 
            'user_id': user_id,
            'message': f'用戶 {user_id} 身份驗證成功'
        })
        
    except Exception as e:
        logger.error(f'Authentication error: {e}')
        emit('auth_status', {'authenticated': False, 'error': str(e)})

@socketio.on('subscribe_requisition')
@jwt_required()
def handle_subscribe_requisition(data):
    """訂閱請購單狀態更新"""
    try:
        user_id = get_jwt_identity()
        requisition_id = data.get('requisition_id')
        
        if not requisition_id:
            emit('subscription_error', {'error': '缺少請購單ID'})
            return
            
        # 加入請購單房間
        room_name = f'requisition_{requisition_id}'
        join_room(room_name)
        
        # 記錄訂閱
        if requisition_id not in requisition_subscribers:
            requisition_subscribers[requisition_id] = set()
        requisition_subscribers[requisition_id].add(request.sid)
        
        logger.info(f'User {user_id} subscribed to requisition {requisition_id}')
        
        emit('subscription_status', {
            'subscribed': True,
            'requisition_id': requisition_id,
            'message': f'已訂閱請購單 {requisition_id} 的狀態更新'
        })
        
    except Exception as e:
        logger.error(f'Subscription error: {e}')
        emit('subscription_error', {'error': str(e)})

@socketio.on('unsubscribe_requisition')
def handle_unsubscribe_requisition(data):
    """取消訂閱請購單狀態更新"""
    try:
        requisition_id = data.get('requisition_id')
        
        if requisition_id:
            room_name = f'requisition_{requisition_id}'
            leave_room(room_name)
            
            # 移除訂閱記錄
            if requisition_id in requisition_subscribers:
                requisition_subscribers[requisition_id].discard(request.sid)
                if not requisition_subscribers[requisition_id]:
                    del requisition_subscribers[requisition_id]
            
            logger.info(f'Session {request.sid} unsubscribed from requisition {requisition_id}')
            
        emit('subscription_status', {
            'subscribed': False,
            'requisition_id': requisition_id,
            'message': f'已取消訂閱請購單 {requisition_id}'
        })
        
    except Exception as e:
        logger.error(f'Unsubscription error: {e}')

def cleanup_subscriptions(session_id):
    """清理斷線用戶的訂閱"""
    try:
        # 清理用戶連線記錄
        for user_id, sessions in user_connections.items():
            sessions.discard(session_id)
        user_connections = {k: v for k, v in user_connections.items() if v}
        
        # 清理請購單訂閱記錄
        for req_id, sessions in requisition_subscribers.items():
            sessions.discard(session_id)
        requisition_subscribers = {k: v for k, v in requisition_subscribers.items() if v}
        
    except Exception as e:
        logger.error(f'Cleanup error: {e}')

# 廣播函數 - 供其他模組使用
def broadcast_requisition_status_change(requisition_id, old_status, new_status, data=None):
    """廣播請購單狀態變更"""
    try:
        room_name = f'requisition_{requisition_id}'
        
        message_data = {
            'event': 'requisition_status_changed',
            'requisition_id': requisition_id,
            'old_status': old_status,
            'new_status': new_status,
            'timestamp': datetime.utcnow().isoformat(),
            'data': data or {}
        }
        
        logger.info(f'Broadcasting status change for requisition {requisition_id}: {old_status} -> {new_status}')
        socketio.emit('requisition_status_changed', message_data, room=room_name)
        
        return True
        
    except Exception as e:
        logger.error(f'Broadcast error: {e}')
        return False

def broadcast_requisition_item_change(requisition_id, item_id, old_status, new_status, data=None):
    """廣播請購單項目狀態變更"""
    try:
        room_name = f'requisition_{requisition_id}'
        
        message_data = {
            'event': 'requisition_item_changed',
            'requisition_id': requisition_id,
            'item_id': item_id,
            'old_status': old_status,
            'new_status': new_status,
            'timestamp': datetime.utcnow().isoformat(),
            'data': data or {}
        }
        
        logger.info(f'Broadcasting item change for requisition {requisition_id}, item {item_id}: {old_status} -> {new_status}')
        socketio.emit('requisition_item_changed', message_data, room=room_name)
        
        return True
        
    except Exception as e:
        logger.error(f'Item broadcast error: {e}')
        return False

def broadcast_user_notification(user_id, notification_type, message, data=None):
    """向特定用戶廣播通知"""
    try:
        room_name = f'user_{user_id}'
        
        message_data = {
            'event': 'user_notification',
            'type': notification_type,
            'message': message,
            'timestamp': datetime.utcnow().isoformat(),
            'data': data or {}
        }
        
        logger.info(f'Broadcasting notification to user {user_id}: {notification_type}')
        socketio.emit('user_notification', message_data, room=room_name)
        
        return True
        
    except Exception as e:
        logger.error(f'User notification error: {e}')
        return False

# 導入必要模組
from datetime import datetime
from flask import request