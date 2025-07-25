#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
统一工作流服务模块
整合了工作域管理、工作流管理、节点管理、权限管理等完整功能
"""

import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from tools.database import DatabaseService, get_database_service
from sqlalchemy import text, create_engine
from sqlalchemy.orm import sessionmaker
from config.base_config import Config
import logging
import requests

logger = logging.getLogger(__name__)

class WorkflowService:
    """统一工作流管理服务 - 支持多工作域和权限控制"""
    
    def __init__(self):
        """初始化工作流服务"""
        self.config = Config()
        
        # 连接到airflow数据库
        self.airflow_db_url = f'mysql+pymysql://{self.config.DB_USER}:{self.config.DB_PASSWORD}@{self.config.DB_HOST}:{self.config.DB_PORT}/airflow'
        self.airflow_engine = create_engine(self.airflow_db_url)
        self.AirflowSession = sessionmaker(bind=self.airflow_engine)
        
        # 连接到主数据库（dataask）
        self.main_db_url = f'mysql+pymysql://{self.config.DB_USER}:{self.config.DB_PASSWORD}@{self.config.DB_HOST}:{self.config.DB_PORT}/{self.config.DB_NAME}'
        self.main_engine = create_engine(self.main_db_url)
        self.MainSession = sessionmaker(bind=self.main_engine)
        
        # Airflow API配置
        self.airflow_api_url = f"http://localhost:8080/api/v1"
        self.airflow_auth = ('admin', 'admin')

    # ================================
    # 工作域管理
    # ================================
    
    def get_workspaces(self, user_id: int) -> Dict:
        """获取用户可访问的工作域列表"""
        try:
            with self.main_engine.begin() as conn:
                # 查询用户有权限的工作域
                sql = text("""
                    SELECT DISTINCT w.*, 
                           COUNT(c.id) as category_count,
                           COUNT(wf.id) as workflow_count
                    FROM workflow_workspaces w
                    LEFT JOIN workflow_categories c ON c.workspace_id = w.id AND c.status = 'active'
                    LEFT JOIN enhanced_workflows wf ON wf.workspace_id = w.id AND wf.status IN ('active', 'inactive')
                    LEFT JOIN workflow_permissions p ON p.resource_type = 'workspace' 
                                                     AND p.resource_id = w.id 
                                                     AND p.subject_type = 'user' 
                                                     AND p.subject_id = :user_id
                                                     AND p.permission_type = 'view'
                                                     AND p.granted = 1
                    WHERE w.status = 'active' 
                      AND (p.id IS NOT NULL OR w.creator_id = :user_id OR :user_id = 1)
                    GROUP BY w.id
                    ORDER BY w.order_num, w.name
                """)
                
                result = conn.execute(sql, {'user_id': user_id})
                workspaces = []
                
                for row in result:
                    workspaces.append({
                        'id': row.id,
                        'name': row.name,
                        'code': row.code,
                        'description': row.description,
                        'icon': row.icon,
                        'color': row.color,
                        'status': row.status,
                        'order_num': row.order_num,
                        'category_count': row.category_count or 0,
                        'workflow_count': row.workflow_count or 0,
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

    def create_workspace(self, workspace_data: Dict, user_id: int) -> Dict:
        """创建新工作域"""
        try:
            with self.main_engine.begin() as conn:
                # 检查代码是否重复
                check_sql = text("SELECT id FROM workflow_workspaces WHERE code = :code")
                existing = conn.execute(check_sql, {'code': workspace_data['code']}).fetchone()
                
                if existing:
                    return {
                        'success': False,
                        'message': f"工作域代码 '{workspace_data['code']}' 已存在"
                    }
                
                # 插入工作域
                insert_sql = text("""
                    INSERT INTO workflow_workspaces (name, code, description, icon, color, order_num, creator_id)
                    VALUES (:name, :code, :description, :icon, :color, :order_num, :creator_id)
                """)
                
                result = conn.execute(insert_sql, {
                    'name': workspace_data['name'],
                    'code': workspace_data['code'],
                    'description': workspace_data.get('description', ''),
                    'icon': workspace_data.get('icon', 'folder'),
                    'color': workspace_data.get('color', '#1890ff'),
                    'order_num': workspace_data.get('order_num', 0),
                    'creator_id': user_id
                })
                
                workspace_id = result.lastrowid
                
                # 自动为创建者分配管理权限
                self._grant_workspace_permission(conn, workspace_id, 'user', user_id, 'manage', user_id)
                
                return {
                    'success': True,
                    'workspace_id': workspace_id,
                    'message': '工作域创建成功'
                }
                
        except Exception as e:
            logger.error(f"创建工作域失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': '创建工作域失败'
            }

    # ================================
    # 工作流管理
    # ================================
    
    def get_workflows(self, workspace_id: int = None, category_id: int = None, 
                     user_id: int = None, filters: Dict = None) -> Dict:
        """获取工作流列表"""
        try:
            with self.main_engine.begin() as conn:
                # 构建查询条件
                conditions = ["wf.status != 'archived'"]
                params = {}
                
                if workspace_id:
                    conditions.append("wf.workspace_id = :workspace_id")
                    params['workspace_id'] = workspace_id
                
                if category_id:
                    conditions.append("wf.category_id = :category_id")
                    params['category_id'] = category_id
                
                if user_id:
                    params['user_id'] = user_id
                
                # 添加过滤条件
                if filters:
                    if filters.get('status'):
                        conditions.append("wf.status = :status")
                        params['status'] = filters['status']
                    
                    if filters.get('type'):
                        conditions.append("wf.type = :type")
                        params['type'] = filters['type']
                    
                    if filters.get('name'):
                        conditions.append("wf.name LIKE :name")
                        params['name'] = f"%{filters['name']}%"
                
                where_clause = " AND ".join(conditions)
                
                sql = text(f"""
                    SELECT wf.*, 
                           w.name as workspace_name, w.code as workspace_code,
                           c.name as category_name, c.code as category_code,
                           u1.username as creator_name,
                           u2.username as updater_name,
                           COUNT(n.id) as node_count,
                           COUNT(DISTINCT i.id) as instance_count,
                           COALESCE(AVG(CASE WHEN i.status = 'completed' THEN 1 ELSE 0 END), 0) * 100 as success_rate
                    FROM enhanced_workflows wf
                    LEFT JOIN workflow_workspaces w ON w.id = wf.workspace_id
                    LEFT JOIN workflow_categories c ON c.id = wf.category_id
                    LEFT JOIN users u1 ON u1.id = wf.creator_id
                    LEFT JOIN users u2 ON u2.id = wf.updater_id
                    LEFT JOIN workflow_nodes n ON n.workflow_id = wf.id AND n.status = 'active'
                    LEFT JOIN workflow_instances i ON i.workflow_id = wf.id
                    WHERE {where_clause}
                    GROUP BY wf.id
                    ORDER BY wf.updated_at DESC
                """)
                
                result = conn.execute(sql, params)
                workflows = []
                
                for row in result:
                    workflows.append({
                        'id': row.id,
                        'workspace_id': row.workspace_id,
                        'workspace_name': row.workspace_name,
                        'workspace_code': row.workspace_code,
                        'category_id': row.category_id,
                        'category_name': row.category_name,
                        'category_code': row.category_code,
                        'name': row.name,
                        'code': row.code,
                        'description': row.description,
                        'version': row.version,
                        'type': row.type,
                        'trigger_type': row.trigger_type,
                        'status': row.status,
                        'priority': row.priority,
                        'dag_id': row.dag_id,
                        'schedule_expression': row.schedule_expression,
                        'timeout_minutes': row.timeout_minutes,
                        'retry_count': row.retry_count,
                        'notification_enabled': bool(row.notification_enabled),
                        'node_count': row.node_count or 0,
                        'instance_count': row.instance_count or 0,
                        'success_rate': float(row.success_rate or 0),
                        'creator_name': row.creator_name,
                        'updater_name': row.updater_name,
                        'published_at': row.published_at.isoformat() if row.published_at else None,
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

    def create_workflow(self, workflow_data: Dict, user_id: int) -> Dict:
        """创建新工作流"""
        try:
            # 检查工作域权限
            if not self._check_workspace_permission(workflow_data['workspace_id'], user_id, 'edit'):
                return {
                    'success': False,
                    'message': '您没有权限在此工作域创建工作流'
                }
            
            with self.main_engine.begin() as conn:
                # 检查代码是否重复
                check_sql = text("""
                    SELECT id FROM enhanced_workflows 
                    WHERE code = :code AND workspace_id = :workspace_id
                """)
                existing = conn.execute(check_sql, {
                    'code': workflow_data['code'],
                    'workspace_id': workflow_data['workspace_id']
                }).fetchone()
                
                if existing:
                    return {
                        'success': False,
                        'message': f"工作流代码 '{workflow_data['code']}' 在此工作域中已存在"
                    }
                
                # 生成唯一的DAG ID
                dag_id = f"enhanced_workflow_{workflow_data['workspace_id']}_{workflow_data['code']}_{uuid.uuid4().hex[:8]}"
                
                # 插入工作流定义
                insert_sql = text("""
                    INSERT INTO enhanced_workflows (
                        workspace_id, category_id, name, code, description, version, type, 
                        trigger_type, status, priority, dag_id, config, variables, 
                        schedule_expression, timeout_minutes, retry_count, retry_delay_minutes,
                        auto_rollback, notification_enabled, notification_config, creator_id
                    ) VALUES (
                        :workspace_id, :category_id, :name, :code, :description, :version, :type,
                        :trigger_type, :status, :priority, :dag_id, :config, :variables,
                        :schedule_expression, :timeout_minutes, :retry_count, :retry_delay_minutes,
                        :auto_rollback, :notification_enabled, :notification_config, :creator_id
                    )
                """)
                
                result = conn.execute(insert_sql, {
                    'workspace_id': workflow_data['workspace_id'],
                    'category_id': workflow_data['category_id'],
                    'name': workflow_data['name'],
                    'code': workflow_data['code'],
                    'description': workflow_data.get('description', ''),
                    'version': workflow_data.get('version', '1.0.0'),
                    'type': workflow_data.get('type', 'sequential'),
                    'trigger_type': workflow_data.get('trigger_type', 'manual'),
                    'status': 'draft',
                    'priority': workflow_data.get('priority', 'normal'),
                    'dag_id': dag_id,
                    'config': json.dumps(workflow_data.get('config', {})),
                    'variables': json.dumps(workflow_data.get('variables', {})),
                    'schedule_expression': workflow_data.get('schedule_expression'),
                    'timeout_minutes': workflow_data.get('timeout_minutes', 60),
                    'retry_count': workflow_data.get('retry_count', 1),
                    'retry_delay_minutes': workflow_data.get('retry_delay_minutes', 5),
                    'auto_rollback': workflow_data.get('auto_rollback', 0),
                    'notification_enabled': workflow_data.get('notification_enabled', 1),
                    'notification_config': json.dumps(workflow_data.get('notification_config', {})),
                    'creator_id': user_id
                })
                
                workflow_id = result.lastrowid
                
                # 自动为创建者分配管理权限
                self._grant_workflow_permission(conn, workflow_id, 'user', user_id, 'manage', user_id)
                
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

    def activate_workflow(self, workflow_id: int) -> Dict:
        """激活工作流"""
        try:
            with self.main_engine.begin() as conn:
                update_sql = text("""
                    UPDATE enhanced_workflows 
                    SET status = 'active', updated_at = NOW()
                    WHERE id = :workflow_id
                """)
                
                conn.execute(update_sql, {'workflow_id': workflow_id})
                
                return {
                    'success': True,
                    'message': '工作流激活成功'
                }
                
        except Exception as e:
            logger.error(f"激活工作流失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': '激活工作流失败'
            }

    def deactivate_workflow(self, workflow_id: int) -> Dict:
        """停用工作流"""
        try:
            with self.main_engine.begin() as conn:
                update_sql = text("""
                    UPDATE enhanced_workflows 
                    SET status = 'inactive', updated_at = NOW()
                    WHERE id = :workflow_id
                """)
                
                conn.execute(update_sql, {'workflow_id': workflow_id})
                
                return {
                    'success': True,
                    'message': '工作流停用成功'
                }
                
        except Exception as e:
            logger.error(f"停用工作流失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': '停用工作流失败'
            }

    def delete_workflow(self, workflow_id: int) -> Dict:
        """删除工作流"""
        try:
            with self.main_engine.begin() as conn:
                update_sql = text("""
                    UPDATE enhanced_workflows 
                    SET status = 'archived', updated_at = NOW()
                    WHERE id = :workflow_id
                """)
                
                conn.execute(update_sql, {'workflow_id': workflow_id})
                
                return {
                    'success': True,
                    'message': '工作流删除成功'
                }
                
        except Exception as e:
            logger.error(f"删除工作流失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': '删除工作流失败'
            }

    def execute_workflow(self, workflow_id: int) -> Dict:
        """执行工作流"""
        try:
            with self.main_engine.begin() as conn:
                # 检查工作流状态
                check_sql = text("SELECT status, dag_id FROM enhanced_workflows WHERE id = :workflow_id")
                workflow = conn.execute(check_sql, {'workflow_id': workflow_id}).fetchone()
                
                if not workflow:
                    return {
                        'success': False,
                        'message': '工作流不存在'
                    }
                
                if workflow.status != 'active':
                    return {
                        'success': False,
                        'message': '只能执行已激活的工作流'
                    }
                
                # 创建执行实例
                instance_sql = text("""
                    INSERT INTO workflow_instances (workflow_id, status, started_at)
                    VALUES (:workflow_id, 'running', NOW())
                """)
                
                result = conn.execute(instance_sql, {'workflow_id': workflow_id})
                instance_id = result.lastrowid
                
                return {
                    'success': True,
                    'instance_id': instance_id,
                    'message': '工作流执行启动成功'
                }
                
        except Exception as e:
            logger.error(f"执行工作流失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': '执行工作流失败'
            }

    # ================================
    # 节点管理
    # ================================
    
    def get_workflow_nodes(self, workflow_id: int, user_id: int) -> Dict:
        """获取工作流的节点列表"""
        try:
            # 检查权限
            if not self._check_workflow_permission(workflow_id, user_id, 'view'):
                return {
                    'success': False,
                    'message': '您没有权限查看此工作流'
                }
            
            with self.main_engine.begin() as conn:
                # 获取节点信息
                nodes_sql = text("""
                    SELECT n.*, 
                           COUNT(DISTINCT conn_from.id) as outgoing_connections,
                           COUNT(DISTINCT conn_to.id) as incoming_connections
                    FROM workflow_nodes n
                    LEFT JOIN workflow_node_connections conn_from ON conn_from.from_node_id = n.id
                    LEFT JOIN workflow_node_connections conn_to ON conn_to.to_node_id = n.id
                    WHERE n.workflow_id = :workflow_id AND n.status = 'active'
                    GROUP BY n.id
                    ORDER BY n.step_order, n.name
                """)
                
                result = conn.execute(nodes_sql, {'workflow_id': workflow_id})
                nodes = []
                
                for row in result:
                    node_config = json.loads(row.config) if row.config else {}
                    
                    nodes.append({
                        'id': row.id,
                        'workflow_id': row.workflow_id,
                        'name': row.name,
                        'code': row.code,
                        'description': row.description,
                        'type': row.type,
                        'subtype': row.subtype,
                        'step_order': row.step_order,
                        'x_position': float(row.x_position) if row.x_position else 0,
                        'y_position': float(row.y_position) if row.y_position else 0,
                        'icon': row.icon,
                        'color': row.color,
                        'config': node_config,
                        'timeout_minutes': row.timeout_minutes,
                        'retry_count': row.retry_count,
                        'retry_delay_minutes': row.retry_delay_minutes,
                        'skip_on_failure': bool(row.skip_on_failure),
                        'rollback_enabled': bool(row.rollback_enabled),
                        'outgoing_connections': row.outgoing_connections or 0,
                        'incoming_connections': row.incoming_connections or 0,
                        'created_at': row.created_at.isoformat() if row.created_at else None,
                        'updated_at': row.updated_at.isoformat() if row.updated_at else None
                    })
                
                return {
                    'success': True,
                    'data': {
                        'nodes': nodes
                    }
                }
                
        except Exception as e:
            logger.error(f"获取工作流节点失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': '获取工作流节点失败'
            }

    def create_workflow_node(self, workflow_id: int, node_data: Dict, user_id: int) -> Dict:
        """创建工作流节点"""
        try:
            # 检查权限
            if not self._check_workflow_permission(workflow_id, user_id, 'edit'):
                return {
                    'success': False,
                    'message': '您没有权限编辑此工作流'
                }
            
            with self.main_engine.begin() as conn:
                node_id = self._create_workflow_node(conn, workflow_id, node_data, user_id)
                
                return {
                    'success': True,
                    'node_id': node_id,
                    'message': '节点创建成功'
                }
                
        except Exception as e:
            logger.error(f"创建工作流节点失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': '创建工作流节点失败'
            }

    # ================================
    # 权限管理
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

    def grant_permission(self, resource_type: str, resource_id: int, 
                        subject_type: str, subject_id: int, permission_type: str,
                        granted_by: int, conditions: Dict = None, expires_at: datetime = None) -> Dict:
        """授予权限"""
        try:
            with self.main_engine.begin() as conn:
                # 检查是否已存在相同权限配置
                check_sql = text("""
                    SELECT id FROM workflow_permissions 
                    WHERE resource_type = :resource_type AND resource_id = :resource_id
                      AND subject_type = :subject_type AND subject_id = :subject_id
                      AND permission_type = :permission_type
                """)
                
                existing = conn.execute(check_sql, {
                    'resource_type': resource_type,
                    'resource_id': resource_id,
                    'subject_type': subject_type,
                    'subject_id': subject_id,
                    'permission_type': permission_type
                }).fetchone()
                
                if existing:
                    # 更新现有权限
                    update_sql = text("""
                        UPDATE workflow_permissions 
                        SET granted = 1, conditions = :conditions, granted_by = :granted_by,
                            granted_at = NOW(), expires_at = :expires_at, updated_at = NOW()
                        WHERE id = :id
                    """)
                    
                    conn.execute(update_sql, {
                        'id': existing.id,
                        'conditions': json.dumps(conditions) if conditions else None,
                        'granted_by': granted_by,
                        'expires_at': expires_at
                    })
                    
                    permission_id = existing.id
                else:
                    # 创建新权限
                    insert_sql = text("""
                        INSERT INTO workflow_permissions (
                            resource_type, resource_id, subject_type, subject_id, 
                            permission_type, granted, conditions, granted_by, expires_at
                        ) VALUES (
                            :resource_type, :resource_id, :subject_type, :subject_id,
                            :permission_type, 1, :conditions, :granted_by, :expires_at
                        )
                    """)
                    
                    result = conn.execute(insert_sql, {
                        'resource_type': resource_type,
                        'resource_id': resource_id,
                        'subject_type': subject_type,
                        'subject_id': subject_id,
                        'permission_type': permission_type,
                        'conditions': json.dumps(conditions) if conditions else None,
                        'granted_by': granted_by,
                        'expires_at': expires_at
                    })
                    
                    permission_id = result.lastrowid
                
                return {
                    'success': True,
                    'permission_id': permission_id,
                    'message': '权限授予成功'
                }
                
        except Exception as e:
            logger.error(f"授予权限失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': '授予权限失败'
            }

    # ================================
    # 辅助方法
    # ================================
    
    def _create_workflow_node(self, conn, workflow_id: int, node_data: Dict, user_id: int) -> int:
        """创建工作流节点的内部方法"""
        insert_sql = text("""
            INSERT INTO workflow_nodes (
                workflow_id, name, code, description, type, subtype, step_order,
                x_position, y_position, icon, color, config, timeout_minutes, 
                retry_count, retry_delay_minutes, skip_on_failure, rollback_enabled, 
                rollback_config, conditions, creator_id
            ) VALUES (
                :workflow_id, :name, :code, :description, :type, :subtype, :step_order,
                :x_position, :y_position, :icon, :color, :config, :timeout_minutes,
                :retry_count, :retry_delay_minutes, :skip_on_failure, :rollback_enabled,
                :rollback_config, :conditions, :creator_id
            )
        """)
        
        result = conn.execute(insert_sql, {
            'workflow_id': workflow_id,
            'name': node_data['name'],
            'code': node_data['code'],
            'description': node_data.get('description', ''),
            'type': node_data['type'],
            'subtype': node_data.get('subtype'),
            'step_order': node_data.get('step_order', 1),
            'x_position': node_data.get('x_position', 0),
            'y_position': node_data.get('y_position', 0),
            'icon': node_data.get('icon', 'play-circle'),
            'color': node_data.get('color', '#1890ff'),
            'config': json.dumps(node_data.get('config', {})),
            'timeout_minutes': node_data.get('timeout_minutes', 30),
            'retry_count': node_data.get('retry_count', 1),
            'retry_delay_minutes': node_data.get('retry_delay_minutes', 2),
            'skip_on_failure': node_data.get('skip_on_failure', 0),
            'rollback_enabled': node_data.get('rollback_enabled', 0),
            'rollback_config': json.dumps(node_data.get('rollback_config')) if node_data.get('rollback_config') else None,
            'conditions': json.dumps(node_data.get('conditions')) if node_data.get('conditions') else None,
            'creator_id': user_id
        })
        
        return result.lastrowid

    def _check_workspace_permission(self, workspace_id: int, user_id: int, permission_type: str) -> bool:
        """检查工作域权限"""
        try:
            with self.main_engine.begin() as conn:
                sql = text("""
                    SELECT COUNT(*) as has_permission
                    FROM workflow_permissions p
                    WHERE p.resource_type = 'workspace' AND p.resource_id = :workspace_id
                      AND p.subject_type = 'user' AND p.subject_id = :user_id
                      AND p.permission_type IN (:permission_type, 'manage')
                      AND p.granted = 1
                      AND (p.expires_at IS NULL OR p.expires_at > NOW())
                    
                    UNION ALL
                    
                    SELECT COUNT(*) as has_permission
                    FROM workflow_workspaces w
                    WHERE w.id = :workspace_id AND w.creator_id = :user_id
                    
                    UNION ALL
                    
                    SELECT CASE WHEN :user_id = 1 THEN 1 ELSE 0 END as has_permission
                """)
                
                result = conn.execute(sql, {
                    'workspace_id': workspace_id,
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
                    FROM enhanced_workflows wf
                    WHERE wf.id = :workflow_id AND wf.creator_id = :user_id
                    
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

    def _grant_workspace_permission(self, conn, workspace_id: int, subject_type: str, 
                                   subject_id: int, permission_type: str, granted_by: int):
        """授予工作域权限的内部方法"""
        sql = text("""
            INSERT INTO workflow_permissions (
                resource_type, resource_id, subject_type, subject_id, permission_type, granted, granted_by
            ) VALUES (
                'workspace', :workspace_id, :subject_type, :subject_id, :permission_type, 1, :granted_by
            ) ON DUPLICATE KEY UPDATE
                granted = 1, granted_by = :granted_by, granted_at = NOW(), updated_at = NOW()
        """)
        
        conn.execute(sql, {
            'workspace_id': workspace_id,
            'subject_type': subject_type,
            'subject_id': subject_id,
            'permission_type': permission_type,
            'granted_by': granted_by
        })

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


# 服务实例化函数
def get_workflow_service() -> WorkflowService:
    """获取工作流服务实例"""
    return WorkflowService()

# 保持向后兼容性的别名
def get_enhanced_workflow_service() -> WorkflowService:
    """获取增强版工作流服务实例（向后兼容）"""
    return WorkflowService() 