# -*- coding: utf-8 -*-
"""
消息管理API路由模块
"""
from flask import request, jsonify, g
from . import api_bp
from tools.auth_middleware import auth_required, permission_required
from tools.exceptions import (
    ValidationException,
    BusinessException,
    ResourceNotFoundException,
    handle_exception,
    create_error_response
)
import logging

logger = logging.getLogger(__name__)

@api_bp.route('/message', methods=['GET'])
@auth_required
def get_messages():
    """获取消息列表"""
    try:
        page = request.args.get('pi', 1, type=int)
        page_size = request.args.get('ps', 20, type=int)
        title = request.args.get('title', '')
        message_type = request.args.get('type', '')
        status = request.args.get('status', '')
        sender = request.args.get('sender', '')
        
        # 模拟数据，实际应该从数据库获取
        messages = [
            {
                'id': 1,
                'title': '系统维护通知',
                'content': '系统将于今晚22:00-24:00进行维护',
                'type': 'system',
                'status': 'sent',
                'sender': '系统管理员',
                'recipient': '全体用户',
                'created_at': '2025-07-25 10:00:00',
                'sent_at': '2025-07-25 10:05:00'
            },
            {
                'id': 2,
                'title': '业务流程更新',
                'content': '业务审批流程已更新，请查看新版本',
                'type': 'business',
                'status': 'draft',
                'sender': '业务管理员',
                'recipient': '相关部门',
                'created_at': '2025-07-25 09:30:00'
            }
        ]
        
        # 简单过滤（实际应该在数据库层面进行）
        if title:
            messages = [m for m in messages if title.lower() in m['title'].lower()]
        if message_type:
            messages = [m for m in messages if m['type'] == message_type]
        if status:
            messages = [m for m in messages if m['status'] == status]
        if sender:
            messages = [m for m in messages if sender.lower() in m['sender'].lower()]
        
        return jsonify({
            'code': 200,
            'success': True,
            'data': messages,
            'total': len(messages),
            'message': '获取消息列表成功'
        })
    except Exception as e:
        logger.error(f"获取消息列表失败: {str(e)}")
        return handle_exception(e)

@api_bp.route('/message/<int:message_id>', methods=['GET'])
@auth_required
def get_message(message_id):
    """获取单个消息详情"""
    try:
        # 模拟数据
        message = {
            'id': message_id,
            'title': '系统维护通知',
            'content': '系统将于今晚22:00-24:00进行维护，期间服务可能不可用。',
            'type': 'system',
            'status': 'sent',
            'sender': '系统管理员',
            'recipient': '全体用户',
            'created_at': '2025-07-25 10:00:00',
            'sent_at': '2025-07-25 10:05:00'
        }
        
        return jsonify({
            'code': 200,
            'success': True,
            'data': message,
            'message': '获取消息详情成功'
        })
    except Exception as e:
        logger.error(f"获取消息详情失败: {str(e)}")
        return handle_exception(e)

@api_bp.route('/message', methods=['POST'])
@auth_required
@permission_required('message:create')
def create_message():
    """创建新消息"""
    try:
        data = request.get_json()
        
        # 验证必填字段
        required_fields = ['title', 'content', 'type']
        for field in required_fields:
            if not data.get(field):
                raise ValidationException(f"缺少必填字段: {field}")
        
        # 模拟创建消息
        message_id = 123  # 实际应该从数据库获取
        
        return jsonify({
            'code': 200,
            'success': True,
            'data': {'id': message_id},
            'message': '消息创建成功'
        })
    except Exception as e:
        logger.error(f"创建消息失败: {str(e)}")
        return handle_exception(e)

@api_bp.route('/message/<int:message_id>', methods=['PUT'])
@auth_required
@permission_required('message:edit')
def update_message(message_id):
    """更新消息"""
    try:
        data = request.get_json()
        
        return jsonify({
            'code': 200,
            'success': True,
            'message': '消息更新成功'
        })
    except Exception as e:
        logger.error(f"更新消息失败: {str(e)}")
        return handle_exception(e)

