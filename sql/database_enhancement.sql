-- ============================================================
-- 百惟数问权限控制体系优化 - 数据库结构增强脚本
-- 执行时间：2025-01-25
-- 目标：实现三级权限控制体系，完全兼容ACL框架
-- ============================================================

USE dataask;

-- ============================================================
-- 第一步：角色表增强
-- ============================================================

-- 1.1 角色表增加字段
ALTER TABLE roles ADD COLUMN data_scope ENUM('ALL', 'ORG', 'SELF') DEFAULT 'SELF' 
    COMMENT '数据范围：ALL-全部数据，ORG-本机构数据，SELF-个人数据';
    
ALTER TABLE roles ADD COLUMN is_system_role TINYINT DEFAULT 0 
    COMMENT '是否系统角色：1-系统预设不可删除，0-可管理';
    
ALTER TABLE roles ADD COLUMN menu_permissions TEXT 
    COMMENT '菜单权限列表，JSON格式存储';
    
ALTER TABLE roles ADD COLUMN button_permissions TEXT 
    COMMENT '按钮权限列表，JSON格式存储';

-- 1.2 更新现有角色数据
UPDATE roles SET 
    data_scope = 'ALL',
    is_system_role = 1,
    menu_permissions = '["*"]',
    button_permissions = '["*"]'
WHERE role_code = 'SUPER_ADMIN';

UPDATE roles SET 
    data_scope = 'ORG',
    is_system_role = 1,
    menu_permissions = JSON_ARRAY(
        "dashboard", "workspace.*", "ai-engine.*", 
        "sys.user", "sys.org", "sys.role", "sys.workflow", "sys.message"
    ),
    button_permissions = JSON_ARRAY(
        "user.create", "user.edit", "user.delete", "user.reset.password",
        "org.create", "org.edit", "role.view", "workflow.manage"
    )
WHERE role_code = 'ORG_ADMIN';

UPDATE roles SET 
    data_scope = 'SELF',
    is_system_role = 1,
    menu_permissions = JSON_ARRAY(
        "dashboard", "workspace.workbench", "ai-engine.ask-data"
    ),
    button_permissions = JSON_ARRAY(
        "data.query", "profile.edit"
    )
WHERE role_code = 'NORMAL_USER';

-- ============================================================
-- 第二步：权限表优化
-- ============================================================

-- 2.1 权限表增加分类字段
ALTER TABLE permissions ADD COLUMN permission_type 
    ENUM('API', 'MENU', 'BUTTON') DEFAULT 'API' 
    COMMENT '权限类型：API-接口权限，MENU-菜单权限，BUTTON-按钮权限';

ALTER TABLE permissions ADD COLUMN parent_code VARCHAR(100) NULL 
    COMMENT '父权限编码，用于层级权限管理';

-- 2.2 更新现有权限数据类型
UPDATE permissions SET permission_type = 'API' WHERE permission_type IS NULL;

-- 2.3 创建菜单权限数据
INSERT INTO permissions (permission_code, permission_name, api_path, api_method, permission_type, description) VALUES
-- 菜单权限
('MENU_DASHBOARD', '监控台菜单', '/dashboard', 'GET', 'MENU', '访问监控台页面'),
('MENU_WORKSPACE', '工作台菜单', '/workspace', 'GET', 'MENU', '访问工作台页面'),
('MENU_WORKSPACE_WORKBENCH', '个人工作台菜单', '/workspace/workbench', 'GET', 'MENU', '访问个人工作台页面'),
('MENU_WORKSPACE_REPORT', '工作报表菜单', '/workspace/report', 'GET', 'MENU', '访问工作报表页面'),
('MENU_WORKSPACE_MONITOR', '系统监控菜单', '/workspace/monitor', 'GET', 'MENU', '访问系统监控页面'),
('MENU_AI_ENGINE', 'AI引擎菜单', '/ai-engine', 'GET', 'MENU', '访问AI引擎页面'),
('MENU_AI_ENGINE_ASK_DATA', 'AI问答菜单', '/ai-engine/ask-data', 'GET', 'MENU', '访问AI问答页面'),
('MENU_AI_ENGINE_KNOWLEDGE_BASE', '知识库菜单', '/ai-engine/knowledge-base', 'GET', 'MENU', '访问知识库页面'),
('MENU_AI_ENGINE_DATASOURCE', '数据源管理菜单', '/ai-engine/datasource', 'GET', 'MENU', '访问数据源管理页面'),
('MENU_AI_ENGINE_LLMMANAGE', '大模型管理菜单', '/ai-engine/llmmanage', 'GET', 'MENU', '访问大模型管理页面'),
('MENU_AI_ENGINE_MULTIMODAL', '多模态管理菜单', '/ai-engine/multimodal', 'GET', 'MENU', '访问多模态管理页面'),
('MENU_SYS', '系统管理菜单', '/sys', 'GET', 'MENU', '访问系统管理页面'),
('MENU_SYS_USER', '用户管理菜单', '/sys/user', 'GET', 'MENU', '访问用户管理页面'),
('MENU_SYS_ORG', '机构管理菜单', '/sys/org', 'GET', 'MENU', '访问机构管理页面'),
('MENU_SYS_ROLE', '角色管理菜单', '/sys/role', 'GET', 'MENU', '访问角色管理页面'),
('MENU_SYS_PERMISSION', '权限管理菜单', '/sys/permission', 'GET', 'MENU', '访问权限管理页面'),
('MENU_SYS_WORKFLOW', '工作流管理菜单', '/sys/workflow', 'GET', 'MENU', '访问工作流管理页面'),
('MENU_SYS_MESSAGE', '消息管理菜单', '/sys/message', 'GET', 'MENU', '访问消息管理页面'),

