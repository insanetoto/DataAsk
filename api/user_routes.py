from flask import request, jsonify, g
from . import api_bp
from tools.auth_middleware import auth_required, permission_required
from service import get_user_service_instance
from tools.exceptions import (
    ValidationException,
    ResourceNotFoundException,
    AuthorizationException,
    handle_exception,
    create_error_response,
    success_response
)
import logging

logger = logging.getLogger(__name__)

@api_bp.route('/users', methods=['GET'])
@auth_required
def get_users():
    """获取用户列表（使用增强权限控制）"""
    try:
        from tools.permission_middleware import require_permission
        
        # 检查权限
        current_user = g.current_user
        if not current_user:
            raise AuthorizationException("用户未登录")
        
        user_id = current_user.get('user_id') or current_user.get('id')
        
        # 获取用户ACL信息
        from tools.permission_middleware import PermissionMiddleware
        middleware = PermissionMiddleware()
        user_acl_info = middleware.get_user_acl_info(user_id)
        
        if not user_acl_info:
            raise AuthorizationException("无法获取用户权限信息")
        
        # 检查USER_LIST权限
        abilities = user_acl_info.get('ability', [])
        if '*' not in abilities and 'USER_LIST' not in abilities:
            raise AuthorizationException("权限不足：需要USER_LIST权限")
        
        # 将ACL信息添加到g对象，供数据过滤使用
        g.user_acl_info = user_acl_info
        
        # 支持ng-alain表格组件的参数格式：pi, ps
        page = request.args.get('pi', request.args.get('page', 1), type=int)
        page_size = request.args.get('ps', request.args.get('page_size', 10), type=int)
        keyword = request.args.get('keyword', '')
        org_code = request.args.get('org_code', '')
        
        # 处理undefined字符串值
        status_str = request.args.get('status')
        if status_str and status_str != 'undefined':
            status = int(status_str)
        else:
            status = None
        
        user_service = get_user_service_instance()
        result = user_service.get_users_list(
            page=page, 
            page_size=page_size, 
            keyword=keyword, 
            status=status,
            org_code=org_code
        )
        
        if not result['success']:
            raise ValidationException(result.get('error', '获取用户列表失败'))
            
        return success_response(result['data'], '获取用户列表成功')
        
    except Exception as e:
        logger.error(f"获取用户列表失败: {str(e)}")
        return handle_exception(e)

@api_bp.route('/users/<int:user_id>', methods=['GET'])
@auth_required
def get_user(user_id):
    """获取用户详情"""
    try:
        user_service = get_user_service_instance()
        result = user_service.get_user_by_id(user_id)
        
        if not result['success']:
            raise ResourceNotFoundException(result.get('error', '用户不存在'))
            
        return jsonify({
            'code': 200,
            'message': '获取用户详情成功',
            'data': result['data']
        })
            
    except Exception as e:
        logger.error(f"获取用户详情失败: {str(e)}")
        return handle_exception(e)

@api_bp.route('/users', methods=['POST'])
@auth_required
@permission_required('user:create')
def create_user():
    """创建用户"""
    try:
        data = request.get_json()
        
        # 验证必填字段
        required_fields = ['username', 'password', 'name', 'email', 'org_code', 'role_id']
        for field in required_fields:
            if not data.get(field):
                raise ValidationException(f'字段 {field} 不能为空')
        
        user_service = get_user_service_instance()
        result = user_service.create_user(data)
        
        if not result['success']:
            raise ValidationException(result.get('error', '创建用户失败'))
            
        return jsonify({
            'code': 200,
            'message': '创建用户成功',
            'data': result['data']
        })
            
    except Exception as e:
        logger.error(f"创建用户失败: {str(e)}")
        return handle_exception(e)

@api_bp.route('/users/<int:user_id>', methods=['PUT'])
@auth_required
@permission_required('user:update')
def update_user(user_id):
    """更新用户信息"""
    try:
        data = request.get_json()
        data['id'] = user_id
        
        user_service = get_user_service_instance()
        result = user_service.update_user(data)
        
        if not result['success']:
            raise ValidationException(result.get('error', '更新用户失败'))
            
        return jsonify({
            'code': 200,
            'message': '更新用户成功',
            'data': result['data']
        })
            
    except Exception as e:
        logger.error(f"更新用户失败: {str(e)}")
        return handle_exception(e)

@api_bp.route('/users/<int:user_id>', methods=['DELETE'])
@auth_required
@permission_required('user:delete')
def delete_user(user_id):
    """删除用户"""
    try:
        user_service = get_user_service_instance()
        result = user_service.delete_user(user_id)
        
        if not result['success']:
            raise ValidationException(result.get('error', '删除用户失败'))
            
        return jsonify({
            'code': 200,
            'message': '删除用户成功',
            'data': None
        })
            
    except Exception as e:
        logger.error(f"删除用户失败: {str(e)}")
        return handle_exception(e)

@api_bp.route('/users/reset-password', methods=['POST'])
@auth_required
def reset_password():
    """重置密码"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        new_password = data.get('new_password')
        
        if not user_id or not new_password:
            raise ValidationException('用户ID和新密码不能为空')
        
        user_service = get_user_service_instance()
        result = user_service.reset_password(user_id, new_password)
        
        if not result['success']:
            raise ValidationException(result.get('error', '重置密码失败'))
            
        return jsonify({
            'code': 200,
            'message': '重置密码成功',
            'data': None
        })
            
    except Exception as e:
        logger.error(f"重置密码失败: {str(e)}")
        return handle_exception(e)

@api_bp.route('/users/change-password', methods=['POST'])
@auth_required
def change_password():
    """修改密码"""
    try:
        data = request.get_json()
        old_password = data.get('old_password')
        new_password = data.get('new_password')
        
        if not old_password or not new_password:
            raise ValidationException('原密码和新密码不能为空')
        
        current_user = g.current_user
        if not current_user:
            raise AuthorizationException('用户未登录')
        
        user_service = get_user_service_instance()
        result = user_service.change_password(
            current_user.get('id'),
            old_password,
            new_password
        )
        
        if not result['success']:
            raise ValidationException(result.get('error', '修改密码失败'))
            
        return jsonify({
            'code': 200,
            'message': '修改密码成功',
            'data': None
        })
            
    except Exception as e:
        logger.error(f"修改密码失败: {str(e)}")
        return handle_exception(e) 