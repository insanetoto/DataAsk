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
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)
JWT_SECRET = Config.JWT_SECRET_KEY

class TokenService:
    """Token管理服务"""
    
    def __init__(self):
        self.redis = get_redis_service()
        self.access_token_expires = 1800  # 30分钟
        self.refresh_token_expires = 604800  # 7天
        self.secret_key = "your-secret-key"  # 应从配置文件读取
        
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

def verify_token(token: str) -> dict:
    """验证JWT token"""
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        logger.warning("Token已过期")
        raise
    except jwt.InvalidTokenError:
        logger.warning("无效的Token")
        raise

def auth_required(f):
    """基本的认证检查装饰器"""
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            # 从请求头获取token
            auth_header = request.headers.get('Authorization')
            if not auth_header:
                return jsonify({
                    'success': False,
                    'error': '缺少Authorization头'
                }), 401
                
            token = auth_header.split(" ")[1]
            
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
            logger.error(f"认证失败: {str(e)}")
            return jsonify({
                'success': False,
                'error': f'认证失败: {str(e)}'
            }), 401
            
    return decorated

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
                    'success': False,
                    'error': '没有所需权限'
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
                'success': False,
                'error': '需要管理员权限'
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
                'success': False,
                'error': '需要超级管理员权限'
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