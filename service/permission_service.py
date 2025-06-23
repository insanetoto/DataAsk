# -*- coding: utf-8 -*-
"""
权限管理服务模块
提供权限的增删改查功能，集成Redis缓存
"""
import json
import logging
from typing import Optional, Dict, Any, List
from tools.database import DatabaseService, get_database_service
from tools.redis_service import RedisService, get_redis_service
from sqlalchemy import select, func, text
from sqlalchemy.orm import Session
from tools.di_container import DIContainer
from models import Permission, Role

logger = logging.getLogger(__name__)

class PermissionService:
    """权限管理服务类"""
    
    def __init__(self, redis_service: RedisService = None, db_service: DatabaseService = None, role_service = None):
        self.cache_prefix = "permission:"
        self.cache_timeout = 3600  # 缓存1小时
        self.list_cache_key = "permission:list"
        self.redis = redis_service or get_redis_service()
        self.db_service = db_service or get_database_service()
        self.role_service = role_service
        
    def get_user_permissions(self, user_id: int) -> Dict[str, Any]:
        """获取用户权限列表"""
        try:
            # 先检查缓存
            cache_key = f"{self.cache_prefix}user:{user_id}"
            cached_data = self.redis.get_cache(cache_key)
            
            if cached_data:
                logger.info(f"从缓存获取用户权限: user_id={user_id}")
                # cached_data 已经是字典对象，不需要再json.loads
                permission_data = cached_data if isinstance(cached_data, dict) else json.loads(cached_data)
                return {
                    'success': True,
                    'data': permission_data
                }
            
            # 从数据库查询
            with self.db_service.get_session() as session:
                # 获取用户角色的权限
                sql = """
                SELECT DISTINCT p.* 
                FROM permissions p
                JOIN role_permissions rp ON p.id = rp.permission_id
                JOIN users u ON u.role_id = rp.role_id
                WHERE u.id = :user_id AND p.status = 1
                """
                permissions = session.execute(text(sql), {'user_id': user_id}).fetchall()
                
                if not permissions:
                    return {
                        'success': True,
                        'data': []
                    }
                
                # 格式化权限数据
                permission_list = []
                for p in permissions:
                    permission_data = {
                        'id': p.id,
                        'permission_code': p.permission_code,
                        'permission_name': p.permission_name,
                        'api_path': p.api_path,
                        'api_method': p.api_method,
                        'resource_type': p.resource_type,
                        'description': p.description,
                        'status': p.status
                    }
                    permission_list.append(permission_data)
                
                # 缓存权限数据
                self.redis.set_cache(cache_key, json.dumps(permission_list), self.cache_timeout)
                
                return {
                    'success': True,
                    'data': permission_list
                }
                
        except Exception as e:
            logger.error(f"获取用户权限失败: {str(e)}")
            return {
                'success': False,
                'error': f'获取用户权限失败: {str(e)}'
            }
    
    def check_permission(self, user_id: int, permission_code: str) -> Dict[str, Any]:
        """检查用户是否有指定权限"""
        try:
            # 获取用户权限列表
            user_permissions = self.get_user_permissions(user_id)
            if not user_permissions['success']:
                return user_permissions
            
            # 检查权限
            has_permission = any(
                p['permission_code'] == permission_code 
                for p in user_permissions['data']
            )
            
            return {
                'success': True,
                'data': {
                    'has_permission': has_permission
                }
            }
            
        except Exception as e:
            logger.error(f"检查用户权限失败: {str(e)}")
            return {
                'success': False,
                'error': f'检查用户权限失败: {str(e)}'
            }
    
    def assign_permissions_to_role(self, role_id: int, permission_codes: List[str]) -> Dict[str, Any]:
        """为角色分配权限"""
        try:
            with self.db_service.get_session() as session:
                # 获取角色
                role = session.get(Role, role_id)
                if not role:
                    return {
                        'success': False,
                        'error': '角色不存在'
                    }
                
                # 获取权限
                permissions = session.query(Permission).filter(
                    Permission.permission_code.in_(permission_codes)
                ).all()
                
                # 设置权限
                role.permissions = permissions
                session.commit()
                
                # 清除相关缓存
                self._clear_role_permissions_cache(role_id)
                
                return {
                    'success': True,
                    'message': '权限分配成功'
                }
                
        except Exception as e:
            logger.error(f"为角色分配权限失败: {str(e)}")
            return {
                'success': False,
                'error': f'为角色分配权限失败: {str(e)}'
            }
    
    def revoke_permissions_from_role(self, role_id: int, permission_ids: List[int]) -> Dict[str, Any]:
        """从角色移除权限"""
        try:
            with self.db_service.get_session() as session:
                # 获取角色
                role = session.get(Role, role_id)
                if not role:
                    return {
                        'success': False,
                        'error': '角色不存在'
                    }
                
                # 获取要移除的权限
                permissions_to_remove = session.query(Permission).filter(
                    Permission.id.in_(permission_ids)
                ).all()
                
                # 移除权限
                for permission in permissions_to_remove:
                    if permission in role.permissions:
                        role.permissions.remove(permission)
                
                session.commit()
                
                # 清除相关缓存
                self._clear_role_permissions_cache(role_id)
                
                return {
                    'success': True,
                    'message': '权限移除成功'
                }
                
        except Exception as e:
            logger.error(f"从角色移除权限失败: {str(e)}")
            return {
                'success': False,
                'error': f'从角色移除权限失败: {str(e)}'
            }
    
    def _clear_role_permissions_cache(self, role_id: int):
        """清除角色权限相关的缓存"""
        try:
            # 获取角色下的所有用户
            with self.db_service.get_session() as session:
                users = session.query('id').select_from('users').filter_by(role_id=role_id).all()
                user_ids = [u.id for u in users]
                
                # 清除每个用户的权限缓存
                for user_id in user_ids:
                    self.redis.delete_cache(f"{self.cache_prefix}user:{user_id}")
                    
        except Exception as e:
            logger.warning(f"清除角色权限缓存失败: {str(e)}")
    
    def get_permissions_list(self, page: int = 1, page_size: int = 10, 
                           keyword: str = None, status: int = None) -> Dict[str, Any]:
        """获取权限列表"""
        try:
            # 生成缓存键
            cache_key = f"{self.list_cache_key}:{page}:{page_size}:{keyword or ''}:{status or ''}"
            cached_data = self.redis.get_cache(cache_key)
            
            if cached_data:
                logger.info(f"从缓存获取权限列表: page={page}, page_size={page_size}")
                # cached_data 已经是字典对象，不需要再json.loads
                list_data = cached_data if isinstance(cached_data, dict) else json.loads(cached_data)
                return {
                    'success': True,
                    'data': list_data
                }
            
            # 从数据库查询
            with self.db_service.get_session() as session:
                # 构建查询条件
                where_conditions = []
                params = {}
                
                if status is not None:
                    where_conditions.append("status = :status")
                    params['status'] = status
                    
                if keyword:
                    where_conditions.append("(permission_code LIKE :keyword OR permission_name LIKE :keyword)")
                    params['keyword'] = f'%{keyword}%'
                
                where_clause = ""
                if where_conditions:
                    where_clause = "WHERE " + " AND ".join(where_conditions)
                
                # 查询总数
                count_sql = f"SELECT COUNT(*) as total FROM permissions {where_clause}"
                count_result = session.execute(text(count_sql), params).fetchone()
                total = count_result.total
                
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
                ORDER BY created_at DESC
                LIMIT :limit OFFSET :offset
                """
                
                permissions = session.execute(text(data_sql), params).fetchall()
                
                # 格式化权限数据
                permission_list = []
                for p in permissions:
                    permission_data = {
                        'id': p.id,
                        'permission_code': p.permission_code,
                        'permission_name': p.permission_name,
                        'api_path': p.api_path,
                        'api_method': p.api_method,
                        'resource_type': p.resource_type,
                        'description': p.description,
                        'status': p.status,
                        'created_at': str(p.created_at),
                        'updated_at': str(p.updated_at) if p.updated_at else None
                    }
                    permission_list.append(permission_data)
                
                result_data = {
                    'list': permission_list,
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
                self.redis.set_cache(cache_key, json.dumps(result_data, default=str), 600)  # 10分钟
                
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
    
    def get_permission_by_id(self, permission_id: int) -> Dict[str, Any]:
        """根据ID获取权限详情"""
        try:
            # 先检查缓存
            cache_key = f"{self.cache_prefix}detail:{permission_id}"
            cached_data = self.redis.get_cache(cache_key)
            
            if cached_data:
                logger.info(f"从缓存获取权限详情: permission_id={permission_id}")
                # cached_data 已经是字典对象，不需要再json.loads
                permission_data = cached_data if isinstance(cached_data, dict) else json.loads(cached_data)
                return {
                    'success': True,
                    'data': permission_data
                }
            
            # 从数据库查询
            with self.db_service.get_session() as session:
                permission = session.get(Permission, permission_id)
                
                if not permission:
                    return {
                        'success': False,
                        'error': '权限不存在'
                    }
                
                permission_data = permission.to_dict()
                
                # 缓存权限详情
                self.redis.set_cache(cache_key, json.dumps(permission_data), self.cache_timeout)
                
                return {
                    'success': True,
                    'data': permission_data
                }
                
        except Exception as e:
            logger.error(f"获取权限详情失败: {str(e)}")
            return {
                'success': False,
                'error': f'获取权限详情失败: {str(e)}'
            }

    def get_permission_tree(self) -> Dict[str, Any]:
        """获取权限树型结构"""
        try:
            # 先检查缓存
            cache_key = f"{self.cache_prefix}tree"
            cached_data = self.redis.get_cache(cache_key)
            
            if cached_data:
                logger.info("从缓存获取权限树型结构")
                tree_data = cached_data if isinstance(cached_data, list) else json.loads(cached_data)
                return {
                    'success': True,
                    'data': tree_data
                }
            
            # 从数据库查询所有权限
            with self.db_service.get_session() as session:
                query = select(Permission).where(Permission.status == 1).order_by(Permission.resource_type, Permission.permission_code)
                permissions = session.scalars(query).all()
                
                if not permissions:
                    return {
                        'success': True,
                        'data': []
                    }
                
                # 按资源类型分组构建树型结构
                tree_data = []
                resource_groups = {}
                
                for permission in permissions:
                    perm_dict = permission.to_dict()
                    resource_type = permission.resource_type or 'other'
                    
                    if resource_type not in resource_groups:
                        resource_groups[resource_type] = {
                            'key': resource_type,
                            'title': self._get_resource_type_name(resource_type),
                            'children': [],
                            'expanded': True,
                            'isLeaf': False
                        }
                    
                    # 添加权限节点
                    permission_node = {
                        'key': f"permission_{permission.id}",
                        'title': f"{permission.permission_name} ({permission.api_method} {permission.api_path})",
                        'isLeaf': True,
                        'origin': perm_dict  # 保存原始数据供前端使用
                    }
                    
                    resource_groups[resource_type]['children'].append(permission_node)
                
                # 转换为数组格式
                for resource_type, group_data in resource_groups.items():
                    tree_data.append(group_data)
                
                # 缓存树型数据
                self.redis.set_cache(cache_key, json.dumps(tree_data), self.cache_timeout)
                
                return {
                    'success': True,
                    'data': tree_data
                }
                
        except Exception as e:
            logger.error(f"获取权限树型结构失败: {str(e)}")
            return {
                'success': False,
                'error': f'获取权限树型结构失败: {str(e)}'
            }
    
    def _get_resource_type_name(self, resource_type: str) -> str:
        """获取资源类型的中文名称"""
        type_names = {
            'user': '用户管理',
            'role': '角色管理', 
            'permission': '权限管理',
            'organization': '机构管理',
            'system': '系统管理',
            'ai': 'AI引擎',
            'ai-engine': 'AI引擎',
            'database': '数据库管理',
            'workspace': '工作空间',
            'other': '其他'
        }
        return type_names.get(resource_type, resource_type)

def get_permission_service_instance() -> PermissionService:
    """获取权限服务实例（单例模式）"""
    # 简化版本，直接返回新实例
    return PermissionService()

def get_permission_service() -> PermissionService:
    """获取权限服务实例（兼容旧代码）"""
    return get_permission_service_instance() 