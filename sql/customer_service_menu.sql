-- 客服服务模块菜单数据
-- 为 DataAsk 系统添加客服服务功能菜单

-- 插入客服服务主菜单
INSERT INTO `sys_menu` (`parent_id`, `name`, `path`, `component`, `type`, `icon`, `order_num`, `status`, `perms`, `visible`) VALUES
-- 客服服务主菜单 (插入在AI引擎和系统管理之间)
(1, '客服服务', '/customer-service', '', 'M', 'team', 4, 1, 'customer-service:view', 1);

-- 获取刚插入的客服服务主菜单ID
SET @customer_service_menu_id = LAST_INSERT_ID();

-- 插入客服服务子菜单
INSERT INTO `sys_menu` (`parent_id`, `name`, `path`, `component`, `type`, `icon`, `order_num`, `status`, `perms`, `visible`) VALUES
-- 客服仪表板
(@customer_service_menu_id, '客服仪表板', 'dashboard', 'customer-service/service-dashboard/service-dashboard', 'C', 'dashboard', 1, 1, 'customer-service:dashboard:view', 1),
-- 客服工作台  
(@customer_service_menu_id, '客服工作台', 'workbench', 'customer-service/service-workbench/service-workbench', 'C', 'monitor', 2, 1, 'customer-service:workbench:view', 1),
-- 服务工单详情
(@customer_service_menu_id, '服务工单详情', 'order-detail', 'customer-service/service-order-detail/service-order-detail', 'C', 'file-text', 3, 1, 'customer-service:order-detail:view', 1);

-- 更新系统管理菜单的排序号，使其排在客服服务之后
UPDATE `sys_menu` SET `order_num` = 5 WHERE `parent_id` = 1 AND `name` = '系统管理';

-- 为超级管理员(user_id=1)分配新的客服服务菜单权限
INSERT INTO `sys_user_menu` (user_id, menu_id)
SELECT 1, id FROM sys_menu 
WHERE name IN ('客服服务', '客服仪表板', '客服工作台', '服务工单详情')
ON DUPLICATE KEY UPDATE user_id = user_id;

-- 验证插入结果
SELECT m.id, m.parent_id, m.name, m.path, m.component, m.type, m.icon, m.order_num
FROM sys_menu m
WHERE m.name IN ('客服服务', '客服仪表板', '客服工作台', '服务工单详情')
ORDER BY m.parent_id, m.order_num; 