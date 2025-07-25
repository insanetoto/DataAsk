from flask import request, jsonify, g
from . import api_bp
from tools.auth_middleware import auth_required, permission_required
from service import get_organization_service_instance
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

@api_bp.route('/organizations', methods=['GET'])
@auth_required
def get_organizations():
    """获取机构列表（使用增强权限控制）"""
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
        
        # 检查ORG_LIST权限
        abilities = user_acl_info.get('ability', [])
        if '*' not in abilities and 'ORG_LIST' not in abilities:
            raise AuthorizationException("权限不足：需要ORG_LIST权限")
        
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
        
        org_service = get_organization_service_instance()
        
        # 数据范围过滤将在service层自动应用
        result = org_service.get_organizations_list(
            page=page,
            page_size=page_size,
            status=status,
            keyword=keyword
        )
        
        if not result['success']:
            raise ValidationException(result.get('error', '获取机构列表失败'))
            
        return success_response(result['data'], '获取机构列表成功')
        
    except Exception as e:
        logger.error(f"获取机构列表失败: {str(e)}")
        return handle_exception(e)

@api_bp.route('/organizations/tree', methods=['GET'])
@auth_required
def get_organization_tree():
    """获取机构树结构"""
    try:
        org_service = get_organization_service_instance()
        current_user = g.current_user
        current_role = current_user.get('role_code', '')
        current_org_code = current_user.get('org_code', '')
        
        if current_role == 'SUPER_ADMIN':
            # 超级管理员可以看到完整的机构树
            result = org_service.get_organization_tree()
        elif current_role == 'ORG_ADMIN' and current_org_code:
            # 机构管理员只能看到自己机构及下级机构的树
            result = org_service.get_organization_tree(root_org_code=current_org_code)
        else:
            raise AuthorizationException('无权限访问机构树')
            
        if not result['success']:
            raise ValidationException(result.get('error', '获取机构树失败'))
            
        return jsonify({
            'code': 200,
            'message': '获取机构树成功',
            'data': result['data']
        })
            
    except Exception as e:
        logger.error(f"获取机构树失败: {str(e)}")
        return handle_exception(e)

@api_bp.route('/organizations/<int:org_id>', methods=['GET'])
@auth_required
def get_organization(org_id):
    """获取机构详情"""
    try:
        org_service = get_organization_service_instance()
        result = org_service.get_organization_by_id(org_id)
        
        if not result['success']:
            raise ResourceNotFoundException(result.get('error', '机构不存在'))
            
        return jsonify({
            'code': 200,
            'message': '获取机构详情成功',
            'data': result['data']
        })
            
    except Exception as e:
        logger.error(f"获取机构详情失败: {str(e)}")
        return handle_exception(e)

@api_bp.route('/organizations', methods=['POST'])
@auth_required
@permission_required('organization:create')
def create_organization():
    """创建机构"""
    try:
        data = request.get_json()
        
        # 验证必填字段
        required_fields = ['org_name', 'org_code', 'parent_org_code']
        for field in required_fields:
            if not data.get(field):
                raise ValidationException(f'字段 {field} 不能为空')
        
        org_service = get_organization_service_instance()
        result = org_service.create_organization(data)
        
        if not result['success']:
            raise ValidationException(result.get('error', '创建机构失败'))
            
        return jsonify({
            'code': 200,
            'message': '创建机构成功',
            'data': result['data']
        })
            
    except Exception as e:
        logger.error(f"创建机构失败: {str(e)}")
        return handle_exception(e)

@api_bp.route('/organizations/<int:org_id>', methods=['PUT'])
@auth_required
@permission_required('organization:update')
def update_organization(org_id):
    """更新机构信息"""
    try:
        data = request.get_json()
        data['id'] = org_id
        
        org_service = get_organization_service_instance()
        result = org_service.update_organization(data)
        
        if not result['success']:
            raise ValidationException(result.get('error', '更新机构失败'))
            
        return jsonify({
            'code': 200,
            'message': '更新机构成功',
            'data': result['data']
        })
            
    except Exception as e:
        logger.error(f"更新机构失败: {str(e)}")
        return handle_exception(e)

@api_bp.route('/organizations/<int:org_id>', methods=['DELETE'])
@auth_required
@permission_required('organization:delete')
def delete_organization(org_id):
    """删除机构"""
    try:
        org_service = get_organization_service_instance()
        result = org_service.delete_organization(org_id)
        
        if not result['success']:
            raise ValidationException(result.get('error', '删除机构失败'))
            
        return jsonify({
            'code': 200,
            'message': '删除机构成功',
            'data': None
        })
            
    except Exception as e:
        logger.error(f"删除机构失败: {str(e)}")
        return handle_exception(e)

@api_bp.route('/organizations/children', methods=['GET'])
@auth_required
def get_organization_children():
    """获取子机构列表"""
    try:
        org_code = request.args.get('org_code')
        include_self = request.args.get('include_self', 'false').lower() == 'true'
        
        if not org_code:
            raise ValidationException('机构编码不能为空')
            
        org_service = get_organization_service_instance()
        result = org_service.get_organization_children(org_code, include_self)
        
        if not result['success']:
            raise ValidationException(result.get('error', '获取子机构列表失败'))
            
        return jsonify({
            'code': 200,
            'message': '获取子机构列表成功',
            'data': result['data']
        })
            
    except Exception as e:
        logger.error(f"获取子机构列表失败: {str(e)}")
        return handle_exception(e) 