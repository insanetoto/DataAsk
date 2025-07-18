-- 增强版工作流数据库设计 - 支持多工作域和权限控制
-- 作者: DataAsk AI Assistant
-- 日期: 2025-01-19

-- ================================
-- 1. 工作域管理表
-- ================================
CREATE TABLE IF NOT EXISTS `workflow_workspaces` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '工作域ID',
  `name` varchar(100) NOT NULL COMMENT '工作域名称',
  `code` varchar(50) NOT NULL COMMENT '工作域代码',
  `description` text COMMENT '工作域描述',
  `icon` varchar(50) DEFAULT 'folder' COMMENT '工作域图标',
  `color` varchar(20) DEFAULT '#1890ff' COMMENT '工作域颜色',
  `status` enum('active','disabled') NOT NULL DEFAULT 'active' COMMENT '状态',
  `order_num` int DEFAULT 0 COMMENT '排序号',
  `creator_id` bigint NOT NULL COMMENT '创建人ID',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_workspace_code` (`code`),
  KEY `idx_workspace_name` (`name`),
  KEY `idx_workspace_status` (`status`),
  KEY `idx_workspace_order` (`order_num`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='工作域管理表';

-- ================================
-- 2. 业务流程分类表
-- ================================
CREATE TABLE IF NOT EXISTS `workflow_categories` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '分类ID',
  `workspace_id` bigint NOT NULL COMMENT '所属工作域ID',
  `name` varchar(100) NOT NULL COMMENT '分类名称',
  `code` varchar(50) NOT NULL COMMENT '分类代码',
  `description` text COMMENT '分类描述',
  `icon` varchar(50) DEFAULT 'folder' COMMENT '分类图标',
  `color` varchar(20) DEFAULT '#52c41a' COMMENT '分类颜色',
  `parent_id` bigint DEFAULT NULL COMMENT '父分类ID',
  `level` int DEFAULT 1 COMMENT '分类层级',
  `path` varchar(500) DEFAULT '/' COMMENT '分类路径',
  `status` enum('active','disabled') NOT NULL DEFAULT 'active' COMMENT '状态',
  `order_num` int DEFAULT 0 COMMENT '排序号',
  `creator_id` bigint NOT NULL COMMENT '创建人ID',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_category_code_workspace` (`code`, `workspace_id`),
  KEY `idx_category_workspace` (`workspace_id`),
  KEY `idx_category_parent` (`parent_id`),
  KEY `idx_category_path` (`path`),
  FOREIGN KEY (`workspace_id`) REFERENCES `workflow_workspaces` (`id`) ON DELETE CASCADE,
  FOREIGN KEY (`parent_id`) REFERENCES `workflow_categories` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='业务流程分类表';

