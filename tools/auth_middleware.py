# -*- coding: utf-8 -*-
"""
认证中间件模块
提供用户认证和授权相关的装饰器和工具函数
"""
import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, g
from typing import Dict, Any, Optional, Callable
import logging

logger = logging.getLogger(__name__)

# JWT配置
JWT_SECRET_KEY = 'your-secret-key'  # 生产环境应该使用安全的密钥
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # 访问令牌过期时间（分钟）
REFRESH_TOKEN_EXPIRE_DAYS = 7    # 刷新令牌过期时间（天）

def generate_token(user_data: Dict[str, Any], token_type: str = 'access') -> str:
    """
    生成JWT令牌
    
    Args:
        user_data: 用户数据
        token_type: 令牌类型（access/refresh）
        
    Returns:
        str: JWT令牌
    """
    try:
        # 设置过期时间
        if token_type == 'refresh':
            expires_delta = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        else:  # access token
            expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            
        expire_time = datetime.utcnow() + expires_delta
        
        # 构建令牌数据
        token_data = {
            'exp': expire_time,
            'iat': datetime.utcnow(),
            'type': token_type,
            'id': user_data.get('id'),
            'username': user_data.get('username'),
            'role_code': user_data.get('role_code'),
            'org_code': user_data.get('org_code')
        }
        
        # 生成令牌
        token = jwt.encode(token_data, JWT_SECRET_KEY, algorithm='HS256')
        return token
        
    except Exception as e:
        logger.error(f"生成令牌失败: {str(e)}")
        raise

def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """
    验证JWT令牌
    
    Args:
        token: JWT令牌
        
    Returns:
        Optional[Dict[str, Any]]: 令牌中的数据，验证失败返回None
    """
    try:
        # 解码并验证令牌
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("令牌已过期")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"无效的令牌: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"验证令牌失败: {str(e)}")
        return None

def auth_required(func: Callable) -> Callable:
    """
    认证装饰器
    要求请求包含有效的访问令牌
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            # 获取令牌
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({
                    'code': 401,
                    'message': '未提供认证令牌',
                    'data': None
                }), 401
                
            token = auth_header.split(' ')[1]
            
            # 验证令牌
            payload = verify_token(token)
            if not payload:
                return jsonify({
                    'code': 401,
                    'message': '无效的认证令牌',
                    'data': None
                }), 401
                
            # 检查令牌类型
            if payload.get('type') != 'access':
                return jsonify({
                    'code': 401,
                    'message': '无效的令牌类型',
                    'data': None
                }), 401
                
            # 将用户信息存储在g对象中
            g.current_user = {
                'id': payload.get('id'),
                'username': payload.get('username'),
                'role_code': payload.get('role_code'),
                'org_code': payload.get('org_code')
            }
            
            return func(*args, **kwargs)
            
        except Exception as e:
            logger.error(f"认证失败: {str(e)}")
            return jsonify({
                'code': 500,
                'message': '认证过程发生错误',
                'data': None
            }), 500
            
    return wrapper

def permission_required(permission: str) -> Callable:
    """
    权限装饰器
    要求用户具有指定的权限
    
    Args:
        permission: 所需的权限代码
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                # 检查是否已通过认证
                current_user = getattr(g, 'current_user', None)
                if not current_user:
                    return jsonify({
                        'code': 401,
                        'message': '用户未登录',
                        'data': None
                    }), 401
                    
                # TODO: 实现权限检查逻辑
                # 这里应该根据current_user中的角色信息检查是否具有指定权限
                # 暂时返回成功
                return func(*args, **kwargs)
                
            except Exception as e:
                logger.error(f"权限检查失败: {str(e)}")
                return jsonify({
                    'code': 500,
                    'message': '权限检查过程发生错误',
                    'data': None
                }), 500
                
        return wrapper
    return decorator

def admin_required(f):
    """要求用户具有管理员权限"""
    @wraps(f)
    def decorated(*args, **kwargs):
        current_user = getattr(g, 'current_user', None)
        if not current_user:
            return jsonify({
                'code': 401,
                'message': '用户未登录',
                'data': None
            }), 401
        
        role_code = current_user.get('role_code')
        if role_code not in ['SUPER_ADMIN', 'ORG_ADMIN']:
            return jsonify({
                'code': 403,
                'message': '需要管理员权限',
                'data': None
            }), 403
        
        return f(*args, **kwargs)
    return decorated

def super_admin_required(f):
    """要求用户具有超级管理员权限"""
    @wraps(f)
    def decorated(*args, **kwargs):
        current_user = getattr(g, 'current_user', None)
        if not current_user:
            return jsonify({
                'code': 401,
                'message': '用户未登录',
                'data': None
            }), 401
        
        if current_user.get('role_code') != 'SUPER_ADMIN':
            return jsonify({
                'code': 403,
                'message': '需要超级管理员权限',
                'data': None
            }), 403
        
        return f(*args, **kwargs)
    return decorated

def org_filter_required(f):
    """组织机构数据过滤装饰器"""
    @wraps(f)
    @auth_required
    def decorated(*args, **kwargs):
        current_user = g.current_user
        org_code = current_user.get('org_code')
        role_level = current_user.get('role_level', 99)
        
        # 设置数据过滤范围
        g.org_filter = {
            'org_code': org_code,
            'role_level': role_level
        }
        
        return f(*args, **kwargs)
    return decorated

def get_current_user() -> Optional[Dict[str, Any]]:
    """获取当前用户信息"""
    return getattr(g, 'current_user', None)

def get_org_filter() -> Optional[str]:
    """获取机构过滤条件"""
    current_user = get_current_user()
    if not current_user:
        return None
    
    role_code = current_user.get('role_code')
    if role_code == 'ORG_ADMIN':
        return current_user.get('org_code')
    elif role_code == 'SUPER_ADMIN':
        return None
    else:
        return current_user.get('org_code') 