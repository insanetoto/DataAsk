-- ============================================================
-- 百惟数问 - 智能数据问答平台
-- 工作流数据库初始化脚本
-- ============================================================

USE airflow;

-- ============================================================
-- 第一部分：基础表结构
-- ============================================================

-- 1. 工作流定义表
CREATE TABLE IF NOT EXISTS `sys_workflow` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '工作流ID',
  `name` varchar(100) NOT NULL COMMENT '工作流名称',
  `description` text COMMENT '工作流描述',
  `category` varchar(50) NOT NULL DEFAULT 'general' COMMENT '工作流分类',
  `status` enum('active','inactive','disabled','deleted') NOT NULL DEFAULT 'inactive' COMMENT '状态',
  `dag_id` varchar(100) NOT NULL COMMENT 'Airflow DAG ID',
  `config` json COMMENT '工作流配置(JSON格式)',
  `schedule` varchar(100) COMMENT '调度表达式',
  `priority` int DEFAULT 0 COMMENT '优先级',
  `timeout` int DEFAULT 3600 COMMENT '超时时间(秒)',
  `retry_count` int DEFAULT 1 COMMENT '重试次数',
  `creator_id` bigint NOT NULL COMMENT '创建人ID（关联dataask.users表）',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_dag_id` (`dag_id`),
  KEY `idx_name` (`name`),
  KEY `idx_category` (`category`),
  KEY `idx_status` (`status`),
  KEY `idx_creator` (`creator_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='工作流定义表';

-- 2. 工作流步骤定义表
CREATE TABLE IF NOT EXISTS `workflow_steps` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '步骤ID',
  `workflow_id` bigint NOT NULL COMMENT '工作流ID',
  `step_name` varchar(100) NOT NULL COMMENT '步骤名称',
  `step_type` varchar(50) NOT NULL COMMENT '步骤类型(python,bash,sql,http,etc.)',
  `step_order` int NOT NULL COMMENT '执行顺序',
  `depends_on` json COMMENT '依赖的步骤ID列表',
  `config` json NOT NULL COMMENT '步骤配置',
  `timeout` int DEFAULT 1800 COMMENT '步骤超时时间(秒)',
  `retry_count` int DEFAULT 1 COMMENT '重试次数',
  `condition` varchar(500) COMMENT '执行条件',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_workflow_id` (`workflow_id`),
  KEY `idx_step_order` (`step_order`),
  FOREIGN KEY (`workflow_id`) REFERENCES `sys_workflow` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='工作流步骤定义表';

-- 3. 工作流执行记录表
CREATE TABLE IF NOT EXISTS `workflow_executions` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '执行记录ID',
  `workflow_id` bigint NOT NULL COMMENT '工作流ID',
  `execution_id` varchar(100) NOT NULL COMMENT '执行ID(对应Airflow dag_run_id)',
  `status` enum('running','success','failed','cancelled','timeout') NOT NULL DEFAULT 'running' COMMENT '执行状态',
  `trigger_type` enum('manual','scheduled','api','webhook') NOT NULL DEFAULT 'manual' COMMENT '触发方式',
  `input_data` json COMMENT '输入数据',
  `output_data` json COMMENT '输出数据',
  `error_message` text COMMENT '错误信息',
  `started_at` timestamp NULL COMMENT '开始时间',
  `finished_at` timestamp NULL COMMENT '结束时间',
  `duration` int COMMENT '执行时长(秒)',
  `executor_id` bigint COMMENT '执行人ID（关联dataask.users表）',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_execution_id` (`execution_id`),
  KEY `idx_workflow_id` (`workflow_id`),
  KEY `idx_status` (`status`),
  KEY `idx_started_at` (`started_at`),
  KEY `idx_executor_id` (`executor_id`),
  FOREIGN KEY (`workflow_id`) REFERENCES `sys_workflow` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='工作流执行记录表';

