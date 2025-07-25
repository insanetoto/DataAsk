from flask import request, jsonify, g
from . import api_bp
from tools.auth_middleware import auth_required, generate_token, verify_token
from service import get_user_service_instance
from tools.exceptions import (
    AuthenticationException, 
    ValidationException,
    handle_exception,
    create_error_response
)
import logging

logger = logging.getLogger(__name__)

@api_bp.route('/auth/login', methods=['POST'])
def login():
    """用户登录"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            raise ValidationException('用户名和密码不能为空')
            
        user_service = get_user_service_instance()
        user = user_service.verify_password(username, password)
        
        if not user:
            raise AuthenticationException('用户名或密码错误')
            
        # 生成访问令牌和刷新令牌
        access_token = generate_token(user, 'access')
        refresh_token = generate_token(user, 'refresh')
        
        return jsonify({
            'code': 200,
            'message': '登录成功',
            'data': {
                'access_token': access_token,  # 改为access_token
                'refresh_token': refresh_token,
                'expires_in': 1800  # 添加过期时间（30分钟）
            }
        })
        
    except Exception as e:
        logger.error(f"登录失败: {str(e)}")
        return handle_exception(e)

@api_bp.route('/auth/refresh', methods=['POST'])
def refresh_token():
    """刷新访问令牌"""
    try:
        refresh_token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not refresh_token:
            raise AuthenticationException('刷新令牌不能为空')
            
        # 验证刷新令牌
        payload = verify_token(refresh_token)
        if not payload or payload.get('type') != 'refresh':
            raise AuthenticationException('无效的刷新令牌')
            
        # 生成新的访问令牌
        user_data = {
            'id': payload.get('id'),
            'username': payload.get('username'),
            'role_code': payload.get('role_code'),
            'org_code': payload.get('org_code')
        }
        new_access_token = generate_token(user_data, 'access')
        
        return jsonify({
            'code': 200,
            'message': '令牌刷新成功',
            'data': {
                'access_token': new_access_token,  # 改为access_token
                'expires_in': 1800  # 添加过期时间（30分钟）
            }
        })
        
    except Exception as e:
        logger.error(f"刷新令牌失败: {str(e)}")
        return handle_exception(e)

@api_bp.route('/auth/logout', methods=['POST'])
@auth_required
def logout():
    """用户登出"""
    try:
        # 这里可以添加令牌黑名单等登出逻辑
        return jsonify({
            'code': 200,
            'message': '登出成功',
            'data': None
        })
    except Exception as e:
        logger.error(f"登出失败: {str(e)}")
        return handle_exception(e)

@api_bp.route('/auth/profile', methods=['GET'])
@auth_required
def get_profile():
    """获取当前用户信息"""
    try:
        current_user = g.current_user
        if not current_user:
            raise AuthenticationException('用户未登录')
            
        # 移除敏感信息
        profile = {
            'id': current_user.get('id'),
            'username': current_user.get('username'),
            'email': current_user.get('email'),
            'name': current_user.get('name'),
            'avatar': current_user.get('avatar'),
            'org_code': current_user.get('org_code'),
            'org_name': current_user.get('org_name'),
            'role_code': current_user.get('role_code'),
            'role_name': current_user.get('role_name'),
            'status': current_user.get('status')
        }
        
        return jsonify({
            'code': 200,
            'message': '获取用户信息成功',
            'data': profile
        })
        
    except Exception as e:
        logger.error(f"获取用户信息失败: {str(e)}")
        return handle_exception(e)

@api_bp.route('/auth/permissions', methods=['GET'])
@auth_required
def get_user_permissions():
    """获取当前用户的权限列表"""
    try:
        current_user = g.current_user
        if not current_user:
            raise AuthenticationException('用户未登录')
            
        user_service = get_user_service_instance()
        permissions = user_service.get_user_permissions(current_user.get('id'))
        
        return jsonify({
            'code': 200,
            'message': '获取权限列表成功',
            'data': permissions
        })
        
    except Exception as e:
        logger.error(f"获取权限列表失败: {str(e)}")
        return handle_exception(e) 