-- 工作流功能增强SQL脚本
-- 在现有数据表基础上扩展支持多工作域和权限控制

-- ================================
-- 1. 扩展现有工作流定义表
-- ================================

-- 为 sys_workflow 表添加工作域支持字段
ALTER TABLE `sys_workflow` 
ADD COLUMN `workspace` varchar(50) DEFAULT 'default' COMMENT '所属工作域' AFTER `category`,
ADD COLUMN `sub_category` varchar(50) DEFAULT NULL COMMENT '子分类' AFTER `workspace`,
ADD COLUMN `trigger_type` enum('manual','automatic','scheduled','event') DEFAULT 'manual' COMMENT '触发方式' AFTER `status`,
ADD COLUMN `priority` enum('low','normal','high','urgent') DEFAULT 'normal' COMMENT '优先级' AFTER `trigger_type`,
ADD COLUMN `version` varchar(20) DEFAULT '1.0.0' COMMENT '版本号' AFTER `priority`,
ADD COLUMN `auto_rollback` tinyint(1) DEFAULT 0 COMMENT '是否自动回滚' AFTER `retry_count`,
ADD COLUMN `notification_enabled` tinyint(1) DEFAULT 1 COMMENT '是否启用通知' AFTER `auto_rollback`,
ADD COLUMN `notification_config` json COMMENT '通知配置' AFTER `notification_enabled`,
ADD INDEX `idx_workspace` (`workspace`),
ADD INDEX `idx_sub_category` (`sub_category`);

-- ================================
-- 2. 扩展现有步骤定义表
-- ================================

-- 为 workflow_steps 表添加节点类型和权限支持
ALTER TABLE `workflow_steps`
ADD COLUMN `node_type` enum('page','button','api','condition','timer','notification','script','approval','python','bash','sql','http') DEFAULT 'python' COMMENT '节点类型' AFTER `step_type`,
ADD COLUMN `position_x` decimal(10,2) DEFAULT 0 COMMENT 'X坐标(流程图)' AFTER `condition`,
ADD COLUMN `position_y` decimal(10,2) DEFAULT 0 COMMENT 'Y坐标(流程图)' AFTER `position_x`,
ADD COLUMN `icon` varchar(50) DEFAULT 'play-circle' COMMENT '节点图标' AFTER `position_y`,
ADD COLUMN `color` varchar(20) DEFAULT '#1890ff' COMMENT '节点颜色' AFTER `icon`,
ADD COLUMN `skip_on_failure` tinyint(1) DEFAULT 0 COMMENT '失败时是否跳过' AFTER `retry_count`,
ADD COLUMN `rollback_enabled` tinyint(1) DEFAULT 0 COMMENT '是否支持回滚' AFTER `skip_on_failure`,
ADD COLUMN `status` enum('active','disabled') DEFAULT 'active' COMMENT '节点状态' AFTER `rollback_enabled`,
ADD INDEX `idx_node_type` (`node_type`),
ADD INDEX `idx_status` (`status`);

-- ================================
-- 3. 新增工作域管理表
-- ================================

CREATE TABLE IF NOT EXISTS `workflow_workspaces` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '工作域ID',
  `code` varchar(50) NOT NULL COMMENT '工作域代码',
  `name` varchar(100) NOT NULL COMMENT '工作域名称',
  `description` text COMMENT '工作域描述',
  `icon` varchar(50) DEFAULT 'folder' COMMENT '工作域图标',
  `color` varchar(20) DEFAULT '#1890ff' COMMENT '工作域颜色',
  `status` enum('active','disabled') NOT NULL DEFAULT 'active' COMMENT '状态',
  `order_num` int(11) DEFAULT 0 COMMENT '排序号',
  `creator_id` int(11) NOT NULL COMMENT '创建人ID',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_workspace_code` (`code`),
  KEY `idx_workspace_name` (`name`),
  KEY `idx_workspace_status` (`status`),
  KEY `idx_workspace_order` (`order_num`),
  FOREIGN KEY (`creator_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='工作域管理表';

-- ================================
-- 4. 新增权限控制表
-- ================================

