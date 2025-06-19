# -*- coding: utf-8 -*-
"""
用户管理服务模块
提供用户的增删改查功能，集成Redis缓存和权限验证
"""
import json
import logging
import secrets
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import bcrypt
import jwt
from tools.database import get_database_service, get_db_session
from tools.redis_service import get_redis_service, RedisService
from sqlalchemy import text, select, func
from sqlalchemy.orm import Session
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
        self.redis = RedisService()
        self.JWT_SECRET = Config.JWT_SECRET_KEY  # 从配置文件读取
        self.ACCESS_TOKEN_EXPIRE_MINUTES = 30
        self.REFRESH_TOKEN_EXPIRE_DAYS = 7
        self.db_service = get_database_service()
        
    def create_user(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """创建用户"""
        try:
            # 验证必要字段
            required_fields = ['org_code', 'user_code', 'username', 'password', 'role_id']
            for field in required_fields:
                if field not in data or not str(data[field]).strip():
                    return {
                        'success': False,
                        'error': f'缺少必要字段: {field}'
                    }
            
            with get_db_session() as session:
                # 检查用户编码是否已存在
                existing_user = self.get_user_by_code(data['user_code'])
                if existing_user['success'] and existing_user['data']:
                    return {
                        'success': False,
                        'error': f'用户编码 {data["user_code"]} 已存在'
                    }
                
                # 加密密码
                password_hash = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt())
                
                # 准备用户数据
                user_data = {
                    'org_code': data['org_code'],
                    'user_code': data['user_code'],
                    'username': data['username'],
                    'password_hash': password_hash,
                    'role_id': data['role_id'],
                    'phone': data.get('phone'),
                    'address': data.get('address'),
                    'status': data.get('status', 1)
                }
                
                # 插入用户数据
                result = session.execute(
                    text("""
                        INSERT INTO users (org_code, user_code, username, password_hash, role_id, phone, address, status)
                        VALUES (:org_code, :user_code, :username, :password_hash, :role_id, :phone, :address, :status)
                    """),
                    user_data
                )
                session.commit()
                
                # 获取新创建的用户ID
                user_id = result.lastrowid
                
                # 清除列表缓存
                self._clear_list_cache()
                
                logger.info(f"成功创建用户: {data['user_code']} - {data['username']}")
                
                return {
                    'success': True,
                    'data': {
                        'id': user_id,
                        'user_code': data['user_code'],
                        'username': data['username'],
                        'org_code': data['org_code'],
                        'role_id': data['role_id']
                    },
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
            with get_db_session() as session:
                user = session.get(User, user_id)
                
                if not user:
                    return {
                        'success': False,
                        'error': '用户不存在或已禁用'
                    }
                
                user_info = user.to_dict()
                
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
            with get_db_session() as session:
                user = session.scalar(select(User).where(User.user_code == user_code))
                
                if not user:
                    return {
                        'success': True,
                        'data': None
                    }
                
                user_info = user.to_dict()
                
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
            # 如果哈希密码是字符串，需要先编码
            if isinstance(hashed_password, str):
                hashed_password = hashed_password.encode('utf-8')
            logger.info(f"Plain password: {plain_password}")
            logger.info(f"Hashed password: {hashed_password}")
            result = bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password)
            logger.info(f"Password verification result: {result}")
            return result
        except Exception as e:
            logger.error(f"密码验证失败: {str(e)}")
            return False

    def authenticate_user(self, username: str, password: str):
        """验证用户"""
        try:
            with get_db_session() as session:
                # 查询用户（支持用户名或用户编码登录）
                logger.info(f"Authenticating user: {username}")
                result = session.execute(
                    text("""
                        SELECT u.*, r.role_code, o.org_name 
                        FROM users u 
                        JOIN roles r ON u.role_id = r.id 
                        JOIN organizations o ON u.org_code = o.org_code 
                        WHERE (u.username = :username OR u.user_code = :username) 
                        AND u.status = 1
                    """),
                    {"username": username}
                ).fetchone()

                if not result:
                    logger.warning(f"用户不存在或已禁用: {username}")
                    return None

                # 验证密码
                logger.info(f"Found user: {result.username}, password_hash: {result.password_hash}")
                password_hash = result.password_hash
                if isinstance(password_hash, str):
                    password_hash = password_hash.encode('utf-8')
                if not self.verify_password(password, password_hash):
                    logger.warning(f"密码验证失败: {username}")
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
                    "user_code": result.user_code,
                    "org_code": result.org_code,
                    "org_name": result.org_name,
                    "role_code": result.role_code,
                    "avatar": result.avatar if hasattr(result, 'avatar') else None,
                    "email": result.email if hasattr(result, 'email') else None
                }

        except Exception as e:
            logger.error(f"用户认证失败: {str(e)}")
            return None

    def create_tokens(self, user_data: dict):
        """创建访问令牌和刷新令牌"""
        try:
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
                self.ACCESS_TOKEN_EXPIRE_MINUTES * 60
            )
            self.redis.set_token(
                f"refresh_token:{user_data['user_id']}", 
                refresh_token,
                self.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
            )

            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "expires_in": self.ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # 转换为秒
                "token_type": "Bearer"
            }

        except Exception as e:
            logger.error(f"创建令牌失败: {str(e)}")
            return None

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
                expire_time=self.ACCESS_TOKEN_EXPIRE_MINUTES * 60
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
            
            query = select(User)
            if keyword:
                query = query.where(
                    (User.username.like(f"%{keyword}%")) |
                    (User.real_name.like(f"%{keyword}%")) |
                    (User.phone.like(f"%{keyword}%"))
                )
            if status is not None:
                query = query.where(User.status == status)

            total = self.db_service.scalar(select(func.count()).select_from(query.subquery()))
            query = query.offset((page - 1) * page_size).limit(page_size)
            users = self.db_service.scalars(query).all()
            
            result_data = {
                'list': [user.to_dict() for user in users],
                'pagination': {
                    'total': total,
                    'page': page,
                    'page_size': page_size
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
            user = self.db_service.get(User, user_id)
            
            if not user:
                return {
                    'success': False,
                    'error': '用户不存在'
                }
            
            user_info = user.to_dict()
            
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
            with get_db_session() as session:
                user = session.get(User, user_id)
                if not user:
                    return {
                        'success': False,
                        'error': '用户不存在'
                    }
                
                # 更新用户信息
                for key, value in data.items():
                    if hasattr(user, key):
                        setattr(user, key, value)
                
                session.commit()
                session.refresh(user)
                
                # 清除缓存
                self._clear_user_cache(user.user_code, user_id)
                self._clear_list_cache()
                
                return {
                    'success': True,
                    'data': user.to_dict(),
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
            with get_db_session() as session:
                user = session.get(User, user_id)
                if not user:
                    return {
                        'success': False,
                        'error': '用户不存在'
                    }
                
                # 软删除用户
                user.status = 0
                session.commit()
                
                # 清除缓存
                self._clear_user_cache(user.user_code, user_id)
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

    def get_user_roles(self, user_id: int) -> List[dict]:
        """获取用户角色列表"""
        with get_db_session() as session:
            user = session.get(User, user_id)
            if not user:
                return []
            return [role.to_dict() for role in user.roles]

    def set_user_roles(self, user_id: int, role_ids: List[int]) -> bool:
        """设置用户角色"""
        try:
            with get_db_session() as session:
                user = session.get(User, user_id)
                if not user:
                    return False
                
                roles = session.query(Role).filter(Role.id.in_(role_ids)).all()
                user.roles = roles
                session.commit()
                return True
        except Exception as e:
            logger.error(f"设置用户角色失败: {str(e)}")
            return False

    def get_user_permissions(self, user_id: int) -> List[dict]:
        """获取用户权限列表"""
        with get_db_session() as session:
            user = session.get(User, user_id)
            if not user:
                return []
            return [permission.to_dict() for permission in user.permissions]

    def verify_password(self, username: str, password: str) -> Optional[dict]:
        """验证用户密码"""
        with get_db_session() as session:
            user = session.scalar(select(User).where(User.username == username))
            if not user:
                return None
            
            if not self.verify_password(password, user.password_hash):
                return None
            
            return user.to_dict()

    def change_password(self, user_id: int, old_password: str, new_password: str) -> bool:
        """修改用户密码"""
        try:
            with get_db_session() as session:
                user = session.get(User, user_id)
                if not user:
                    return False
                
                if not self.verify_password(old_password, user.password_hash):
                    return False
                
                # 加密新密码
                salt = bcrypt.gensalt()
                password_hash = bcrypt.hashpw(new_password.encode('utf-8'), salt)
                user.password_hash = password_hash
                
                session.commit()
                return True
        except Exception as e:
            logger.error(f"修改密码失败: {str(e)}")
            return False

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