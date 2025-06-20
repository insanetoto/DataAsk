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
from service.permission_service import get_permission_service
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
                
                # 准备用户数据
                user_data = {
                    'org_code': data['org_code'],
                    'user_code': data['user_code'],
                    'username': data['username'],
                    'password_hash': data['password'],  # 直接存储明文密码
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
                result = session.execute(
                    text("""
                        SELECT u.*, r.role_code, o.org_name 
                        FROM users u 
                        JOIN roles r ON u.role_id = r.id 
                        JOIN organizations o ON u.org_code = o.org_code 
                        WHERE u.id = :user_id
                    """),
                    {"user_id": user_id}
                ).fetchone()
                
                if not result:
                    return {
                        'success': False,
                        'error': '用户不存在或已禁用'
                    }
                
                user_info = {
                    'id': result.id,
                    'org_code': result.org_code,
                    'user_code': result.user_code,
                    'username': result.username,
                    'role_id': result.role_id,
                    'role_code': result.role_code,
                    'org_name': result.org_name,
                    'status': result.status,
                    'created_at': str(result.created_at),
                    'updated_at': str(result.updated_at) if result.updated_at else None
                }
                
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
                result = session.execute(
                    text("""
                        SELECT u.*, r.role_code, o.org_name 
                        FROM users u 
                        JOIN roles r ON u.role_id = r.id 
                        JOIN organizations o ON u.org_code = o.org_code 
                        WHERE u.user_code = :user_code
                    """),
                    {"user_code": user_code}
                ).fetchone()
                
                if not result:
                    return {
                        'success': True,
                        'data': None
                    }
                
                user_info = {
                    'id': result.id,
                    'org_code': result.org_code,
                    'user_code': result.user_code,
                    'username': result.username,
                    'role_id': result.role_id,
                    'role_code': result.role_code,
                    'org_name': result.org_name,
                    'status': result.status,
                    'created_at': str(result.created_at),
                    'updated_at': str(result.updated_at) if result.updated_at else None
                }
                
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
    
    def verify_password(self, plain_password: str, stored_password: str) -> bool:
        """验证密码"""
        try:
            if not plain_password or not stored_password:
                logger.warning("密码为空")
                return False
            
            logger.info("开始验证密码")
            
            # 使用bcrypt验证密码
            try:
                result = bcrypt.checkpw(
                    plain_password.encode('utf-8'),
                    stored_password.encode('utf-8')
                )
                logger.info(f"密码验证结果: {result}")
                return result
            except ValueError as e:
                logger.error(f"密码格式错误: {str(e)}")
                return False
            
        except Exception as e:
            logger.error(f"密码验证失败: {str(e)}")
            return False

    def authenticate_user(self, username: str, password: str):
        """验证用户"""
        try:
            logger.info(f"开始验证用户: {username}")
            
            # 查询用户
            with get_db_session() as session:
                sql = """
                    SELECT u.*, r.role_code, o.org_name 
                    FROM users u 
                    JOIN roles r ON u.role_id = r.id 
                    JOIN organizations o ON u.org_code = o.org_code 
                    WHERE (u.username = :username OR u.user_code = :username) 
                    AND u.status = 1
                """
                logger.info(f"执行SQL查询: {sql}")
                logger.info(f"查询参数: username={username}")
                result = session.execute(text(sql), {"username": username}).fetchone()
                
                if not result:
                    logger.warning(f"用户不存在或已禁用: {username}")
                    return None
                
                logger.info(f"找到用户: {username}")
                
                # 将查询结果转换为字典
                user_data = {
                    'id': result.id,
                    'username': result.username,
                    'user_code': result.user_code,
                    'password_hash': result.password_hash,
                    'org_code': result.org_code,
                    'org_name': result.org_name,
                    'role_code': result.role_code
                }
                
                logger.info(f"用户数据: {user_data}")

                # 验证密码
                logger.info(f"开始验证密码")
                if not self.verify_password(password, user_data['password_hash']):
                    logger.warning(f"密码验证失败: {username}")
                    return None
                
                logger.info(f"密码验证成功: {username}")
                
                return {
                    "user_id": user_data['id'],
                    "username": user_data['username'],
                    "user_code": user_data['user_code'],
                    "org_code": user_data['org_code'],
                    "org_name": user_data['org_name'],
                    "role_code": user_data['role_code']
                }
                
        except Exception as e:
            logger.error(f"用户验证失败: {str(e)}")
            raise

    def create_tokens(self, user_info: Dict[str, Any]) -> Dict[str, str]:
        """生成访问令牌和刷新令牌"""
        try:
            # 生成访问令牌
            access_token_payload = {
                'user_id': user_info['user_id'],
                'username': user_info['username'],
                'user_code': user_info['user_code'],
                'org_code': user_info['org_code'],
                'role_code': user_info['role_code'],
                'type': 'access',
                'exp': datetime.utcnow() + timedelta(minutes=30)  # 30分钟过期
            }
            access_token = jwt.encode(access_token_payload, self.JWT_SECRET, algorithm='HS256')
            
            # 生成刷新令牌
            refresh_token_payload = {
                'user_id': user_info['user_id'],
                'type': 'refresh',
                'exp': datetime.utcnow() + timedelta(days=7)  # 7天过期
            }
            refresh_token = jwt.encode(refresh_token_payload, self.JWT_SECRET, algorithm='HS256')
            
            # 存储刷新令牌到Redis
            redis_service = get_redis_service()
            refresh_token_key = f"refresh_token:{user_info['user_id']}"
            redis_service.set_cache(refresh_token_key, refresh_token, 7 * 24 * 60 * 60)  # 7天过期
            
            return {
                'access_token': access_token,
                'refresh_token': refresh_token,
                'token_type': 'Bearer',
                'expires_in': 1800  # 30分钟（秒）
            }
        except Exception as e:
            logger.error(f"生成令牌失败: {str(e)}")
            raise Exception('令牌生成失败')
            
    def verify_token(self, token: str) -> Dict[str, Any]:
        """验证令牌"""
        try:
            # 解码并验证令牌
            payload = jwt.decode(token, self.JWT_SECRET, algorithms=['HS256'])
            
            # 检查令牌类型
            if payload.get('type') != 'access':
                raise Exception('无效的令牌类型')
            
            # 获取用户信息
            user_info = self.get_user_by_id(payload['user_id'])
            if not user_info['success']:
                raise Exception('用户不存在或已禁用')
            
            return {
                'success': True,
                'data': user_info['data']
            }
        except jwt.ExpiredSignatureError:
            return {
                'success': False,
                'error': '令牌已过期'
            }
        except jwt.InvalidTokenError:
            return {
                'success': False,
                'error': '无效的令牌'
            }
        except Exception as e:
            logger.error(f"验证令牌失败: {str(e)}")
            return {
                'success': False,
                'error': f'令牌验证失败: {str(e)}'
            }

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
            
            # 构建SQL查询
            with get_db_session() as session:
                # 计算总数
                count_sql = """
                    SELECT COUNT(*) as total
                    FROM users u
                    JOIN roles r ON u.role_id = r.id
                    JOIN organizations o ON u.org_code = o.org_code
                    WHERE 1=1
                """
                params = {}
                
                if keyword:
                    count_sql += " AND (u.username LIKE :keyword OR u.user_code LIKE :keyword)"
                    params['keyword'] = f"%{keyword}%"
                if status is not None:
                    count_sql += " AND u.status = :status"
                    params['status'] = status
                if org_code:
                    count_sql += " AND u.org_code LIKE :org_code"
                    params['org_code'] = f"{org_code}%"
                
                total = session.execute(text(count_sql), params).scalar()
                
                # 查询用户列表
                sql = """
                    SELECT u.*, r.role_code, r.role_name, o.org_name
                    FROM users u
                    JOIN roles r ON u.role_id = r.id
                    JOIN organizations o ON u.org_code = o.org_code
                    WHERE 1=1
                """
                
                if keyword:
                    sql += " AND (u.username LIKE :keyword OR u.user_code LIKE :keyword)"
                if status is not None:
                    sql += " AND u.status = :status"
                if org_code:
                    sql += " AND u.org_code LIKE :org_code"
                
                sql += " ORDER BY u.created_at DESC LIMIT :offset, :limit"
                params['offset'] = (page - 1) * page_size
                params['limit'] = page_size
                
                users = session.execute(text(sql), params).fetchall()
                
                result_data = {
                    'list': [dict(user) for user in users],
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
            with get_db_session() as session:
                result = session.execute(
                    text("""
                        SELECT u.*, r.role_code, o.org_name 
                        FROM users u 
                        JOIN roles r ON u.role_id = r.id 
                        JOIN organizations o ON u.org_code = o.org_code 
                        WHERE u.id = :user_id
                    """),
                    {"user_id": user_id}
                ).fetchone()
                
                if not result:
                    return {
                        'success': False,
                        'error': '用户不存在'
                    }
                
                user_info = {
                    'id': result.id,
                    'org_code': result.org_code,
                    'user_code': result.user_code,
                    'username': result.username,
                    'role_id': result.role_id,
                    'role_code': result.role_code,
                    'org_name': result.org_name,
                    'status': result.status,
                    'created_at': str(result.created_at),
                    'updated_at': str(result.updated_at) if result.updated_at else None
                }
                
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
        permission_service = get_permission_service()
        return permission_service.get_user_permissions(user_id)

    def change_password(self, user_id: int, old_password: str, new_password: str) -> bool:
        """修改密码"""
        try:
            # 获取用户信息
            user_info = self.get_user_by_id(user_id)
            if not user_info['success']:
                return False
            
            # 验证旧密码
            if not self.verify_password(old_password, user_info['data']['password_hash']):
                return False
            
            # 更新密码
            with get_db_session() as session:
                sql = """
                    UPDATE users 
                    SET password_hash = :new_password,
                        updated_at = NOW()
                    WHERE id = :user_id
                """
                session.execute(text(sql), {
                    'user_id': user_id,
                    'new_password': self._hash_password(new_password)
                })
                session.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"修改密码失败: {str(e)}")
            return False

    def _hash_password(self, password: str) -> str:
        """对密码进行哈希处理"""
        try:
            # 使用bcrypt加密密码
            salt = bcrypt.gensalt()
            hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
            return hashed.decode('utf-8')
        except Exception as e:
            logger.error(f"密码加密失败: {str(e)}")
            raise

# 创建单例实例
_user_service_instance = None

def get_user_service_instance() -> UserService:
    """获取UserService的单例实例"""
    global _user_service_instance
    if _user_service_instance is None:
        _user_service_instance = UserService()
    return _user_service_instance

# 保持原有的get_user_service函数以兼容现有代码
def get_user_service() -> UserService:
    return get_user_service_instance() 