USE dataask;

-- 清空现有数据
DELETE FROM user_sessions;
DELETE FROM users;
DELETE FROM role_permissions;
DELETE FROM roles;
DELETE FROM organizations;

-- 重置自增ID
ALTER TABLE users AUTO_INCREMENT = 1;
ALTER TABLE user_sessions AUTO_INCREMENT = 1;
ALTER TABLE roles AUTO_INCREMENT = 1;
ALTER TABLE organizations AUTO_INCREMENT = 1;

-- 插入测试机构数据
INSERT INTO organizations (org_code, org_name, contact_person, contact_phone, contact_email) VALUES 
('05', '测试总部', '张三', '13800138001', 'zhangsan@test.com'),
('0501', '测试分部', '李四', '13800138002', 'lisi@test.com'),
('050101', '测试部门', '王五', '13800138003', 'wangwu@test.com');

-- 插入测试角色数据
INSERT INTO roles (role_code, role_name, role_level, org_code, description) VALUES
('SUPER_ADMIN', '超级管理员', 1, '05', '系统超级管理员'),
('ORG_ADMIN', '机构管理员', 2, '0501', '机构管理员'),
('NORMAL_USER', '普通用户', 3, '050101', '普通用户');

-- 插入测试用户数据
INSERT INTO users (org_code, user_code, username, password_hash, phone, role_id, status) VALUES
('05', 'superadmin', 'superadmin', 'superadmin123', '13900000001', 
(SELECT id FROM roles WHERE role_code = 'SUPER_ADMIN'), 1),
('0501', 'admin', 'admin', 'admin123', '13900000002', 
(SELECT id FROM roles WHERE role_code = 'ORG_ADMIN'), 1),
('0501', 'test', 'test', 'test123', '13900000003', 
(SELECT id FROM roles WHERE role_code = 'NORMAL_USER'), 1),
('0501', 'user', 'user', 'user123', '13900000004', 
(SELECT id FROM roles WHERE role_code = 'NORMAL_USER'), 1); 