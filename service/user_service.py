# -*- coding: utf-8 -*-
"""
用户服务模块
提供用户管理相关的业务逻辑
"""
import logging
from typing import Dict, Any, List, Optional
import bcrypt
from tools.database import get_database_service
from tools.exceptions import (
    ValidationException, BusinessException,
    DatabaseException, AuthenticationException
)

logger = logging.getLogger(__name__)

class UserService:
    """用户服务类"""
    
    def __init__(self):
        self.db = get_database_service()
    
    def get_users_list(
        self,
        page: int = 1,
        page_size: int = 10,
        keyword: str = '',
        status: Optional[int] = None,
        org_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取用户列表（支持数据范围过滤）
        
        Args:
            page: 页码
            page_size: 每页数量
            keyword: 搜索关键词
            status: 用户状态
            org_code: 机构编码
        
        Returns:
            用户列表数据
        """
        try:
            # 构建查询条件
            conditions = []
            params = {}
            
            if keyword:
                conditions.append("(u.username LIKE :keyword OR u.user_code LIKE :keyword)")
                params['keyword'] = f"%{keyword}%"
            
            if status is not None:
                conditions.append("u.status = :status")
                params['status'] = status
            
            if org_code:
                conditions.append("u.org_code = :org_code")
                params['org_code'] = org_code
            
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            
            # 基础查询SQL（添加role_level用于权限过滤）
            base_sql = f"""
                SELECT u.id, u.user_code, u.username, u.phone, u.address, 
                       u.status, u.created_at, u.updated_at, u.org_code,
                       o.org_name, r.role_name, r.role_code, r.role_level
                FROM users u
                LEFT JOIN organizations o ON u.org_code = o.org_code
                LEFT JOIN roles r ON u.role_id = r.id
                WHERE {where_clause}
            """
            
            # 应用数据范围过滤和角色级别过滤
            from flask import g
            filtered_sql = base_sql
            if hasattr(g, 'user_acl_info') and g.user_acl_info:
                from service.enhanced_permission_service import get_enhanced_permission_service_instance
                permission_service = get_enhanced_permission_service_instance()
                filtered_sql = permission_service.apply_data_scope_filter(base_sql, g.user_acl_info, 'u')
                
                # 添加角色级别过滤：只能管理级别高于等于自己的用户
                user_role_level = g.user_acl_info.get('role_level', 3)
                if user_role_level > 1:
                    # 机构管理员不能看到超级管理员
                    if 'WHERE' in filtered_sql.upper():
                        filtered_sql = f"{filtered_sql} AND r.role_level >= {user_role_level}"
                    else:
                        filtered_sql = f"{filtered_sql} WHERE r.role_level >= {user_role_level}"
            
            # 计算分页
            offset = (page - 1) * page_size
            params['limit'] = page_size
            params['offset'] = offset
            
            # 查询总数
            count_sql = f"SELECT COUNT(*) as total FROM ({filtered_sql}) as filtered_users"
            total_result = self.db.execute_query(count_sql, params)
            total = total_result[0]['total'] if total_result else 0
            
            # 查询数据
            data_sql = f"""
                {filtered_sql}
                ORDER BY u.created_at DESC
                LIMIT :limit OFFSET :offset
            """
            
            users = self.db.execute_query(data_sql, params)
            
            return {
                'success': True,
                'data': {
                    'list': users,
                    'total': total,
                    'page': page,
                    'page_size': page_size
                },
                'error': None
            }
                
        except Exception as e:
            logger.error(f"获取用户列表失败: {str(e)}")
            return {
                'success': False,
                'data': None,
                'error': str(e)
            }
    
    def get_user_by_id(self, user_id: int) -> Dict[str, Any]:
        """
        根据ID获取用户信息（支持数据范围过滤）
        
        Args:
            user_id: 用户ID
        
        Returns:
            用户信息
        """
        try:
                        # 基础查询SQL（添加role_level用于权限过滤）
            base_sql = """
                SELECT u.id, u.user_code, u.username, u.phone, u.address, 
                       u.status, u.created_at, u.updated_at, u.org_code,
                       o.org_name, r.role_name, r.role_code, r.role_level
                FROM users u
                LEFT JOIN organizations o ON u.org_code = o.org_code
                LEFT JOIN roles r ON u.role_id = r.id
                WHERE u.id = :user_id
            """
            
            # 应用数据范围过滤和角色级别过滤
            from flask import g
            filtered_sql = base_sql
            if hasattr(g, 'user_acl_info') and g.user_acl_info:
                from service.enhanced_permission_service import get_enhanced_permission_service_instance
                permission_service = get_enhanced_permission_service_instance()
                filtered_sql = permission_service.apply_data_scope_filter(base_sql, g.user_acl_info, 'u')
                
                # 添加角色级别过滤：只能查看级别高于等于自己的用户
                user_role_level = g.user_acl_info.get('role_level', 3)
                if user_role_level > 1:
                    # 机构管理员不能查看超级管理员
                    if 'WHERE' in filtered_sql.upper():
                        filtered_sql = f"{filtered_sql} AND r.role_level >= {user_role_level}"
                    else:
                        filtered_sql = f"{filtered_sql} WHERE r.role_level >= {user_role_level}"
            
            result = self.db.execute_query(filtered_sql, {'user_id': user_id})
            
            if not result:
                return {
                    'success': False,
                    'data': None,
                    'error': '用户不存在或无权限访问'
                }
            
            user = result[0]
            
            return {
                'success': True,
                'data': user,
                'error': None
            }
            
        except Exception as e:
            logger.error(f"获取用户信息失败: {str(e)}")
            return {
                'success': False,
                'data': None,
                'error': str(e)
            }
    
    def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建用户
        
        Args:
            user_data: 用户数据
        
        Returns:
            创建的用户信息
        """
        try:
            # 验证必要字段
            required_fields = ['username', 'password', 'real_name', 'email']
            for field in required_fields:
                if not user_data.get(field):
                    raise ValidationException(f"缺少必要字段: {field}")
            
            # 检查用户名是否已存在
            if self.check_username_exists(user_data['username']):
                raise BusinessException("用户名已存在")
            
            # 检查邮箱是否已存在
            if self.check_email_exists(user_data['email']):
                raise BusinessException("邮箱已被使用")
            
            # 生成用户编码
            user_data['user_code'] = self.generate_user_code()
            
            # 加密密码
            user_data['password'] = bcrypt.hashpw(user_data['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            # 插入数据
            sql = """
                INSERT INTO users (
                    user_code, username, password, real_name,
                    email, mobile, org_code, role_id,
                    status, remark, created_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = [
                user_data['user_code'],
                user_data['username'],
                user_data['password'],
                user_data['real_name'],
                user_data['email'],
                user_data.get('mobile'),
                user_data.get('org_code'),
                user_data.get('role_id'),
                user_data.get('status', 1),
                user_data.get('remark'),
                user_data.get('created_by')
            ]
            
            user_id = self.db.execute(sql, params)
            
            # 返回创建的用户信息
            return self.get_user_by_id(user_id)
            
        except (ValidationException, BusinessException):
            raise
        except Exception as e:
            logger.error(f"创建用户失败: {str(e)}")
            raise DatabaseException("创建用户失败")
    
    def update_user(self, user_id: int, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        更新用户信息
        
        Args:
            user_id: 用户ID
            user_data: 用户数据
        
        Returns:
            更新后的用户信息
        """
        try:
            # 检查用户是否存在
            existing_user = self.get_user_by_id(user_id)
            if not existing_user:
                raise BusinessException("用户不存在")
            
            # 如果更新用户名,检查是否已存在
            if 'username' in user_data and user_data['username'] != existing_user['username']:
                if self.check_username_exists(user_data['username']):
                    raise BusinessException("用户名已存在")
            
            # 如果更新邮箱,检查是否已存在
            if 'email' in user_data and user_data['email'] != existing_user['email']:
                if self.check_email_exists(user_data['email']):
                    raise BusinessException("邮箱已被使用")
            
            # 如果包含密码,进行加密
            if 'password' in user_data:
                user_data['password'] = bcrypt.hashpw(user_data['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            # 构建更新SQL
            update_fields = []
            params = []
            for key, value in user_data.items():
                if key not in ['id', 'user_code', 'created_at', 'created_by']:
                    update_fields.append(f"{key} = ?")
                    params.append(value)
            
            if not update_fields:
                raise ValidationException("没有需要更新的字段")
            
            sql = f"""
                UPDATE users
                SET {', '.join(update_fields)}
                WHERE id = ?
            """
            params.append(user_id)
            
            self.db.execute(sql, params)
            
            # 返回更新后的用户信息
            return self.get_user_by_id(user_id)
            
        except (ValidationException, BusinessException):
            raise
        except Exception as e:
            logger.error(f"更新用户失败: {str(e)}")
            raise DatabaseException("更新用户失败")
    
    def delete_user(self, user_id: int) -> bool:
        """
        删除用户
        
        Args:
            user_id: 用户ID
            
        Returns:
            是否删除成功
        """
        try:
            # 检查用户是否存在
            if not self.get_user_by_id(user_id):
                raise BusinessException("用户不存在")
            
            # 执行删除
            sql = "DELETE FROM users WHERE id = ?"
            self.db.execute(sql, [user_id])
            
            return True
            
        except BusinessException:
            raise
        except Exception as e:
            logger.error(f"删除用户失败: {str(e)}")
            raise DatabaseException("删除用户失败")
    
    def verify_password(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """
        验证用户密码
        
        Args:
            username: 用户名
            password: 密码
        
        Returns:
            验证成功返回用户信息,失败返回None
        """
        try:
            # 查询用户
            sql = """
                SELECT u.*, o.org_name, r.role_name, r.role_code
                FROM users u
                LEFT JOIN organizations o ON u.org_code = o.org_code
                LEFT JOIN roles r ON u.role_id = r.id
                WHERE u.username = :username
            """
            users = self.db.execute_query(sql, {'username': username})
            if not users:
                raise AuthenticationException("用户名或密码错误")
            
            user = users[0]
            
            # 检查用户状态
            if user['status'] != 1:
                raise AuthenticationException("用户已被禁用")
            
            # 验证密码
            if not bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
                raise AuthenticationException("用户名或密码错误")
            
            return user
            
        except AuthenticationException:
            raise
        except Exception as e:
            logger.error(f"密码验证失败: {str(e)}")
            raise DatabaseException("密码验证失败")
    
    def check_username_exists(self, username: str) -> bool:
        """检查用户名是否已存在"""
        sql = "SELECT COUNT(*) as count FROM users WHERE username = ?"
        result = self.db.fetch_one(sql, [username])
        return result['count'] > 0
    
    def check_email_exists(self, email: str) -> bool:
        """检查邮箱是否已存在"""
        sql = "SELECT COUNT(*) as count FROM users WHERE email = ?"
        result = self.db.fetch_one(sql, [email])
        return result['count'] > 0
    
    def generate_user_code(self) -> str:
        """生成用户编码"""
        sql = "SELECT MAX(CAST(SUBSTRING(user_code, 2) AS UNSIGNED)) as max_code FROM users WHERE user_code LIKE 'U%'"
        result = self.db.fetch_one(sql)
        next_num = (result['max_code'] or 0) + 1
        return f"U{next_num:06d}"

# 用户服务单例
_user_service = None

def get_user_service_instance() -> UserService:
    """获取用户服务实例"""
    global _user_service
    if _user_service is None:
        _user_service = UserService()
    return _user_service 