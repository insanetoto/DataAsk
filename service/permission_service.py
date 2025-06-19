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
from service.role_service import get_role_service

logger = logging.getLogger(__name__)

class PermissionService:
    """权限管理服务类"""
    
    def __init__(self):
        """初始化权限服务"""
        self.db_service = get_database_service()
        self.redis_service = get_redis_service()
        self.cache_prefix = "permission:"
        self.user_permissions_prefix = "user_permissions:"
        self.cache_timeout = 3600  # 缓存1小时
        self.list_cache_key = "permission:list"
        
    def get_permissions_list(self, page: int = 1, page_size: int = 10, keyword: str = None) -> Dict[str, Any]:
        """
        获取权限列表
        :param page: 页码
        :param page_size: 每页数量
        :param keyword: 搜索关键词
        :return: 权限列表
        """
        try:
            # 构建基础SQL
            sql = """
                SELECT id, permission_code, permission_name, description, status, created_at, updated_at
                FROM permissions
                WHERE status = 1
            """
            params = {}
            
            # 添加搜索条件
            if keyword:
                sql += " AND (permission_code LIKE :keyword OR permission_name LIKE :keyword OR description LIKE :keyword)"
                params['keyword'] = f"%{keyword}%"
            
            # 添加分页
            sql += " ORDER BY id DESC LIMIT :limit OFFSET :offset"
            params['limit'] = page_size
            params['offset'] = (page - 1) * page_size
            
            # 执行查询
            result = self.db_service.execute_query(sql, params)
            
            # 获取总数
            count_sql = """
                SELECT COUNT(*) as total
                FROM permissions
                WHERE status = 1
            """
            count_params = {}
            if keyword:
                count_sql += " AND (permission_code LIKE :keyword OR permission_name LIKE :keyword OR description LIKE :keyword)"
                count_params['keyword'] = f"%{keyword}%"
            
            count_result = self.db_service.execute_query(count_sql, count_params)
            total = count_result[0]['total'] if count_result else 0
            
            return {
                'success': True,
                'data': {
                    'list': result,
                    'total': total,
                    'page': page,
                    'page_size': page_size
                }
            }
        except Exception as e:
            logger.error(f"获取权限列表失败: {str(e)}")
            raise Exception(f"获取权限列表失败: {str(e)}")
    
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
    
    def assign_permissions_to_role(self, role_id: int, permission_codes: List[str]) -> Dict[str, Any]:
        """
        为角色分配权限
        :param role_id: 角色ID
        :param permission_codes: 权限代码列表
        :return: 分配结果
        """
        try:
            # 获取权限ID列表
            sql = """
                SELECT id, permission_code
                FROM permissions
                WHERE permission_code IN :permission_codes AND status = 1
            """
            permissions = self.db_service.execute_query(sql, {'permission_codes': tuple(permission_codes)})
            
            if not permissions:
                raise Exception("没有找到有效的权限")
            
            # 检查权限是否都存在
            found_codes = {p['permission_code'] for p in permissions}
            missing_codes = set(permission_codes) - found_codes
            if missing_codes:
                raise Exception(f"权限代码 {', '.join(missing_codes)} 不存在或已禁用")
            
            # 删除现有权限
            delete_sql = """
                DELETE FROM role_permissions
                WHERE role_id = :role_id
            """
            self.db_service.execute_update(delete_sql, {'role_id': role_id})
            
            # 添加新权限
            insert_sql = """
                INSERT INTO role_permissions (role_id, permission_id)
                VALUES (:role_id, :permission_id)
            """
            for permission in permissions:
                self.db_service.execute_update(insert_sql, {
                    'role_id': role_id,
                    'permission_id': permission['id']
                })
            
            # 清除缓存
            self.redis_service.delete(f"role_permissions:{role_id}")
            
            return {
                'success': True,
                'message': '权限分配成功',
                'data': {
                    'role_id': role_id,
                    'permissions': [p['permission_code'] for p in permissions]
                }
            }
        except Exception as e:
            logger.error(f"权限分配失败: {str(e)}")
            raise Exception(f"权限分配失败: {str(e)}")
    
    def revoke_permissions_from_role(self, role_id: int, permission_ids: List[int]) -> Dict[str, Any]:
        """从角色回收指定权限"""
        try:
            db_service = get_database_service()
            
            # 检查角色是否存在
            role_service = get_role_service()
            role = role_service._get_role_by_id_without_status_check(role_id)
            if not role['success'] or not role['data']:
                return {
                    'success': False,
                    'error': '角色不存在'
                }
            
            # 删除指定权限
            sql = """
            DELETE FROM role_permissions 
            WHERE role_id = :role_id AND permission_id IN :permission_ids
            """
            
            db_service.execute_update(sql, {
                'role_id': role_id,
                'permission_ids': tuple(permission_ids)
            })
            
            # 清除相关缓存
            self.clear_role_permissions_cache(role_id)
            
            return {
                'success': True,
                'message': '权限回收成功'
            }
            
        except Exception as e:
            logger.error(f"回收权限失败: {str(e)}")
            return {
                'success': False,
                'error': f'回收权限失败: {str(e)}'
            }
    
    def get_inherited_permissions(self, role_id: int) -> Dict[str, Any]:
        """获取角色继承的权限（包括直接权限和继承权限）"""
        try:
            db_service = get_database_service()
            
            # 获取角色信息
            role_service = get_role_service()
            role = role_service._get_role_by_id_without_status_check(role_id)
            if not role['success'] or not role['data']:
                return {
                    'success': False,
                    'error': '角色不存在'
                }
            
            # 获取角色级别
            role_level = role['data']['role_level']
            
            # 获取所有权限（包括继承的权限）
            sql = """
            SELECT DISTINCT p.id, p.permission_code, p.permission_name, p.api_path, 
                   p.api_method, p.resource_type, p.description, p.status,
                   r.role_level as from_role_level,
                   r.role_name as from_role_name
            FROM permissions p
            JOIN role_permissions rp ON p.id = rp.permission_id
            JOIN roles r ON rp.role_id = r.id
            WHERE r.role_level <= :role_level
              AND p.status = 1
              AND r.status = 1
            ORDER BY p.resource_type, p.permission_code
            """
            
            result = db_service.execute_query(sql, {'role_level': role_level})
            
            return {
                'success': True,
                'data': result
            }
            
        except Exception as e:
            logger.error(f"获取继承权限失败: {str(e)}")
            return {
                'success': False,
                'error': f'获取继承权限失败: {str(e)}'
            }
    
    def clear_role_permissions_cache(self, role_id: int):
        """清除角色权限相关的缓存"""
        try:
            # 获取角色下的所有用户
            db_service = get_database_service()
            sql = """
            SELECT id FROM users WHERE role_id = :role_id AND status = 1
            """
            users = db_service.execute_query(sql, {'role_id': role_id})
            
            # 清除每个用户的权限缓存
            redis_service = get_redis_service()
            for user in users:
                cache_key = f"{self.user_permissions_prefix}{user['id']}"
                redis_service.delete_cache(cache_key)
                
        except Exception as e:
            logger.warning(f"清除角色权限缓存失败: {str(e)}")
    
    def check_permission_with_inheritance(self, user_id: int, api_path: str, api_method: str) -> Dict[str, Any]:
        """检查用户是否有指定API的权限（包括继承的权限）"""
        try:
            # 获取用户角色信息
            db_service = get_database_service()
            sql = """
            SELECT r.role_level
            FROM users u
            JOIN roles r ON u.role_id = r.id
            WHERE u.id = :user_id AND u.status = 1 AND r.status = 1
            """
            
            result = db_service.execute_query(sql, {'user_id': user_id})
            if not result:
                return {
                    'success': False,
                    'error': '用户不存在或已禁用'
                }
            
            role_level = result[0]['role_level']
            
            # 检查权限（包括继承的权限）
            permission_sql = """
            SELECT p.id, p.permission_code, p.permission_name, p.api_path, p.api_method
            FROM permissions p
            JOIN role_permissions rp ON p.id = rp.permission_id
            JOIN roles r ON rp.role_id = r.id
            WHERE r.role_level <= :role_level
              AND p.status = 1
              AND r.status = 1
              AND (
                  p.api_path = :api_path
                  OR (
                      p.api_path LIKE '%*'
                      AND :api_path LIKE CONCAT(SUBSTRING(p.api_path, 1, LENGTH(p.api_path) - 1), '%')
                  )
              )
              AND p.api_method = :api_method
            """
            
            params = {
                'role_level': role_level,
                'api_path': api_path,
                'api_method': api_method.upper()
            }
            
            permissions = db_service.execute_query(permission_sql, params)
            
            if permissions:
                return {
                    'success': True,
                    'has_permission': True,
                    'permission': permissions[0]
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

    def get_role_permissions(self, role_id: int) -> Dict[str, Any]:
        """
        获取角色的权限列表
        :param role_id: 角色ID
        :return: 权限列表
        """
        try:
            # 先从缓存中获取
            cache_key = f"role_permissions:{role_id}"
            cached_permissions = self.redis_service.get(cache_key)
            if cached_permissions:
                return {
                    'success': True,
                    'data': json.loads(cached_permissions)
                }

            # 从数据库中获取
            sql = """
                SELECT p.permission_code
                FROM role_permissions rp
                JOIN permissions p ON rp.permission_id = p.id
                WHERE rp.role_id = :role_id AND p.status = 1
            """
            result = self.db_service.execute_query(sql, {'role_id': role_id})
            permissions = [row['permission_code'] for row in result]

            # 更新缓存
            self.redis_service.set(cache_key, json.dumps(permissions), ex=3600)
            
            return {
                'success': True,
                'data': permissions
            }
        except Exception as e:
            logger.error(f"获取角色权限失败: {str(e)}")
            raise Exception(f"获取角色权限失败: {str(e)}")

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