-- 4. 工作流步骤执行记录表
CREATE TABLE IF NOT EXISTS `workflow_step_executions` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '步骤执行记录ID',
  `execution_id` bigint NOT NULL COMMENT '工作流执行记录ID',
  `step_id` bigint NOT NULL COMMENT '步骤ID',
  `task_id` varchar(100) NOT NULL COMMENT 'Airflow任务ID',
  `status` enum('running','success','failed','skipped','retry') NOT NULL DEFAULT 'running' COMMENT '执行状态',
  `input_data` json COMMENT '输入数据',
  `output_data` json COMMENT '输出数据',
  `error_message` text COMMENT '错误信息',
  `logs` longtext COMMENT '执行日志',
  `started_at` timestamp NULL COMMENT '开始时间',
  `finished_at` timestamp NULL COMMENT '结束时间',
  `duration` int COMMENT '执行时长(秒)',
  `retry_count` int DEFAULT 0 COMMENT '重试次数',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_execution_id` (`execution_id`),
  KEY `idx_step_id` (`step_id`),
  KEY `idx_task_id` (`task_id`),
  KEY `idx_status` (`status`),
  FOREIGN KEY (`execution_id`) REFERENCES `workflow_executions` (`id`) ON DELETE CASCADE,
  FOREIGN KEY (`step_id`) REFERENCES `workflow_steps` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='工作流步骤执行记录表';

-- 5. 工作流模板表
CREATE TABLE IF NOT EXISTS `workflow_templates` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '模板ID',
  `name` varchar(100) NOT NULL COMMENT '模板名称',
  `description` text COMMENT '模板描述',
  `category` varchar(50) NOT NULL COMMENT '模板分类',
  `icon` varchar(100) COMMENT '图标',
  `template_config` json NOT NULL COMMENT '模板配置',
  `usage_count` int DEFAULT 0 COMMENT '使用次数',
  `is_public` tinyint(1) DEFAULT 1 COMMENT '是否公开',
  `creator_id` bigint NOT NULL COMMENT '创建人ID（关联dataask.users表）',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_name` (`name`),
  KEY `idx_category` (`category`),
  KEY `idx_creator` (`creator_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='工作流模板表';

-- 6. 工作流变量表
CREATE TABLE IF NOT EXISTS `workflow_variables` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '变量ID',
  `workflow_id` bigint NOT NULL COMMENT '工作流ID',
  `var_name` varchar(100) NOT NULL COMMENT '变量名称',
  `var_type` enum('string','number','boolean','json','secret') NOT NULL DEFAULT 'string' COMMENT '变量类型',
  `var_value` text COMMENT '变量值',
  `description` varchar(500) COMMENT '变量描述',
  `is_required` tinyint(1) DEFAULT 0 COMMENT '是否必需',
  `default_value` text COMMENT '默认值',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_workflow_var` (`workflow_id`, `var_name`),
  KEY `idx_var_name` (`var_name`),
  FOREIGN KEY (`workflow_id`) REFERENCES `sys_workflow` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='工作流变量表';

-- ============================================================
-- 第二部分：初始化基础数据
-- ============================================================

-- 插入工作流模板数据
INSERT INTO `workflow_templates` (`name`, `description`, `category`, `icon`, `template_config`, `creator_id`) VALUES
('数据ETL流程', '标准的数据提取、转换、加载流程模板', 'data_processing', 'database', 
'{"steps": [{"name": "数据提取", "type": "sql", "config": {"query": "SELECT * FROM source_table"}}, {"name": "数据转换", "type": "python", "config": {"script": "transform_data.py"}}, {"name": "数据加载", "type": "sql", "config": {"query": "INSERT INTO target_table"}}]}', 1),

('AI模型训练', 'AI模型训练和评估流程模板', 'ai_ml', 'robot', 
'{"steps": [{"name": "数据预处理", "type": "python", "config": {"script": "preprocess.py"}}, {"name": "模型训练", "type": "python", "config": {"script": "train_model.py"}}, {"name": "模型评估", "type": "python", "config": {"script": "evaluate_model.py"}}]}', 1),

('报表生成', '自动化报表生成流程模板', 'report', 'file-text', 
'{"steps": [{"name": "数据查询", "type": "sql", "config": {"query": "SELECT * FROM report_data"}}, {"name": "报表生成", "type": "python", "config": {"script": "generate_report.py"}}, {"name": "邮件发送", "type": "email", "config": {"to": "admin@company.com"}}]}', 1),

('数据监控', '数据质量监控和告警流程模板', 'monitoring', 'eye', 
'{"steps": [{"name": "数据检查", "type": "python", "config": {"script": "data_quality_check.py"}}, {"name": "异常检测", "type": "python", "config": {"script": "anomaly_detection.py"}}, {"name": "告警通知", "type": "webhook", "config": {"url": "https://api.alert.com/notify"}}]}', 1); 