-- 新增市场营销域的客户服务工作流数据
-- ================================
-- 1. 创建"客户服务"工作流
-- ================================

INSERT INTO `sys_workflow` (
    `name`,
    `description`,
    `category`,
    `workspace`,
    `sub_category`,
    `status`,
    `trigger_type`,
    `version`,
    `dag_id`,
    `config`,
    `schedule`,
    `priority`,
    `timeout`,
    `retry_count`,
    `creator_id`,
    `created_at`,
    `updated_at`
) VALUES (
    '客户服务',
    '市场营销域客户服务业务流程，包含坐席受理、服务处理、完结审批、客服回访等环节',
    'customer_service',
    'marketing',
    'service_process',
    'active',
    'manual',
    '1.0.0',
    'workflow_marketing_customer_service_001',
    '{"description": "客户服务流程", "timeout": 3600, "max_retry": 3, "notification": {"email": true, "sms": false}}',
    NULL,
    1,
    3600,
    3,
    1,
    NOW(),
    NOW()
);

-- ================================
-- 2. 创建工作流步骤/节点
-- ================================

-- 获取刚创建的工作流ID
SET @workflow_id = LAST_INSERT_ID();

-- 步骤1: 坐席受理
INSERT INTO `workflow_steps` (
    `workflow_id`,
    `step_name`,
    `step_type`,
    `step_order`,
    `depends_on`,
    `config`,
    `timeout`,
    `retry_count`,
    `condition`,
    `created_at`,
    `updated_at`
) VALUES (
    @workflow_id,
    '坐席受理',
    'manual',
    1,
    NULL,
    '{"node_type": "page", "route": "/customer-service/reception", "icon": "phone", "color": "#1890ff", "description": "客服坐席接收客户服务请求，进行初步处理和分类"}',
    1800,
    1,
    NULL,
    NOW(),
    NOW()
);

-- 获取第一个步骤的ID
SET @step1_id = LAST_INSERT_ID();

-- 步骤2: 服务处理
INSERT INTO `workflow_steps` (
    `workflow_id`,
    `step_name`,
    `step_type`,
    `step_order`,
    `depends_on`,
    `config`,
    `timeout`,
    `retry_count`,
    `condition`,
    `created_at`,
    `updated_at`
) VALUES (
    @workflow_id,
    '服务处理',
    'manual',
    2,
    JSON_ARRAY(@step1_id),
    '{"node_type": "page", "route": "/customer-service/processing", "icon": "tool", "color": "#52c41a", "description": "根据客户需求进行具体的服务处理和问题解决"}',
    3600,
    2,
    NULL,
    NOW(),
    NOW()
);

-- 获取第二个步骤的ID
SET @step2_id = LAST_INSERT_ID();

-- 步骤3: 完结审批
INSERT INTO `workflow_steps` (
    `workflow_id`,
    `step_name`,
    `step_type`,
    `step_order`,
    `depends_on`,
    `config`,
    `timeout`,
    `retry_count`,
    `condition`,
    `created_at`,
    `updated_at`
) VALUES (
    @workflow_id,
    '完结审批',
    'approval',
    3,
    JSON_ARRAY(@step2_id),
    '{"node_type": "approval", "route": "/customer-service/approval", "icon": "check-circle", "color": "#fa8c16", "description": "主管或质检人员对服务处理结果进行审批确认"}',
    1800,
    1,
    'status == "completed"',
    NOW(),
    NOW()
);

-- 获取第三个步骤的ID
SET @step3_id = LAST_INSERT_ID();

-- 步骤4: 客服回访
INSERT INTO `workflow_steps` (
    `workflow_id`,
    `step_name`,
    `step_type`,
    `step_order`,
    `depends_on`,
    `config`,
    `timeout`,
    `retry_count`,
    `condition`,
    `created_at`,
    `updated_at`
) VALUES (
    @workflow_id,
    '客服回访',
    'manual',
    4,
    JSON_ARRAY(@step3_id),
    '{"node_type": "page", "route": "/customer-service/followup", "icon": "message", "color": "#722ed1", "description": "服务完成后对客户进行回访，收集满意度反馈"}',
    1800,
    1,
    'approval_status == "approved"',
    NOW(),
    NOW()
);

-- ================================
-- 3. 创建工作流变量配置
-- ================================

-- 客户信息变量
INSERT INTO `workflow_variables` (
    `workflow_id`,
    `var_name`,
    `var_type`,
    `var_value`,
    `description`,
    `is_required`,
    `created_at`,
    `updated_at`
) VALUES (
    @workflow_id,
    'customer_info',
    'json',
    '{"customer_id": "", "customer_name": "", "contact_phone": "", "service_type": ""}',
    '客户基本信息',
    1,
    NOW(),
    NOW()
);

-- 服务处理结果变量
INSERT INTO `workflow_variables` (
    `workflow_id`,
    `var_name`,
    `var_type`,
    `var_value`,
    `description`,
    `is_required`,
    `created_at`,
    `updated_at`
) VALUES (
    @workflow_id,
    'service_result',
    'json',
    '{"status": "", "solution": "", "processing_time": "", "agent_notes": ""}',
    '服务处理结果记录',
    1,
    NOW(),
    NOW()
);

-- 审批结果变量
INSERT INTO `workflow_variables` (
    `workflow_id`,
    `var_name`,
    `var_type`,
    `var_value`,
    `description`,
    `is_required`,
    `created_at`,
    `updated_at`
) VALUES (
    @workflow_id,
    'approval_result',
    'json',
    '{"approval_status": "", "approver_id": "", "approval_notes": "", "approval_time": ""}',
    '审批结果记录',
    0,
    NOW(),
    NOW()
);

-- 回访结果变量
INSERT INTO `workflow_variables` (
    `workflow_id`,
    `var_name`,
    `var_type`,
    `var_value`,
    `description`,
    `is_required`,
    `created_at`,
    `updated_at`
) VALUES (
    @workflow_id,
    'followup_result',
    'json',
    '{"satisfaction_score": "", "feedback_comments": "", "followup_agent": "", "followup_time": ""}',
    '客服回访结果',
    0,
    NOW(),
    NOW()
);

-- ================================
-- 4. 验证创建结果
-- ================================

-- 显示创建结果
SELECT 
    '市场营销域客户服务工作流创建成功！' as message,
    w.id as workspace_id,
    w.name as workspace_name,
    wf.id as workflow_id,
    wf.name as workflow_name,
    COUNT(ws.id) as steps_count
FROM workflow_workspaces w
JOIN sys_workflow wf ON wf.workspace = w.code
LEFT JOIN workflow_steps ws ON ws.workflow_id = wf.id
WHERE w.code = 'marketing' AND wf.name = '客户服务'
GROUP BY w.id, w.name, wf.id, wf.name;

-- 显示工作流步骤详情
SELECT 
    'Steps Detail:' as section,
    ws.step_order,
    ws.step_name,
    ws.step_type,
    JSON_EXTRACT(ws.config, '$.node_type') as node_type,
    JSON_EXTRACT(ws.config, '$.icon') as icon,
    JSON_EXTRACT(ws.config, '$.color') as color,
    JSON_EXTRACT(ws.config, '$.description') as description
FROM workflow_steps ws
JOIN sys_workflow wf ON ws.workflow_id = wf.id
WHERE wf.workspace = 'marketing' AND wf.name = '客户服务'
ORDER BY ws.step_order; 