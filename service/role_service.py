# -*- coding: utf-8 -*-
"""
角色服务模块
提供角色管理相关的业务逻辑
"""
import logging
from typing import Dict, Any, List, Optional
from tools.database import get_database_service
from tools.exceptions import (
    ValidationException, BusinessException,
    DatabaseException
)

logger = logging.getLogger(__name__)

class RoleService:
    """角色服务类"""
    
    def __init__(self):
        self.db = get_database_service()
    
    def get_roles_list(
        self,
        page: int = 1,
        page_size: int = 10,
        keyword: str = '',
        status: Optional[int] = None,
        role_level: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        获取角色列表（支持数据范围过滤）
        
        Args:
            page: 页码
            page_size: 每页数量
            keyword: 搜索关键词
            status: 角色状态
            role_level: 角色级别
        
        Returns:
            角色列表数据
        """
        try:
            # 构建查询条件
            conditions = []
            params = {}
            
            if keyword:
                conditions.append("(r.role_code LIKE :keyword OR r.role_name LIKE :keyword)")
                params['keyword'] = f"%{keyword}%"
            
            if status is not None:
                conditions.append("r.status = :status")
                params['status'] = status
            
            if role_level is not None:
                conditions.append("r.role_level = :role_level")
                params['role_level'] = role_level
            
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            
            # 基础查询SQL  
            base_sql = f"""
                SELECT r.id, r.role_code, r.role_name, r.role_level, 
                       r.data_scope, r.status, r.description as remark, r.created_at, r.updated_at
                FROM roles r
                WHERE {where_clause}
            """
            
            # 应用数据范围过滤（角色管理基于角色级别控制，不按机构过滤）
            from flask import g
            filtered_sql = base_sql
            if hasattr(g, 'user_acl_info') and g.user_acl_info:
                # 角色表按角色级别过滤，不使用标准的机构过滤
                user_role_level = g.user_acl_info.get('role_level', 3)
                # 只能管理级别高于等于自己的角色（数字越小级别越高）
                if user_role_level > 1:
                    filtered_sql = f"{base_sql} AND r.role_level >= {user_role_level}"
            
            # 计算分页
            offset = (page - 1) * page_size
            params['limit'] = page_size
            params['offset'] = offset
            
            # 查询总数
            count_sql = f"SELECT COUNT(*) as total FROM ({filtered_sql}) as filtered_roles"
            total_result = self.db.execute_query(count_sql, params)
            total = total_result[0]['total'] if total_result else 0
            
            # 查询数据
            data_sql = f"""
                {filtered_sql}
                ORDER BY r.role_level, r.created_at DESC
                LIMIT :limit OFFSET :offset
            """
            
            roles = self.db.execute_query(data_sql, params)
            
            return {
                'success': True,
                'data': {
                    'list': roles,
                    'total': total,
                    'page': page,
                    'page_size': page_size
                },
                'error': None
            }
            
        except Exception as e:
            logger.error(f"获取角色列表失败: {str(e)}")
            return {
                'success': False,
                'data': None,
                'error': str(e)
            }
    
    def get_role_by_id(self, role_id: int) -> Dict[str, Any]:
        """
        根据ID获取角色信息
        
        Args:
            role_id: 角色ID
        
        Returns:
            角色信息
        """
        try:
            sql = "SELECT * FROM roles WHERE id = ?"
            role = self.db.fetch_one(sql, [role_id])
            
            if not role:
                raise BusinessException("角色不存在")
            
            return role
            
        except BusinessException:
            raise
        except Exception as e:
            logger.error(f"获取角色信息失败: {str(e)}")
            raise DatabaseException("获取角色信息失败")
    
    def get_role_by_code(self, role_code: str) -> Dict[str, Any]:
        """
        根据编码获取角色信息
        
        Args:
            role_code: 角色编码
        
        Returns:
            角色信息
        """
        try:
            sql = "SELECT * FROM roles WHERE role_code = ?"
            role = self.db.fetch_one(sql, [role_code])
            
            if not role:
                raise BusinessException("角色不存在")
            
            return role
            
        except BusinessException:
            raise
        except Exception as e:
            logger.error(f"获取角色信息失败: {str(e)}")
            raise DatabaseException("获取角色信息失败")
    
    def create_role(self, role_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建角色
        
        Args:
            role_data: 角色数据
        
        Returns:
            创建的角色信息
        """
        try:
            # 验证必要字段
            required_fields = ['role_name', 'role_code', 'role_level']
            for field in required_fields:
                if not role_data.get(field):
                    raise ValidationException(f"缺少必要字段: {field}")
            
            # 检查角色编码是否已存在
            if self.check_role_code_exists(role_data['role_code']):
                raise BusinessException("角色编码已存在")
            
            # 插入数据
            sql = """
                INSERT INTO roles (
                    role_code, role_name, role_level,
                    status, remark, created_by
                ) VALUES (?, ?, ?, ?, ?, ?)
            """
            params = [
                role_data['role_code'],
                role_data['role_name'],
                role_data['role_level'],
                role_data.get('status', 1),
                role_data.get('remark'),
                role_data.get('created_by')
            ]
            
            role_id = self.db.execute(sql, params)
            
            # 返回创建的角色信息
            return self.get_role_by_id(role_id)
            
        except (ValidationException, BusinessException):
            raise
        except Exception as e:
            logger.error(f"创建角色失败: {str(e)}")
            raise DatabaseException("创建角色失败")
    
    def update_role(self, role_id: int, role_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        更新角色信息
        
        Args:
            role_id: 角色ID
            role_data: 角色数据
        
        Returns:
            更新后的角色信息
        """
        try:
            # 检查角色是否存在
            existing_role = self.get_role_by_id(role_id)
            if not existing_role:
                raise BusinessException("角色不存在")
            
            # 如果更新角色编码,检查是否已存在
            if 'role_code' in role_data and role_data['role_code'] != existing_role['role_code']:
                if self.check_role_code_exists(role_data['role_code']):
                    raise BusinessException("角色编码已存在")
            
            # 构建更新SQL
            update_fields = []
            params = []
            for key, value in role_data.items():
                if key not in ['id', 'created_at', 'created_by']:
                    update_fields.append(f"{key} = ?")
                    params.append(value)
            
            if not update_fields:
                raise ValidationException("没有需要更新的字段")
            
            sql = f"""
                UPDATE roles
                SET {', '.join(update_fields)}
                WHERE id = ?
            """
            params.append(role_id)
            
            self.db.execute(sql, params)
            
            # 返回更新后的角色信息
            return self.get_role_by_id(role_id)
            
        except (ValidationException, BusinessException):
            raise
        except Exception as e:
            logger.error(f"更新角色失败: {str(e)}")
            raise DatabaseException("更新角色失败")
    
    def delete_role(self, role_id: int) -> bool:
        """
        删除角色
        
        Args:
            role_id: 角色ID
        
        Returns:
            是否删除成功
        """
        try:
            # 检查角色是否存在
            role = self.get_role_by_id(role_id)
            if not role:
                raise BusinessException("角色不存在")
            
            # 检查是否有关联用户
            if self.has_users(role_id):
                raise BusinessException("该角色下存在用户,不能删除")
            
            # 执行删除
            sql = "DELETE FROM roles WHERE id = ?"
            self.db.execute(sql, [role_id])
            
            return True
            
        except BusinessException:
            raise
        except Exception as e:
            logger.error(f"删除角色失败: {str(e)}")
            raise DatabaseException("删除角色失败")
    
    def get_role_permissions(self, role_id: int) -> List[Dict[str, Any]]:
        """
        获取角色权限
        
        Args:
            role_id: 角色ID
        
        Returns:
            权限列表
        """
        try:
            sql = """
                SELECT p.*
                FROM permissions p
                INNER JOIN role_permissions rp ON p.id = rp.permission_id
                WHERE rp.role_id = ?
                ORDER BY p.permission_code
            """
            permissions = self.db.fetch_all(sql, [role_id])
            
            return permissions
            
        except Exception as e:
            logger.error(f"获取角色权限失败: {str(e)}")
            raise DatabaseException("获取角色权限失败")
    
    def set_role_permissions(self, role_id: int, permission_ids: List[int]) -> bool:
        """
        设置角色权限
        
        Args:
            role_id: 角色ID
            permission_ids: 权限ID列表
        
        Returns:
            是否设置成功
        """
        try:
            # 检查角色是否存在
            if not self.get_role_by_id(role_id):
                raise BusinessException("角色不存在")
            
            # 开始事务
            self.db.begin()
            
            try:
                # 删除原有权限
                sql = "DELETE FROM role_permissions WHERE role_id = ?"
                self.db.execute(sql, [role_id])
                
                # 添加新权限
                if permission_ids:
                    values = [(role_id, pid) for pid in permission_ids]
                    sql = "INSERT INTO role_permissions (role_id, permission_id) VALUES (?, ?)"
                    self.db.executemany(sql, values)
                
                # 提交事务
                self.db.commit()
                return True
                
            except Exception as e:
                # 回滚事务
                self.db.rollback()
                raise
            
        except BusinessException:
            raise
        except Exception as e:
            logger.error(f"设置角色权限失败: {str(e)}")
            raise DatabaseException("设置角色权限失败")
    
    def check_role_code_exists(self, role_code: str) -> bool:
        """检查角色编码是否已存在"""
        sql = "SELECT COUNT(*) as count FROM roles WHERE role_code = ?"
        result = self.db.fetch_one(sql, [role_code])
        return result['count'] > 0
    
    def has_users(self, role_id: int) -> bool:
        """检查是否有关联用户"""
        sql = "SELECT COUNT(*) as count FROM users WHERE role_id = ?"
        result = self.db.fetch_one(sql, [role_id])
        return result['count'] > 0

# 角色服务单例
_role_service = None

def get_role_service_instance() -> RoleService:
    """获取角色服务实例"""
    global _role_service
    if _role_service is None:
        _role_service = RoleService()
    return _role_service 