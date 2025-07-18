#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
工作流服务增强功能
在原有WorkflowService基础上扩展多工作域和权限控制功能
"""

import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy import text
from service.workflow_service import WorkflowService, get_workflow_service
import logging

logger = logging.getLogger(__name__)

class WorkflowServiceEnhancement:
    """工作流服务增强功能"""
    
    def __init__(self, base_service: WorkflowService):
        """初始化增强功能"""
        self.base_service = base_service
        self.main_engine = base_service.main_engine
        self.airflow_engine = base_service.airflow_engine

    # ================================
    # 工作域管理功能
    # ================================

    def get_workspaces(self, user_id: int) -> Dict:
        """获取用户可访问的工作域列表"""
        try:
            with self.main_engine.begin() as conn:
                # 查询用户有权限的工作域
                sql = text("""
                    SELECT DISTINCT w.*, 
                           COUNT(DISTINCT wf.id) as workflow_count,
                           COUNT(DISTINCT CASE WHEN wf.status = 'active' THEN wf.id END) as active_workflow_count
                    FROM workflow_workspaces w
                    LEFT JOIN sys_workflow wf ON wf.workspace = w.code AND wf.status != 'deleted'
                    LEFT JOIN workflow_permissions p ON p.resource_type = 'workspace' 
                                                     AND p.resource_id = w.id 
                                                     AND p.subject_type = 'user' 
                                                     AND p.subject_id = :user_id
                                                     AND p.permission_type IN ('view', 'manage')
                                                     AND p.granted = 1
                    LEFT JOIN users u ON u.id = :user_id
                    LEFT JOIN roles r ON r.id = u.role_id
                    WHERE w.status = 'active' 
                      AND (p.id IS NOT NULL OR w.creator_id = :user_id OR r.role_name IN ('admin', 'super_admin') OR :user_id IN (1, 2))
                    GROUP BY w.id
                    ORDER BY w.order_num, w.name
                """)
                
                result = conn.execute(sql, {'user_id': user_id})
                workspaces = []
                
                for row in result:
                    workspaces.append({
                        'id': row.id,
                        'code': row.code,
                        'name': row.name,
                        'description': row.description,
                        'icon': row.icon,
                        'color': row.color,
                        'status': row.status,
                        'order_num': row.order_num,
                        'workflow_count': row.workflow_count or 0,
                        'active_workflow_count': row.active_workflow_count or 0,
                        'created_at': row.created_at.isoformat() if row.created_at else None,
                        'updated_at': row.updated_at.isoformat() if row.updated_at else None
                    })
                
                return {
                    'success': True,
                    'data': workspaces,
                    'total': len(workspaces)
                }
        
        except Exception as e:
            logger.error(f"获取工作域列表失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': '获取工作域列表失败'
            }

    def get_workspace_categories(self, workspace_code: str, user_id: int) -> Dict:
        """获取工作域下的业务流程分类"""
        try:
            # 检查权限
            if not self._check_workspace_permission(workspace_code, user_id, 'view'):
                return {
                    'success': False,
                    'message': '您没有权限访问此工作域'
                }
            
            with self.main_engine.begin() as conn:
                sql = text("""
                    SELECT 
                        category,
                        sub_category,
                        COUNT(*) as workflow_count,
                        COUNT(CASE WHEN status = 'active' THEN 1 END) as active_count,
                        COUNT(CASE WHEN status = 'inactive' THEN 1 END) as inactive_count,
                        MIN(created_at) as first_created,
                        MAX(updated_at) as last_updated
                    FROM sys_workflow 
                    WHERE workspace = :workspace_code AND status != 'deleted'
                    GROUP BY category, sub_category
                    ORDER BY category, sub_category
                """)
                
                result = conn.execute(sql, {'workspace_code': workspace_code})
                categories = []
                
                for row in result:
                    categories.append({
                        'category': row.category,
                        'sub_category': row.sub_category,
                        'workflow_count': row.workflow_count,
                        'active_count': row.active_count,
                        'inactive_count': row.inactive_count,
                        'first_created': row.first_created.isoformat() if row.first_created else None,
                        'last_updated': row.last_updated.isoformat() if row.last_updated else None
                    })
                
                return {
                    'success': True,
                    'data': categories,
                    'total': len(categories)
                }
                
        except Exception as e:
            logger.error(f"获取分类列表失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': '获取分类列表失败'
            }

    def get_workflows_enhanced(self, filters: Dict = None, user_id: int = None) -> Dict:
        """获取增强的工作流列表"""
        try:
            with self.main_engine.begin() as conn:
                # 构建查询条件
                conditions = ["w.status != 'deleted'"]
                params = {}
                
                if filters:
                    if filters.get('workspace'):
                        conditions.append("w.workspace = :workspace")
                        params['workspace'] = filters['workspace']
                    
                    if filters.get('category'):
                        conditions.append("w.category = :category")
                        params['category'] = filters['category']
                    
                    if filters.get('sub_category'):
                        conditions.append("w.sub_category = :sub_category")
                        params['sub_category'] = filters['sub_category']
                    
                    if filters.get('status'):
                        conditions.append("w.status = :status")
                        params['status'] = filters['status']
                    
                    if filters.get('name'):
                        conditions.append("w.name LIKE :name")
                        params['name'] = f"%{filters['name']}%"
                
                if user_id:
                    params['user_id'] = user_id
                
                where_clause = " AND ".join(conditions)
                
                sql = text(f"""
                    SELECT w.*, 
                           ws.name as workspace_name, ws.icon as workspace_icon, ws.color as workspace_color,
                           u1.username as creator_name,
                           COUNT(DISTINCT s.id) as step_count,
                           COUNT(DISTINCT s.id) as active_step_count,
                           COUNT(DISTINCT e.id) as execution_count,
                           COALESCE(AVG(CASE WHEN e.status = 'success' THEN 1 ELSE 0 END), 0) * 100 as success_rate,
                           MAX(e.started_at) as last_execution_time
                    FROM sys_workflow w
                    LEFT JOIN workflow_workspaces ws ON ws.code = w.workspace
                    LEFT JOIN users u1 ON u1.id = w.creator_id
                    LEFT JOIN workflow_steps s ON s.workflow_id = w.id
                    LEFT JOIN workflow_executions e ON e.workflow_id = w.id
                    WHERE {where_clause}
                    GROUP BY w.id
                    ORDER BY w.updated_at DESC
                """)
                
                result = conn.execute(sql, params)
                workflows = []
                
                for row in result:
                    workflows.append({
                        'id': row.id,
                        'name': row.name,
                        'description': row.description,
                        'category': row.category,
                        'sub_category': row.sub_category,
                        'workspace': row.workspace,
                        'workspace_name': row.workspace_name,
                        'workspace_icon': row.workspace_icon,
                        'workspace_color': row.workspace_color,
                        'status': row.status,
                        'trigger_type': row.trigger_type,
                        'priority': row.priority,
                        'version': row.version,
                        'dag_id': row.dag_id,
                        'schedule': row.schedule,
                        'timeout': row.timeout,
                        'retry_count': row.retry_count,
                        'auto_rollback': False,  # 默认值，因为表中不存在此列
                        'notification_enabled': False,  # 默认值，因为表中不存在此列
                        'step_count': row.step_count or 0,
                        'active_step_count': row.active_step_count or 0,
                        'execution_count': row.execution_count or 0,
                        'success_rate': float(row.success_rate or 0),
                        'creator_name': row.creator_name,
                        'last_execution_time': row.last_execution_time.isoformat() if row.last_execution_time else None,
                        'created_at': row.created_at.isoformat() if row.created_at else None,
                        'updated_at': row.updated_at.isoformat() if row.updated_at else None
                    })
                
                return {
                    'success': True,
                    'data': workflows,
                    'total': len(workflows)
                }
                
        except Exception as e:
            logger.error(f"获取工作流列表失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': '获取工作流列表失败'
            }

    def create_workflow_enhanced(self, workflow_data: Dict, user_id: int) -> Dict:
        """创建增强版工作流"""
        try:
            # 检查工作域权限
            if not self._check_workspace_permission(workflow_data.get('workspace', 'default'), user_id, 'edit'):
                return {
                    'success': False,
                    'message': '您没有权限在此工作域创建工作流'
                }
            
            with self.main_engine.begin() as conn:
                # 生成唯一的DAG ID
                workspace = workflow_data.get('workspace', 'default')
                dag_id = f"workflow_{workspace}_{uuid.uuid4().hex[:8]}"
                
                # 插入工作流定义
                workflow_sql = text("""
                    INSERT INTO sys_workflow (
                        name, description, category, workspace, sub_category, status, 
                        trigger_type, priority, version, dag_id, config, schedule, 
                        timeout, retry_count, auto_rollback, notification_enabled, 
                        notification_config, creator_id
                    ) VALUES (
                        :name, :description, :category, :workspace, :sub_category, :status,
                        :trigger_type, :priority, :version, :dag_id, :config, :schedule,
                        :timeout, :retry_count, :auto_rollback, :notification_enabled,
                        :notification_config, :creator_id
                    )
                """)
                
                result = conn.execute(workflow_sql, {
                    'name': workflow_data['name'],
                    'description': workflow_data.get('description', ''),
                    'category': workflow_data.get('category', 'general'),
                    'workspace': workspace,
                    'sub_category': workflow_data.get('sub_category'),
                    'status': 'inactive',
                    'trigger_type': workflow_data.get('trigger_type', 'manual'),
                    'priority': workflow_data.get('priority', 'normal'),
                    'version': workflow_data.get('version', '1.0.0'),
                    'dag_id': dag_id,
                    'config': json.dumps(workflow_data.get('config', {})),
                    'schedule': workflow_data.get('schedule', ''),
                    'timeout': workflow_data.get('timeout', 3600),
                    'retry_count': workflow_data.get('retry_count', 1),
                    'auto_rollback': workflow_data.get('auto_rollback', 0),
                    'notification_enabled': workflow_data.get('notification_enabled', 1),
                    'notification_config': json.dumps(workflow_data.get('notification_config', {})),
                    'creator_id': user_id
                })
                
                workflow_id = result.lastrowid
                
                # 自动为创建者分配管理权限
                self._grant_workflow_permission(conn, workflow_id, 'user', user_id, 'manage', user_id)
                
                # 如果提供了步骤配置，创建步骤
                if 'steps' in workflow_data:
                    for step_data in workflow_data['steps']:
                        self._create_workflow_step_enhanced(conn, workflow_id, step_data, user_id)
                
                return {
                    'success': True,
                    'workflow_id': workflow_id,
                    'dag_id': dag_id,
                    'message': '工作流创建成功'
                }
                
        except Exception as e:
            logger.error(f"创建工作流失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': '创建工作流失败'
            }

    # ================================
    # 步骤/节点管理功能  
    # ================================

    def get_workflow_steps_enhanced(self, workflow_id: int, user_id: int) -> Dict:
        """获取增强的工作流步骤列表"""
        try:
            # 检查权限
            if not self._check_workflow_permission(workflow_id, user_id, 'view'):
                return {
                    'success': False,
                    'message': '您没有权限查看此工作流'
                }
            
            with self.main_engine.begin() as conn:
                # 获取步骤信息
                steps_sql = text("""
                    SELECT s.*, 
                           COUNT(DISTINCT conn_from.id) as outgoing_connections,
                           COUNT(DISTINCT conn_to.id) as incoming_connections,
                           COUNT(DISTINCT se.id) as execution_count,
                           COALESCE(AVG(CASE WHEN se.status = 'success' THEN 1 ELSE 0 END), 0) * 100 as success_rate
                    FROM workflow_steps s
                    LEFT JOIN workflow_step_connections conn_from ON conn_from.from_step_id = s.id
                    LEFT JOIN workflow_step_connections conn_to ON conn_to.to_step_id = s.id
                    LEFT JOIN workflow_step_executions se ON se.step_id = s.id
                    WHERE s.workflow_id = :workflow_id
                    GROUP BY s.id
                    ORDER BY s.step_order, s.step_name
                """)
                
                result = conn.execute(steps_sql, {'workflow_id': workflow_id})
                steps = []
                
                for row in result:
                    step_config = json.loads(row.config) if row.config else {}
                    
                    steps.append({
                        'id': row.id,
                        'workflow_id': row.workflow_id,
                        'step_name': row.step_name,
                        'step_type': row.step_type,
                        'node_type': row.node_type,
                        'step_order': row.step_order,
                        'position_x': float(row.position_x) if row.position_x else 0,
                        'position_y': float(row.position_y) if row.position_y else 0,
                        'icon': row.icon,
                        'color': row.color,
                        'config': step_config,
                        'timeout': row.timeout,
                        'retry_count': row.retry_count,
                        'condition': row.condition,
                        'skip_on_failure': bool(row.skip_on_failure),
                        'rollback_enabled': bool(row.rollback_enabled),
                        'status': row.status,
                        'outgoing_connections': row.outgoing_connections or 0,
                        'incoming_connections': row.incoming_connections or 0,
                        'execution_count': row.execution_count or 0,
                        'success_rate': float(row.success_rate or 0),
                        'created_at': row.created_at.isoformat() if row.created_at else None,
                        'updated_at': row.updated_at.isoformat() if row.updated_at else None
                    })
                
                # 获取连接信息
                connections_sql = text("""
                    SELECT c.*, 
                           s1.step_name as from_step_name, 
                           s2.step_name as to_step_name
                    FROM workflow_step_connections c
                    LEFT JOIN workflow_steps s1 ON s1.id = c.from_step_id
                    LEFT JOIN workflow_steps s2 ON s2.id = c.to_step_id
                    WHERE c.workflow_id = :workflow_id
                    ORDER BY c.order_num
                """)
                
                conn_result = conn.execute(connections_sql, {'workflow_id': workflow_id})
                connections = []
                
                for row in conn_result:
                    connections.append({
                        'id': row.id,
                        'workflow_id': row.workflow_id,
                        'from_step_id': row.from_step_id,
                        'from_step_name': row.from_step_name,
                        'to_step_id': row.to_step_id,
                        'to_step_name': row.to_step_name,
                        'condition_type': row.condition_type,
                        'condition_expression': row.condition_expression,
                        'condition_config': json.loads(row.condition_config) if row.condition_config else None,
                        'style_config': json.loads(row.style_config) if row.style_config else None,
                        'order_num': row.order_num
                    })
                
                return {
                    'success': True,
                    'data': {
                        'steps': steps,
                        'connections': connections
                    }
                }
                
        except Exception as e:
            logger.error(f"获取工作流步骤失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': '获取工作流步骤失败'
            }

    def create_step_enhanced(self, workflow_id: int, step_data: Dict, user_id: int) -> Dict:
        """创建增强版工作流步骤"""
        try:
            # 检查权限
            if not self._check_workflow_permission(workflow_id, user_id, 'edit'):
                return {
                    'success': False,
                    'message': '您没有权限编辑此工作流'
                }
            
            with self.main_engine.begin() as conn:
                step_id = self._create_workflow_step_enhanced(conn, workflow_id, step_data, user_id)
                
                return {
                    'success': True,
                    'step_id': step_id,
                    'message': '步骤创建成功'
                }
                
        except Exception as e:
            logger.error(f"创建工作流步骤失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': '创建工作流步骤失败'
            }

    # ================================
    # 权限管理功能
    # ================================

    def get_resource_permissions(self, resource_type: str, resource_id: int, user_id: int) -> Dict:
        """获取资源的权限配置"""
        try:
            with self.main_engine.begin() as conn:
                sql = text("""
                    SELECT p.*, 
                           CASE p.subject_type
                               WHEN 'user' THEN u.username
                               WHEN 'role' THEN r.name
                               WHEN 'organization' THEN o.name
                           END as subject_name,
                           ub.username as granted_by_name
                    FROM workflow_permissions p
                    LEFT JOIN users u ON p.subject_type = 'user' AND p.subject_id = u.id
                    LEFT JOIN sys_role r ON p.subject_type = 'role' AND p.subject_id = r.id
                    LEFT JOIN organizations o ON p.subject_type = 'organization' AND p.subject_id = o.id
                    LEFT JOIN users ub ON ub.id = p.granted_by
                    WHERE p.resource_type = :resource_type AND p.resource_id = :resource_id
                    ORDER BY p.subject_type, p.permission_type, p.granted_at
                """)
                
                result = conn.execute(sql, {
                    'resource_type': resource_type,
                    'resource_id': resource_id
                })
                
                permissions = []
                for row in result:
                    permissions.append({
                        'id': row.id,
                        'resource_type': row.resource_type,
                        'resource_id': row.resource_id,
                        'subject_type': row.subject_type,
                        'subject_id': row.subject_id,
                        'subject_name': row.subject_name,
                        'permission_type': row.permission_type,
                        'granted': bool(row.granted),
                        'conditions': json.loads(row.conditions) if row.conditions else None,
                        'granted_by': row.granted_by,
                        'granted_by_name': row.granted_by_name,
                        'granted_at': row.granted_at.isoformat() if row.granted_at else None,
                        'expires_at': row.expires_at.isoformat() if row.expires_at else None
                    })
                
                return {
                    'success': True,
                    'data': permissions
                }
                
        except Exception as e:
            logger.error(f"获取权限配置失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': '获取权限配置失败'
            }

    # ================================
    # 辅助方法
    # ================================

    def _create_workflow_step_enhanced(self, conn, workflow_id: int, step_data: Dict, user_id: int) -> int:
        """创建增强版工作流步骤的内部方法"""
        insert_sql = text("""
            INSERT INTO workflow_steps (
                workflow_id, step_name, step_type, node_type, step_order, depends_on,
                config, timeout, retry_count, condition, position_x, position_y,
                icon, color, skip_on_failure, rollback_enabled, status
            ) VALUES (
                :workflow_id, :step_name, :step_type, :node_type, :step_order, :depends_on,
                :config, :timeout, :retry_count, :condition, :position_x, :position_y,
                :icon, :color, :skip_on_failure, :rollback_enabled, :status
            )
        """)
        
        result = conn.execute(insert_sql, {
            'workflow_id': workflow_id,
            'step_name': step_data['step_name'],
            'step_type': step_data.get('step_type', 'python'),
            'node_type': step_data.get('node_type', 'script'),
            'step_order': step_data.get('step_order', 1),
            'depends_on': json.dumps(step_data.get('depends_on', [])),
            'config': json.dumps(step_data.get('config', {})),
            'timeout': step_data.get('timeout', 1800),
            'retry_count': step_data.get('retry_count', 1),
            'condition': step_data.get('condition', ''),
            'position_x': step_data.get('position_x', 0),
            'position_y': step_data.get('position_y', 0),
            'icon': step_data.get('icon', 'play-circle'),
            'color': step_data.get('color', '#1890ff'),
            'skip_on_failure': step_data.get('skip_on_failure', 0),
            'rollback_enabled': step_data.get('rollback_enabled', 0),
            'status': step_data.get('status', 'active')
        })
        
        return result.lastrowid

    def _check_workspace_permission(self, workspace_code: str, user_id: int, permission_type: str) -> bool:
        """检查工作域权限"""
        try:
            with self.main_engine.begin() as conn:
                sql = text("""
                    SELECT COUNT(*) as has_permission
                    FROM workflow_permissions p
                    JOIN workflow_workspaces w ON w.id = p.resource_id
                    WHERE p.resource_type = 'workspace' AND w.code = :workspace_code
                      AND p.subject_type = 'user' AND p.subject_id = :user_id
                      AND p.permission_type IN (:permission_type, 'manage')
                      AND p.granted = 1
                      AND (p.expires_at IS NULL OR p.expires_at > NOW())
                    
                    UNION ALL
                    
                    SELECT COUNT(*) as has_permission
                    FROM workflow_workspaces w
                    WHERE w.code = :workspace_code AND w.creator_id = :user_id
                    
                    UNION ALL
                    
                    SELECT CASE WHEN :user_id = 1 THEN 1 ELSE 0 END as has_permission
                """)
                
                result = conn.execute(sql, {
                    'workspace_code': workspace_code,
                    'user_id': user_id,
                    'permission_type': permission_type
                })
                
                for row in result:
                    if row.has_permission > 0:
                        return True
                
                return False
                
        except Exception as e:
            logger.error(f"检查工作域权限失败: {e}")
            return False

    def _check_workflow_permission(self, workflow_id: int, user_id: int, permission_type: str) -> bool:
        """检查工作流权限"""
        try:
            with self.main_engine.begin() as conn:
                sql = text("""
                    SELECT COUNT(*) as has_permission
                    FROM workflow_permissions p
                    WHERE p.resource_type = 'workflow' AND p.resource_id = :workflow_id
                      AND p.subject_type = 'user' AND p.subject_id = :user_id
                      AND p.permission_type IN (:permission_type, 'manage')
                      AND p.granted = 1
                      AND (p.expires_at IS NULL OR p.expires_at > NOW())
                    
                    UNION ALL
                    
                    SELECT COUNT(*) as has_permission
                    FROM sys_workflow w
                    WHERE w.id = :workflow_id AND w.creator_id = :user_id
                    
                    UNION ALL
                    
                    SELECT CASE WHEN :user_id = 1 THEN 1 ELSE 0 END as has_permission
                """)
                
                result = conn.execute(sql, {
                    'workflow_id': workflow_id,
                    'user_id': user_id,
                    'permission_type': permission_type
                })
                
                for row in result:
                    if row.has_permission > 0:
                        return True
                
                return False
                
        except Exception as e:
            logger.error(f"检查工作流权限失败: {e}")
            return False

    def _grant_workflow_permission(self, conn, workflow_id: int, subject_type: str,
                                  subject_id: int, permission_type: str, granted_by: int):
        """授予工作流权限的内部方法"""
        sql = text("""
            INSERT INTO workflow_permissions (
                resource_type, resource_id, subject_type, subject_id, permission_type, granted, granted_by
            ) VALUES (
                'workflow', :workflow_id, :subject_type, :subject_id, :permission_type, 1, :granted_by
            ) ON DUPLICATE KEY UPDATE
                granted = 1, granted_by = :granted_by, granted_at = NOW(), updated_at = NOW()
        """)
        
        conn.execute(sql, {
            'workflow_id': workflow_id,
            'subject_type': subject_type,
            'subject_id': subject_id,
            'permission_type': permission_type,
            'granted_by': granted_by
        })


# 工厂函数
def get_workflow_service_enhanced() -> WorkflowServiceEnhancement:
    """获取增强版工作流服务实例"""
    base_service = get_workflow_service()
    return WorkflowServiceEnhancement(base_service) 