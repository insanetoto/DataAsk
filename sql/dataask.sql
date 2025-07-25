-- ============================================================
-- 百惟数问 - 智能数据问答平台
-- 主数据库初始化脚本
-- ============================================================

-- 创建主数据库
CREATE DATABASE IF NOT EXISTS dataask CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE dataask;

-- ============================================================
-- 第一部分：基础表结构
-- ============================================================

-- 机构管理表
CREATE TABLE IF NOT EXISTS organizations (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    org_code VARCHAR(50) NOT NULL UNIQUE COMMENT '机构编码',
    org_name VARCHAR(200) NOT NULL COMMENT '机构名称',
    parent_org_code VARCHAR(50) NULL COMMENT '上级机构编码',
    level_depth INT DEFAULT 0 COMMENT '层级深度：0-顶级机构，1-二级机构，以此类推',
    level_path TEXT NULL COMMENT '层级路径，如：/ORG001/ORG001-01/ORG001-01-01/',
    contact_person VARCHAR(100) NOT NULL COMMENT '负责人姓名',
    contact_phone VARCHAR(20) NOT NULL COMMENT '负责人联系电话',
    contact_email VARCHAR(100) NOT NULL COMMENT '负责人邮箱',
    status TINYINT DEFAULT 1 COMMENT '状态：1-启用，0-禁用',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_org_code (org_code),
    INDEX idx_org_name (org_name),
    INDEX idx_parent_org_code (parent_org_code),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at),
    FOREIGN KEY (parent_org_code) REFERENCES organizations(org_code) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='机构管理表';

