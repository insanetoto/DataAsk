# -*- coding: utf-8 -*-
"""
认证中间件
提供JWT认证和权限验证功能
"""
import logging
from functools import wraps
from typing import Dict, Any, Optional
import jwt
from flask import request, jsonify, g, current_app
from service.user_service import get_user_service, get_user_service_instance, UserService
from service.permission_service import get_permission_service
from tools.redis_service import get_redis_service
from config import Config
from datetime import datetime, timedelta
import functools

logger = logging.getLogger(__name__)
JWT_SECRET = Config.JWT_SECRET_KEY

class TokenService:
    """Token管理服务"""
    
    def __init__(self):
        self.redis = get_redis_service()
        self.access_token_expires = 1800  # 30分钟
        self.refresh_token_expires = 604800  # 7天
        self.secret_key = JWT_SECRET  # 使用配置中的密钥
        
    def _generate_token(self, user_id: int, token_type: str = "access") -> str:
        """生成JWT token"""
        now = datetime.utcnow()
        expires_in = self.access_token_expires if token_type == "access" else self.refresh_token_expires
        expires = now + timedelta(seconds=expires_in)
        
        payload = {
            "user_id": user_id,
            "type": token_type,
            "exp": expires,
            "iat": now
        }
        
        return jwt.encode(payload, self.secret_key, algorithm="HS256")
    
    def generate_tokens(self, user_id: int) -> Dict[str, Any]:
        """生成访问令牌和刷新令牌"""
        access_token = self._generate_token(user_id, "access")
        refresh_token = self._generate_token(user_id, "refresh")
        
        # 存储到Redis
        self.redis.set_token(f"access_token:{user_id}", access_token, self.access_token_expires)
        self.redis.set_token(f"refresh_token:{user_id}", refresh_token, self.refresh_token_expires)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": self.access_token_expires
        }
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """验证token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            user_id = payload.get("user_id")
            token_type = payload.get("type")
            
            # 检查token是否在Redis中
            stored_token = self.redis.get_token(f"{token_type}_token:{user_id}")
            if not stored_token or stored_token != token:
                return None
                
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token已过期")
            return None
        except jwt.InvalidTokenError:
            logger.warning("无效的Token")
            return None
    
    def refresh_access_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """使用刷新令牌获取新的访问令牌"""
        payload = self.verify_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            return None
            
        user_id = payload.get("user_id")
        return {
            "access_token": self._generate_token(user_id, "access"),
            "token_type": "bearer",
            "expires_in": self.access_token_expires
        }
    
    def revoke_tokens(self, user_id: int) -> bool:
        """撤销用户的所有令牌"""
        try:
            self.redis.delete_token(f"access_token:{user_id}")
            self.redis.delete_token(f"refresh_token:{user_id}")
            return True
        except Exception as e:
            logger.error(f"撤销令牌失败: {str(e)}")
            return False

def generate_token(user_id: int, expires_in: int = 3600 * 24) -> dict:
    """
    生成JWT token
    :param user_id: 用户ID
    :param expires_in: 过期时间(秒)，默认24小时
    :return: token信息
    """
    now = datetime.utcnow()
    exp = now + timedelta(seconds=expires_in)
    refresh_exp = now + timedelta(days=7)  # 刷新token7天有效
    
    access_token = jwt.encode(
        {
            'user_id': user_id,
            'exp': exp,
            'iat': now,
            'type': 'access'
        },
        JWT_SECRET,
        algorithm='HS256'
    )
    
    refresh_token = jwt.encode(
        {
            'user_id': user_id,
            'exp': refresh_exp,
            'iat': now,
            'refresh': True,
            'type': 'refresh'
        },
        JWT_SECRET,
        algorithm='HS256'
    )
    
    return {
        'access_token': access_token,
        'refresh_token': refresh_token,
        'expires_in': expires_in
    }

def verify_token(token: str) -> dict:
    """
    验证JWT token
    :param token: JWT token
    :return: 解码后的payload
    """
    try:
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=['HS256']
        )
        return {'success': True, 'data': payload}
    except jwt.ExpiredSignatureError:
        return {'success': False, 'error': 'Token已过期'}
    except jwt.InvalidTokenError:
        return {'success': False, 'error': '无效的Token'}

def auth_required(f):
    """
    认证装饰器
    """
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({
                'code': 401,
                'message': '未提供认证信息'
            }), 401
        
        try:
            token_type, token = auth_header.split(' ')
            if token_type.lower() != 'bearer':
                return jsonify({
                    'code': 401,
                    'message': '无效的认证类型'
                }), 401
        except ValueError:
            return jsonify({
                'code': 401,
                'message': '无效的认证头格式'
            }), 401
        
        verify_result = verify_token(token)
        if not verify_result['success']:
            return jsonify({
                'code': 401,
                'message': verify_result['error']
            }), 401
        
        # 获取用户信息
        user_id = verify_result['data']['user_id']
        user_service = get_user_service()
        user_result = user_service.get_user_by_id(user_id)
        if not user_result['success'] or not user_result['data']:
            return jsonify({
                'code': 401,
                'message': '用户不存在或已被禁用'
            }), 401
        
        user_info = user_result['data']
        
        # 将用户信息存储在请求上下文中
        request.user = user_info
        return f(*args, **kwargs)
    
    return decorated

def refresh_token_required(f):
    """
    刷新token装饰器
    """
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({
                'code': 401,
                'message': '未提供认证信息'
            }), 401
        
        try:
            token_type, token = auth_header.split(' ')
            if token_type.lower() != 'bearer':
                return jsonify({
                    'code': 401,
                    'message': '无效的认证类型'
                }), 401
        except ValueError:
            return jsonify({
                'code': 401,
                'message': '无效的认证头格式'
            }), 401
        
        verify_result = verify_token(token)
        if not verify_result['success']:
            return jsonify({
                'code': 401,
                'message': verify_result['error']
            }), 401
        
        # 验证是否为刷新token
        payload = verify_result['data']
        if not payload.get('refresh'):
            return jsonify({
                'code': 401,
                'message': '无效的刷新Token'
            }), 401
        
        # 获取用户信息
        user_id = payload['user_id']
        user_service = get_user_service()
        user_result = user_service.get_user_by_id(user_id)
        if not user_result['success'] or not user_result['data']:
            return jsonify({
                'code': 401,
                'message': '用户不存在或已被禁用'
            }), 401
        
        user_info = user_result['data']
        
        # 将用户信息存储在请求上下文中
        request.user = user_info
        return f(*args, **kwargs)
    
    return decorated

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # 从请求头获取令牌
        auth_header = request.headers.get('Authorization')
        if auth_header:
            try:
                token_type, token = auth_header.split(' ')
                if token_type.lower() != 'bearer':
                    return jsonify({
                        'code': 401,
                        'message': '无效的令牌类型'
                    }), 401
            except ValueError:
                return jsonify({
                    'code': 401,
                    'message': '无效的Authorization头'
                }), 401
        
        if not token:
            return jsonify({
                'code': 401,
                'message': '缺少访问令牌'
            }), 401
            
        # 验证令牌
        result = get_user_service_instance().verify_token(token)
        if not result['success']:
            return jsonify({
                'code': 401,
                'message': result['error']
            }), 401
            
        # 将用户信息添加到请求上下文
        request.user = result['data']
        return f(*args, **kwargs)
        
    return decorated

def permission_required(permission_code):
    """权限检查装饰器"""
    def decorator(f):
        @wraps(f)
        @auth_required
        def decorated(*args, **kwargs):
            current_user = g.current_user
            user_permissions = current_user.get('permissions', [])
            
            # 检查是否有所需权限
            if not any(p['permission_code'] == permission_code for p in user_permissions):
                return jsonify({
                    'code': 403,
                    'message': '没有所需权限',
                    'data': None
                }), 403
                
            return f(*args, **kwargs)
        return decorated
    return decorator

def admin_required(f):
    """管理员权限检查装饰器"""
    @wraps(f)
    @auth_required
    def decorated(*args, **kwargs):
        current_user = g.current_user
        if current_user.get('role_level', 99) > 2:  # 角色级别1-2为管理员
            return jsonify({
                'code': 403,
                'message': '需要管理员权限',
                'data': None
            }), 403
            
        return f(*args, **kwargs)
    return decorated

def super_admin_required(f):
    """超级管理员权限检查装饰器"""
    @wraps(f)
    @auth_required
    def decorated(*args, **kwargs):
        current_user = g.current_user
        if current_user.get('role_level', 99) != 1:  # 角色级别1为超级管理员
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

def get_current_user():
    """获取当前用户信息"""
    return getattr(g, 'current_user', None)

def get_org_filter():
    """获取组织机构过滤条件"""
    return getattr(g, 'org_filter', None)

# 初始化TokenService实例
token_service = TokenService() 