-- 按钮权限
('BTN_USER_CREATE', '创建用户按钮', '/api/v1/users', 'POST', 'BUTTON', '用户创建按钮权限'),
('BTN_USER_EDIT', '编辑用户按钮', '/api/v1/users/*', 'PUT', 'BUTTON', '用户编辑按钮权限'),
('BTN_USER_DELETE', '删除用户按钮', '/api/v1/users/*', 'DELETE', 'BUTTON', '用户删除按钮权限'),
('BTN_USER_RESET_PWD', '重置密码按钮', '/api/v1/users/*/password', 'PUT', 'BUTTON', '重置用户密码按钮权限'),
('BTN_USER_VIEW', '查看用户按钮', '/api/v1/users/*', 'GET', 'BUTTON', '查看用户详情按钮权限'),
('BTN_ORG_CREATE', '创建机构按钮', '/api/v1/organizations', 'POST', 'BUTTON', '机构创建按钮权限'),
('BTN_ORG_EDIT', '编辑机构按钮', '/api/v1/organizations/*', 'PUT', 'BUTTON', '机构编辑按钮权限'),
('BTN_ORG_DELETE', '删除机构按钮', '/api/v1/organizations/*', 'DELETE', 'BUTTON', '机构删除按钮权限'),
('BTN_ORG_VIEW', '查看机构按钮', '/api/v1/organizations/*', 'GET', 'BUTTON', '查看机构详情按钮权限'),
('BTN_ROLE_CREATE', '创建角色按钮', '/api/v1/roles', 'POST', 'BUTTON', '角色创建按钮权限'),
('BTN_ROLE_EDIT', '编辑角色按钮', '/api/v1/roles/*', 'PUT', 'BUTTON', '角色编辑按钮权限'),
('BTN_ROLE_DELETE', '删除角色按钮', '/api/v1/roles/*', 'DELETE', 'BUTTON', '角色删除按钮权限'),
('BTN_ROLE_VIEW', '查看角色按钮', '/api/v1/roles/*', 'GET', 'BUTTON', '查看角色详情按钮权限'),
('BTN_PERMISSION_CREATE', '创建权限按钮', '/api/v1/permissions', 'POST', 'BUTTON', '权限创建按钮权限'),
('BTN_PERMISSION_EDIT', '编辑权限按钮', '/api/v1/permissions/*', 'PUT', 'BUTTON', '权限编辑按钮权限'),
('BTN_PERMISSION_DELETE', '删除权限按钮', '/api/v1/permissions/*', 'DELETE', 'BUTTON', '权限删除按钮权限'),
('BTN_PERMISSION_VIEW', '查看权限按钮', '/api/v1/permissions/*', 'GET', 'BUTTON', '查看权限详情按钮权限'),
('BTN_WORKFLOW_CREATE', '创建工作流按钮', '/api/v1/workflows', 'POST', 'BUTTON', '工作流创建按钮权限'),
('BTN_WORKFLOW_EDIT', '编辑工作流按钮', '/api/v1/workflows/*', 'PUT', 'BUTTON', '工作流编辑按钮权限'),
('BTN_WORKFLOW_DELETE', '删除工作流按钮', '/api/v1/workflows/*', 'DELETE', 'BUTTON', '工作流删除按钮权限'),
('BTN_WORKFLOW_EXECUTE', '执行工作流按钮', '/api/v1/workflows/*/execute', 'POST', 'BUTTON', '执行工作流按钮权限'),
('BTN_DATA_EXPORT', '数据导出按钮', '/api/v1/export/*', 'POST', 'BUTTON', '数据导出按钮权限'),
('BTN_DATA_IMPORT', '数据导入按钮', '/api/v1/import/*', 'POST', 'BUTTON', '数据导入按钮权限');

-- ============================================================
-- 第三步：创建权限模板表
-- ============================================================

