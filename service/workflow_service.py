#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from tools.database import DatabaseService, get_database_service
from sqlalchemy import text, create_engine
from sqlalchemy.orm import sessionmaker
from config.base_config import Config
import logging
import requests

logger = logging.getLogger(__name__)

class WorkflowService:
    """工作流管理服务"""
    
    def __init__(self):
        """初始化工作流服务"""
        self.config = Config()
        
        # 连接到airflow数据库
        self.airflow_db_url = f'mysql+pymysql://{self.config.DB_USER}:{self.config.DB_PASSWORD}@{self.config.DB_HOST}:{self.config.DB_PORT}/airflow'
        self.airflow_engine = create_engine(self.airflow_db_url)
        self.AirflowSession = sessionmaker(bind=self.airflow_engine)
        
        # 连接到主数据库（dataask）用于获取用户信息
        self.main_db_url = f'mysql+pymysql://{self.config.DB_USER}:{self.config.DB_PASSWORD}@{self.config.DB_HOST}:{self.config.DB_PORT}/{self.config.DB_NAME}'
        self.main_engine = create_engine(self.main_db_url)
        self.MainSession = sessionmaker(bind=self.main_engine)
        
        # Airflow API配置（Airflow 3.0）
        self.airflow_api_url = f"http://localhost:8080/api/v1"
        self.airflow_auth = ('admin', 'admin')  # 默认认证，生产环境需要更改

    def create_workflow(self, workflow_data: Dict) -> Dict:
        """创建新工作流"""
        try:
            with self.airflow_engine.begin() as conn:  # 使用事务
                # 生成唯一的DAG ID
                dag_id = f"workflow_{uuid.uuid4().hex[:8]}"
                
                # 插入工作流定义
                workflow_sql = text("""
                    INSERT INTO sys_workflow (name, description, category, status, dag_id, config, schedule, 
                                            priority, timeout, retry_count, creator_id, created_at, updated_at)
                    VALUES (:name, :description, :category, :status, :dag_id, :config, :schedule, 
                            :priority, :timeout, :retry_count, :creator_id, NOW(), NOW())
                """)
                
                result = conn.execute(workflow_sql, {
                    'name': workflow_data['name'],
                    'description': workflow_data.get('description', ''),
                    'category': workflow_data.get('category', 'general'),
                    'status': 'inactive',
                    'dag_id': dag_id,
                    'config': json.dumps(workflow_data.get('config', {})),
                    'schedule': workflow_data.get('schedule', ''),
                    'priority': workflow_data.get('priority', 0),
                    'timeout': workflow_data.get('timeout', 3600),
                    'retry_count': workflow_data.get('retry_count', 1),
                    'creator_id': workflow_data['creator_id']
                })
                
                workflow_id = result.lastrowid
                
                # 插入工作流步骤
                if 'steps' in workflow_data:
                    for step in workflow_data['steps']:
                        step_sql = text("""
                            INSERT INTO workflow_steps (workflow_id, step_name, step_type, step_order, 
                                                      depends_on, config, timeout, retry_count, `condition`, 
                                                      created_at, updated_at)
                            VALUES (:workflow_id, :step_name, :step_type, :step_order, :depends_on, 
                                    :config, :timeout, :retry_count, :condition, NOW(), NOW())
                        """)
                        
                        conn.execute(step_sql, {
                            'workflow_id': workflow_id,
                            'step_name': step['name'],
                            'step_type': step['type'],
                            'step_order': step.get('order', 1),
                            'depends_on': json.dumps(step.get('depends_on', [])),
                            'config': json.dumps(step.get('config', {})),
                            'timeout': step.get('timeout', 1800),
                            'retry_count': step.get('retry_count', 1),
                            'condition': step.get('condition', '')
                        })
                
                # 生成并部署Airflow DAG
                dag_content = self._generate_airflow_dag(workflow_id, dag_id, workflow_data)
                self._deploy_dag_to_airflow(dag_id, dag_content)
                
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
                'message': '工作流创建失败'
            }

    def get_workflow_list(self, user_id: int = None, category: str = None, 
                         status: str = None, page: int = 1, page_size: int = 20) -> Dict:
        """获取工作流列表"""
        try:
            with self.airflow_engine.connect() as conn:
                # 构建查询条件
                where_conditions = []
                params = {}
                
                if user_id:
                    where_conditions.append("creator_id = :user_id")
                    params['user_id'] = user_id
                
                if category:
                    where_conditions.append("category = :category")
                    params['category'] = category
                
                if status:
                    where_conditions.append("status = :status")
                    params['status'] = status
                
                where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
                
                # 计算总数
                count_sql = text(f"SELECT COUNT(*) as total FROM sys_workflow WHERE {where_clause}")
                total_result = conn.execute(count_sql, params)
                total = total_result.fetchone()[0]
                
                # 分页查询
                offset = (page - 1) * page_size
                params.update({'limit': page_size, 'offset': offset})
                
                list_sql = text(f"""
                    SELECT id, name, description, category, status, dag_id, schedule, priority, 
                           timeout, retry_count, creator_id, created_at, updated_at
                    FROM sys_workflow 
                    WHERE {where_clause}
                    ORDER BY created_at DESC
                    LIMIT :limit OFFSET :offset
                """)
                
                workflows = []
                for row in conn.execute(list_sql, params):
                    workflows.append({
                        'id': row[0],
                        'name': row[1],
                        'description': row[2],
                        'category': row[3],
                        'status': row[4],
                        'dag_id': row[5],
                        'schedule': row[6],
                        'priority': row[7],
                        'timeout': row[8],
                        'retry_count': row[9],
                        'creator_id': row[10],
                        'created_at': row[11].isoformat() if row[11] else None,
                        'updated_at': row[12].isoformat() if row[12] else None
                    })
                
                return {
                    'success': True,
                    'data': {
                        'workflows': workflows,
                        'total': total,
                        'page': page,
                        'page_size': page_size,
                        'total_pages': (total + page_size - 1) // page_size
                    }
                }
                
        except Exception as e:
            logger.error(f"获取工作流列表失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': '获取工作流列表失败'
            }

    def get_workflow_detail(self, workflow_id: int) -> Dict:
        """获取工作流详情"""
        try:
            with self.airflow_engine.connect() as conn:
                # 获取工作流基本信息
                workflow_sql = text("""
                    SELECT id, name, description, category, status, dag_id, config, schedule, 
                           priority, timeout, retry_count, creator_id, created_at, updated_at
                    FROM sys_workflow WHERE id = :workflow_id
                """)
                
                workflow_result = conn.execute(workflow_sql, {'workflow_id': workflow_id})
                workflow_row = workflow_result.fetchone()
                
                if not workflow_row:
                    return {
                        'success': False,
                        'error': 'NOT_FOUND',
                        'message': '工作流不存在'
                    }
                
                # 获取工作流步骤
                steps_sql = text("""
                    SELECT id, step_name, step_type, step_order, depends_on, config, 
                           timeout, retry_count, `condition`, created_at, updated_at
                    FROM workflow_steps 
                    WHERE workflow_id = :workflow_id 
                    ORDER BY step_order
                """)
                
                steps = []
                for step_row in conn.execute(steps_sql, {'workflow_id': workflow_id}):
                    steps.append({
                        'id': step_row[0],
                        'name': step_row[1],
                        'type': step_row[2],
                        'order': step_row[3],
                        'depends_on': json.loads(step_row[4]) if step_row[4] else [],
                        'config': json.loads(step_row[5]) if step_row[5] else {},
                        'timeout': step_row[6],
                        'retry_count': step_row[7],
                        'condition': step_row[8],
                        'created_at': step_row[9].isoformat() if step_row[9] else None,
                        'updated_at': step_row[10].isoformat() if step_row[10] else None
                    })
                
                workflow_detail = {
                    'id': workflow_row[0],
                    'name': workflow_row[1],
                    'description': workflow_row[2],
                    'category': workflow_row[3],
                    'status': workflow_row[4],
                    'dag_id': workflow_row[5],
                    'config': json.loads(workflow_row[6]) if workflow_row[6] else {},
                    'schedule': workflow_row[7],
                    'priority': workflow_row[8],
                    'timeout': workflow_row[9],
                    'retry_count': workflow_row[10],
                    'creator_id': workflow_row[11],
                    'created_at': workflow_row[12].isoformat() if workflow_row[12] else None,
                    'updated_at': workflow_row[13].isoformat() if workflow_row[13] else None,
                    'steps': steps
                }
                
                return {
                    'success': True,
                    'data': workflow_detail
                }
                
        except Exception as e:
            logger.error(f"获取工作流详情失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': '获取工作流详情失败'
            }

    def execute_workflow(self, workflow_id: int, input_data: Dict = None, user_id: int = None) -> Dict:
        """手动执行工作流"""
        try:
            # 获取工作流信息
            workflow_detail = self.get_workflow_detail(workflow_id)
            if not workflow_detail['success']:
                return workflow_detail
            
            workflow = workflow_detail['data']
            dag_id = workflow['dag_id']
            
            # 生成执行ID
            execution_id = f"{dag_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
            
            # 记录执行记录
            with self.airflow_engine.begin() as conn:  # 使用事务
                execution_sql = text("""
                    INSERT INTO workflow_executions (workflow_id, execution_id, status, trigger_type, 
                                                   input_data, executor_id, started_at, created_at, updated_at)
                    VALUES (:workflow_id, :execution_id, 'running', 'manual', :input_data, 
                            :executor_id, NOW(), NOW(), NOW())
                """)
                
                conn.execute(execution_sql, {
                    'workflow_id': workflow_id,
                    'execution_id': execution_id,
                    'input_data': json.dumps(input_data or {}),
                    'executor_id': user_id
                })
            
            # 通过Airflow API触发DAG执行
            trigger_result = self._trigger_dag_run(dag_id, execution_id, input_data)
            
            if trigger_result['success']:
                return {
                    'success': True,
                    'execution_id': execution_id,
                    'dag_run_id': trigger_result.get('dag_run_id'),
                    'message': '工作流执行已启动'
                }
            else:
                # 更新执行状态为失败
                with self.airflow_engine.begin() as conn:  # 使用事务
                    update_sql = text("""
                        UPDATE workflow_executions 
                        SET status = 'failed', error_message = :error_message, 
                            finished_at = NOW(), updated_at = NOW()
                        WHERE execution_id = :execution_id
                    """)
                    conn.execute(update_sql, {
                        'execution_id': execution_id,
                        'error_message': trigger_result.get('error', '启动失败')
                    })
                
                return trigger_result
                
        except Exception as e:
            logger.error(f"执行工作流失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': '工作流执行失败'
            }

    def get_execution_history(self, workflow_id: int = None, page: int = 1, page_size: int = 20) -> Dict:
        """获取工作流执行历史"""
        try:
            with self.airflow_engine.connect() as conn:
                # 构建查询条件
                where_clause = "WHERE w.id = we.workflow_id"
                params = {'limit': page_size, 'offset': (page - 1) * page_size}
                
                if workflow_id:
                    where_clause += " AND we.workflow_id = :workflow_id"
                    params['workflow_id'] = workflow_id
                
                # 计算总数
                count_sql = text(f"""
                    SELECT COUNT(*) as total 
                    FROM workflow_executions we 
                    JOIN sys_workflow w ON w.id = we.workflow_id 
                    {where_clause}
                """)
                total_result = conn.execute(count_sql, params)
                total = total_result.fetchone()[0]
                
                # 分页查询
                list_sql = text(f"""
                    SELECT we.id, we.workflow_id, w.name as workflow_name, we.execution_id, 
                           we.status, we.trigger_type, we.started_at, we.finished_at, 
                           we.duration, we.executor_id, we.error_message, we.created_at
                    FROM workflow_executions we
                    JOIN sys_workflow w ON w.id = we.workflow_id
                    {where_clause}
                    ORDER BY we.created_at DESC
                    LIMIT :limit OFFSET :offset
                """)
                
                executions = []
                for row in conn.execute(list_sql, params):
                    executions.append({
                        'id': row[0],
                        'workflow_id': row[1],
                        'workflow_name': row[2],
                        'execution_id': row[3],
                        'status': row[4],
                        'trigger_type': row[5],
                        'started_at': row[6].isoformat() if row[6] else None,
                        'finished_at': row[7].isoformat() if row[7] else None,
                        'duration': row[8],
                        'executor_id': row[9],
                        'error_message': row[10],
                        'created_at': row[11].isoformat() if row[11] else None
                    })
                
                return {
                    'success': True,
                    'data': {
                        'executions': executions,
                        'total': total,
                        'page': page,
                        'page_size': page_size,
                        'total_pages': (total + page_size - 1) // page_size
                    }
                }
                
        except Exception as e:
            logger.error(f"获取执行历史失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': '获取执行历史失败'
            }

    def get_workflow_templates(self, category: str = None) -> Dict:
        """获取工作流模板列表"""
        try:
            with self.airflow_engine.connect() as conn:
                where_clause = "WHERE is_public = 1"
                params = {}
                
                if category:
                    where_clause += " AND category = :category"
                    params['category'] = category
                
                templates_sql = text(f"""
                    SELECT id, name, description, category, icon, template_config, usage_count, creator_id
                    FROM workflow_templates 
                    {where_clause}
                    ORDER BY usage_count DESC, created_at DESC
                """)
                
                templates = []
                for row in conn.execute(templates_sql, params):
                    templates.append({
                        'id': row[0],
                        'name': row[1],
                        'description': row[2],
                        'category': row[3],
                        'icon': row[4],
                        'template_config': json.loads(row[5]) if row[5] else {},
                        'usage_count': row[6],
                        'creator_id': row[7]
                    })
                
                return {
                    'success': True,
                    'data': templates
                }
                
        except Exception as e:
            logger.error(f"获取工作流模板失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': '获取工作流模板失败'
            }

    def _generate_airflow_dag(self, workflow_id: int, dag_id: str, workflow_data: Dict) -> str:
        """生成Airflow DAG代码"""
        dag_template = f'''
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.providers.mysql.operators.mysql import MySqlOperator
from airflow.providers.http.operators.http import SimpleHttpOperator

# DAG默认参数
default_args = {{
    'owner': 'dataask',
    'depends_on_past': False,
    'start_date': datetime.now(),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': {workflow_data.get('retry_count', 1)},
    'retry_delay': timedelta(minutes=5)
}}

# 定义DAG
dag = DAG(
    '{dag_id}',
    default_args=default_args,
    description='{workflow_data.get('description', '')}',
    schedule_interval='{workflow_data.get('schedule', None)}',
    catchup=False,
    tags=['{workflow_data.get('category', 'general')}']
)

def update_workflow_status(workflow_id, execution_id, status, **context):
    """更新工作流执行状态"""
    import pymysql
    import json
    from datetime import datetime
    
    try:
        connection = pymysql.connect(
            host='localhost',
            user='root',
            password='llmstudy',
            database='airflow',
            charset='utf8mb4'
        )
        
        with connection.cursor() as cursor:
            if status == 'success':
                sql = """
                    UPDATE workflow_executions 
                    SET status = %s, finished_at = %s, duration = TIMESTAMPDIFF(SECOND, started_at, %s), updated_at = %s
                    WHERE execution_id = %s
                """
                now = datetime.now()
                cursor.execute(sql, (status, now, now, now, execution_id))
            elif status == 'failed':
                error_msg = context.get('exception', '执行失败')
                sql = """
                    UPDATE workflow_executions 
                    SET status = %s, error_message = %s, finished_at = %s, updated_at = %s
                    WHERE execution_id = %s
                """
                now = datetime.now()
                cursor.execute(sql, (status, str(error_msg), now, now, execution_id))
            
            connection.commit()
        connection.close()
        
    except Exception as e:
        print(f"更新状态失败: {{e}}")

'''

        # 添加任务定义
        if 'steps' in workflow_data:
            tasks = []
            for i, step in enumerate(workflow_data['steps']):
                task_id = f"step_{i+1}_{step['name'].replace(' ', '_')}"
                
                if step['type'] == 'python':
                    task_code = f'''
# Python任务: {step['name']}
def {task_id}_function(**context):
    """执行步骤: {step['name']}"""
    import sys
    import os
    sys.path.append('/Users/xinz/Dev/DataAsk')
    
    # 从配置中获取脚本路径或代码
    config = {json.dumps(step.get('config', {}), ensure_ascii=False)}
    
    if 'script' in config:
        # 执行脚本文件
        script_path = config['script']
        if os.path.exists(script_path):
            exec(open(script_path).read())
        else:
            print(f"脚本文件不存在: {{script_path}}")
    elif 'code' in config:
        # 执行代码片段
        exec(config['code'])
    else:
        print("步骤配置中未找到可执行的脚本或代码")
    
    return "步骤执行完成"

{task_id} = PythonOperator(
    task_id='{task_id}',
    python_callable={task_id}_function,
    dag=dag
)
'''
                
                elif step['type'] == 'bash':
                    command = step.get('config', {}).get('command', 'echo "Hello World"')
                    task_code = f'''
# Bash任务: {step['name']}
{task_id} = BashOperator(
    task_id='{task_id}',
    bash_command='{command}',
    dag=dag
)
'''
                
                elif step['type'] == 'sql':
                    query = step.get('config', {}).get('query', 'SELECT 1')
                    task_code = f'''
# SQL任务: {step['name']}
{task_id} = MySqlOperator(
    task_id='{task_id}',
    mysql_conn_id='mysql_default',
    sql="""{query}""",
    dag=dag
)
'''
                
                else:
                    # 默认Python任务
                    task_code = f'''
# 默认任务: {step['name']}
def {task_id}_function(**context):
    print("执行步骤: {step['name']}")
    return "步骤执行完成"

{task_id} = PythonOperator(
    task_id='{task_id}',
    python_callable={task_id}_function,
    dag=dag
)
'''
                
                dag_template += task_code
                tasks.append(task_id)
            
            # 添加成功回调任务
            dag_template += f'''
# 成功回调任务
success_callback = PythonOperator(
    task_id='success_callback',
    python_callable=update_workflow_status,
    op_kwargs={{'workflow_id': {workflow_id}, 'execution_id': '{{{{ dag_run.run_id }}}}', 'status': 'success'}},
    dag=dag
)

# 失败回调任务
def failure_callback_function(**context):
    update_workflow_status({workflow_id}, context['dag_run'].run_id, 'failed', **context)

failure_callback = PythonOperator(
    task_id='failure_callback',
    python_callable=failure_callback_function,
    trigger_rule='one_failed',
    dag=dag
)

# 设置任务依赖关系
'''
            
            # 设置任务依赖关系
            if len(tasks) > 1:
                for i in range(len(tasks) - 1):
                    dag_template += f"{tasks[i]} >> {tasks[i + 1]}\n"
            
            if tasks:
                dag_template += f"{tasks[-1]} >> success_callback\n"
                dag_template += f"failure_callback\n"
        
        return dag_template

    def _deploy_dag_to_airflow(self, dag_id: str, dag_content: str) -> bool:
        """部署DAG到Airflow"""
        try:
            # 在生产环境中，这里应该将DAG文件写入Airflow的dags目录
            # 或者通过Airflow API进行部署
            
            # 简化版本：暂时跳过实际部署
            logger.info(f"DAG {dag_id} 生成完成，待部署到Airflow")
            return True
            
        except Exception as e:
            logger.error(f"部署DAG失败: {e}")
            return False

    def _trigger_dag_run(self, dag_id: str, run_id: str, input_data: Dict = None) -> Dict:
        """通过Airflow API触发DAG执行"""
        try:
            url = f"{self.airflow_api_url}/dags/{dag_id}/dagRuns"
            
            payload = {
                "dag_run_id": run_id,
                "conf": input_data or {}
            }
            
            response = requests.post(
                url,
                json=payload,
                auth=self.airflow_auth,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'dag_run_id': result.get('dag_run_id'),
                    'message': 'DAG执行已触发'
                }
            else:
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}",
                    'message': f"触发DAG失败: {response.text}"
                }
                
        except requests.RequestException as e:
            logger.error(f"触发DAG失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': '无法连接到Airflow API'
            }

    def get_dag_status(self, dag_id: str) -> Dict:
        """获取DAG状态"""
        try:
            url = f"{self.airflow_api_url}/dags/{dag_id}"
            
            response = requests.get(
                url,
                auth=self.airflow_auth,
                timeout=30
            )
            
            if response.status_code == 200:
                dag_info = response.json()
                return {
                    'success': True,
                    'data': dag_info
                }
            else:
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}",
                    'message': f"获取DAG状态失败: {response.text}"
                }
                
        except requests.RequestException as e:
            logger.error(f"获取DAG状态失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': '无法连接到Airflow API'
            }

def get_workflow_service():
    """获取工作流服务实例"""
    return WorkflowService() 