# -*- coding: utf-8 -*-
"""
角色管理服务模块
提供角色的增删改查功能，集成Redis缓存
"""
import json
import logging
from typing import Optional, Dict, Any, List
from tools.database import get_database_service
from tools.redis_service import get_redis_service

logger = logging.getLogger(__name__)

class RoleService:
    """角色管理服务类"""
    
    def __init__(self):
        self.cache_prefix = "role:"
        self.cache_timeout = 3600  # 缓存1小时
        self.list_cache_key = "role:list"
        
    def create_role(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """创建角色"""
        try:
            db_service = get_database_service()
            
            # 验证必要字段
            required_fields = ['role_code', 'role_name', 'role_level']
            for field in required_fields:
                if field not in data or not str(data[field]).strip():
                    return {
                        'success': False,
                        'error': f'缺少必要字段: {field}'
                    }
            
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
                admin_result = db_service.execute_query(admin_check_sql, {'org_code': data['org_code']})
                if admin_result[0]['count'] > 0:
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
                super_result = db_service.execute_query(super_admin_check_sql)
                if super_result[0]['count'] > 0:
                    return {
                        'success': False,
                        'error': '系统已存在超级管理员角色'
                    }
            
            # 插入角色数据
            sql = """
            INSERT INTO roles (role_code, role_name, role_level, org_code, description, status)
            VALUES (:role_code, :role_name, :role_level, :org_code, :description, :status)
            """
            
            params = {
                'role_code': data['role_code'].strip(),
                'role_name': data['role_name'].strip(),
                'role_level': data['role_level'],
                'org_code': data.get('org_code', '').strip() if data.get('org_code') else None,
                'description': data.get('description', '').strip() if data.get('description') else None,
                'status': data.get('status', 1)
            }
            
            db_service.execute_update(sql, params)
            
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
            redis_service = get_redis_service()
            cached_data = redis_service.get_cache(cache_key)
            
            if cached_data:
                logger.info(f"从缓存获取角色信息: ID={role_id}")
                return {
                    'success': True,
                    'data': json.loads(cached_data)
                }
            
            # 从数据库查询
            db_service = get_database_service()
            sql = """
            SELECT r.id, r.role_code, r.role_name, r.role_level, r.org_code, r.description,
                   r.status, r.created_at, r.updated_at,
                   o.org_name
            FROM roles r
            LEFT JOIN organizations o ON r.org_code = o.org_code
            WHERE r.id = :role_id
            """
            
            result = db_service.execute_query(sql, {'role_id': role_id})
            
            if not result:
                return {
                    'success': False,
                    'error': '角色不存在'
                }
            
            role_data = result[0]
            role_info = self._format_role_data(role_data)
            
            # 缓存数据
            redis_service.set_cache(cache_key, json.dumps(role_info, default=str), self.cache_timeout)
            
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
            redis_service = get_redis_service()
            cached_data = redis_service.get_cache(cache_key)
            
            if cached_data:
                logger.info(f"从缓存获取角色信息: code={role_code}")
                return {
                    'success': True,
                    'data': json.loads(cached_data)
                }
            
            # 从数据库查询
            db_service = get_database_service()
            sql = """
            SELECT r.id, r.role_code, r.role_name, r.role_level, r.org_code, r.description,
                   r.status, r.created_at, r.updated_at,
                   o.org_name
            FROM roles r
            LEFT JOIN organizations o ON r.org_code = o.org_code
            WHERE r.role_code = :role_code
            """
            
            result = db_service.execute_query(sql, {'role_code': role_code})
            
            if not result:
                return {
                    'success': True,
                    'data': None
                }
            
            role_data = result[0]
            role_info = self._format_role_data(role_data)
            
            # 缓存数据
            redis_service.set_cache(cache_key, json.dumps(role_info, default=str), self.cache_timeout)
            
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
            redis_service = get_redis_service()
            cached_data = redis_service.get_cache(cache_key)
            
            if cached_data:
                logger.info(f"从缓存获取角色列表: page={page}, page_size={page_size}")
                return {
                    'success': True,
                    'data': json.loads(cached_data)
                }
            
            db_service = get_database_service()
            
            # 构建查询条件
            where_conditions = []
            params = {}
            
            if status is not None:
                where_conditions.append("r.status = :status")
                params['status'] = status
            
            if org_code:
                where_conditions.append("r.org_code = :org_code")
                params['org_code'] = org_code
            
            if role_level is not None:
                where_conditions.append("r.role_level = :role_level")
                params['role_level'] = role_level
                
            if keyword:
                where_conditions.append("(r.role_code LIKE :keyword OR r.role_name LIKE :keyword)")
                params['keyword'] = f'%{keyword}%'
            
            where_clause = ""
            if where_conditions:
                where_clause = "WHERE " + " AND ".join(where_conditions)
            
            # 查询总数
            count_sql = f"""
            SELECT COUNT(*) as total 
            FROM roles r
            LEFT JOIN organizations o ON r.org_code = o.org_code
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
            SELECT r.id, r.role_code, r.role_name, r.role_level, r.org_code, r.description,
                   r.status, r.created_at, r.updated_at,
                   o.org_name
            FROM roles r
            LEFT JOIN organizations o ON r.org_code = o.org_code
            {where_clause}
            ORDER BY r.role_level ASC, r.created_at DESC
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
            logger.error(f"获取角色列表失败: {str(e)}")
            return {
                'success': False,
                'error': f'获取角色列表失败: {str(e)}'
            }
    
    def get_role_permissions(self, role_id: int) -> Dict[str, Any]:
        """获取角色权限列表"""
        try:
            db_service = get_database_service()
            
            sql = """
            SELECT p.id, p.permission_code, p.permission_name, p.api_path, p.api_method,
                   p.resource_type, p.description, p.status
            FROM permissions p
            JOIN role_permissions rp ON p.id = rp.permission_id
            WHERE rp.role_id = :role_id AND p.status = 1
            ORDER BY p.resource_type, p.permission_code
            """
            
            result = db_service.execute_query(sql, {'role_id': role_id})
            
            return {
                'success': True,
                'data': result
            }
            
        except Exception as e:
            logger.error(f"获取角色权限失败: {str(e)}")
            return {
                'success': False,
                'error': f'获取角色权限失败: {str(e)}'
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
            redis_service = get_redis_service()
            redis_service.delete_cache(f"{self.cache_prefix}code:{role_code}")
            redis_service.delete_cache(f"{self.cache_prefix}id:{role_id}")
        except Exception as e:
            logger.warning(f"清除角色缓存失败: {str(e)}")
    
    def _clear_list_cache(self):
        """清除角色列表缓存"""
        try:
            redis_service = get_redis_service()
            keys = redis_service.get_keys_by_pattern(f"{self.list_cache_key}:*")
            if keys:
                for key in keys:
                    redis_service.delete_cache(key)
        except Exception as e:
            logger.warning(f"清除角色列表缓存失败: {str(e)}")
    
    def _get_role_by_id_without_status_check(self, role_id: int) -> Dict[str, Any]:
        """根据ID获取角色信息（不检查状态）"""
        try:
            db_service = get_database_service()
            sql = """
            SELECT r.id, r.role_code, r.role_name, r.role_level, r.org_code, r.description,
                   r.status, r.created_at, r.updated_at,
                   o.org_name
            FROM roles r
            LEFT JOIN organizations o ON r.org_code = o.org_code
            WHERE r.id = :role_id
            """
            
            result = db_service.execute_query(sql, {'role_id': role_id})
            
            if not result:
                return {
                    'success': False,
                    'error': '角色不存在'
                }
            
            role_data = result[0]
            role_info = self._format_role_data(role_data)
            
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
            db_service = get_database_service()
            
            # 获取现有角色信息（不检查状态）
            current_role = self._get_role_by_id_without_status_check(role_id)
            if not current_role['success'] or not current_role['data']:
                return {
                    'success': False,
                    'error': '角色不存在'
                }
            
            # 构建更新字段
            update_fields = []
            params = {'role_id': role_id}
            
            # 可更新字段列表
            updatable_fields = {
                'role_name': str,
                'description': str,
                'status': int
            }
            
            # 处理每个可更新字段
            for field, field_type in updatable_fields.items():
                if field in data:
                    value = data[field]
                    if isinstance(value, str):
                        value = value.strip()
                    if value is not None:
                        update_fields.append(f"{field} = :{field}")
                        params[field] = field_type(value)
            
            if not update_fields:
                return {
                    'success': False,
                    'error': '没有提供需要更新的字段'
                }
            
            # 执行更新
            sql = f"""
            UPDATE roles 
            SET {', '.join(update_fields)}
            WHERE id = :role_id
            """
            
            db_service.execute_update(sql, params)
            
            # 清除缓存
            self._clear_role_cache(current_role['data']['role_code'], role_id)
            self._clear_list_cache()
            
            # 获取更新后的角色信息
            updated_role = self._get_role_by_id_without_status_check(role_id)
            
            return {
                'success': True,
                'data': updated_role['data'],
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
            db_service = get_database_service()
            
            # 获取角色信息（不检查状态）
            current_role = self._get_role_by_id_without_status_check(role_id)
            if not current_role['success'] or not current_role['data']:
                return {
                    'success': False,
                    'error': '角色不存在'
                }
            
            # 检查是否有用户使用该角色
            users_sql = """
            SELECT COUNT(*) as count
            FROM users
            WHERE role_id = :role_id AND status = 1
            """
            users_result = db_service.execute_query(users_sql, {'role_id': role_id})
            if users_result[0]['count'] > 0:
                return {
                    'success': False,
                    'error': '该角色下存在用户，无法删除'
                }
            
            # 软删除角色（将状态设置为0）
            sql = """
            UPDATE roles 
            SET status = 0
            WHERE id = :role_id
            """
            
            db_service.execute_update(sql, {'role_id': role_id})
            
            # 清除缓存
            self._clear_role_cache(current_role['data']['role_code'], role_id)
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