CREATE TABLE IF NOT EXISTS `workflow_permissions` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '权限ID',
  `resource_type` enum('workspace','workflow','step') NOT NULL COMMENT '资源类型',
  `resource_id` int(11) NOT NULL COMMENT '资源ID',
  `subject_type` enum('user','role','organization') NOT NULL COMMENT '主体类型',
  `subject_id` int(11) NOT NULL COMMENT '主体ID',
  `permission_type` enum('view','edit','execute','delete','manage') NOT NULL COMMENT '权限类型',
  `granted` tinyint(1) NOT NULL DEFAULT 1 COMMENT '是否授权',
  `conditions` json COMMENT '权限条件',
  `granted_by` int(11) NOT NULL COMMENT '授权人ID',
  `granted_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '授权时间',
  `expires_at` datetime NULL COMMENT '过期时间',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_permission` (`resource_type`, `resource_id`, `subject_type`, `subject_id`, `permission_type`),
  KEY `idx_permission_resource` (`resource_type`, `resource_id`),
  KEY `idx_permission_subject` (`subject_type`, `subject_id`),
  KEY `idx_permission_type` (`permission_type`),
  KEY `idx_permission_granted` (`granted`),
  FOREIGN KEY (`granted_by`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='工作流权限控制表';

-- ================================
-- 5. 新增节点连接关系表
-- ================================

CREATE TABLE IF NOT EXISTS `workflow_step_connections` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '连接ID',
  `workflow_id` int(11) NOT NULL COMMENT '工作流ID',
  `from_step_id` int(11) NOT NULL COMMENT '源步骤ID',
  `to_step_id` int(11) NOT NULL COMMENT '目标步骤ID',
  `condition_type` enum('always','success','failure','condition') DEFAULT 'always' COMMENT '连接条件类型',
  `condition_expression` text COMMENT '条件表达式',
  `condition_config` json COMMENT '条件配置',
  `order_num` int(11) DEFAULT 0 COMMENT '连接排序',
  `style_config` json COMMENT '连接样式配置',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_connection` (`from_step_id`, `to_step_id`, `condition_type`),
  KEY `idx_connection_workflow` (`workflow_id`),
  KEY `idx_connection_from` (`from_step_id`),
  KEY `idx_connection_to` (`to_step_id`),
  FOREIGN KEY (`workflow_id`) REFERENCES `sys_workflow` (`id`) ON DELETE CASCADE,
  FOREIGN KEY (`from_step_id`) REFERENCES `workflow_steps` (`id`) ON DELETE CASCADE,
  FOREIGN KEY (`to_step_id`) REFERENCES `workflow_steps` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='步骤连接关系表';

-- ================================
-- 6. 初始化默认工作域数据
-- ================================

INSERT INTO `workflow_workspaces` (`code`, `name`, `description`, `icon`, `color`, `order_num`, `creator_id`) VALUES
('system', '系统管理', '系统级工作流和管理流程', 'setting', '#722ed1', 1, 1),
('business', '业务流程', '核心业务流程管理', 'project', '#1890ff', 2, 1),
('data', '数据处理', '数据相关的工作流', 'database', '#52c41a', 3, 1),
('customer_service', '客服服务', '客服相关的业务流程', 'team', '#fa8c16', 4, 1),
('ai_app', 'AI应用', 'AI相关的工作流', 'robot', '#eb2f96', 5, 1);

-- ================================
-- 7. 更新现有工作流数据的工作域字段
-- ================================

-- 根据现有分类自动分配工作域
UPDATE `sys_workflow` SET 
  `workspace` = CASE 
    WHEN `category` IN ('approval', 'task_scheduling') THEN 'business'
    WHEN `category` IN ('data_processing', 'etl', 'monitoring') THEN 'data'
    WHEN `category` = 'notification' THEN 'system'
    WHEN `category` = 'ai_ml' THEN 'ai_app'
    ELSE 'business'
  END
WHERE `workspace` = 'default';

-- ================================
-- 8. 更新工作流模板的分类映射
-- ================================

-- 为超级管理员自动分配所有工作域的管理权限
INSERT INTO `workflow_permissions` (`resource_type`, `resource_id`, `subject_type`, `subject_id`, `permission_type`, `granted_by`)
SELECT 'workspace', w.id, 'user', 1, 'manage', 1
FROM `workflow_workspaces` w
WHERE NOT EXISTS (
  SELECT 1 FROM `workflow_permissions` p 
  WHERE p.resource_type = 'workspace' AND p.resource_id = w.id 
    AND p.subject_type = 'user' AND p.subject_id = 1 
    AND p.permission_type = 'manage'
);

-- ================================
-- 9. 扩展工作流分类枚举值
-- ================================

-- 更新现有分类到更细粒度的分类
UPDATE `sys_workflow` SET 
  `category` = 'user_management',
  `sub_category` = 'approval'
WHERE `category` = 'approval' AND `workspace` = 'system';

UPDATE `sys_workflow` SET 
  `category` = 'etl_process',
  `sub_category` = 'data_import'
WHERE `category` = 'data_processing' AND `workspace` = 'data';

UPDATE `sys_workflow` SET 
  `category` = 'model_training',
  `sub_category` = 'training'
WHERE `category` = 'ai_ml' AND `workspace` = 'ai_app';

-- ================================
-- 10. 添加示例节点类型配置
-- ================================

-- 更新现有步骤的节点类型
UPDATE `workflow_steps` SET 
  `node_type` = CASE 
    WHEN `step_type` = 'python' THEN 'script'
    WHEN `step_type` = 'bash' THEN 'script'
    WHEN `step_type` = 'sql' THEN 'script'
    WHEN `step_type` = 'http' THEN 'api'
    ELSE 'script'
  END
WHERE `node_type` = 'python';

-- ================================
-- 11. 创建节点类型配置示例
-- ================================

-- 页面节点配置示例
INSERT INTO `workflow_variables` (`workflow_id`, `var_name`, `var_type`, `var_value`, `description`, `is_required`) 
SELECT w.id, 'page_node_config', 'json', 
  '{"type": "page", "route": "/customer-service/workbench", "params": {}, "target": "_current"}',
  '页面节点配置示例', 0
FROM `sys_workflow` w 
WHERE w.category = 'user_management' 
LIMIT 1;

-- 按钮节点配置示例  
INSERT INTO `workflow_variables` (`workflow_id`, `var_name`, `var_type`, `var_value`, `description`, `is_required`)
SELECT w.id, 'button_node_config', 'json',
  '{"type": "button", "selector": "#approve-btn", "action": "click", "waitFor": ".success-message"}',
  '按钮节点配置示例', 0
FROM `sys_workflow` w 
WHERE w.category = 'user_management' 
LIMIT 1;

-- API节点配置示例
INSERT INTO `workflow_variables` (`workflow_id`, `var_name`, `var_type`, `var_value`, `description`, `is_required`)
SELECT w.id, 'api_node_config', 'json',
  '{"type": "api", "url": "/api/workflow/execute", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": {}}',
  'API节点配置示例', 0
FROM `sys_workflow` w 
WHERE w.category = 'etl_process' 
LIMIT 1; 