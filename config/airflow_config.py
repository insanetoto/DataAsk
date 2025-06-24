#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from typing import Dict, Any

class AirflowConfig:
    """Airflow配置管理"""
    
    # Airflow核心配置
    AIRFLOW_HOME = os.environ.get('AIRFLOW_HOME', '/opt/airflow')
    AIRFLOW_API_URL = "http://localhost:8080/api/v1"
    AIRFLOW_WEB_PORT = 8080
    AIRFLOW_USERNAME = "admin"
    AIRFLOW_PASSWORD = "admin"
    
    # 数据库配置
    AIRFLOW_DB_URL = "mysql+pymysql://dataask:dataask123@localhost:3306/airflow"
    
    # 执行器配置
    EXECUTOR = "LocalExecutor"  # 可选: LocalExecutor, CeleryExecutor, SequentialExecutor
    
    # Celery配置（如果使用CeleryExecutor）
    CELERY_BROKER_URL = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND = "db+mysql+pymysql://dataask:dataask123@localhost:3306/airflow"
    
    # 调度器配置
    SCHEDULER_CATCHUP_BY_DEFAULT = False
    SCHEDULER_DAG_DIR_LIST_INTERVAL = 300
    SCHEDULER_HEARTBEAT_SEC = 5
    
    # Web服务器配置
    WEB_SERVER_HOST = "0.0.0.0"
    WEB_SERVER_PORT = 8080
    WEB_SERVER_WORKER_TIMEOUT = 120
    
    # 安全配置
    AUTHENTICATE = True
    AUTH_BACKEND = "airflow.contrib.auth.backends.password_auth"
    
    # 日志配置
    BASE_LOG_FOLDER = f"{AIRFLOW_HOME}/logs"
    REMOTE_LOGGING = False
    
    # 邮件配置
    SMTP_HOST = "smtp.gmail.com"
    SMTP_PORT = 587
    SMTP_USER = ""
    SMTP_PASSWORD = ""
    SMTP_MAIL_FROM = "noreply@dataask.com"
    
    @classmethod
    def get_airflow_cfg(cls) -> str:
        """生成airflow.cfg配置内容"""
        return f"""
[core]
dags_folder = {cls.AIRFLOW_HOME}/dags
base_log_folder = {cls.BASE_LOG_FOLDER}
remote_logging = {str(cls.REMOTE_LOGGING).lower()}
executor = {cls.EXECUTOR}
sql_alchemy_conn = {cls.AIRFLOW_DB_URL}
load_examples = False
max_active_runs_per_dag = 16
dags_are_paused_at_creation = True
non_pooled_task_slot_count = 128
catchup_by_default = {str(cls.SCHEDULER_CATCHUP_BY_DEFAULT).lower()}

[scheduler]
dag_dir_list_interval = {cls.SCHEDULER_DAG_DIR_LIST_INTERVAL}
child_process_log_directory = {cls.BASE_LOG_FOLDER}/scheduler
catchup_by_default = {str(cls.SCHEDULER_CATCHUP_BY_DEFAULT).lower()}
scheduler_heartbeat_sec = {cls.SCHEDULER_HEARTBEAT_SEC}

[webserver]
base_url = http://localhost:{cls.WEB_SERVER_PORT}
web_server_host = {cls.WEB_SERVER_HOST}
web_server_port = {cls.WEB_SERVER_PORT}
worker_timeout = {cls.WEB_SERVER_WORKER_TIMEOUT}
authenticate = {str(cls.AUTHENTICATE).lower()}
auth_backend = {cls.AUTH_BACKEND}

[celery]
broker_url = {cls.CELERY_BROKER_URL}
result_backend = {cls.CELERY_RESULT_BACKEND}
worker_concurrency = 16

[smtp]
smtp_host = {cls.SMTP_HOST}
smtp_starttls = True
smtp_ssl = False
smtp_port = {cls.SMTP_PORT}
smtp_mail_from = {cls.SMTP_MAIL_FROM}

[api]
auth_backend = airflow.api.auth.backend.basic_auth
"""

    @classmethod
    def get_environment_vars(cls) -> Dict[str, str]:
        """获取环境变量配置"""
        return {
            'AIRFLOW_HOME': cls.AIRFLOW_HOME,
            'AIRFLOW__CORE__EXECUTOR': cls.EXECUTOR,
            'AIRFLOW__CORE__SQL_ALCHEMY_CONN': cls.AIRFLOW_DB_URL,
            'AIRFLOW__CELERY__BROKER_URL': cls.CELERY_BROKER_URL,
            'AIRFLOW__CELERY__RESULT_BACKEND': cls.CELERY_RESULT_BACKEND,
            'AIRFLOW__WEBSERVER__WEB_SERVER_PORT': str(cls.WEB_SERVER_PORT),
            'AIRFLOW__API__AUTH_BACKEND': 'airflow.api.auth.backend.basic_auth',
        }

# 获取配置实例
airflow_config = AirflowConfig() 