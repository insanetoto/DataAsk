# -*- coding: utf-8 -*-
"""
权限验证中间件模块
提供API权限验证和数据范围过滤功能
"""
import logging
from functools import wraps
from flask import request, g, jsonify
from typing import Dict, Any, Optional
from service.enhanced_permission_service import get_enhanced_permission_service_instance
from tools.exceptions import AuthorizationException, AuthenticationException

logger = logging.getLogger(__name__)

class PermissionMiddleware:
    """权限验证中间件，完全兼容现有ACL框架"""
    
    @staticmethod
    def check_api_permission(user_info: dict, api_path: str, method: str) -> bool:
        """
        检查API权限，兼容ACL ability验证
        """
        try:
            abilities = user_info.get('ability', [])
            
            # 超级管理员拥有所有权限
            if '*' in abilities:
                return True
                
            # 根据API路径和方法查找对应的权限编码
            permission_service = get_enhanced_permission_service_instance()
            required_permission = permission_service.get_permission_by_api(api_path, method)
            
            if not required_permission:
                return True  # 如果没有配置权限要求，默认允许
                
            return required_permission in abilities
            
        except Exception as e:
            logger.error(f"检查API权限失败: {str(e)}")
            return False
    
    @staticmethod
    def apply_data_filter(base_sql: str, user_info: dict, table_alias: str = '') -> str:
        """应用数据范围过滤"""
        try:
            permission_service = get_enhanced_permission_service_instance()
            return permission_service.apply_data_scope_filter(base_sql, user_info, table_alias)
        except Exception as e:
            logger.error(f"应用数据过滤失败: {str(e)}")
            return base_sql
    
    @staticmethod
    def get_user_acl_info(user_id: int) -> Optional[Dict[str, Any]]:
        """获取用户ACL信息"""
        try:
            permission_service = get_enhanced_permission_service_instance()
            acl_config = permission_service.get_user_acl_config(user_id)
            
            # 获取用户基本信息
            user_info = permission_service.get_user_with_role(user_id)
            if not user_info:
                return None
                
            # 合并ACL配置和用户信息
            return {
                'user_id': user_id,
                'username': user_info['username'],
                'user_code': user_info['user_code'],
                'org_code': user_info['org_code'],
                'role_code': user_info['role_code'],
                'role_level': user_info['role_level'],
                'dataScope': acl_config.get('dataScope'),
                'orgCode': acl_config.get('orgCode'),
                'role': acl_config.get('role', []),
                'ability': acl_config.get('ability', []),
                'mode': acl_config.get('mode', 'oneOf')
            }
            
        except Exception as e:
            logger.error(f"获取用户ACL信息失败: {str(e)}")
            return None

def require_permission(permission_code: str):
    """
    权限验证装饰器
    用于API接口的权限控制
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                # 检查用户是否已登录
                if not hasattr(g, 'current_user') or not g.current_user:
                    raise AuthenticationException("用户未登录")
                
                user_id = g.current_user.get('user_id')
                if not user_id:
                    raise AuthenticationException("无效的用户信息")
                
                # 获取用户ACL信息
                middleware = PermissionMiddleware()
                user_acl_info = middleware.get_user_acl_info(user_id)
                
                if not user_acl_info:
                    raise AuthorizationException("无法获取用户权限信息")
                
                # 检查权限
                abilities = user_acl_info.get('ability', [])
                if '*' not in abilities and permission_code not in abilities:
                    raise AuthorizationException(f"权限不足，需要权限: {permission_code}")
                
                # 将用户ACL信息添加到g对象，供后续使用
                g.user_acl_info = user_acl_info
                
                return f(*args, **kwargs)
                
            except (AuthenticationException, AuthorizationException):
                raise
            except Exception as e:
                logger.error(f"权限验证失败: {str(e)}")
                raise AuthorizationException("权限验证失败")
                
        return decorated_function
    return decorator

def require_role(role_codes):
    """
    角色验证装饰器
    用于基于角色的访问控制
    """
    if isinstance(role_codes, str):
        role_codes = [role_codes]
        
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                # 检查用户是否已登录
                if not hasattr(g, 'current_user') or not g.current_user:
                    raise AuthenticationException("用户未登录")
                
                user_id = g.current_user.get('user_id')
                if not user_id:
                    raise AuthenticationException("无效的用户信息")
                
                # 获取用户ACL信息
                middleware = PermissionMiddleware()
                user_acl_info = middleware.get_user_acl_info(user_id)
                
                if not user_acl_info:
                    raise AuthorizationException("无法获取用户角色信息")
                
                # 检查角色
                user_roles = user_acl_info.get('role', [])
                if not any(role in user_roles for role in role_codes):
                    raise AuthorizationException(f"角色权限不足，需要角色: {', '.join(role_codes)}")
                
                # 将用户ACL信息添加到g对象，供后续使用
                g.user_acl_info = user_acl_info
                
                return f(*args, **kwargs)
                
            except (AuthenticationException, AuthorizationException):
                raise
            except Exception as e:
                logger.error(f"角色验证失败: {str(e)}")
                raise AuthorizationException("角色验证失败")
                
        return decorated_function
    return decorator

def apply_data_scope_filter(base_sql: str, table_alias: str = '') -> str:
    """
    应用数据范围过滤的辅助函数
    可在业务逻辑中直接调用
    """
    try:
        if hasattr(g, 'user_acl_info') and g.user_acl_info:
            middleware = PermissionMiddleware()
            return middleware.apply_data_filter(base_sql, g.user_acl_info, table_alias)
        else:
            logger.warning("未找到用户ACL信息，跳过数据范围过滤")
            return base_sql
            
    except Exception as e:
        logger.error(f"应用数据范围过滤失败: {str(e)}")
        return base_sql

def get_current_user_org_code() -> Optional[str]:
    """获取当前用户的机构编码"""
    try:
        if hasattr(g, 'user_acl_info') and g.user_acl_info:
            return g.user_acl_info.get('org_code')
        return None
    except Exception as e:
        logger.error(f"获取用户机构编码失败: {str(e)}")
        return None

def get_current_user_data_scope() -> str:
    """获取当前用户的数据范围"""
    try:
        if hasattr(g, 'user_acl_info') and g.user_acl_info:
            return g.user_acl_info.get('dataScope', 'SELF')
        return 'SELF'
    except Exception as e:
        logger.error(f"获取用户数据范围失败: {str(e)}")
        return 'SELF'

def has_permission(permission_code: str) -> bool:
    """检查当前用户是否具有指定权限"""
    try:
        if hasattr(g, 'user_acl_info') and g.user_acl_info:
            abilities = g.user_acl_info.get('ability', [])
            return '*' in abilities or permission_code in abilities
        return False
    except Exception as e:
        logger.error(f"检查权限失败: {str(e)}")
        return False

def has_role(role_code: str) -> bool:
    """检查当前用户是否具有指定角色"""
    try:
        if hasattr(g, 'user_acl_info') and g.user_acl_info:
            roles = g.user_acl_info.get('role', [])
            return role_code in roles
        return False
    except Exception as e:
        logger.error(f"检查角色失败: {str(e)}")
        return False 