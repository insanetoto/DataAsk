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
from tools.database import DatabaseService, get_database_service
from tools.redis_service import RedisService, get_redis_service
from sqlalchemy import text, select, func
from sqlalchemy.orm import Session
from config import Config
from tools.di_container import DIContainer

logger = logging.getLogger(__name__)

class UserService:
    """用户管理服务类"""
    
    def __init__(self, redis_service: RedisService = None, db_service: DatabaseService = None, permission_service = None):
        self.cache_prefix = "user:"
        self.session_prefix = "session:"
        self.cache_timeout = 3600  # 缓存1小时
        self.session_timeout = 7200  # 会话2小时
        self.list_cache_key = "user:list"
        self.redis = redis_service or get_redis_service()
        self.JWT_SECRET = Config.JWT_SECRET_KEY  # 从配置文件读取
        self.ACCESS_TOKEN_EXPIRE_MINUTES = 30
        self.REFRESH_TOKEN_EXPIRE_DAYS = 7
        self.db_service = db_service or get_database_service()
        self.permission_service = permission_service or get_permission_service()
        
    def create_user(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """创建用户"""
        try:
            # 验证必要字段
            required_fields = ['user_code', 'username', 'password', 'org_code', 'role_id']
            for field in required_fields:
                if field not in data or not data[field]:
                    return {
                        'success': False,
                        'error': f'缺少必要字段: {field}'
                    }
            
            # 检查用户编码是否已存在
            existing_user = self.get_user_by_code(data['user_code'])
            if existing_user['success'] and existing_user['data']:
                return {
                    'success': False,
                    'error': '用户编码已存在'
                }
            
            # 密码hash处理
            password_hash = self._hash_password(data['password'])
            
            # 准备插入数据
            insert_data = {
                'user_code': data['user_code'],
                'username': data['username'],
                'password_hash': password_hash,
                'org_code': data['org_code'],
                'role_id': int(data['role_id']),
                'phone': data.get('phone', ''),
                'address': data.get('address', ''),
                'status': data.get('status', 1)  # 默认启用
            }
            
            # 插入数据库
            with self.db_service.get_session() as session:
                result = session.execute(
                    text("""
                        INSERT INTO users (user_code, username, password_hash, org_code, role_id, phone, address, status, created_at, updated_at)
                        VALUES (:user_code, :username, :password_hash, :org_code, :role_id, :phone, :address, :status, NOW(), NOW())
                    """),
                    insert_data
                )
                session.commit()
                
                # 获取插入的用户ID
                user_id = result.lastrowid
                
                # 获取创建后的完整用户数据
                new_user_result = self._get_user_by_id_without_status_check(user_id)
                new_user_data = new_user_result['data'] if new_user_result['success'] else None
                
                # 记录审计日志
                from service.audit_service import audit_operation
                audit_operation(
                    module='user',
                    operation='create',
                    target_type='user',
                    target_id=str(user_id),
                    target_name=data['username'],
                    old_data=None,
                    new_data=new_user_data,
                    operation_desc=f"创建用户: {data['username']}"
                )
                
                # 清除缓存
                self._clear_list_cache()
                
                return {
                    'success': True,
                    'message': '用户创建成功',
                    'data': {'user_id': user_id}
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
            cached_data = self.redis.get_cache(cache_key)
            
            if cached_data:
        
                # cached_data 已经是字典对象，不需要再json.loads
                cached_user = cached_data if isinstance(cached_data, dict) else json.loads(cached_data)
                if cached_user.get('status') != 1:
                    return {
                        'success': False,
                        'error': '用户不存在或已禁用'
                    }
                return {
                    'success': True,
                    'data': cached_user
                }
            
            # 从数据库查询
            with self.db_service.get_session() as session:
                result = session.execute(
                    text("""
                        SELECT u.id, u.org_code, u.user_code, u.username, u.phone, u.address, 
                               u.role_id, u.status, u.created_at, u.updated_at,
                               r.role_code, o.org_name 
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
                    'phone': result.phone,
                    'address': result.address,
                    'role_id': result.role_id,
                    'role_code': result.role_code,
                    'org_name': result.org_name,
                    'status': result.status,
                    'created_at': str(result.created_at),
                    'updated_at': str(result.updated_at) if result.updated_at else None
                }
                
                # 缓存数据
                self.redis.set_cache(cache_key, json.dumps(user_info, default=str), self.cache_timeout)
                
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
            cached_data = self.redis.get_cache(cache_key)
            
            if cached_data:
        
                # cached_data 已经是字典对象，不需要再json.loads
                user_data = cached_data if isinstance(cached_data, dict) else json.loads(cached_data)
                return {
                    'success': True,
                    'data': user_data
                }
            
            # 从数据库查询
            with self.db_service.get_session() as session:
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
                self.redis.set_cache(cache_key, json.dumps(user_info, default=str), self.cache_timeout)
                
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
    
    def verify_password(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """
        验证用户名和密码
        :param username: 用户名
        :param password: 密码
        :return: 用户信息或None
        """
        try:
            # 查询用户
            with self.db_service.get_session() as session:
                query = """
                    SELECT id, username, password_hash as password, status
                    FROM users
                    WHERE username = :username AND status = 1
                """
                result = session.execute(text(query), {"username": username}).fetchone()
                
                if not result:
                    return None
                
                # 验证密码
                stored_password = result.password
                if not bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8')):
                    return None
                
                # 返回用户信息（不包含密码）
                return {
                    'id': result.id,
                    'username': result.username,
                    'status': result.status
                }
                
        except Exception as e:
            logger.error(f"Error in verify_password: {str(e)}")
            return None

    def authenticate_user(self, username: str, password: str):
        """验证用户"""
        try:
            logger.info(f"开始验证用户: {username}")
            
            # 验证密码
            user_info = self.verify_password(username, password)
            if not user_info:
                logger.warning(f"密码验证失败: {username}")
                return {
                    'success': False,
                    'error': '用户名或密码错误'
                }
            
            logger.info(f"密码验证成功: {username}")
            
            # 生成令牌
            tokens = self.create_tokens(user_info)
            
            return {
                'success': True,
                'data': {
                    'user': user_info,
                    'access_token': tokens['access_token'],
                    'refresh_token': tokens['refresh_token'],
                    'token_type': tokens['token_type'],
                    'expires_in': tokens['expires_in']
                }
            }
                
        except Exception as e:
            logger.error(f"用户验证失败: {str(e)}")
            return {
                'success': False,
                'error': f'用户验证失败: {str(e)}'
            }

    def create_tokens(self, user_info: Dict[str, Any]) -> Dict[str, str]:
        """生成访问令牌和刷新令牌"""
        try:
            # 生成访问令牌
            access_token_payload = {
                'user_id': user_info['id'],
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
                'user_id': user_info['id'],
                'type': 'refresh',
                'exp': datetime.utcnow() + timedelta(days=7)  # 7天过期
            }
            refresh_token = jwt.encode(refresh_token_payload, self.JWT_SECRET, algorithm='HS256')
            
            # 存储刷新令牌到Redis
            redis_service = get_redis_service()
            refresh_token_key = f"refresh_token:{user_info['id']}"
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
        
                # cached_data 已经是字典对象，不需要再json.loads
                list_data = cached_data if isinstance(cached_data, dict) else json.loads(cached_data)
                return {
                    'success': True,
                    'data': list_data
                }
            
            # 构建SQL查询
            with self.db_service.get_session() as session:
                # 基础查询条件
                where_clauses = ["1=1"]
                params = {}
                
                if status is not None:
                    where_clauses.append("u.status = :status")
                    params['status'] = status
                
                if org_code:
                    where_clauses.append("u.org_code = :org_code")
                    params['org_code'] = org_code
                
                if role_level is not None:
                    where_clauses.append("r.role_level = :role_level")
                    params['role_level'] = role_level
                
                if keyword:
                    where_clauses.append("(u.username LIKE :keyword OR u.user_code LIKE :keyword)")
                    params['keyword'] = f"%{keyword}%"
                
                if current_user_org:
                    where_clauses.append("u.org_code = :current_user_org")
                    params['current_user_org'] = current_user_org
                
                # 计算总数
                count_sql = f"""
                    SELECT COUNT(*) as total
                    FROM users u
                    JOIN roles r ON u.role_id = r.id
                    JOIN organizations o ON u.org_code = o.org_code
                    WHERE {' AND '.join(where_clauses)}
                """
                total = session.execute(text(count_sql), params).scalar()
                
                # 获取分页数据
                params['offset'] = (page - 1) * page_size
                params['limit'] = page_size
                
                list_sql = f"""
                    SELECT u.*, r.role_code, r.role_name, o.org_name
                    FROM users u
                    JOIN roles r ON u.role_id = r.id
                    JOIN organizations o ON u.org_code = o.org_code
                    WHERE {' AND '.join(where_clauses)}
                    ORDER BY u.created_at DESC
                    LIMIT :limit OFFSET :offset
                """
                
                users = session.execute(text(list_sql), params).fetchall()
                
                # 格式化用户数据 - 包含完整的机构和角色对象信息
                user_list = []
                for user in users:
                    user_dict = {
                        'id': user.id,
                        'user_code': user.user_code,
                        'username': user.username,
                        'org_code': user.org_code,
                        'role_id': user.role_id,
                        'phone': getattr(user, 'phone', None),
                        'address': getattr(user, 'address', None),
                        'login_count': getattr(user, 'login_count', 0),
                        'last_login_at': str(user.last_login_at) if getattr(user, 'last_login_at', None) else None,
                        'status': user.status,
                        'created_at': str(user.created_at),
                        'updated_at': str(user.updated_at) if user.updated_at else None
                    }
                    
                    # 添加机构信息对象
                    user_dict['organization'] = {
                        'org_code': user.org_code,
                        'org_name': user.org_name
                    }
                    
                    # 添加角色信息对象
                    user_dict['role'] = {
                        'id': user.role_id,
                        'role_code': user.role_code,
                        'role_name': user.role_name
                    }
                    
                    user_list.append(user_dict)
                
                result = {
                    'items': user_list,
                    'total': total,
                    'page': page,
                    'page_size': page_size
                }
                
                # 缓存结果
                redis_service.set_cache(cache_key, json.dumps(result), self.cache_timeout)
                
                return {
                    'success': True,
                    'data': result
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
            with self.db_service.get_session() as session:
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
            # 先获取原始数据用于审计
            old_user_result = self._get_user_by_id_without_status_check(user_id)
            if not old_user_result['success']:
                return {
                    'success': False,
                    'error': '用户不存在'
                }
            old_user_data = old_user_result['data']
            
            # 清除缓存
            user_code = old_user_data.get('user_code')
            self._clear_user_cache(user_code, user_id)
            # 清除用户列表缓存，确保前端获取到最新数据
            self._clear_list_cache()
            
            # 如果修改了密码，需要hash处理
            if 'password' in data and data['password']:
                data['password_hash'] = self._hash_password(data['password'])
                del data['password']
            
            # 更新数据库
            with self.db_service.get_session() as session:
                # 构建更新语句
                update_fields = []
                params = {'user_id': user_id}
                
                for key, value in data.items():
                    if key not in ['id', 'created_at']:  # 排除不可更新的字段
                        update_fields.append(f"{key} = :{key}")
                        params[key] = value
                
                if not update_fields:
                    return {
                        'success': False,
                        'error': '没有需要更新的字段'
                    }
                
                update_fields.append("updated_at = NOW()")
                update_sql = f"UPDATE users SET {', '.join(update_fields)} WHERE id = :user_id"
                
                session.execute(text(update_sql), params)
                session.commit()
                
                # 获取更新后的数据
                new_user_result = self._get_user_by_id_without_status_check(user_id)
                new_user_data = new_user_result['data'] if new_user_result['success'] else None
                
                # 记录审计日志
                from service.audit_service import audit_operation
                operation_type = 'disable' if data.get('status') == 0 else 'update'
                operation_desc = f"{'停用' if operation_type == 'disable' else '更新'}用户: {old_user_data.get('username')}"
                
                audit_operation(
                    module='user',
                    operation=operation_type,
                    target_type='user',
                    target_id=str(user_id),
                    target_name=old_user_data.get('username'),
                    old_data=old_user_data,
                    new_data=new_user_data,
                    operation_desc=operation_desc
                )
                
                return {
                    'success': True,
                    'message': '用户信息更新成功'
                }
                
        except Exception as e:
            logger.error(f"更新用户信息失败: {str(e)}")
            return {
                'success': False,
                'error': f'更新用户信息失败: {str(e)}'
            }
    
    def delete_user(self, user_id: int) -> Dict[str, Any]:
        """删除用户"""
        try:
            # 先获取用户数据用于审计
            user_result = self._get_user_by_id_without_status_check(user_id)
            if not user_result['success']:
                return {
                    'success': False,
                    'error': '用户不存在'
                }
            user_data = user_result['data']
            user_code = user_data.get('user_code')
            username = user_data.get('username')
            
            # 检查是否可以删除（不能删除自己）
            from flask import g
            current_user = getattr(g, 'current_user', None)
            if current_user and current_user.get('id') == user_id:
                return {
                    'success': False,
                    'error': '不能删除自己的账户'
                }
            
            # 开始删除流程
            with self.db_service.get_session() as session:
                # 删除用户会话记录（如果存在）
                try:
                    session.execute(
                        text("DELETE FROM user_sessions WHERE user_id = :user_id"),
                        {"user_id": user_id}
                    )
                except Exception as e:
                    # 如果user_sessions表不存在，忽略错误
                    logger.warning(f"删除用户会话记录时出错（可能表不存在）: {str(e)}")
                
                # 删除用户
                session.execute(
                    text("DELETE FROM users WHERE id = :user_id"),
                    {"user_id": user_id}
                )
                
                session.commit()
                
                # 清除所有相关缓存和token
                self._clear_user_all_cache_and_tokens(user_id, user_code)
                # 清除用户列表缓存，确保前端获取到最新数据
                self._clear_list_cache()
                
                # 记录审计日志
                from service.audit_service import audit_operation
                audit_operation(
                    module='user',
                    operation='delete',
                    target_type='user',
                    target_id=str(user_id),
                    target_name=username,
                    old_data=user_data,
                    new_data=None,
                    operation_desc=f"永久删除用户: {username}"
                )
                
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
        with self.db_service.get_session() as session:
            user = session.get(User, user_id)
            if not user:
                return []
            return [role.to_dict() for role in user.roles]

    def set_user_roles(self, user_id: int, role_ids: List[int]) -> bool:
        """设置用户角色"""
        try:
            with self.db_service.get_session() as session:
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
        return self.permission_service.get_user_permissions(user_id)

    def change_password(self, user_id: int, old_password: str, new_password: str) -> bool:
        """修改密码"""
        try:
            # 获取用户信息
            user_info = self.get_user_by_id(user_id)
            if not user_info['success']:
                return False
            
            # 验证旧密码
            if not self.verify_password(user_info['data']['username'], old_password):
                return False
            
            # 更新密码
            with self.db_service.get_session() as session:
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

    def reset_user_password(self, user_id: int, new_password: str, operator_user: Dict[str, Any]) -> Dict[str, Any]:
        """
        重置用户密码
        包含权限控制：超级管理员可重置所有用户，机构管理员只能重置本机构用户
        
        Args:
            user_id: 目标用户ID
            new_password: 新密码
            operator_user: 操作者用户信息
            
        Returns:
            操作结果
        """
        try:
            # 获取目标用户信息
            target_user_result = self.get_user_by_id(user_id)
            if not target_user_result['success']:
                return {
                    'success': False,
                    'error': '目标用户不存在或已禁用'
                }
            
            target_user = target_user_result['data']
            operator_role_code = operator_user.get('role_code', '')
            operator_org_code = operator_user.get('org_code', '')
            
            # 权限控制检查
            if operator_role_code == 'SUPER_ADMIN':
                # 超级管理员可以重置所有用户密码
                pass
            elif operator_role_code == 'ORG_ADMIN':
                # 机构管理员只能重置本机构用户密码
                if target_user['org_code'] != operator_org_code:
                    return {
                        'success': False,
                        'error': '权限不足：只能重置本机构用户的密码'
                    }
            else:
                # 其他角色无权限重置密码
                return {
                    'success': False,
                    'error': '权限不足：无重置密码权限'
                }
            
            # 更新密码
            with self.db_service.get_session() as session:
                session.execute(
                    text("""
                        UPDATE users 
                        SET password_hash = :password_hash, updated_at = NOW()
                        WHERE id = :user_id
                    """),
                    {
                        'password_hash': new_password,  # 直接存储明文密码
                        'user_id': user_id
                    }
                )
                session.commit()
            
            # 清除目标用户的所有缓存和token
            self._clear_user_all_cache_and_tokens(user_id, target_user['user_code'])
            
            logger.info(f"管理员 {operator_user.get('username')} 重置了用户 {target_user['username']} 的密码")
            
            return {
                'success': True,
                'message': f'用户 {target_user["username"]} 的密码重置成功'
            }
            
        except Exception as e:
            logger.error(f"重置用户密码失败: {str(e)}")
            return {
                'success': False,
                'error': f'重置密码失败: {str(e)}'
            }
    
    def _clear_user_all_cache_and_tokens(self, user_id: int, user_code: str):
        """
        清除用户的所有缓存和token，强制重新登录
        
        Args:
            user_id: 用户ID
            user_code: 用户编码
        """
        try:
            # 清除用户基本信息缓存
            cache_keys = [
                f"{self.cache_prefix}id:{user_id}",
                f"{self.cache_prefix}code:{user_code}",
                f"{self.session_prefix}{user_id}"
            ]
            
            for cache_key in cache_keys:
                self.redis.delete_cache(cache_key)
            
            # 清除用户的所有token
            token_keys = [
                f"access_token:{user_id}",
                f"refresh_token:{user_id}",
                f"session:{user_id}"
            ]
            
            for token_key in token_keys:
                self.redis.delete_token(token_key)
            
            # 清除列表缓存
            self._clear_list_cache()
            
            logger.info(f"已清除用户 {user_code} 的所有缓存和token")
            
        except Exception as e:
            logger.error(f"清除用户缓存和token失败: {str(e)}")

def get_user_service_instance() -> UserService:
    """
    获取UserService实例的工厂函数
    """
    from tools.redis_service import get_redis_service
    from tools.database import get_database_service
    from service.permission_service import get_permission_service_instance
    
    redis_service = get_redis_service()
    db_service = get_database_service()
    permission_service = get_permission_service_instance()
    return UserService(redis_service=redis_service, db_service=db_service, permission_service=permission_service)

def get_user_service() -> UserService:
    """
    获取UserService的单例实例
    """
    # 简化版本，直接返回新实例
    return get_user_service_instance() 