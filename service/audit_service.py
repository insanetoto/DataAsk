# -*- coding: utf-8 -*-
"""
操作审计服务
记录系统管理操作的审计日志
"""
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from flask import request, g
from sqlalchemy import text
from tools.database import DatabaseService
from tools.redis_service import RedisService

logger = logging.getLogger(__name__)

class AuditService:
    """操作审计服务"""
    
    def __init__(self, db_service: DatabaseService = None, redis_service: RedisService = None):
        """
        初始化审计服务
        
        Args:
            db_service: 数据库服务实例
            redis_service: Redis服务实例（可选，用于缓存）
        """
        from tools.database import get_database_service
        from tools.redis_service import get_redis_service
        
        self.db_service = db_service or get_database_service()
        self.redis_service = redis_service or get_redis_service()
        self.cache_prefix = "audit:"
        self.cache_timeout = 3600  # 1小时
        
    def record_operation(self, 
                        user_info: Dict[str, Any],
                        module: str,
                        operation: str,
                        target_type: str,
                        target_id: str = None,
                        target_name: str = None,
                        old_data: Dict[str, Any] = None,
                        new_data: Dict[str, Any] = None,
                        operation_desc: str = None,
                        result: str = 'success',
                        error_message: str = None) -> bool:
        """
        记录操作审计日志
        
        Args:
            user_info: 操作用户信息
            module: 操作模块（user/org/role/permission）
            operation: 操作类型（create/update/delete/disable/enable）
            target_type: 目标对象类型
            target_id: 目标对象ID
            target_name: 目标对象名称
            old_data: 操作前数据
            new_data: 操作后数据
            operation_desc: 操作描述
            result: 操作结果（success/failure）
            error_message: 错误信息
            
        Returns:
            bool: 是否记录成功
        """
        try:
            # 生成请求ID
            request_id = str(uuid.uuid4())
            
            # 获取请求信息
            ip_address = self._get_client_ip()
            user_agent = self._get_user_agent()
            
            # 准备审计数据
            audit_data = {
                'user_id': user_info.get('id', 0),
                'username': user_info.get('username', ''),
                'user_code': user_info.get('user_code', ''),
                'org_code': user_info.get('org_code', ''),
                'module': module,
                'operation': operation,
                'target_type': target_type,
                'target_id': str(target_id) if target_id else None,
                'target_name': target_name,
                'old_data': json.dumps(old_data, ensure_ascii=False, default=str) if old_data else None,
                'new_data': json.dumps(new_data, ensure_ascii=False, default=str) if new_data else None,
                'operation_desc': operation_desc,
                'ip_address': ip_address,
                'user_agent': user_agent,
                'request_id': request_id,
                'operation_time': datetime.now(),
                'result': result,
                'error_message': error_message
            }
            
            # 插入数据库
            with self.db_service.get_session() as session:
                session.execute(
                    text("""
                        INSERT INTO operation_audit (
                            user_id, username, user_code, org_code, module, operation,
                            target_type, target_id, target_name, old_data, new_data,
                            operation_desc, ip_address, user_agent, request_id,
                            operation_time, result, error_message
                        ) VALUES (
                            :user_id, :username, :user_code, :org_code, :module, :operation,
                            :target_type, :target_id, :target_name, :old_data, :new_data,
                            :operation_desc, :ip_address, :user_agent, :request_id,
                            :operation_time, :result, :error_message
                        )
                    """),
                    audit_data
                )
                session.commit()
                
            logger.info(f"审计日志记录成功: {module}.{operation} by {user_info.get('username')}")
            return True
            
        except Exception as e:
            logger.error(f"记录审计日志失败: {str(e)}")
            return False
    
    def get_audit_logs(self, 
                      page: int = 1, 
                      page_size: int = 10,
                      module: str = None,
                      operation: str = None,
                      user_id: int = None,
                      start_time: str = None,
                      end_time: str = None,
                      org_code: str = None) -> Dict[str, Any]:
        """
        获取审计日志列表
        
        Args:
            page: 页码
            page_size: 每页大小
            module: 模块筛选
            operation: 操作类型筛选
            user_id: 用户ID筛选
            start_time: 开始时间
            end_time: 结束时间
            org_code: 机构代码筛选
            
        Returns:
            Dict: 审计日志列表和分页信息
        """
        try:
            # 构建查询条件
            where_conditions = []
            params = {}
            
            if module:
                where_conditions.append("module = :module")
                params['module'] = module
                
            if operation:
                where_conditions.append("operation = :operation")
                params['operation'] = operation
                
            if user_id:
                where_conditions.append("user_id = :user_id")
                params['user_id'] = user_id
                
            if org_code:
                where_conditions.append("org_code = :org_code")
                params['org_code'] = org_code
                
            if start_time:
                where_conditions.append("operation_time >= :start_time")
                params['start_time'] = start_time
                
            if end_time:
                where_conditions.append("operation_time <= :end_time")
                params['end_time'] = end_time
            
            where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
            
            # 计算总数
            with self.db_service.get_session() as session:
                count_result = session.execute(
                    text(f"SELECT COUNT(*) as total FROM operation_audit WHERE {where_clause}"),
                    params
                ).fetchone()
                total = count_result.total if count_result else 0
                
                # 查询数据
                offset = (page - 1) * page_size
                params.update({'limit': page_size, 'offset': offset})
                
                results = session.execute(
                    text(f"""
                        SELECT id, user_id, username, user_code, org_code, module, operation,
                               target_type, target_id, target_name, operation_desc,
                               ip_address, operation_time, result, error_message
                        FROM operation_audit 
                        WHERE {where_clause}
                        ORDER BY operation_time DESC
                        LIMIT :limit OFFSET :offset
                    """),
                    params
                ).fetchall()
                
                audit_logs = []
                for row in results:
                    audit_logs.append({
                        'id': row.id,
                        'user_id': row.user_id,
                        'username': row.username,
                        'user_code': row.user_code,
                        'org_code': row.org_code,
                        'module': row.module,
                        'operation': row.operation,
                        'target_type': row.target_type,
                        'target_id': row.target_id,
                        'target_name': row.target_name,
                        'operation_desc': row.operation_desc,
                        'ip_address': row.ip_address,
                        'operation_time': str(row.operation_time),
                        'result': row.result,
                        'error_message': row.error_message
                    })
                
                return {
                    'success': True,
                    'data': {
                        'list': audit_logs,
                        'total': total,
                        'page': page,
                        'page_size': page_size,
                        'total_pages': (total + page_size - 1) // page_size
                    }
                }
                
        except Exception as e:
            logger.error(f"获取审计日志失败: {str(e)}")
            return {
                'success': False,
                'error': f'获取审计日志失败: {str(e)}'
            }
    
    def get_audit_detail(self, audit_id: int) -> Dict[str, Any]:
        """
        获取审计日志详情
        
        Args:
            audit_id: 审计记录ID
            
        Returns:
            Dict: 审计日志详情
        """
        try:
            with self.db_service.get_session() as session:
                result = session.execute(
                    text("""
                        SELECT * FROM operation_audit WHERE id = :audit_id
                    """),
                    {'audit_id': audit_id}
                ).fetchone()
                
                if not result:
                    return {
                        'success': False,
                        'error': '审计记录不存在'
                    }
                
                audit_detail = {
                    'id': result.id,
                    'user_id': result.user_id,
                    'username': result.username,
                    'user_code': result.user_code,
                    'org_code': result.org_code,
                    'module': result.module,
                    'operation': result.operation,
                    'target_type': result.target_type,
                    'target_id': result.target_id,
                    'target_name': result.target_name,
                    'old_data': json.loads(result.old_data) if result.old_data else None,
                    'new_data': json.loads(result.new_data) if result.new_data else None,
                    'operation_desc': result.operation_desc,
                    'ip_address': result.ip_address,
                    'user_agent': result.user_agent,
                    'request_id': result.request_id,
                    'operation_time': str(result.operation_time),
                    'result': result.result,
                    'error_message': result.error_message,
                    'created_at': str(result.created_at)
                }
                
                return {
                    'success': True,
                    'data': audit_detail
                }
                
        except Exception as e:
            logger.error(f"获取审计日志详情失败: {str(e)}")
            return {
                'success': False,
                'error': f'获取审计日志详情失败: {str(e)}'
            }
    
    def _get_client_ip(self) -> str:
        """获取客户端IP地址"""
        try:
            # 优先获取X-Forwarded-For头（代理环境）
            if request.headers.get('X-Forwarded-For'):
                return request.headers.get('X-Forwarded-For').split(',')[0].strip()
            
            # 其次获取X-Real-IP头（Nginx代理）
            if request.headers.get('X-Real-IP'):
                return request.headers.get('X-Real-IP')
            
            # 最后使用remote_addr
            return request.remote_addr or 'unknown'
        except:
            return 'unknown'
    
    def _get_user_agent(self) -> str:
        """获取用户代理信息"""
        try:
            return request.headers.get('User-Agent', 'unknown')[:500]  # 限制长度
        except:
            return 'unknown'

