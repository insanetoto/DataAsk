# -*- coding: utf-8 -*-
"""
权限管理服务模块
提供权限验证和RBAC权限控制功能
"""
import json
import logging
from typing import Optional, Dict, Any, List
from tools.database import get_database_service
from tools.redis_service import get_redis_service

logger = logging.getLogger(__name__)

class PermissionService:
    """权限管理服务类"""
    
    def __init__(self):
        self.cache_prefix = "permission:"
        self.user_permissions_prefix = "user_permissions:"
        self.cache_timeout = 3600  # 缓存1小时
        self.list_cache_key = "permission:list"
        
    def get_permissions_list(self, page: int = 1, page_size: int = 10, status: Optional[int] = None,
                           resource_type: Optional[str] = None, keyword: Optional[str] = None) -> Dict[str, Any]:
        """获取权限列表"""
        try:
            # 生成缓存键
            cache_key = f"{self.list_cache_key}:{page}:{page_size}:{status}:{resource_type or ''}:{keyword or ''}"
            redis_service = get_redis_service()
            cached_data = redis_service.get_cache(cache_key)
            
            if cached_data:
                logger.info(f"从缓存获取权限列表: page={page}, page_size={page_size}")
                return {
                    'success': True,
                    'data': json.loads(cached_data)
                }
            
            db_service = get_database_service()
            
            # 构建查询条件
            where_conditions = []
            params = {}
            
            if status is not None:
                where_conditions.append("status = :status")
                params['status'] = status
            
            if resource_type:
                where_conditions.append("resource_type = :resource_type")
                params['resource_type'] = resource_type
                
            if keyword:
                where_conditions.append("(permission_code LIKE :keyword OR permission_name LIKE :keyword)")
                params['keyword'] = f'%{keyword}%'
            
            where_clause = ""
            if where_conditions:
                where_clause = "WHERE " + " AND ".join(where_conditions)
            
            # 查询总数
            count_sql = f"""
            SELECT COUNT(*) as total 
            FROM permissions
            {where_clause}
            """
            count_result = db_service.execute_query(count_sql, params)
            total = count_result[0]['total']
            
            # 计算分页参数
            offset = (page - 1) * page_size
            total_pages = (total + page_size - 1) // page_size
            
            # 查询数据
            params['limit'] = page_size
            params['offset'] = offset
            
            data_sql = f"""
            SELECT id, permission_code, permission_name, api_path, api_method,
                   resource_type, description, status, created_at, updated_at
            FROM permissions
            {where_clause}
            ORDER BY resource_type, permission_code
            LIMIT :limit OFFSET :offset
            """
            
            data_result = db_service.execute_query(data_sql, params)
            
            result_data = {
                'list': data_result,
                'pagination': {
                    'page': page,
                    'page_size': page_size,
                    'total': total,
                    'total_pages': total_pages,
                    'has_next': page < total_pages,
                    'has_prev': page > 1
                }
            }
            
            # 缓存结果
            redis_service.set_cache(cache_key, json.dumps(result_data, default=str), 600)  # 10分钟
            
            return {
                'success': True,
                'data': result_data
            }
            
        except Exception as e:
            logger.error(f"获取权限列表失败: {str(e)}")
            return {
                'success': False,
                'error': f'获取权限列表失败: {str(e)}'
            }
    
    def get_user_permissions(self, user_id: int) -> Dict[str, Any]:
        """获取用户权限列表（通过角色）"""
        try:
            # 先检查缓存
            cache_key = f"{self.user_permissions_prefix}{user_id}"
            redis_service = get_redis_service()
            cached_data = redis_service.get_cache(cache_key)
            
            if cached_data:
                logger.info(f"从缓存获取用户权限: user_id={user_id}")
                return {
                    'success': True,
                    'data': json.loads(cached_data)
                }
            
            db_service = get_database_service()
            
            # 获取用户角色权限
            sql = """
            SELECT DISTINCT p.id, p.permission_code, p.permission_name, p.api_path, 
                   p.api_method, p.resource_type, p.description, p.status
            FROM permissions p
            JOIN role_permissions rp ON p.id = rp.permission_id
            JOIN roles r ON rp.role_id = r.id
            JOIN users u ON u.role_id = r.id
            WHERE u.id = :user_id AND u.status = 1 AND r.status = 1 AND p.status = 1
            ORDER BY p.resource_type, p.permission_code
            """
            
            result = db_service.execute_query(sql, {'user_id': user_id})
            
            # 缓存结果
            redis_service.set_cache(cache_key, json.dumps(result, default=str), self.cache_timeout)
            
            return {
                'success': True,
                'data': result
            }
            
        except Exception as e:
            logger.error(f"获取用户权限失败: {str(e)}")
            return {
                'success': False,
                'error': f'获取用户权限失败: {str(e)}'
            }
    
    def check_permission(self, user_id: int, api_path: str, api_method: str) -> Dict[str, Any]:
        """检查用户是否有指定API的权限"""
        try:
            # 获取用户权限
            user_permissions = self.get_user_permissions(user_id)
            if not user_permissions['success']:
                return user_permissions
            
            permissions = user_permissions['data']
            
            # 检查权限
            for permission in permissions:
                # 精确匹配
                if permission['api_path'] == api_path and permission['api_method'].upper() == api_method.upper():
                    return {
                        'success': True,
                        'has_permission': True,
                        'permission': permission
                    }
                
                # 通配符匹配（如 /api/v1/users/* 匹配 /api/v1/users/123）
                if permission['api_path'].endswith('*'):
                    base_path = permission['api_path'][:-1]  # 移除 *
                    if api_path.startswith(base_path) and permission['api_method'].upper() == api_method.upper():
                        return {
                            'success': True,
                            'has_permission': True,
                            'permission': permission
                        }
            
            return {
                'success': True,
                'has_permission': False,
                'message': f'用户没有访问 {api_method} {api_path} 的权限'
            }
            
        except Exception as e:
            logger.error(f"检查权限失败: {str(e)}")
            return {
                'success': False,
                'error': f'检查权限失败: {str(e)}'
            }
    
    def get_user_org_filter(self, user_id: int) -> Dict[str, Any]:
        """获取用户的机构数据过滤条件"""
        try:
            db_service = get_database_service()
            
            # 获取用户信息和角色
            sql = """
            SELECT u.id, u.org_code, u.username, r.role_level, r.role_code
            FROM users u
            JOIN roles r ON u.role_id = r.id
            WHERE u.id = :user_id AND u.status = 1
            """
            
            result = db_service.execute_query(sql, {'user_id': user_id})
            
            if not result:
                return {
                    'success': False,
                    'error': '用户不存在或已禁用'
                }
            
            user_info = result[0]
            
            # 根据角色等级确定数据过滤范围
            if user_info['role_level'] == 1:  # 超级管理员
                # 可以访问所有机构的数据
                filter_condition = {
                    'type': 'all',
                    'org_codes': None,
                    'message': '超级管理员可访问所有数据'
                }
            elif user_info['role_level'] == 2:  # 机构管理员
                # 只能访问本机构的数据
                filter_condition = {
                    'type': 'org',
                    'org_codes': [user_info['org_code']],
                    'message': f'机构管理员只能访问机构 {user_info["org_code"]} 的数据'
                }
            else:  # 普通用户
                # 只能访问本机构的数据
                filter_condition = {
                    'type': 'org',
                    'org_codes': [user_info['org_code']],
                    'message': f'普通用户只能访问机构 {user_info["org_code"]} 的数据'
                }
            
            return {
                'success': True,
                'data': filter_condition
            }
            
        except Exception as e:
            logger.error(f"获取用户机构过滤条件失败: {str(e)}")
            return {
                'success': False,
                'error': f'获取用户机构过滤条件失败: {str(e)}'
            }
    
    def apply_org_filter(self, sql: str, params: dict, user_id: int, table_alias: str = None) -> Dict[str, Any]:
        """为SQL查询应用机构数据过滤"""
        try:
            # 获取用户机构过滤条件
            filter_result = self.get_user_org_filter(user_id)
            if not filter_result['success']:
                return filter_result
            
            filter_condition = filter_result['data']
            
            # 如果是超级管理员，不需要过滤
            if filter_condition['type'] == 'all':
                return {
                    'success': True,
                    'sql': sql,
                    'params': params
                }
            
            # 为机构管理员和普通用户添加机构过滤
            org_codes = filter_condition['org_codes']
            
            if len(org_codes) == 1:
                # 单个机构
                table_prefix = f"{table_alias}." if table_alias else ""
                org_filter = f" AND {table_prefix}org_code = :filter_org_code"
                params['filter_org_code'] = org_codes[0]
            else:
                # 多个机构（预留扩展）
                table_prefix = f"{table_alias}." if table_alias else ""
                placeholders = ', '.join([f':filter_org_code_{i}' for i in range(len(org_codes))])
                org_filter = f" AND {table_prefix}org_code IN ({placeholders})"
                for i, org_code in enumerate(org_codes):
                    params[f'filter_org_code_{i}'] = org_code
            
            # 将过滤条件添加到SQL
            if ' WHERE ' in sql.upper():
                filtered_sql = sql + org_filter
            else:
                # 如果没有WHERE子句，需要添加WHERE
                filtered_sql = sql + f" WHERE 1=1{org_filter}"
            
            return {
                'success': True,
                'sql': filtered_sql,
                'params': params
            }
            
        except Exception as e:
            logger.error(f"应用机构过滤失败: {str(e)}")
            return {
                'success': False,
                'error': f'应用机构过滤失败: {str(e)}'
            }
    
    def clear_user_permissions_cache(self, user_id: int):
        """清除用户权限缓存"""
        try:
            redis_service = get_redis_service()
            redis_service.delete_cache(f"{self.user_permissions_prefix}{user_id}")
        except Exception as e:
            logger.warning(f"清除用户权限缓存失败: {str(e)}")
    
    def _clear_list_cache(self):
        """清除权限列表缓存"""
        try:
            redis_service = get_redis_service()
            keys = redis_service.get_keys_by_pattern(f"{self.list_cache_key}:*")
            if keys:
                for key in keys:
                    redis_service.delete_cache(key)
        except Exception as e:
            logger.warning(f"清除权限列表缓存失败: {str(e)}")

# 全局权限服务实例
permission_service = None

def init_permission_service():
    """初始化权限管理服务"""
    global permission_service
    permission_service = PermissionService()
    return permission_service

def get_permission_service():
    """获取权限管理服务实例"""
    if permission_service is None:
        return init_permission_service()
    return permission_service 