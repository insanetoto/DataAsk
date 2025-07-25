from flask import request, jsonify, g
from . import api_bp
from tools.auth_middleware import auth_required, permission_required
from service import get_role_service_instance, get_permission_service_instance
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

@api_bp.route('/roles', methods=['GET'])
@auth_required
def get_roles():
    """获取角色列表（使用增强权限控制）"""
    try:
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
        
        # 检查ROLE_LIST权限
        abilities = user_acl_info.get('ability', [])
        if '*' not in abilities and 'ROLE_LIST' not in abilities:
            raise AuthorizationException("权限不足：需要ROLE_LIST权限")
        
        # 将ACL信息添加到g对象，供数据过滤使用
        g.user_acl_info = user_acl_info
        
        # 支持ng-alain表格组件的参数格式：pi, ps
        page = request.args.get('pi', request.args.get('page', 1), type=int)
        page_size = request.args.get('ps', request.args.get('page_size', 10), type=int)
        keyword = request.args.get('keyword', '')
        
        # 处理undefined字符串值
        status_str = request.args.get('status')
        if status_str and status_str != 'undefined':
            status = int(status_str)
        else:
            status = None
            
        role_level_str = request.args.get('role_level')
        if role_level_str and role_level_str != 'undefined':
            role_level = int(role_level_str)
        else:
            role_level = None
        
        role_service = get_role_service_instance()
        
        # 数据范围过滤将在service层自动应用
        result = role_service.get_roles_list(
            page=page, 
            page_size=page_size, 
            keyword=keyword, 
            status=status, 
            role_level=role_level
        )
        
        if not result['success']:
            raise ValidationException(result.get('error', '获取角色列表失败'))
            
        return success_response(result['data'], '获取角色列表成功')
        
    except Exception as e:
        logger.error(f"获取角色列表失败: {str(e)}")
        return handle_exception(e)

@api_bp.route('/roles/<int:role_id>', methods=['GET'])
@auth_required
def get_role(role_id):
    """获取角色详情"""
    try:
        role_service = get_role_service_instance()
        result = role_service.get_role_by_id(role_id)
        
        if not result['success']:
            raise ResourceNotFoundException(result.get('error', '角色不存在'))
            
        return jsonify({
            'code': 200,
            'message': '获取角色详情成功',
            'data': result['data']
        })
            
    except Exception as e:
        logger.error(f"获取角色详情失败: {str(e)}")
        return handle_exception(e)

@api_bp.route('/roles', methods=['POST'])
@auth_required
@permission_required('role:create')
def create_role():
    """创建角色"""
    try:
        data = request.get_json()
        
        # 验证必填字段
        required_fields = ['role_name', 'role_code', 'role_level']
        for field in required_fields:
            if not data.get(field):
                raise ValidationException(f'字段 {field} 不能为空')
        
        role_service = get_role_service_instance()
        result = role_service.create_role(data)
        
        if not result['success']:
            raise ValidationException(result.get('error', '创建角色失败'))
            
        return jsonify({
            'code': 200,
            'message': '创建角色成功',
            'data': result['data']
        })
            
    except Exception as e:
        logger.error(f"创建角色失败: {str(e)}")
        return handle_exception(e)

@api_bp.route('/roles/<int:role_id>', methods=['PUT'])
@auth_required
@permission_required('role:update')
def update_role(role_id):
    """更新角色信息"""
    try:
        data = request.get_json()
        data['id'] = role_id
        
        role_service = get_role_service_instance()
        result = role_service.update_role(data)
        
        if not result['success']:
            raise ValidationException(result.get('error', '更新角色失败'))
            
        return jsonify({
            'code': 200,
            'message': '更新角色成功',
            'data': result['data']
        })
            
    except Exception as e:
        logger.error(f"更新角色失败: {str(e)}")
        return handle_exception(e)

@api_bp.route('/roles/<int:role_id>', methods=['DELETE'])
@auth_required
@permission_required('role:delete')
def delete_role(role_id):
    """删除角色"""
    try:
        role_service = get_role_service_instance()
        result = role_service.delete_role(role_id)
        
        if not result['success']:
            raise ValidationException(result.get('error', '删除角色失败'))
            
        return jsonify({
            'code': 200,
            'message': '删除角色成功',
            'data': None
        })
            
    except Exception as e:
        logger.error(f"删除角色失败: {str(e)}")
        return handle_exception(e)

@api_bp.route('/roles/<int:role_id>/permissions', methods=['GET'])
@auth_required
def get_role_permissions(role_id):
    """获取角色的权限列表"""
    try:
        role_service = get_role_service_instance()
        result = role_service.get_role_permissions(role_id)
        
        if not result['success']:
            raise ValidationException(result.get('error', '获取角色权限失败'))
            
        return jsonify({
            'code': 200,
            'message': '获取角色权限成功',
            'data': result['data']
        })
            
    except Exception as e:
        logger.error(f"获取角色权限失败: {str(e)}")
        return handle_exception(e)

@api_bp.route('/roles/<int:role_id>/permissions', methods=['POST'])
@auth_required
@permission_required('role:assign_permission')
def assign_role_permissions(role_id):
    """分配角色权限"""
    try:
        data = request.get_json()
        permission_ids = data.get('permission_ids', [])
        
        role_service = get_role_service_instance()
        result = role_service.assign_permissions(role_id, permission_ids)
        
        if not result['success']:
            raise ValidationException(result.get('error', '分配权限失败'))
            
        return jsonify({
            'code': 200,
            'message': '分配权限成功',
            'data': None
        })
            
    except Exception as e:
        logger.error(f"分配权限失败: {str(e)}")
        return handle_exception(e)

@api_bp.route('/permissions', methods=['GET'])
@auth_required
def get_permissions():
    """获取权限列表"""
    try:
        permission_service = get_permission_service_instance()
        result = permission_service.get_permissions_list()
        
        if not result['success']:
            raise ValidationException(result.get('error', '获取权限列表失败'))
            
        return jsonify({
            'code': 200,
            'message': '获取权限列表成功',
            'data': result['data']
        })
            
    except Exception as e:
        logger.error(f"获取权限列表失败: {str(e)}")
        return handle_exception(e)

@api_bp.route('/permissions/tree', methods=['GET'])
@auth_required
def get_permissions_tree():
    """获取权限树结构"""
    try:
        permission_service = get_permission_service_instance()
        result = permission_service.get_permissions_tree()
        
        if not result['success']:
            raise ValidationException(result.get('error', '获取权限树失败'))
            
        return jsonify({
            'code': 200,
            'message': '获取权限树成功',
            'data': result['data']
        })
            
    except Exception as e:
        logger.error(f"获取权限树失败: {str(e)}")
        return handle_exception(e) 