-- 角色表
CREATE TABLE IF NOT EXISTS roles (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    role_code VARCHAR(50) NOT NULL UNIQUE COMMENT '角色编码',
    role_name VARCHAR(100) NOT NULL COMMENT '角色名称',
    role_level TINYINT NOT NULL COMMENT '角色等级：1-超级管理员，2-机构管理员，3-普通用户',
    org_code VARCHAR(50) NULL COMMENT '所属机构编码（机构管理员专用）',
    description TEXT NULL COMMENT '角色描述',
    status TINYINT DEFAULT 1 COMMENT '状态：1-启用，0-禁用',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY uk_org_admin (org_code, role_level),
    INDEX idx_role_code (role_code),
    INDEX idx_role_level (role_level),
    INDEX idx_org_code (org_code),
    INDEX idx_status (status),
    FOREIGN KEY (org_code) REFERENCES organizations(org_code) ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='角色表';

-- 权限表
CREATE TABLE IF NOT EXISTS permissions (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    permission_code VARCHAR(100) NOT NULL UNIQUE COMMENT '权限编码',
    permission_name VARCHAR(100) NOT NULL COMMENT '权限名称',
    api_path VARCHAR(200) NOT NULL COMMENT 'API路径',
    api_method VARCHAR(10) NOT NULL COMMENT 'HTTP方法',
    resource_type VARCHAR(50) NULL COMMENT '资源类型',
    description TEXT NULL COMMENT '权限描述',
    status TINYINT DEFAULT 1 COMMENT '状态：1-启用，0-禁用',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_permission_code (permission_code),
    INDEX idx_api_path (api_path),
    INDEX idx_resource_type (resource_type),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='权限表';

-- 角色权限关联表
CREATE TABLE IF NOT EXISTS role_permissions (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    role_id BIGINT NOT NULL COMMENT '角色ID',
    permission_id BIGINT NOT NULL COMMENT '权限ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    UNIQUE KEY uk_role_permission (role_id, permission_id),
    INDEX idx_role_id (role_id),
    INDEX idx_permission_id (permission_id),
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,
    FOREIGN KEY (permission_id) REFERENCES permissions(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='角色权限关联表';

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    org_code VARCHAR(50) NOT NULL COMMENT '所属机构编码',
    user_code VARCHAR(50) NOT NULL UNIQUE COMMENT '用户编码',
    username VARCHAR(100) NOT NULL COMMENT '用户名称',
    password_hash VARCHAR(255) NOT NULL COMMENT '密码哈希',
    phone VARCHAR(20) NULL COMMENT '联系电话',
    address VARCHAR(500) NULL COMMENT '联系地址',
    role_id BIGINT NOT NULL COMMENT '角色ID',
    last_login_at TIMESTAMP NULL COMMENT '最后登录时间',
    login_count INT DEFAULT 0 COMMENT '登录次数',
    status TINYINT DEFAULT 1 COMMENT '状态：1-启用，0-禁用',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_user_code (user_code),
    INDEX idx_org_code (org_code),
    INDEX idx_username (username),
    INDEX idx_role_id (role_id),
    INDEX idx_status (status),
    FOREIGN KEY (org_code) REFERENCES organizations(org_code) ON UPDATE CASCADE,
    FOREIGN KEY (role_id) REFERENCES roles(id) ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

-- 用户会话表
CREATE TABLE IF NOT EXISTS user_sessions (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    user_id BIGINT NOT NULL COMMENT '用户ID',
    session_token VARCHAR(255) NOT NULL UNIQUE COMMENT '会话令牌',
    expires_at TIMESTAMP NOT NULL COMMENT '过期时间',
    ip_address VARCHAR(45) NULL COMMENT 'IP地址',
    user_agent TEXT NULL COMMENT '用户代理',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_user_id (user_id),
    INDEX idx_session_token (session_token),
    INDEX idx_expires_at (expires_at),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户会话表';

-- 操作审计表
CREATE TABLE IF NOT EXISTS operation_audit (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '审计记录ID',
    user_id INT NOT NULL COMMENT '操作用户ID',
    username VARCHAR(50) NOT NULL COMMENT '操作用户名',
    user_code VARCHAR(50) NOT NULL COMMENT '操作用户编码',
    org_code VARCHAR(50) NOT NULL COMMENT '操作用户机构编码',
    module VARCHAR(50) NOT NULL COMMENT '操作模块（user/org/role/permission）',
    operation VARCHAR(20) NOT NULL COMMENT '操作类型（create/update/delete/disable/enable）',
    target_type VARCHAR(50) NOT NULL COMMENT '目标对象类型',
    target_id VARCHAR(50) DEFAULT NULL COMMENT '目标对象ID',
    target_name VARCHAR(200) DEFAULT NULL COMMENT '目标对象名称',
    old_data TEXT COMMENT '操作前数据（JSON格式）',
    new_data TEXT COMMENT '操作后数据（JSON格式）',
    operation_desc VARCHAR(500) DEFAULT NULL COMMENT '操作描述',
    ip_address VARCHAR(45) DEFAULT NULL COMMENT '操作IP地址',
    user_agent VARCHAR(500) DEFAULT NULL COMMENT '用户代理信息',
    request_id VARCHAR(100) DEFAULT NULL COMMENT '请求ID',
    operation_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '操作时间',
    result VARCHAR(20) NOT NULL DEFAULT 'success' COMMENT '操作结果（success/failure）',
    error_message TEXT COMMENT '错误信息（操作失败时）',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (id),
    KEY idx_user_id (user_id),
    KEY idx_operation_time (operation_time),
    KEY idx_module_operation (module, operation),
    KEY idx_target (target_type, target_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='操作审计表';

-- ============================================================
-- 第二部分：初始化基础数据
-- ============================================================

-- 插入基础机构数据
INSERT INTO organizations (org_code, parent_org_code, org_name, contact_person, contact_phone, contact_email, level_depth, level_path) VALUES
('05', NULL, '集团总部', '集团总经理', '13800000001', 'group@example.com', 0, '/05/'),
('0501', '05', '省公司', '省公司总经理', '13800000002', 'province@example.com', 1, '/05/0501/'),
('050101', '0501', '科数部', '科数部主任', '13800000003', 'tech@example.com', 2, '/05/0501/050101/');

-- 插入默认角色
INSERT INTO roles (role_code, role_name, role_level, description) VALUES
('SUPER_ADMIN', '超级系统管理员', 1, '系统最高管理员，拥有所有权限'),
('ORG_ADMIN', '机构管理员', 2, '机构管理员，管理本机构用户和数据'),
('NORMAL_USER', '普通用户', 3, '普通用户，具有基本查询权限');

-- 插入默认权限
INSERT INTO permissions (permission_code, permission_name, api_path, api_method, resource_type, description) VALUES
-- 系统管理权限
('SYSTEM_HEALTH', '系统健康检查', '/api/v1/health', 'GET', 'system', '查看系统健康状态'),
('SYSTEM_CACHE_CLEAR', '清除系统缓存', '/api/v1/cache/clear', 'POST', 'system', '清除系统缓存'),

-- 机构管理权限
('ORG_CREATE', '创建机构', '/api/v1/organizations', 'POST', 'organization', '创建新机构'),
('ORG_READ', '查看机构', '/api/v1/organizations/*', 'GET', 'organization', '查看机构信息'),
('ORG_UPDATE', '更新机构', '/api/v1/organizations/*', 'PUT', 'organization', '更新机构信息'),
('ORG_DELETE', '删除机构', '/api/v1/organizations/*', 'DELETE', 'organization', '删除机构'),
('ORG_LIST', '机构列表', '/api/v1/organizations', 'GET', 'organization', '查看机构列表'),

-- 用户管理权限
('USER_CREATE', '创建用户', '/api/v1/users', 'POST', 'user', '创建新用户'),
('USER_READ', '查看用户', '/api/v1/users/*', 'GET', 'user', '查看用户信息'),
('USER_UPDATE', '更新用户', '/api/v1/users/*', 'PUT', 'user', '更新用户信息'),
('USER_DELETE', '删除用户', '/api/v1/users/*', 'DELETE', 'user', '删除用户'),
('USER_LIST', '用户列表', '/api/v1/users', 'GET', 'user', '查看用户列表'),

-- 角色管理权限
('ROLE_CREATE', '创建角色', '/api/v1/roles', 'POST', 'role', '创建新角色'),
('ROLE_READ', '查看角色', '/api/v1/roles/*', 'GET', 'role', '查看角色信息'),
('ROLE_UPDATE', '更新角色', '/api/v1/roles/*', 'PUT', 'role', '更新角色信息'),
('ROLE_DELETE', '删除角色', '/api/v1/roles/*', 'DELETE', 'role', '删除角色'),
('ROLE_LIST', '角色列表', '/api/v1/roles', 'GET', 'role', '查看角色列表'),

-- 权限管理权限
('PERMISSION_READ', '查看权限', '/api/v1/permissions/*', 'GET', 'permission', '查看权限信息'),
('PERMISSION_LIST', '权限列表', '/api/v1/permissions', 'GET', 'permission', '查看权限列表'),

-- AI问答权限
('AI_ASK', 'AI问答', '/api/v1/ask', 'POST', 'ai', 'AI智能问答'),
('AI_SQL_GENERATE', 'SQL生成', '/api/v1/generate_sql', 'POST', 'ai', '生成SQL语句'),
('AI_SQL_EXECUTE', 'SQL执行', '/api/v1/execute_sql', 'POST', 'ai', '执行SQL语句'),
('AI_TRAIN', 'AI训练', '/api/v1/train', 'POST', 'ai', 'AI模型训练'),
('AI_AUTO_TRAIN', 'AI自动训练', '/api/v1/auto_train', 'POST', 'ai', 'AI自动训练'),

-- 数据库管理权限
('DB_INFO', '数据库信息', '/api/v1/database/info', 'GET', 'database', '查看数据库信息'),
('DB_SCHEMA', '数据库架构', '/api/v1/database/schema', 'GET', 'database', '查看数据库架构');

-- 为超级管理员分配所有权限
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r, permissions p
WHERE r.role_code = 'SUPER_ADMIN';

-- 为机构管理员分配基本权限
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r, permissions p
WHERE r.role_code = 'ORG_ADMIN'
AND p.permission_code IN (
    'SYSTEM_HEALTH',
    'ORG_READ', 'ORG_UPDATE', 'ORG_LIST',
    'USER_CREATE', 'USER_READ', 'USER_UPDATE', 'USER_DELETE', 'USER_LIST',
    'ROLE_READ', 'ROLE_LIST',
    'PERMISSION_READ', 'PERMISSION_LIST',
    'AI_ASK', 'AI_SQL_GENERATE', 'AI_SQL_EXECUTE',
    'DB_INFO', 'DB_SCHEMA'
);

-- 为普通用户分配基础权限
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r, permissions p
WHERE r.role_code = 'NORMAL_USER'
AND p.permission_code IN (
    'SYSTEM_HEALTH',
    'USER_READ',
    'AI_ASK', 'AI_SQL_GENERATE', 'AI_SQL_EXECUTE',
    'DB_INFO', 'DB_SCHEMA'
);

-- 创建默认超级管理员用户（密码：admin123）
INSERT INTO users (org_code, user_code, username, password_hash, role_id, phone, address) 
SELECT '05', 'admin', '超级管理员', 
       '$2b$12$LQv3c1yqBW/BaJv0p1vZPej7eGCZHU5ZZ5ZXzT8Q7Q9Y1F2YGS5b.', -- admin123的bcrypt哈希
       r.id, '13800000000', '系统默认地址'
FROM roles r 
WHERE r.role_code = 'SUPER_ADMIN'
LIMIT 1;

-- ============================================================
-- 第三部分：创建视图和函数
-- ============================================================

-- 创建视图：机构层级关系视图
CREATE OR REPLACE VIEW v_organization_hierarchy AS
SELECT 
    child.id,
    child.org_code,
    child.org_name,
    child.parent_org_code,
    parent.org_name AS parent_org_name,
    child.level_depth,
    child.level_path,
    child.contact_person,
    child.contact_phone,
    child.contact_email,
    child.status,
    child.created_at,
    child.updated_at
FROM organizations child
LEFT JOIN organizations parent ON child.parent_org_code = parent.org_code
ORDER BY child.level_path, child.org_code;

-- 创建函数：计算机构层级深度
DELIMITER $$
CREATE FUNCTION CalculateOrgDepth(org_code_param VARCHAR(50)) 
RETURNS INT
READS SQL DATA
DETERMINISTIC
BEGIN
    DECLARE depth INT DEFAULT 0;
    DECLARE current_parent VARCHAR(50);
    
    SELECT parent_org_code INTO current_parent 
    FROM organizations 
    WHERE org_code = org_code_param;
    
    WHILE current_parent IS NOT NULL DO
        SET depth = depth + 1;
        SELECT parent_org_code INTO current_parent 
        FROM organizations 
        WHERE org_code = current_parent;
    END WHILE;
    
    RETURN depth;
END$$
DELIMITER ;

-- 创建触发器：自动维护层级信息
DELIMITER $$
CREATE TRIGGER tr_organizations_level_update
    BEFORE INSERT ON organizations
    FOR EACH ROW
BEGIN
    -- 自动计算层级深度
    IF NEW.parent_org_code IS NOT NULL THEN
        SET NEW.level_depth = CalculateOrgDepth(NEW.org_code);
        
        -- 自动生成层级路径
        SELECT CONCAT(level_path, NEW.org_code, '/') INTO NEW.level_path
        FROM organizations 
        WHERE org_code = NEW.parent_org_code;
    ELSE
        SET NEW.level_depth = 0;
        SET NEW.level_path = CONCAT('/', NEW.org_code, '/');
    END IF;
END$$
DELIMITER ; 