-- 3.1 创建权限模板表
CREATE TABLE IF NOT EXISTS permission_templates (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    role_level TINYINT NOT NULL COMMENT '角色等级：1-超级管理员，2-机构管理员，3-普通用户',
    permission_code VARCHAR(100) NOT NULL COMMENT '权限编码',
    permission_type ENUM('API', 'MENU', 'BUTTON') NOT NULL COMMENT '权限类型',
    is_required TINYINT DEFAULT 1 COMMENT '是否必需权限：1-是，0-否',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_role_level (role_level),
    INDEX idx_permission_type (permission_type),
    INDEX idx_permission_code (permission_code),
    UNIQUE KEY uk_role_permission (role_level, permission_code, permission_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='权限模板表';

-- 3.2 插入权限模板数据
INSERT INTO permission_templates (role_level, permission_code, permission_type, is_required) VALUES
-- 超级管理员权限模板（拥有所有权限）
(1, '*', 'API', 1),
(1, '*', 'MENU', 1),
(1, '*', 'BUTTON', 1),

-- 机构管理员权限模板 - API权限
(2, 'SYSTEM_HEALTH', 'API', 1),
(2, 'ORG_CREATE', 'API', 1),
(2, 'ORG_READ', 'API', 1),
(2, 'ORG_UPDATE', 'API', 1),
(2, 'ORG_DELETE', 'API', 1),
(2, 'ORG_LIST', 'API', 1),
(2, 'USER_CREATE', 'API', 1),
(2, 'USER_READ', 'API', 1),
(2, 'USER_UPDATE', 'API', 1),
(2, 'USER_DELETE', 'API', 1),
(2, 'USER_LIST', 'API', 1),
(2, 'ROLE_READ', 'API', 1),
(2, 'ROLE_LIST', 'API', 1),
(2, 'PERMISSION_READ', 'API', 1),
(2, 'PERMISSION_LIST', 'API', 1),
(2, 'AI_ASK', 'API', 1),
(2, 'AI_SQL_GENERATE', 'API', 1),
(2, 'AI_SQL_EXECUTE', 'API', 1),
(2, 'DB_INFO', 'API', 1),
(2, 'DB_SCHEMA', 'API', 1),

-- 机构管理员权限模板 - 菜单权限
(2, 'MENU_DASHBOARD', 'MENU', 1),
(2, 'MENU_WORKSPACE', 'MENU', 1),
(2, 'MENU_WORKSPACE_WORKBENCH', 'MENU', 1),
(2, 'MENU_WORKSPACE_REPORT', 'MENU', 1),
(2, 'MENU_WORKSPACE_MONITOR', 'MENU', 1),
(2, 'MENU_AI_ENGINE', 'MENU', 1),
(2, 'MENU_AI_ENGINE_ASK_DATA', 'MENU', 1),
(2, 'MENU_AI_ENGINE_KNOWLEDGE_BASE', 'MENU', 1),
(2, 'MENU_AI_ENGINE_DATASOURCE', 'MENU', 1),
(2, 'MENU_AI_ENGINE_LLMMANAGE', 'MENU', 1),
(2, 'MENU_AI_ENGINE_MULTIMODAL', 'MENU', 1),
(2, 'MENU_SYS', 'MENU', 1),
(2, 'MENU_SYS_USER', 'MENU', 1),
(2, 'MENU_SYS_ORG', 'MENU', 1),
(2, 'MENU_SYS_ROLE', 'MENU', 1),
(2, 'MENU_SYS_WORKFLOW', 'MENU', 1),
(2, 'MENU_SYS_MESSAGE', 'MENU', 1),

-- 机构管理员权限模板 - 按钮权限
(2, 'BTN_USER_CREATE', 'BUTTON', 1),
(2, 'BTN_USER_EDIT', 'BUTTON', 1),
(2, 'BTN_USER_DELETE', 'BUTTON', 1),
(2, 'BTN_USER_RESET_PWD', 'BUTTON', 1),
(2, 'BTN_USER_VIEW', 'BUTTON', 1),
(2, 'BTN_ORG_EDIT', 'BUTTON', 1),
(2, 'BTN_ORG_VIEW', 'BUTTON', 1),
(2, 'BTN_ROLE_VIEW', 'BUTTON', 1),
(2, 'BTN_WORKFLOW_CREATE', 'BUTTON', 1),
(2, 'BTN_WORKFLOW_EDIT', 'BUTTON', 1),
(2, 'BTN_WORKFLOW_DELETE', 'BUTTON', 1),
(2, 'BTN_WORKFLOW_EXECUTE', 'BUTTON', 1),
(2, 'BTN_DATA_EXPORT', 'BUTTON', 1),

-- 普通用户权限模板 - API权限
(3, 'SYSTEM_HEALTH', 'API', 1),
(3, 'USER_READ', 'API', 1),
(3, 'AI_ASK', 'API', 1),
(3, 'AI_SQL_GENERATE', 'API', 1),
(3, 'AI_SQL_EXECUTE', 'API', 1),
(3, 'DB_INFO', 'API', 1),
(3, 'DB_SCHEMA', 'API', 1),

-- 普通用户权限模板 - 菜单权限
(3, 'MENU_DASHBOARD', 'MENU', 1),
(3, 'MENU_WORKSPACE_WORKBENCH', 'MENU', 1),
(3, 'MENU_AI_ENGINE_ASK_DATA', 'MENU', 1),

-- 普通用户权限模板 - 按钮权限
(3, 'BTN_DATA_EXPORT', 'BUTTON', 0);

-- ============================================================
-- 第四步：为现有角色分配权限
-- ============================================================

-- 4.1 清理现有角色权限关联（重新分配）
DELETE FROM role_permissions;

-- 4.2 为超级管理员分配所有权限
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r, permissions p
WHERE r.role_code = 'SUPER_ADMIN' AND p.status = 1;

-- 4.3 为机构管理员分配权限（基于权限模板）
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r
JOIN permission_templates pt ON pt.role_level = 2
JOIN permissions p ON pt.permission_code = p.permission_code AND pt.permission_type = p.permission_type
WHERE r.role_code = 'ORG_ADMIN' AND p.status = 1;

-- 4.4 为普通用户分配权限（基于权限模板）
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r
JOIN permission_templates pt ON pt.role_level = 3
JOIN permissions p ON pt.permission_code = p.permission_code AND pt.permission_type = p.permission_type
WHERE r.role_code = 'NORMAL_USER' AND p.status = 1;

-- ============================================================
-- 第五步：创建辅助视图和函数
-- ============================================================

-- 5.1 创建角色权限视图
CREATE OR REPLACE VIEW v_role_permissions AS
SELECT 
    r.id as role_id,
    r.role_code,
    r.role_name,
    r.role_level,
    r.data_scope,
    p.permission_code,
    p.permission_name,
    p.permission_type,
    p.api_path,
    p.api_method
FROM roles r
JOIN role_permissions rp ON r.id = rp.role_id
JOIN permissions p ON rp.permission_id = p.id
WHERE r.status = 1 AND p.status = 1;

-- 5.2 创建用户权限视图
CREATE OR REPLACE VIEW v_user_permissions AS
SELECT 
    u.id as user_id,
    u.user_code,
    u.username,
    u.org_code,
    r.role_code,
    r.role_level,
    r.data_scope,
    p.permission_code,
    p.permission_name,
    p.permission_type,
    p.api_path,
    p.api_method
FROM users u
JOIN roles r ON u.role_id = r.id
JOIN role_permissions rp ON r.id = rp.role_id
JOIN permissions p ON rp.permission_id = p.id
WHERE u.status = 1 AND r.status = 1 AND p.status = 1;

-- ============================================================
-- 第六步：验证数据完整性
-- ============================================================

-- 验证角色表结构
SELECT 'roles表结构验证' as check_type, COUNT(*) as count FROM information_schema.columns 
WHERE table_schema = 'dataask' AND table_name = 'roles' AND column_name IN ('data_scope', 'is_system_role', 'menu_permissions', 'button_permissions');

-- 验证权限表结构
SELECT 'permissions表结构验证' as check_type, COUNT(*) as count FROM information_schema.columns 
WHERE table_schema = 'dataask' AND table_name = 'permissions' AND column_name IN ('permission_type', 'parent_code');

-- 验证权限模板表
SELECT 'permission_templates表记录数' as check_type, COUNT(*) as count FROM permission_templates;

-- 验证角色权限分配
SELECT 'SUPER_ADMIN权限数' as check_type, COUNT(*) as count FROM v_role_permissions WHERE role_code = 'SUPER_ADMIN';
SELECT 'ORG_ADMIN权限数' as check_type, COUNT(*) as count FROM v_role_permissions WHERE role_code = 'ORG_ADMIN';
SELECT 'NORMAL_USER权限数' as check_type, COUNT(*) as count FROM v_role_permissions WHERE role_code = 'NORMAL_USER';

-- 验证菜单和按钮权限
SELECT 'MENU权限数' as check_type, COUNT(*) as count FROM permissions WHERE permission_type = 'MENU';
SELECT 'BUTTON权限数' as check_type, COUNT(*) as count FROM permissions WHERE permission_type = 'BUTTON';
SELECT 'API权限数' as check_type, COUNT(*) as count FROM permissions WHERE permission_type = 'API';

-- ============================================================
-- 脚本执行完成
-- ============================================================
SELECT '数据库结构优化完成！' as message, NOW() as completion_time; 