-- ================================
-- 3. 增强版工作流定义表
-- ================================
CREATE TABLE IF NOT EXISTS `enhanced_workflows` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '工作流ID',
  `workspace_id` bigint NOT NULL COMMENT '所属工作域ID',
  `category_id` bigint NOT NULL COMMENT '所属分类ID',
  `name` varchar(200) NOT NULL COMMENT '工作流名称',
  `code` varchar(100) NOT NULL COMMENT '工作流代码',
  `description` text COMMENT '工作流描述',
  `version` varchar(20) DEFAULT '1.0.0' COMMENT '版本号',
  `type` enum('sequential','parallel','conditional','loop') DEFAULT 'sequential' COMMENT '流程类型',
  `trigger_type` enum('manual','automatic','scheduled','event') DEFAULT 'manual' COMMENT '触发方式',
  `status` enum('draft','active','inactive','disabled','archived') NOT NULL DEFAULT 'draft' COMMENT '状态',
  `priority` enum('low','normal','high','urgent') DEFAULT 'normal' COMMENT '优先级',
  `dag_id` varchar(200) NOT NULL COMMENT 'Airflow DAG ID',
  `config` json COMMENT '工作流配置(JSON格式)',
  `variables` json COMMENT '工作流变量',
  `schedule_expression` varchar(100) COMMENT '调度表达式(Cron)',
  `timeout_minutes` int DEFAULT 60 COMMENT '超时时间(分钟)',
  `retry_count` int DEFAULT 1 COMMENT '重试次数',
  `retry_delay_minutes` int DEFAULT 5 COMMENT '重试间隔(分钟)',
  `auto_rollback` tinyint(1) DEFAULT 0 COMMENT '是否自动回滚',
  `notification_enabled` tinyint(1) DEFAULT 1 COMMENT '是否启用通知',
  `notification_config` json COMMENT '通知配置',
  `creator_id` bigint NOT NULL COMMENT '创建人ID',
  `updater_id` bigint COMMENT '最后修改人ID',
  `published_at` timestamp NULL COMMENT '发布时间',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_workflow_code_workspace` (`code`, `workspace_id`),
  UNIQUE KEY `uk_dag_id` (`dag_id`),
  KEY `idx_workflow_workspace` (`workspace_id`),
  KEY `idx_workflow_category` (`category_id`),
  KEY `idx_workflow_status` (`status`),
  KEY `idx_workflow_type` (`type`),
  KEY `idx_workflow_creator` (`creator_id`),
  FOREIGN KEY (`workspace_id`) REFERENCES `workflow_workspaces` (`id`) ON DELETE CASCADE,
  FOREIGN KEY (`category_id`) REFERENCES `workflow_categories` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='增强版工作流定义表';

-- ================================
-- 4. 工作流节点定义表
-- ================================
CREATE TABLE IF NOT EXISTS `workflow_nodes` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '节点ID',
  `workflow_id` bigint NOT NULL COMMENT '工作流ID',
  `name` varchar(200) NOT NULL COMMENT '节点名称',
  `code` varchar(100) NOT NULL COMMENT '节点代码',
  `description` text COMMENT '节点描述',
  `type` enum('page','button','api','condition','timer','notification','script','approval') NOT NULL COMMENT '节点类型',
  `subtype` varchar(50) COMMENT '节点子类型',
  `step_order` int NOT NULL COMMENT '执行顺序',
  `x_position` decimal(10,2) DEFAULT 0 COMMENT 'X坐标(流程图)',
  `y_position` decimal(10,2) DEFAULT 0 COMMENT 'Y坐标(流程图)',
  `icon` varchar(50) DEFAULT 'play-circle' COMMENT '节点图标',
  `color` varchar(20) DEFAULT '#1890ff' COMMENT '节点颜色',
  `config` json NOT NULL COMMENT '节点配置',
  `input_schema` json COMMENT '输入数据结构',
  `output_schema` json COMMENT '输出数据结构',
  `validation_rules` json COMMENT '数据验证规则',
  `timeout_minutes` int DEFAULT 30 COMMENT '节点超时时间(分钟)',
  `retry_count` int DEFAULT 1 COMMENT '重试次数',
  `retry_delay_minutes` int DEFAULT 2 COMMENT '重试间隔(分钟)',
  `skip_on_failure` tinyint(1) DEFAULT 0 COMMENT '失败时是否跳过',
  `rollback_enabled` tinyint(1) DEFAULT 0 COMMENT '是否支持回滚',
  `rollback_config` json COMMENT '回滚配置',
  `conditions` json COMMENT '执行条件',
  `status` enum('active','disabled') NOT NULL DEFAULT 'active' COMMENT '状态',
  `creator_id` bigint NOT NULL COMMENT '创建人ID',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_node_code_workflow` (`code`, `workflow_id`),
  KEY `idx_node_workflow` (`workflow_id`),
  KEY `idx_node_type` (`type`),
  KEY `idx_node_order` (`step_order`),
  KEY `idx_node_status` (`status`),
  FOREIGN KEY (`workflow_id`) REFERENCES `enhanced_workflows` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='工作流节点定义表';