# 全局审计服务实例
_audit_service_instance = None

def get_audit_service() -> AuditService:
    """获取审计服务实例"""
    global _audit_service_instance
    if _audit_service_instance is None:
        _audit_service_instance = AuditService()
    return _audit_service_instance

def audit_operation(module: str, 
                   operation: str, 
                   target_type: str,
                   target_id: str = None,
                   target_name: str = None,
                   old_data: Dict[str, Any] = None,
                   new_data: Dict[str, Any] = None,
                   operation_desc: str = None):
    """
    审计操作装饰器辅助函数
    
    Args:
        module: 操作模块
        operation: 操作类型
        target_type: 目标对象类型
        target_id: 目标对象ID
        target_name: 目标对象名称
        old_data: 操作前数据
        new_data: 操作后数据
        operation_desc: 操作描述
    """
    try:
        # 获取当前用户信息
        current_user = getattr(g, 'current_user', None)
        if not current_user:
            logger.warning("无法获取当前用户信息，跳过审计记录")
            return
        
        # 记录审计日志
        audit_service = get_audit_service()
        audit_service.record_operation(
            user_info=current_user,
            module=module,
            operation=operation,
            target_type=target_type,
            target_id=target_id,
            target_name=target_name,
            old_data=old_data,
            new_data=new_data,
            operation_desc=operation_desc
        )
    except Exception as e:
        logger.error(f"审计记录失败: {str(e)}") 