@api_bp.route('/message/<int:message_id>', methods=['DELETE'])
@auth_required
@permission_required('message:delete')
def delete_message(message_id):
    """删除消息"""
    try:
        return jsonify({
            'code': 200,
            'success': True,
            'message': '消息删除成功'
        })
    except Exception as e:
        logger.error(f"删除消息失败: {str(e)}")
        return handle_exception(e)

@api_bp.route('/message/<int:message_id>/send', methods=['POST'])
@auth_required
@permission_required('message:send')
def send_message(message_id):
    """发送消息"""
    try:
        return jsonify({
            'code': 200,
            'success': True,
            'message': '消息发送成功'
        })
    except Exception as e:
        logger.error(f"发送消息失败: {str(e)}")
        return handle_exception(e)

@api_bp.route('/message/batch/delete', methods=['POST'])
@auth_required
@permission_required('message:delete')
def batch_delete_messages():
    """批量删除消息"""
    try:
        data = request.get_json()
        ids = data.get('ids', [])
        
        return jsonify({
            'code': 200,
            'success': True,
            'message': f'成功删除 {len(ids)} 条消息'
        })
    except Exception as e:
        logger.error(f"批量删除消息失败: {str(e)}")
        return handle_exception(e)

@api_bp.route('/message/batch/send', methods=['POST'])
@auth_required
@permission_required('message:send')
def batch_send_messages():
    """批量发送消息"""
    try:
        data = request.get_json()
        ids = data.get('ids', [])
        
        return jsonify({
            'code': 200,
            'success': True,
            'message': f'成功发送 {len(ids)} 条消息'
        })
    except Exception as e:
        logger.error(f"批量发送消息失败: {str(e)}")
        return handle_exception(e)

@api_bp.route('/message/stats', methods=['GET'])
@auth_required
def get_message_stats():
    """获取消息统计信息"""
    try:
        stats = {
            'total': 156,
            'sent': 89,
            'draft': 45,
            'failed': 12,
            'today_sent': 23
        }
        
        return jsonify({
            'code': 200,
            'success': True,
            'data': stats,
            'message': '获取统计信息成功'
        })
    except Exception as e:
        logger.error(f"获取消息统计失败: {str(e)}")
        return handle_exception(e)

@api_bp.route('/message/types', methods=['GET'])
@auth_required
def get_message_types():
    """获取消息类型列表"""
    try:
        types = [
            {'value': 'system', 'label': '系统通知'},
            {'value': 'business', 'label': '业务消息'},
            {'value': 'alert', 'label': '告警消息'}
        ]
        
        return jsonify({
            'code': 200,
            'success': True,
            'data': types,
            'message': '获取消息类型成功'
        })
    except Exception as e:
        logger.error(f"获取消息类型失败: {str(e)}")
        return handle_exception(e)

@api_bp.route('/message/channels', methods=['GET'])
@auth_required
def get_message_channels():
    """获取推送渠道列表"""
    try:
        channels = [
            {'value': 'email', 'label': '邮件'},
            {'value': 'sms', 'label': '短信'},
            {'value': 'system', 'label': '系统内消息'},
            {'value': 'wechat', 'label': '微信'}
        ]
        
        return jsonify({
            'code': 200,
            'success': True,
            'data': channels,
            'message': '获取推送渠道成功'
        })
    except Exception as e:
        logger.error(f"获取推送渠道失败: {str(e)}")
        return handle_exception(e)

@api_bp.route('/message/subscriptions/<int:user_id>', methods=['GET'])
@auth_required
def get_user_subscriptions(user_id):
    """获取用户订阅设置"""
    try:
        subscriptions = {
            'email': True,
            'sms': False,
            'system': True,
            'wechat': True
        }
        
        return jsonify({
            'code': 200,
            'success': True,
            'data': subscriptions,
            'message': '获取订阅设置成功'
        })
    except Exception as e:
        logger.error(f"获取用户订阅设置失败: {str(e)}")
        return handle_exception(e)

@api_bp.route('/message/subscriptions/<int:user_id>', methods=['PUT'])
@auth_required
def update_user_subscriptions(user_id):
    """更新用户订阅设置"""
    try:
        data = request.get_json()
        
        return jsonify({
            'code': 200,
            'success': True,
            'message': '订阅设置更新成功'
        })
    except Exception as e:
        logger.error(f"更新用户订阅设置失败: {str(e)}")
        return handle_exception(e) 