-- ================================
-- 5. 节点连接关系表
-- ================================
CREATE TABLE IF NOT EXISTS `workflow_node_connections` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '连接ID',
  `workflow_id` bigint NOT NULL COMMENT '工作流ID',
  `from_node_id` bigint NOT NULL COMMENT '源节点ID',
  `to_node_id` bigint NOT NULL COMMENT '目标节点ID',
  `condition_type` enum('always','success','failure','condition') DEFAULT 'always' COMMENT '连接条件类型',
  `condition_expression` text COMMENT '条件表达式',
  `condition_config` json COMMENT '条件配置',
  `order_num` int DEFAULT 0 COMMENT '连接排序',
  `style_config` json COMMENT '连接样式配置',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_connection` (`from_node_id`, `to_node_id`, `condition_type`),
  KEY `idx_connection_workflow` (`workflow_id`),
  KEY `idx_connection_from` (`from_node_id`),
  KEY `idx_connection_to` (`to_node_id`),
  FOREIGN KEY (`workflow_id`) REFERENCES `enhanced_workflows` (`id`) ON DELETE CASCADE,
  FOREIGN KEY (`from_node_id`) REFERENCES `workflow_nodes` (`id`) ON DELETE CASCADE,
  FOREIGN KEY (`to_node_id`) REFERENCES `workflow_nodes` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='节点连接关系表';

-- ================================
-- 6. 工作流权限控制表
-- ================================
CREATE TABLE IF NOT EXISTS `workflow_permissions` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '权限ID',
  `resource_type` enum('workspace','category','workflow','node') NOT NULL COMMENT '资源类型',
  `resource_id` bigint NOT NULL COMMENT '资源ID',
  `subject_type` enum('user','role','organization') NOT NULL COMMENT '主体类型',
  `subject_id` bigint NOT NULL COMMENT '主体ID',
  `permission_type` enum('view','edit','execute','delete','manage') NOT NULL COMMENT '权限类型',
  `granted` tinyint(1) NOT NULL DEFAULT 1 COMMENT '是否授权',
  `conditions` json COMMENT '权限条件',
  `granted_by` bigint NOT NULL COMMENT '授权人ID',
  `granted_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '授权时间',
  `expires_at` timestamp NULL COMMENT '过期时间',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_permission` (`resource_type`, `resource_id`, `subject_type`, `subject_id`, `permission_type`),
  KEY `idx_permission_resource` (`resource_type`, `resource_id`),
  KEY `idx_permission_subject` (`subject_type`, `subject_id`),
  KEY `idx_permission_type` (`permission_type`),
  KEY `idx_permission_granted` (`granted`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='工作流权限控制表';

-- ================================
-- 7. 工作流执行实例表
-- ================================
CREATE TABLE IF NOT EXISTS `workflow_instances` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '实例ID',
  `workflow_id` bigint NOT NULL COMMENT '工作流ID',
  `instance_code` varchar(100) NOT NULL COMMENT '实例代码',
  `dag_run_id` varchar(200) NOT NULL COMMENT 'Airflow DAG运行ID',
  `status` enum('pending','running','paused','completed','failed','cancelled','timeout') NOT NULL DEFAULT 'pending' COMMENT '执行状态',
  `trigger_type` enum('manual','scheduled','api','webhook','event') NOT NULL DEFAULT 'manual' COMMENT '触发方式',
  `trigger_user_id` bigint COMMENT '触发用户ID',
  `trigger_data` json COMMENT '触发数据',
  `context_data` json COMMENT '上下文数据',
  `current_node_id` bigint COMMENT '当前执行节点ID',
  `progress_percentage` decimal(5,2) DEFAULT 0.00 COMMENT '执行进度百分比',
  `error_message` text COMMENT '错误信息',
  `error_stack` text COMMENT '错误堆栈',
  `started_at` timestamp NULL COMMENT '开始时间',
  `completed_at` timestamp NULL COMMENT '完成时间',
  `duration_seconds` int COMMENT '执行时长(秒)',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_instance_code` (`instance_code`),
  UNIQUE KEY `uk_dag_run_id` (`dag_run_id`),
  KEY `idx_instance_workflow` (`workflow_id`),
  KEY `idx_instance_status` (`status`),
  KEY `idx_instance_trigger` (`trigger_type`),
  KEY `idx_instance_user` (`trigger_user_id`),
  KEY `idx_instance_started` (`started_at`),
  FOREIGN KEY (`workflow_id`) REFERENCES `enhanced_workflows` (`id`) ON DELETE CASCADE,
  FOREIGN KEY (`current_node_id`) REFERENCES `workflow_nodes` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='工作流执行实例表';

