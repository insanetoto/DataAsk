# -*- coding: utf-8 -*-
"""
用户管理服务模块
提供用户的增删改查功能，集成Redis缓存和权限验证
"""
import json
import logging
import secrets
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import bcrypt
from tools.database import get_database_service
from tools.redis_service import get_redis_service

logger = logging.getLogger(__name__)

class UserService:
    """用户管理服务类"""
    
    def __init__(self):
        self.cache_prefix = "user:"
        self.session_prefix = "session:"
        self.cache_timeout = 3600  # 缓存1小时
        self.session_timeout = 7200  # 会话2小时
        self.list_cache_key = "user:list"
        
    def create_user(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """创建用户"""
        try:
            db_service = get_database_service()
            
            # 验证必要字段
            required_fields = ['org_code', 'user_code', 'username', 'password', 'role_id']
            for field in required_fields:
                if field not in data or not str(data[field]).strip():
                    return {
                        'success': False,
                        'error': f'缺少必要字段: {field}'
                    }
            
            # 检查用户编码是否已存在
            existing_user = self.get_user_by_code(data['user_code'])
            if existing_user['success'] and existing_user['data']:
                return {
                    'success': False,
                    'error': f'用户编码 {data["user_code"]} 已存在'
                }
            
            # 加密密码
            password_hash = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            # 插入用户数据
            sql = """
            INSERT INTO users (org_code, user_code, username, password_hash, phone, address, role_id, status)
            VALUES (:org_code, :user_code, :username, :password_hash, :phone, :address, :role_id, :status)
            """
            
            params = {
                'org_code': data['org_code'].strip(),
                'user_code': data['user_code'].strip(),
                'username': data['username'].strip(),
                'password_hash': password_hash,
                'phone': data.get('phone', '').strip() if data.get('phone') else None,
                'address': data.get('address', '').strip() if data.get('address') else None,
                'role_id': data['role_id'],
                'status': data.get('status', 1)
            }
            
            db_service.execute_update(sql, params)
            
            # 获取新创建的用户信息
            new_user = self.get_user_by_code(data['user_code'])
            
            # 清除列表缓存
            self._clear_list_cache()
            
            logger.info(f"成功创建用户: {data['user_code']} - {data['username']}")
            
            return {
                'success': True,
                'data': new_user['data'],
                'message': '用户创建成功'
            }
            
        except Exception as e:
            logger.error(f"创建用户失败: {str(e)}")
            return {
                'success': False,
                'error': f'创建用户失败: {str(e)}'
            }
    
    def get_user_by_id(self, user_id: int) -> Dict[str, Any]:
        """根据ID获取用户信息"""
        try:
            # 先检查缓存
            cache_key = f"{self.cache_prefix}id:{user_id}"
            redis_service = get_redis_service()
            cached_data = redis_service.get_cache(cache_key)
            
            if cached_data:
                logger.info(f"从缓存获取用户信息: ID={user_id}")
                return {
                    'success': True,
                    'data': json.loads(cached_data)
                }
            
            # 从数据库查询
            db_service = get_database_service()
            sql = """
            SELECT u.id, u.org_code, u.user_code, u.username, u.phone, u.address, 
                   u.role_id, u.last_login_at, u.login_count, u.status, u.created_at, u.updated_at,
                   r.role_code, r.role_name, r.role_level,
                   o.org_name
            FROM users u
            LEFT JOIN roles r ON u.role_id = r.id
            LEFT JOIN organizations o ON u.org_code = o.org_code
            WHERE u.id = :user_id
            """
            
            result = db_service.execute_query(sql, {'user_id': user_id})
            
            if not result:
                return {
                    'success': False,
                    'error': '用户不存在'
                }
            
            user_data = result[0]
            user_info = self._format_user_data(user_data)
            
            # 缓存数据
            redis_service.set_cache(cache_key, json.dumps(user_info, default=str), self.cache_timeout)
            
            return {
                'success': True,
                'data': user_info
            }
            
        except Exception as e:
            logger.error(f"根据ID获取用户信息失败: {str(e)}")
            return {
                'success': False,
                'error': f'获取用户信息失败: {str(e)}'
            }
    
    def get_user_by_code(self, user_code: str) -> Dict[str, Any]:
        """根据用户编码获取用户信息"""
        try:
            # 先检查缓存
            cache_key = f"{self.cache_prefix}code:{user_code}"
            redis_service = get_redis_service()
            cached_data = redis_service.get_cache(cache_key)
            
            if cached_data:
                logger.info(f"从缓存获取用户信息: code={user_code}")
                return {
                    'success': True,
                    'data': json.loads(cached_data)
                }
            
            # 从数据库查询
            db_service = get_database_service()
            sql = """
            SELECT u.id, u.org_code, u.user_code, u.username, u.phone, u.address, 
                   u.role_id, u.last_login_at, u.login_count, u.status, u.created_at, u.updated_at,
                   r.role_code, r.role_name, r.role_level,
                   o.org_name
            FROM users u
            LEFT JOIN roles r ON u.role_id = r.id
            LEFT JOIN organizations o ON u.org_code = o.org_code
            WHERE u.user_code = :user_code
            """
            
            result = db_service.execute_query(sql, {'user_code': user_code})
            
            if not result:
                return {
                    'success': True,
                    'data': None
                }
            
            user_data = result[0]
            user_info = self._format_user_data(user_data)
            
            # 缓存数据
            redis_service.set_cache(cache_key, json.dumps(user_info, default=str), self.cache_timeout)
            
            return {
                'success': True,
                'data': user_info
            }
            
        except Exception as e:
            logger.error(f"根据编码获取用户信息失败: {str(e)}")
            return {
                'success': False,
                'error': f'获取用户信息失败: {str(e)}'
            }
    
    def authenticate_user(self, user_code: str, password: str) -> Dict[str, Any]:
        """用户认证"""
        try:
            db_service = get_database_service()
            
            # 获取用户信息（包含密码哈希）
            sql = """
            SELECT u.id, u.org_code, u.user_code, u.username, u.password_hash, u.phone, u.address,
                   u.role_id, u.last_login_at, u.login_count, u.status, u.created_at, u.updated_at,
                   r.role_code, r.role_name, r.role_level,
                   o.org_name
            FROM users u
            LEFT JOIN roles r ON u.role_id = r.id
            LEFT JOIN organizations o ON u.org_code = o.org_code
            WHERE u.user_code = :user_code AND u.status = 1
            """
            
            result = db_service.execute_query(sql, {'user_code': user_code})
            
            if not result:
                return {
                    'success': False,
                    'error': '用户不存在或已禁用'
                }
            
            user_data = result[0]
            
            # 验证密码
            if not bcrypt.checkpw(password.encode('utf-8'), user_data['password_hash'].encode('utf-8')):
                return {
                    'success': False,
                    'error': '密码错误'
                }
            
            # 更新登录信息
            update_sql = """
            UPDATE users 
            SET last_login_at = :login_time, login_count = login_count + 1
            WHERE id = :user_id
            """
            db_service.execute_update(update_sql, {
                'login_time': datetime.now(),
                'user_id': user_data['id']
            })
            
            # 清除用户缓存
            self._clear_user_cache(user_data['user_code'], user_data['id'])
            
            # 返回用户信息（不包含密码）
            user_info = self._format_user_data(user_data)
            user_info['last_login_at'] = datetime.now().isoformat()
            user_info['login_count'] = user_data['login_count'] + 1
            
            return {
                'success': True,
                'data': user_info,
                'message': '认证成功'
            }
            
        except Exception as e:
            logger.error(f"用户认证失败: {str(e)}")
            return {
                'success': False,
                'error': f'认证失败: {str(e)}'
            }
    
    def get_users_list(self, page: int = 1, page_size: int = 10, status: Optional[int] = None,
                      org_code: Optional[str] = None, role_level: Optional[int] = None,
                      keyword: Optional[str] = None, current_user_org: Optional[str] = None) -> Dict[str, Any]:
        """获取用户列表"""
        try:
            # 生成缓存键
            cache_key = f"{self.list_cache_key}:{page}:{page_size}:{status}:{org_code or ''}:{role_level or ''}:{keyword or ''}:{current_user_org or ''}"
            redis_service = get_redis_service()
            cached_data = redis_service.get_cache(cache_key)
            
            if cached_data:
                logger.info(f"从缓存获取用户列表: page={page}, page_size={page_size}")
                return {
                    'success': True,
                    'data': json.loads(cached_data)
                }
            
            db_service = get_database_service()
            
            # 构建查询条件
            where_conditions = []
            params = {}
            
            if status is not None:
                where_conditions.append("u.status = :status")
                params['status'] = status
            
            if org_code:
                where_conditions.append("u.org_code = :org_code")
                params['org_code'] = org_code
            elif current_user_org:  # 如果指定了当前用户机构，只显示该机构的用户
                where_conditions.append("u.org_code = :current_user_org")
                params['current_user_org'] = current_user_org
            
            if role_level is not None:
                where_conditions.append("r.role_level = :role_level")
                params['role_level'] = role_level
                
            if keyword:
                where_conditions.append("(u.user_code LIKE :keyword OR u.username LIKE :keyword OR u.phone LIKE :keyword)")
                params['keyword'] = f'%{keyword}%'
            
            where_clause = ""
            if where_conditions:
                where_clause = "WHERE " + " AND ".join(where_conditions)
            
            # 查询总数
            count_sql = f"""
            SELECT COUNT(*) as total 
            FROM users u
            LEFT JOIN roles r ON u.role_id = r.id
            LEFT JOIN organizations o ON u.org_code = o.org_code
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
            SELECT u.id, u.org_code, u.user_code, u.username, u.phone, u.address,
                   u.role_id, u.last_login_at, u.login_count, u.status, u.created_at, u.updated_at,
                   r.role_code, r.role_name, r.role_level,
                   o.org_name
            FROM users u
            LEFT JOIN roles r ON u.role_id = r.id
            LEFT JOIN organizations o ON u.org_code = o.org_code
            {where_clause}
            ORDER BY u.created_at DESC
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
            logger.error(f"获取用户列表失败: {str(e)}")
            return {
                'success': False,
                'error': f'获取用户列表失败: {str(e)}'
            }
    
    def _format_user_data(self, user_data: Dict) -> Dict:
        """格式化用户数据，移除敏感信息"""
        return {
            'id': user_data['id'],
            'org_code': user_data['org_code'],
            'org_name': user_data['org_name'],
            'user_code': user_data['user_code'],
            'username': user_data['username'],
            'phone': user_data['phone'],
            'address': user_data['address'],
            'role_id': user_data['role_id'],
            'role_code': user_data['role_code'],
            'role_name': user_data['role_name'],
            'role_level': user_data['role_level'],
            'last_login_at': user_data['last_login_at'],
            'login_count': user_data['login_count'],
            'status': user_data['status'],
            'created_at': user_data['created_at'],
            'updated_at': user_data['updated_at']
        }
    
    def _clear_user_cache(self, user_code: str, user_id: int):
        """清除单个用户的缓存"""
        try:
            redis_service = get_redis_service()
            redis_service.delete_cache(f"{self.cache_prefix}code:{user_code}")
            redis_service.delete_cache(f"{self.cache_prefix}id:{user_id}")
        except Exception as e:
            logger.warning(f"清除用户缓存失败: {str(e)}")
    
    def _clear_list_cache(self):
        """清除用户列表缓存"""
        try:
            redis_service = get_redis_service()
            keys = redis_service.get_keys_by_pattern(f"{self.list_cache_key}:*")
            if keys:
                for key in keys:
                    redis_service.delete_cache(key)
        except Exception as e:
            logger.warning(f"清除用户列表缓存失败: {str(e)}")

# 全局用户服务实例
user_service = None

def init_user_service():
    """初始化用户管理服务"""
    global user_service
    user_service = UserService()
    return user_service

def get_user_service():
    """获取用户管理服务实例"""
    if user_service is None:
        return init_user_service()
    return user_service 