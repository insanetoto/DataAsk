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
import jwt
from tools.database import get_database_service, get_db_session
from tools.redis_service import get_redis_service, RedisService
from sqlalchemy import text
from config import Config

logger = logging.getLogger(__name__)

class UserService:
    """用户管理服务类"""
    
    def __init__(self):
        self.cache_prefix = "user:"
        self.session_prefix = "session:"
        self.cache_timeout = 3600  # 缓存1小时
        self.session_timeout = 7200  # 会话2小时
        self.list_cache_key = "user:list"
        self.redis = get_redis_service()  # 使用全局Redis服务实例
        self.JWT_SECRET = Config.JWT_SECRET_KEY  # 从配置文件读取
        self.ACCESS_TOKEN_EXPIRE_MINUTES = 30
        self.REFRESH_TOKEN_EXPIRE_DAYS = 7
        
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
            salt = bcrypt.gensalt()
            password_hash = bcrypt.hashpw(data['password'].encode('utf-8'), salt)
            
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
                cached_user = json.loads(cached_data)
                if cached_user['status'] != 1:
                    return {
                        'success': False,
                        'error': '用户不存在或已禁用'
                    }
                return {
                    'success': True,
                    'data': cached_user
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
            WHERE u.id = :user_id AND u.status = 1
            """
            
            result = db_service.execute_query(sql, {'user_id': user_id})
            
            if not result:
                return {
                    'success': False,
                    'error': '用户不存在或已禁用'
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
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        try:
            return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
        except Exception as e:
            logger.error(f"密码验证失败: {str(e)}")
            return False

    def authenticate_user(self, username: str, password: str):
        """验证用户"""
        with get_db_session() as session:
            # 查询用户
            result = session.execute(
                text("""
                    SELECT u.*, r.role_code, o.org_name 
                    FROM users u 
                    JOIN roles r ON u.role_id = r.id 
                    JOIN organizations o ON u.org_code = o.org_code 
                    WHERE u.user_code = :username AND u.status = 1
                """),
                {"username": username}
            ).fetchone()

            if not result:
                return None

            # 验证密码
            if not self.verify_password(password, result.password_hash):
                return None

            # 更新登录信息
            session.execute(
                text("""
                    UPDATE users 
                    SET last_login_at = :login_time, 
                        login_count = login_count + 1 
                    WHERE id = :user_id
                """),
                {
                    "login_time": datetime.now(),
                    "user_id": result.id
                }
            )
            session.commit()

            return {
                "user_id": result.id,
                "username": result.username,
                "org_code": result.org_code,
                "org_name": result.org_name,
                "role_code": result.role_code
            }

    def create_tokens(self, user_data: dict):
        """创建访问令牌和刷新令牌"""
        # 创建访问令牌
        access_token_expires = datetime.utcnow() + timedelta(minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token_data = {
            **user_data,
            "exp": access_token_expires,
            "token_type": "access"
        }
        access_token = jwt.encode(access_token_data, self.JWT_SECRET, algorithm="HS256")

        # 创建刷新令牌
        refresh_token_expires = datetime.utcnow() + timedelta(days=self.REFRESH_TOKEN_EXPIRE_DAYS)
        refresh_token_data = {
            "user_id": user_data["user_id"],
            "exp": refresh_token_expires,
            "token_type": "refresh"
        }
        refresh_token = jwt.encode(refresh_token_data, self.JWT_SECRET, algorithm="HS256")

        # 将令牌存储在Redis中
        self.redis.set_token(
            f"access_token:{user_data['user_id']}", 
            access_token,
            expire_seconds=self.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
        self.redis.set_token(
            f"refresh_token:{user_data['user_id']}", 
            refresh_token,
            expire_seconds=self.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": self.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }

    def refresh_access_token(self, refresh_token: str):
        """使用刷新令牌获取新的访问令牌"""
        try:
            # 验证刷新令牌
            payload = jwt.decode(refresh_token, self.JWT_SECRET, algorithms=["HS256"])
            if payload["token_type"] != "refresh":
                return None

            user_id = payload["user_id"]
            stored_refresh_token = self.redis.get_token(f"refresh_token:{user_id}")
            
            if not stored_refresh_token or stored_refresh_token != refresh_token:
                return None

            # 获取用户信息
            with get_db_session() as session:
                result = session.execute(
                    text("""
                        SELECT u.*, r.role_code, o.org_name 
                        FROM users u 
                        JOIN roles r ON u.role_id = r.id 
                        JOIN organizations o ON u.org_code = o.org_code 
                        WHERE u.id = :user_id AND u.status = 1
                    """),
                    {"user_id": user_id}
                ).fetchone()

                if not result:
                    return None

                user_data = {
                    "user_id": result.id,
                    "username": result.username,
                    "org_code": result.org_code,
                    "org_name": result.org_name,
                    "role_code": result.role_code
                }

            # 创建新的访问令牌
            access_token_expires = datetime.utcnow() + timedelta(minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token_data = {
                **user_data,
                "exp": access_token_expires,
                "token_type": "access"
            }
            new_access_token = jwt.encode(access_token_data, self.JWT_SECRET, algorithm="HS256")

            # 更新Redis中的访问令牌
            self.redis.set_token(
                f"access_token:{user_id}", 
                new_access_token,
                expire_seconds=self.ACCESS_TOKEN_EXPIRE_MINUTES * 60
            )

            return {
                "access_token": new_access_token,
                "token_type": "bearer",
                "expires_in": self.ACCESS_TOKEN_EXPIRE_MINUTES * 60
            }

        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    def revoke_tokens(self, user_id: int):
        """撤销用户的所有令牌"""
        self.redis.delete_token(f"access_token:{user_id}")
        self.redis.delete_token(f"refresh_token:{user_id}")
    
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
    
    def _get_user_by_id_without_status_check(self, user_id: int) -> Dict[str, Any]:
        """根据ID获取用户信息（不检查状态）"""
        try:
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
    
    def update_user(self, user_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """更新用户信息"""
        try:
            db_service = get_database_service()
            
            # 获取现有用户信息（不检查状态）
            current_user = self._get_user_by_id_without_status_check(user_id)
            if not current_user['success'] or not current_user['data']:
                return {
                    'success': False,
                    'error': '用户不存在'
                }
            
            # 构建更新字段
            update_fields = []
            params = {'user_id': user_id}
            
            # 可更新字段列表
            updatable_fields = {
                'username': str,
                'phone': str,
                'address': str,
                'role_id': int,
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
            
            # 如果提供了新密码，更新密码
            if 'password' in data and data['password']:
                salt = bcrypt.gensalt()
                password_hash = bcrypt.hashpw(data['password'].encode('utf-8'), salt)
                update_fields.append("password_hash = :password_hash")
                params['password_hash'] = password_hash
            
            if not update_fields:
                return {
                    'success': False,
                    'error': '没有提供需要更新的字段'
                }
            
            # 执行更新
            sql = f"""
            UPDATE users 
            SET {', '.join(update_fields)}
            WHERE id = :user_id
            """
            
            db_service.execute_update(sql, params)
            
            # 清除缓存
            self._clear_user_cache(current_user['data']['user_code'], user_id)
            self._clear_list_cache()
            
            # 获取更新后的用户信息（不检查状态）
            updated_user = self._get_user_by_id_without_status_check(user_id)
            
            return {
                'success': True,
                'data': updated_user['data'],
                'message': '用户信息更新成功'
            }
            
        except Exception as e:
            logger.error(f"更新用户信息失败: {str(e)}")
            return {
                'success': False,
                'error': f'更新用户信息失败: {str(e)}'
            }
    
    def delete_user(self, user_id: int) -> Dict[str, Any]:
        """删除用户（软删除）"""
        try:
            db_service = get_database_service()
            
            # 获取用户信息（不检查状态）
            current_user = self._get_user_by_id_without_status_check(user_id)
            if not current_user['success'] or not current_user['data']:
                return {
                    'success': False,
                    'error': '用户不存在'
                }
            
            # 软删除用户（将状态设置为0）
            sql = """
            UPDATE users 
            SET status = 0
            WHERE id = :user_id
            """
            
            db_service.execute_update(sql, {'user_id': user_id})
            
            # 清除缓存
            self._clear_user_cache(current_user['data']['user_code'], user_id)
            self._clear_list_cache()
            
            return {
                'success': True,
                'message': '用户删除成功'
            }
            
        except Exception as e:
            logger.error(f"删除用户失败: {str(e)}")
            return {
                'success': False,
                'error': f'删除用户失败: {str(e)}'
            }

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