-- ================================
-- 8. 节点执行记录表
-- ================================
CREATE TABLE IF NOT EXISTS `workflow_node_executions` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '执行记录ID',
  `instance_id` bigint NOT NULL COMMENT '工作流实例ID',
  `node_id` bigint NOT NULL COMMENT '节点ID',
  `execution_code` varchar(100) NOT NULL COMMENT '执行代码',
  `task_id` varchar(200) COMMENT 'Airflow任务ID',
  `status` enum('pending','running','success','failed','skipped','retry','timeout') NOT NULL DEFAULT 'pending' COMMENT '执行状态',
  `attempt_count` int DEFAULT 1 COMMENT '尝试次数',
  `input_data` json COMMENT '输入数据',
  `output_data` json COMMENT '输出数据',
  `error_message` text COMMENT '错误信息',
  `error_details` json COMMENT '错误详情',
  `execution_logs` longtext COMMENT '执行日志',
  `started_at` timestamp NULL COMMENT '开始时间',
  `completed_at` timestamp NULL COMMENT '完成时间',
  `duration_seconds` int COMMENT '执行时长(秒)',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_execution_code` (`execution_code`),
  KEY `idx_execution_instance` (`instance_id`),
  KEY `idx_execution_node` (`node_id`),
  KEY `idx_execution_status` (`status`),
  KEY `idx_execution_started` (`started_at`),
  FOREIGN KEY (`instance_id`) REFERENCES `workflow_instances` (`id`) ON DELETE CASCADE,
  FOREIGN KEY (`node_id`) REFERENCES `workflow_nodes` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='节点执行记录表';

-- ================================
-- 9. 审批节点记录表
-- ================================
CREATE TABLE IF NOT EXISTS `workflow_approvals` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '审批记录ID',
  `instance_id` bigint NOT NULL COMMENT '工作流实例ID',
  `node_id` bigint NOT NULL COMMENT '审批节点ID',
  `approver_id` bigint NOT NULL COMMENT '审批人ID',
  `approval_type` enum('approve','reject','delegate','withdraw') NOT NULL COMMENT '审批类型',
  `approval_result` enum('pending','approved','rejected','delegated','withdrawn','timeout') NOT NULL DEFAULT 'pending' COMMENT '审批结果',
  `comments` text COMMENT '审批意见',
  `attachments` json COMMENT '附件信息',
  `delegate_to_id` bigint COMMENT '委托给用户ID',
  `delegate_reason` text COMMENT '委托原因',
  `approval_data` json COMMENT '审批数据',
  `deadline` timestamp NULL COMMENT '审批截止时间',
  `approved_at` timestamp NULL COMMENT '审批时间',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_approval_instance` (`instance_id`),
  KEY `idx_approval_node` (`node_id`),
  KEY `idx_approval_approver` (`approver_id`),
  KEY `idx_approval_result` (`approval_result`),
  KEY `idx_approval_deadline` (`deadline`),
  FOREIGN KEY (`instance_id`) REFERENCES `workflow_instances` (`id`) ON DELETE CASCADE,
  FOREIGN KEY (`node_id`) REFERENCES `workflow_nodes` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='审批节点记录表';

-- ================================
-- 初始化数据
-- ================================

-- 插入默认工作域
INSERT INTO `workflow_workspaces` (`name`, `code`, `description`, `icon`, `color`, `order_num`, `creator_id`) VALUES
('系统管理', 'system', '系统级工作流和管理流程', 'setting', '#722ed1', 1, 1),
('业务流程', 'business', '核心业务流程管理', 'project', '#1890ff', 2, 1),
('数据处理', 'data', '数据相关的工作流', 'database', '#52c41a', 3, 1),
('客服服务', 'customer_service', '客服相关的业务流程', 'customer-service', '#fa8c16', 4, 1),
('AI应用', 'ai_app', 'AI相关的工作流', 'robot', '#eb2f96', 5, 1);

-- 插入业务流程分类
INSERT INTO `workflow_categories` (`workspace_id`, `name`, `code`, `description`, `icon`, `color`, `order_num`, `creator_id`) VALUES
-- 系统管理分类
(1, '用户管理', 'user_management', '用户相关的管理流程', 'user', '#1890ff', 1, 1),
(1, '权限管理', 'permission_management', '权限和角色管理流程', 'lock', '#722ed1', 2, 1),
(1, '系统配置', 'system_config', '系统配置相关流程', 'setting', '#52c41a', 3, 1),

-- 业务流程分类
(2, '审批流程', 'approval', '各类审批业务流程', 'audit', '#1890ff', 1, 1),
(2, '订单处理', 'order_processing', '订单相关的业务流程', 'shopping-cart', '#52c41a', 2, 1),
(2, '财务流程', 'finance', '财务相关的业务流程', 'dollar', '#fa8c16', 3, 1),

-- 数据处理分类
(3, 'ETL流程', 'etl', '数据提取、转换、加载流程', 'swap', '#1890ff', 1, 1),
(3, '数据分析', 'data_analysis', '数据分析相关流程', 'bar-chart', '#52c41a', 2, 1),
(3, '报表生成', 'report_generation', '报表生成相关流程', 'file-text', '#fa8c16', 3, 1),

-- 客服服务分类
(4, '工单处理', 'ticket_processing', '客服工单处理流程', 'file-text', '#1890ff', 1, 1),
(4, '客户沟通', 'customer_communication', '客户沟通相关流程', 'message', '#52c41a', 2, 1),
(4, '问题升级', 'issue_escalation', '问题升级处理流程', 'exclamation-circle', '#fa8c16', 3, 1),

-- AI应用分类
(5, '模型训练', 'model_training', 'AI模型训练流程', 'robot', '#1890ff', 1, 1),
(5, '数据预处理', 'data_preprocessing', 'AI数据预处理流程', 'filter', '#52c41a', 2, 1),
(5, '模型部署', 'model_deployment', 'AI模型部署流程', 'cloud-upload', '#fa8c16', 3, 1); 