# -*- coding: utf-8 -*-
"""
角色管理服务模块
提供角色的增删改查功能，集成Redis缓存
"""
import json
import logging
from typing import Optional, Dict, Any, List
from tools.database import DatabaseService, get_database_service
from tools.redis_service import RedisService, get_redis_service
from sqlalchemy import select, func, text
from sqlalchemy.orm import Session
from tools.di_container import DIContainer
from models import Role

logger = logging.getLogger(__name__)

class RoleService:
    """角色管理服务类"""
    
    def __init__(self, redis_service: RedisService = None, db_service: DatabaseService = None):
        self.cache_prefix = "role:"
        self.cache_timeout = 3600  # 缓存1小时
        self.list_cache_key = "role:list"
        self.redis = redis_service or get_redis_service()
        self.db_service = db_service or get_database_service()
        
    def create_role(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """创建角色"""
        try:
            # 验证必要字段
            required_fields = ['role_code', 'role_name', 'role_level']
            for field in required_fields:
                if field not in data or not str(data[field]).strip():
                    return {
                        'success': False,
                        'error': f'缺少必要字段: {field}'
                    }
            
            with self.db_service.get_session() as session:
                # 检查角色编码是否已存在
                existing_role = self.get_role_by_code(data['role_code'])
                if existing_role['success'] and existing_role['data']:
                    return {
                        'success': False,
                        'error': f'角色编码 {data["role_code"]} 已存在'
                    }
                

                
                # 验证超级管理员角色的唯一性
                if data['role_level'] == 1:  # 超级管理员
                    super_admin_check_sql = """
                    SELECT COUNT(*) as count 
                    FROM roles 
                    WHERE role_level = 1 AND status = 1
                    """
                    super_result = session.execute(text(super_admin_check_sql))
                    if super_result.scalar() > 0:
                        return {
                            'success': False,
                            'error': '系统已存在超级管理员角色'
                        }
                
                # 插入角色数据
                role = Role(**data)
                session.add(role)
                session.commit()
                session.refresh(role)
                
                # 获取新创建的角色信息
                new_role = self.get_role_by_code(data['role_code'])
                
                # 清除列表缓存
                self._clear_list_cache()
                
                logger.info(f"成功创建角色: {data['role_code']} - {data['role_name']}")
                
                return {
                    'success': True,
                    'data': new_role['data'],
                    'message': '角色创建成功'
                }
                
        except Exception as e:
            logger.error(f"创建角色失败: {str(e)}")
            return {
                'success': False,
                'error': f'创建角色失败: {str(e)}'
            }
    
    def get_role_by_id(self, role_id: int) -> Dict[str, Any]:
        """根据ID获取角色信息"""
        try:
            # 先检查缓存
            cache_key = f"{self.cache_prefix}id:{role_id}"
            cached_data = self.redis.get_cache(cache_key)
            
            if cached_data:
        
                # cached_data 已经是字典对象，不需要再json.loads
                role_data = cached_data if isinstance(cached_data, dict) else json.loads(cached_data)
                return {
                    'success': True,
                    'data': role_data
                }
            
            # 从数据库查询
            with self.db_service.get_session() as session:
                role = session.get(Role, role_id)
                
                if not role:
                    return {
                        'success': False,
                        'error': '角色不存在'
                    }
                
                role_info = role.to_dict()
                
                # 缓存数据
                self.redis.set_cache(cache_key, json.dumps(role_info, default=str), self.cache_timeout)
                
                return {
                    'success': True,
                    'data': role_info
                }
                
        except Exception as e:
            logger.error(f"根据ID获取角色信息失败: {str(e)}")
            return {
                'success': False,
                'error': f'获取角色信息失败: {str(e)}'
            }
    
    def get_role_by_code(self, role_code: str) -> Dict[str, Any]:
        """根据角色编码获取角色信息"""
        try:
            # 先检查缓存
            cache_key = f"{self.cache_prefix}code:{role_code}"
            cached_data = self.redis.get_cache(cache_key)
            
            if cached_data:
        
                # cached_data 已经是字典对象，不需要再json.loads
                role_data = cached_data if isinstance(cached_data, dict) else json.loads(cached_data)
                return {
                    'success': True,
                    'data': role_data
                }
            
            # 从数据库查询
            with self.db_service.get_session() as session:
                role = session.query(Role).filter(Role.role_code == role_code).first()
                
                if not role:
                    return {
                        'success': True,
                        'data': None
                    }
                
                role_info = role.to_dict()
                
                # 缓存数据
                self.redis.set_cache(cache_key, json.dumps(role_info, default=str), self.cache_timeout)
                
                return {
                    'success': True,
                    'data': role_info
                }
                
        except Exception as e:
            logger.error(f"根据编码获取角色信息失败: {str(e)}")
            return {
                'success': False,
                'error': f'获取角色信息失败: {str(e)}'
            }
    
    def get_roles_list(self, page: int = 1, page_size: int = 10, status: Optional[int] = None,
                      role_level: Optional[int] = None, keyword: Optional[str] = None) -> Dict[str, Any]:
        """获取角色列表"""
        try:
            # 生成缓存键
            cache_key = f"{self.list_cache_key}:{page}:{page_size}:{status}:{role_level or ''}:{keyword or ''}"
            cached_data = self.redis.get_cache(cache_key)
            
            if cached_data:
        
                # cached_data 已经是字典对象，不需要再json.loads
                list_data = cached_data if isinstance(cached_data, dict) else json.loads(cached_data)
                return {
                    'success': True,
                    'data': list_data
                }
            
            with self.db_service.get_session() as session:
                query = select(Role)
                if keyword:
                    query = query.where(
                        (Role.role_name.like(f"%{keyword}%")) |
                        (Role.role_code.like(f"%{keyword}%"))
                    )
                if status is not None:
                    query = query.where(Role.status == status)

                if role_level is not None:
                    query = query.where(Role.role_level == role_level)
                
                total = session.scalar(select(func.count()).select_from(query.subquery()))
                query = query.offset((page - 1) * page_size).limit(page_size)
                roles = session.scalars(query).all()
                
                # 构建角色列表
                role_list = [role.to_dict() for role in roles]
                
                result_data = {
                    'list': role_list,
                    'pagination': {
                        'page': page,
                        'page_size': page_size,
                        'total': total,
                        'total_pages': (total + page_size - 1) // page_size,
                        'has_next': page < (total + page_size - 1) // page_size,
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
            logger.error(f"获取角色列表失败: {str(e)}")
            return {
                'success': False,
                'error': f'获取角色列表失败: {str(e)}'
            }
    
    def get_role_permissions(self, role_id: int) -> Dict[str, Any]:
        """获取角色权限列表"""
        try:
            with self.db_service.get_session() as session:
                role = session.get(Role, role_id)
                if not role:
                    return {
                        'success': False,
                        'error': '角色不存在'
                    }
                
                permissions = [p.to_dict() for p in role.permissions]
                return {
                    'success': True,
                    'data': permissions
                }
        except Exception as e:
            logger.error(f"获取角色权限列表失败: {str(e)}")
            return {
                'success': False,
                'error': f'获取角色权限列表失败: {str(e)}'
            }
    
    def _format_role_data(self, role_data: Dict) -> Dict:
        """格式化角色数据"""
        formatted_data = {}
        for key, value in role_data.items():
            if value is not None:  # 只保留非空字段
                formatted_data[key] = value
        return formatted_data
    
    def _clear_role_cache(self, role_code: str, role_id: int):
        """清除角色相关缓存"""
        self.redis.delete_cache(f"{self.cache_prefix}code:{role_code}")
        self.redis.delete_cache(f"{self.cache_prefix}id:{role_id}")
        self._clear_list_cache()
    
    def _clear_list_cache(self):
        """清除列表缓存"""
        pattern = f"{self.list_cache_key}:*"
        self.redis.delete_pattern(pattern)
    
    def _get_role_by_id_without_status_check(self, role_id: int) -> Dict[str, Any]:
        """根据ID获取角色信息（不检查状态）"""
        try:
            with self.db_service.get_session() as session:
                role = session.get(Role, role_id)
                if not role:
                    return {
                        'success': False,
                        'error': '角色不存在'
                    }
                return {
                    'success': True,
                    'data': role.to_dict()
                }
        except Exception as e:
            logger.error(f"获取角色信息失败: {str(e)}")
            return {
                'success': False,
                'error': f'获取角色信息失败: {str(e)}'
            }
    
    def update_role(self, role_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """更新角色信息"""
        try:
            with self.db_service.get_session() as session:
                # 获取角色信息
                role = session.get(Role, role_id)
                if not role:
                    return {
                        'success': False,
                        'error': '角色不存在'
                    }
                
                # 如果要修改角色编码，检查新编码是否已存在
                if 'role_code' in data and data['role_code'] != role.role_code:
                    existing_role = self.get_role_by_code(data['role_code'])
                    if existing_role['success'] and existing_role['data']:
                        return {
                            'success': False,
                            'error': f'角色编码 {data["role_code"]} 已存在'
                        }
                
                # 如果要修改角色等级，进行相应验证
                if 'role_level' in data:
                    # 验证超级管理员角色的唯一性
                    if data['role_level'] == 1:
                        super_admin_check_sql = """
                        SELECT COUNT(*) as count 
                        FROM roles 
                        WHERE role_level = 1 AND status = 1 AND id != :role_id
                        """
                        super_result = session.execute(
                            text(super_admin_check_sql),
                            {'role_id': role_id}
                        )
                        if super_result.scalar() > 0:
                            return {
                                'success': False,
                                'error': '系统已存在超级管理员角色'
                            }
                
                # 更新角色信息
                formatted_data = self._format_role_data(data)
                for key, value in formatted_data.items():
                    setattr(role, key, value)
                
                session.commit()
                session.refresh(role)
                
                # 清除缓存
                self._clear_role_cache(role.role_code, role.id)
                
                logger.info(f"成功更新角色: {role.role_code} - {role.role_name}")
                
                return {
                    'success': True,
                    'data': role.to_dict(),
                    'message': '角色更新成功'
                }
                
        except Exception as e:
            logger.error(f"更新角色信息失败: {str(e)}")
            return {
                'success': False,
                'error': f'更新角色信息失败: {str(e)}'
            }
    
    def delete_role(self, role_id: int) -> Dict[str, Any]:
        """删除角色"""
        try:
            with self.db_service.get_session() as session:
                # 获取角色信息
                role = session.get(Role, role_id)
                if not role:
                    return {
                        'success': False,
                        'error': '角色不存在'
                    }
                
                # 检查是否有用户正在使用该角色
                user_check_sql = """
                SELECT COUNT(*) as count 
                FROM users 
                WHERE role_id = :role_id AND status = 1
                """
                user_result = session.execute(text(user_check_sql), {'role_id': role_id})
                if user_result.scalar() > 0:
                    return {
                        'success': False,
                        'error': '该角色下存在用户，无法删除'
                    }
                
                # 删除角色（软删除）
                role.status = 0
                session.commit()
                
                # 清除缓存
                self._clear_role_cache(role.role_code, role.id)
                
                logger.info(f"成功删除角色: {role.role_code} - {role.role_name}")
                
                return {
                    'success': True,
                    'message': '角色删除成功'
                }
                
        except Exception as e:
            logger.error(f"删除角色失败: {str(e)}")
            return {
                'success': False,
                'error': f'删除角色失败: {str(e)}'
            }
    
    def get_roles(self, page: int = 1, page_size: int = 10, keyword: str = None, status: int = None) -> dict:
        """获取角色列表（分页）"""
        try:
            with self.db_service.get_session() as session:
                query = select(Role)
                
                # 添加查询条件
                if keyword:
                    query = query.where(
                        (Role.role_name.like(f"%{keyword}%")) |
                        (Role.role_code.like(f"%{keyword}%"))
                    )
                if status is not None:
                    query = query.where(Role.status == status)
                
                # 计算总数
                total = session.scalar(select(func.count()).select_from(query.subquery()))
                
                # 分页
                query = query.offset((page - 1) * page_size).limit(page_size)
                roles = session.scalars(query).all()
                
                return {
                    'success': True,
                    'data': {
                        'list': [role.to_dict() for role in roles],
                        'total': total,
                        'page': page,
                        'page_size': page_size
                    }
                }
        except Exception as e:
            logger.error(f"获取角色列表失败: {str(e)}")
            return {
                'success': False,
                'error': f'获取角色列表失败: {str(e)}'
            }
    
    def set_role_permissions(self, role_id: int, permission_codes: List[str]) -> bool:
        """设置角色权限"""
        try:
            with self.db_service.get_session() as session:
                # 获取角色
                role = session.get(Role, role_id)
                if not role:
                    return False
                
                # 获取权限
                permissions = session.query(Permission).filter(
                    Permission.permission_code.in_(permission_codes)
                ).all()
                
                # 设置权限
                role.permissions = permissions
                session.commit()
                
                return True
        except Exception as e:
            logger.error(f"设置角色权限失败: {str(e)}")
            return False

def get_role_service_instance() -> RoleService:
    """获取角色服务实例（单例模式）"""
    container = DIContainer()
    if not container.has_service('role_service'):
        container.register('role_service', RoleService())
    return container.get('role_service')

def get_role_service() -> RoleService:
    """获取角色服务实例（兼容旧代码）"""
    return get_role_service_instance() 