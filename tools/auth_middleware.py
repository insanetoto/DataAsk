# -*- coding: utf-8 -*-
"""
权限验证中间件
提供JWT认证和RBAC权限控制
"""
import jwt
import json
import logging
from functools import wraps
from flask import request, jsonify, g, current_app
from service.user_service import get_user_service
from service.permission_service import get_permission_service

logger = logging.getLogger(__name__)

def token_required(f):
    """JWT令牌验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None
        
        # 从Header中获取token
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]  # Bearer <token>
            except IndexError:
                return jsonify({
                    'success': False,
                    'error': 'Token格式错误，应为: Bearer <token>'
                }), 401
        
        if not token:
            return jsonify({
                'success': False,
                'error': '缺少认证令牌'
            }), 401
        
        try:
            # 解码JWT令牌
            secret_key = current_app.config.get('SECRET_KEY', 'default-secret-key')
            data = jwt.decode(token, secret_key, algorithms=["HS256"])
            current_user_id = data['user_id']
            
            # 获取用户信息
            user_service = get_user_service()
            user_result = user_service.get_user_by_id(current_user_id)
            
            if not user_result['success'] or not user_result['data']:
                return jsonify({
                    'success': False,
                    'error': '用户不存在或已禁用'
                }), 401
            
            # 将当前用户信息存储到g对象中
            g.current_user = user_result['data']
            
        except jwt.ExpiredSignatureError:
            return jsonify({
                'success': False,
                'error': '令牌已过期'
            }), 401
        except jwt.InvalidTokenError:
            return jsonify({
                'success': False,
                'error': '无效的令牌'
            }), 401
        except Exception as e:
            logger.error(f"令牌验证失败: {str(e)}")
            return jsonify({
                'success': False,
                'error': '令牌验证失败'
            }), 401
        
        return f(*args, **kwargs)
    
    return decorated_function

def permission_required(required_permission: str = None):
    """权限验证装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 检查是否已经通过token验证
            if not hasattr(g, 'current_user'):
                return jsonify({
                    'success': False,
                    'error': '未进行身份验证'
                }), 401
            
            current_user = g.current_user
            permission_service = get_permission_service()
            
            # 如果指定了具体权限，检查该权限
            if required_permission:
                # 从权限编码获取API路径和方法（这里需要根据实际情况调整）
                api_path = request.path
                api_method = request.method
                
                permission_result = permission_service.check_permission(
                    current_user['id'], api_path, api_method
                )
                
                if not permission_result['success']:
                    return jsonify({
                        'success': False,
                        'error': permission_result['error']
                    }), 403
                
                if not permission_result['has_permission']:
                    return jsonify({
                        'success': False,
                        'error': permission_result.get('message', '权限不足')
                    }), 403
            else:
                # 自动检查当前API路径的权限
                api_path = request.path
                api_method = request.method
                
                permission_result = permission_service.check_permission(
                    current_user['id'], api_path, api_method
                )
                
                if not permission_result['success']:
                    logger.warning(f"权限检查失败: {permission_result['error']}")
                    # 权限检查失败时可以选择继续执行或返回错误
                    # 这里选择继续执行，因为可能是权限配置问题
                elif not permission_result['has_permission']:
                    return jsonify({
                        'success': False,
                        'error': permission_result.get('message', '权限不足')
                    }), 403
            
            return f(*args, **kwargs)
        
        return decorated_function
    
    return decorator

def admin_required(f):
    """管理员权限验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 检查是否已经通过token验证
        if not hasattr(g, 'current_user'):
            return jsonify({
                'success': False,
                'error': '未进行身份验证'
            }), 401
        
        current_user = g.current_user
        
        # 检查是否为管理员（角色等级为1或2）
        if current_user['role_level'] not in [1, 2]:
            return jsonify({
                'success': False,
                'error': '需要管理员权限'
            }), 403
        
        return f(*args, **kwargs)
    
    return decorated_function

def super_admin_required(f):
    """超级管理员权限验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 检查是否已经通过token验证
        if not hasattr(g, 'current_user'):
            return jsonify({
                'success': False,
                'error': '未进行身份验证'
            }), 401
        
        current_user = g.current_user
        
        # 检查是否为超级管理员（角色等级为1）
        if current_user['role_level'] != 1:
            return jsonify({
                'success': False,
                'error': '需要超级管理员权限'
            }), 403
        
        return f(*args, **kwargs)
    
    return decorated_function

def org_filter_required(table_alias: str = None):
    """机构数据过滤装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 检查是否已经通过token验证
            if not hasattr(g, 'current_user'):
                return jsonify({
                    'success': False,
                    'error': '未进行身份验证'
                }), 401
            
            current_user = g.current_user
            permission_service = get_permission_service()
            
            # 获取用户的机构过滤条件
            filter_result = permission_service.get_user_org_filter(current_user['id'])
            
            if not filter_result['success']:
                return jsonify({
                    'success': False,
                    'error': filter_result['error']
                }), 500
            
            # 将过滤条件存储到g对象中，供业务逻辑使用
            g.org_filter = filter_result['data']
            
            return f(*args, **kwargs)
        
        return decorated_function
    
    return decorator

def generate_token(user_data: dict) -> str:
    """生成JWT令牌"""
    try:
        secret_key = current_app.config.get('SECRET_KEY', 'default-secret-key')
        
        payload = {
            'user_id': user_data['id'],
            'user_code': user_data['user_code'],
            'username': user_data['username'],
            'role_code': user_data['role_code'],
            'role_level': user_data['role_level'],
            'org_code': user_data['org_code']
        }
        
        token = jwt.encode(payload, secret_key, algorithm='HS256')
        return token
        
    except Exception as e:
        logger.error(f"生成令牌失败: {str(e)}")
        raise Exception(f"生成令牌失败: {str(e)}")

def get_current_user():
    """获取当前登录用户"""
    if hasattr(g, 'current_user'):
        return g.current_user
    return None

def get_org_filter():
    """获取当前用户的机构过滤条件"""
    if hasattr(g, 'org_filter'):
        return g.org_filter
    return None 