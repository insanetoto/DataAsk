# -*- coding: utf-8 -*-
"""
角色管理服务模块
提供角色的增删改查功能，集成Redis缓存
"""
import json
import logging
from typing import Optional, Dict, Any, List
from tools.database import get_database_service, get_db_session
from tools.redis_service import get_redis_service, RedisService
from sqlalchemy import select, func, text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

class RoleService:
    """角色管理服务类"""
    
    def __init__(self):
        self.cache_prefix = "role:"
        self.cache_timeout = 3600  # 缓存1小时
        self.list_cache_key = "role:list"
        self.redis = RedisService()
        
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
            
            with get_db_session() as session:
                # 检查角色编码是否已存在
                existing_role = self.get_role_by_code(data['role_code'])
                if existing_role['success'] and existing_role['data']:
                    return {
                        'success': False,
                        'error': f'角色编码 {data["role_code"]} 已存在'
                    }
                
                # 验证机构管理员角色的唯一性
                if data['role_level'] == 2:  # 机构管理员
                    if not data.get('org_code'):
                        return {
                            'success': False,
                            'error': '机构管理员角色必须指定机构编码'
                        }
                    # 检查该机构是否已有管理员角色
                    admin_check_sql = """
                    SELECT COUNT(*) as count 
                    FROM roles 
                    WHERE org_code = :org_code AND role_level = 2 AND status = 1
                    """
                    admin_result = session.execute(text(admin_check_sql), {'org_code': data['org_code']})
                    if admin_result.scalar() > 0:
                        return {
                            'success': False,
                            'error': f'机构 {data["org_code"]} 已存在管理员角色'
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
                logger.info(f"从缓存获取角色信息: ID={role_id}")
                return {
                    'success': True,
                    'data': json.loads(cached_data)
                }
            
            # 从数据库查询
            with get_db_session() as session:
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
                logger.info(f"从缓存获取角色信息: code={role_code}")
                return {
                    'success': True,
                    'data': json.loads(cached_data)
                }
            
            # 从数据库查询
            with get_db_session() as session:
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
                      org_code: Optional[str] = None, role_level: Optional[int] = None,
                      keyword: Optional[str] = None) -> Dict[str, Any]:
        """获取角色列表"""
        try:
            # 生成缓存键
            cache_key = f"{self.list_cache_key}:{page}:{page_size}:{status}:{org_code or ''}:{role_level or ''}:{keyword or ''}"
            cached_data = self.redis.get_cache(cache_key)
            
            if cached_data:
                logger.info(f"从缓存获取角色列表: page={page}, page_size={page_size}")
                return {
                    'success': True,
                    'data': json.loads(cached_data)
                }
            
            with get_db_session() as session:
                query = select(Role)
                if keyword:
                    query = query.where(
                        (Role.role_name.like(f"%{keyword}%")) |
                        (Role.role_code.like(f"%{keyword}%"))
                    )
                if status is not None:
                    query = query.where(Role.status == status)
                if org_code:
                    query = query.where(Role.org_code == org_code)
                if role_level is not None:
                    query = query.where(Role.role_level == role_level)
                
                total = session.scalar(select(func.count()).select_from(query.subquery()))
                query = query.offset((page - 1) * page_size).limit(page_size)
                roles = session.scalars(query).all()
                
                result_data = {
                    'list': [role.to_dict() for role in roles],
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
            with get_db_session() as session:
                role = session.get(Role, role_id)
                if not role:
                    return {
                        'success': False,
                        'error': '角色不存在'
                    }
                
                return {
                    'success': True,
                    'data': [permission.to_dict() for permission in role.permissions]
                }
                
        except Exception as e:
            logger.error(f"获取角色权限列表失败: {str(e)}")
            return {
                'success': False,
                'error': f'获取角色权限列表失败: {str(e)}'
            }
    
    def _format_role_data(self, role_data: Dict) -> Dict:
        """格式化角色数据"""
        return {
            'id': role_data['id'],
            'role_code': role_data['role_code'],
            'role_name': role_data['role_name'],
            'role_level': role_data['role_level'],
            'org_code': role_data['org_code'],
            'org_name': role_data['org_name'],
            'description': role_data['description'],
            'status': role_data['status'],
            'created_at': role_data['created_at'],
            'updated_at': role_data['updated_at']
        }
    
    def _clear_role_cache(self, role_code: str, role_id: int):
        """清除单个角色的缓存"""
        try:
            self.redis.delete_cache(f"{self.cache_prefix}code:{role_code}")
            self.redis.delete_cache(f"{self.cache_prefix}id:{role_id}")
        except Exception as e:
            logger.warning(f"清除角色缓存失败: {str(e)}")
    
    def _clear_list_cache(self):
        """清除角色列表缓存"""
        try:
            keys = self.redis.get_keys_by_pattern(f"{self.list_cache_key}:*")
            if keys:
                for key in keys:
                    self.redis.delete_cache(key)
        except Exception as e:
            logger.warning(f"清除角色列表缓存失败: {str(e)}")
    
    def _get_role_by_id_without_status_check(self, role_id: int) -> Dict[str, Any]:
        """根据ID获取角色信息（不检查状态）"""
        try:
            role = self.db.get(Role, role_id)
            
            if not role:
                return {
                    'success': False,
                    'error': '角色不存在'
                }
            
            role_info = role.to_dict()
            
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
    
    def update_role(self, role_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """更新角色信息"""
        try:
            with get_db_session() as session:
                role = session.get(Role, role_id)
                if not role:
                    return {
                        'success': False,
                        'error': '角色不存在'
                    }
                
                # 更新角色信息
                for key, value in data.items():
                    if hasattr(role, key):
                        setattr(role, key, value)
                
                session.commit()
                session.refresh(role)
                
                # 清除缓存
                self._clear_role_cache(role.role_code, role_id)
                self._clear_list_cache()
                
                return {
                    'success': True,
                    'data': role.to_dict(),
                    'message': '角色信息更新成功'
                }
                
        except Exception as e:
            logger.error(f"更新角色信息失败: {str(e)}")
            return {
                'success': False,
                'error': f'更新角色信息失败: {str(e)}'
            }
    
    def delete_role(self, role_id: int) -> Dict[str, Any]:
        """删除角色（软删除）"""
        try:
            with get_db_session() as session:
                role = session.get(Role, role_id)
                if not role:
                    return {
                        'success': False,
                        'error': '角色不存在'
                    }
                
                # 软删除角色
                role.status = 0
                session.commit()
                
                # 清除缓存
                self._clear_role_cache(role.role_code, role_id)
                self._clear_list_cache()
                
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
        """获取角色列表"""
        query = select(Role)
        if keyword:
            query = query.where(
                (Role.role_name.like(f"%{keyword}%")) |
                (Role.role_code.like(f"%{keyword}%"))
            )
        if status is not None:
            query = query.where(Role.status == status)

        total = self.db.scalar(select(func.count()).select_from(query.subquery()))
        query = query.offset((page - 1) * page_size).limit(page_size)
        roles = self.db.scalars(query).all()

        return {
            "list": [role.to_dict() for role in roles],
            "pagination": {
                "total": total,
                "page": page,
                "page_size": page_size
            }
        }

    def set_role_permissions(self, role_id: int, permission_codes: List[str]) -> bool:
        """设置角色权限"""
        try:
            with get_db_session() as session:
                role = session.get(Role, role_id)
                if not role:
                    return False
                
                # 查询权限
                permissions = session.query(Permission).filter(Permission.permission_code.in_(permission_codes)).all()
                role.permissions = permissions
                session.commit()
                
                # 清除缓存
                self._clear_role_cache(role.role_code, role_id)
                
                return True
                
        except Exception as e:
            logger.error(f"设置角色权限失败: {str(e)}")
            return False

# 全局角色服务实例
role_service = None

def init_role_service():
    """初始化角色管理服务"""
    global role_service
    role_service = RoleService()
    return role_service

def get_role_service():
    """获取角色管理服务实例"""
    if role_service is None:
        return init_role_service()
    return role_service 