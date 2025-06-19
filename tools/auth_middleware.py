# -*- coding: utf-8 -*-
"""
认证中间件
提供JWT认证和权限验证功能
"""
import logging
from functools import wraps
from typing import Dict, Any, Optional
import jwt
from flask import request, jsonify, g
from service.user_service import get_user_service
from service.permission_service import get_permission_service
from tools.redis_service import get_redis_service
from config import Config

logger = logging.getLogger(__name__)
JWT_SECRET = Config.JWT_SECRET_KEY

def auth_required(f):
    """基本的认证检查装饰器"""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({
                'code': 401,
                'message': '无效的认证头'
            }), 401

        token = auth_header.split(' ')[1]
        try:
            # 验证令牌
            payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
            if payload.get("token_type") != "access":
                return jsonify({
                    'code': 401,
                    'message': '无效的令牌类型'
                }), 401

            # 检查Redis中是否存在该令牌
            redis_service = get_redis_service()
            if not redis_service.check_token_exists(f"access_token:{payload['user_id']}"):
                return jsonify({
                    'code': 401,
                    'message': '令牌已失效'
                }), 401

            # 将用户信息添加到请求对象中
            request.user = payload
            return f(*args, **kwargs)

        except jwt.ExpiredSignatureError:
            return jsonify({
                'code': 401,
                'message': '令牌已过期'
            }), 401
        except jwt.InvalidTokenError:
            return jsonify({
                'code': 401,
                'message': '无效的令牌'
            }), 401

    return decorated

def generate_token(payload: Dict[str, Any]) -> str:
    """
    生成JWT Token
    :param payload: Token载荷
    :return: Token字符串
    """
    try:
        token = jwt.encode(
            payload,
            JWT_SECRET,
            algorithm='HS256'
        )
        return token
    except Exception as e:
        logger.error(f"生成Token失败: {str(e)}")
        raise Exception(f"生成Token失败: {str(e)}")

def verify_token(token: str) -> Dict[str, Any]:
    """
    验证JWT Token
    :param token: Token字符串
    :return: Token载荷
    """
    try:
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=['HS256']
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise Exception("Token已过期")
    except jwt.InvalidTokenError:
        raise Exception("无效的Token")

def token_required(f):
    """Token验证装饰器"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # 从请求头获取token
        auth_header = request.headers.get('Authorization')
        if auth_header:
            try:
                token = auth_header.split(" ")[1]
            except IndexError:
                return jsonify({
                    'success': False,
                    'error': '无效的Authorization头'
                }), 401
        
        if not token:
            return jsonify({
                'success': False,
                'error': '缺少Token'
            }), 401
        
        try:
            # 验证token
            payload = verify_token(token)
            user_id = payload.get('user_id')
            
            # 检查token是否在Redis中
            redis_service = get_redis_service()
            stored_token = redis_service.get_token(f"access_token:{user_id}")
            if not stored_token or stored_token != token:
                return jsonify({
                    'success': False,
                    'error': 'Token已失效'
                }), 401
            
            # 获取用户信息（不检查状态）
            user_service = get_user_service()
            user = user_service._get_user_by_id_without_status_check(user_id)
            if not user['success']:
                return jsonify({
                    'success': False,
                    'error': '用户不存在'
                }), 401
            
            # 检查用户状态
            if user['data']['status'] != 1:
                return jsonify({
                    'success': False,
                    'error': '用户已禁用'
                }), 401
            
            # 获取用户权限
            permission_service = get_permission_service()
            permissions = permission_service.get_user_permissions(user_id)
            if permissions['success']:
                user['data']['permissions'] = permissions['data']
            
            # 保存用户信息到g对象
            g.current_user = user['data']
            return f(*args, **kwargs)
            
        except Exception as e:
            logger.error(f"Token验证失败: {str(e)}")
            return jsonify({
                'success': False,
                'error': f'Token验证失败: {str(e)}'
            }), 401
            
    return decorated

def get_current_user() -> Optional[Dict[str, Any]]:
    """获取当前用户信息"""
    return getattr(g, 'current_user', None)

def get_org_filter():
    """获取机构过滤条件"""
    current_user = get_current_user()
    if not current_user:
        return None
    return current_user.get('org_code')

def admin_required(f):
    """管理员权限验证装饰器"""
    @wraps(f)
    def decorated(*args, **kwargs):
        current_user = get_current_user()
        if not current_user:
            return jsonify({
                'success': False,
                'error': '用户未登录'
            }), 401
        
        if current_user['role_level'] > 2:  # 角色级别1-2为管理员
            return jsonify({
                'success': False,
                'error': '需要管理员权限'
            }), 403
            
        return f(*args, **kwargs)
    return decorated

def super_admin_required(f):
    """超级管理员权限验证装饰器"""
    @wraps(f)
    def decorated(*args, **kwargs):
        current_user = get_current_user()
        if not current_user:
            return jsonify({
                'success': False,
                'error': '用户未登录'
            }), 401
        
        if current_user['role_level'] != 1:  # 角色级别1为超级管理员
            return jsonify({
                'success': False,
                'error': '需要超级管理员权限'
            }), 403
            
        return f(*args, **kwargs)
    return decorated

def permission_required(permission_code: str):
    """权限验证装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            current_user = get_current_user()
            if not current_user:
                return jsonify({
                    'success': False,
                    'error': '用户未登录'
                }), 401
            
            # 超级管理员拥有所有权限
            if current_user['role_level'] == 1:
                return f(*args, **kwargs)
            
            # 检查用户权限
            user_permissions = current_user.get('permissions', [])
            if permission_code not in user_permissions:
                return jsonify({
                    'success': False,
                    'error': f'需要{permission_code}权限'
                }), 403
                
            return f(*args, **kwargs)
        return decorated
    return decorator

def org_filter_required(allow_cross_org: bool = False):
    """机构数据隔离装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            current_user = get_current_user()
            if not current_user:
                return jsonify({
                    'success': False,
                    'error': '用户未登录'
                }), 401
            
            # 超级管理员可以跨机构访问
            if current_user['role_level'] == 1:
                return f(*args, **kwargs)
            
            # 检查是否允许跨机构访问
            if not allow_cross_org:
                try:
                    # 从请求参数获取机构编码
                    org_code = request.args.get('org_code')
                    
                    # 如果是POST/PUT请求，尝试从JSON数据获取
                    if request.method in ['POST', 'PUT'] and request.is_json:
                        json_data = request.get_json()
                        if json_data and 'org_code' in json_data:
                            org_code = json_data['org_code']
                    
                    if org_code and org_code != current_user['org_code']:
                        return jsonify({
                            'success': False,
                            'error': '不允许跨机构访问数据'
                        }), 403
                except Exception as e:
                    logger.error(f"检查机构权限失败: {str(e)}")
                    # 如果JSON解析失败，继续执行，让具体的接口处理错误
                    pass
            
            return f(*args, **kwargs)
        return decorated
    return decorator 