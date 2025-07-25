from flask import request, jsonify, g
from . import api_bp
from tools.auth_middleware import auth_required, permission_required
from service import get_audit_service_instance
from tools.exceptions import (
    ValidationException,
    BusinessException,
    handle_exception,
    create_error_response
)
import logging

logger = logging.getLogger(__name__)

@api_bp.route('/audit/logs', methods=['GET'])
@auth_required
@permission_required('audit:view')
def get_audit_logs():
    """获取审计日志列表"""
    try:
        page = request.args.get('pi', request.args.get('page', 1), type=int)
        page_size = request.args.get('ps', request.args.get('page_size', 10), type=int)
        
        # 过滤条件
        start_time = request.args.get('start_time')
        end_time = request.args.get('end_time')
        operation_type = request.args.get('operation_type')
        operator = request.args.get('operator')
        status = request.args.get('status')
        
        audit_service = get_audit_service_instance()
        result = audit_service.get_audit_logs(
            page=page,
            page_size=page_size,
            start_time=start_time,
            end_time=end_time,
            operation_type=operation_type,
            operator=operator,
            status=status
        )
        
        if not result['success']:
            raise BusinessException(result.get('error', '获取审计日志失败'))
            
        return jsonify({
            'code': 200,
            'message': '获取审计日志成功',
            'data': result['data']
        })
            
    except Exception as e:
        logger.error(f"获取审计日志失败: {str(e)}")
        return handle_exception(e)

@api_bp.route('/audit/logs/<int:log_id>', methods=['GET'])
@auth_required
@permission_required('audit:view')
def get_audit_log(log_id):
    """获取审计日志详情"""
    try:
        audit_service = get_audit_service_instance()
        result = audit_service.get_audit_log_by_id(log_id)
        
        if not result['success']:
            raise BusinessException(result.get('error', '获取审计日志详情失败'))
            
        return jsonify({
            'code': 200,
            'message': '获取审计日志详情成功',
            'data': result['data']
        })
            
    except Exception as e:
        logger.error(f"获取审计日志详情失败: {str(e)}")
        return handle_exception(e)

@api_bp.route('/audit/login-logs', methods=['GET'])
@auth_required
@permission_required('audit:view')
def get_login_logs():
    """获取登录日志列表"""
    try:
        page = request.args.get('pi', request.args.get('page', 1), type=int)
        page_size = request.args.get('ps', request.args.get('page_size', 10), type=int)
        
        # 过滤条件
        start_time = request.args.get('start_time')
        end_time = request.args.get('end_time')
        username = request.args.get('username')
        status = request.args.get('status')
        ip = request.args.get('ip')
        
        audit_service = get_audit_service_instance()
        result = audit_service.get_login_logs(
            page=page,
            page_size=page_size,
            start_time=start_time,
            end_time=end_time,
            username=username,
            status=status,
            ip=ip
        )
        
        if not result['success']:
            raise BusinessException(result.get('error', '获取登录日志失败'))
            
        return jsonify({
            'code': 200,
            'message': '获取登录日志成功',
            'data': result['data']
        })
            
    except Exception as e:
        logger.error(f"获取登录日志失败: {str(e)}")
        return handle_exception(e)

@api_bp.route('/audit/export', methods=['POST'])
@auth_required
@permission_required('audit:export')
def export_audit_logs():
    """导出审计日志"""
    try:
        data = request.get_json()
        log_type = data.get('log_type', 'operation')  # operation/login
        filters = data.get('filters', {})
        
        audit_service = get_audit_service_instance()
        result = audit_service.export_logs(log_type, filters)
        
        if not result['success']:
            raise BusinessException(result.get('error', '导出审计日志失败'))
            
        return jsonify({
            'code': 200,
            'message': '导出审计日志成功',
            'data': result['data']
        })
            
    except Exception as e:
        logger.error(f"导出审计日志失败: {str(e)}")
        return handle_exception(e)

@api_bp.route('/audit/stats', methods=['GET'])
@auth_required
@permission_required('audit:view')
def get_audit_stats():
    """获取审计统计数据"""
    try:
        # 统计维度
        dimension = request.args.get('dimension', 'day')  # day/week/month
        start_time = request.args.get('start_time')
        end_time = request.args.get('end_time')
        
        audit_service = get_audit_service_instance()
        result = audit_service.get_audit_stats(
            dimension=dimension,
            start_time=start_time,
            end_time=end_time
        )
        
        if not result['success']:
            raise BusinessException(result.get('error', '获取审计统计数据失败'))
            
        return jsonify({
            'code': 200,
            'message': '获取审计统计数据成功',
            'data': result['data']
        })
            
    except Exception as e:
        logger.error(f"获取审计统计数据失败: {str(e)}")
        return handle_exception(e) 