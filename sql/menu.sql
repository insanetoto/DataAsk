-- 创建菜单表
CREATE TABLE IF NOT EXISTS `sys_menu` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '菜单ID',
  `parent_id` int(11) DEFAULT 0 COMMENT '父菜单ID',
  `name` varchar(50) NOT NULL COMMENT '菜单名称',
  `path` varchar(200) DEFAULT '' COMMENT '路由地址',
  `component` varchar(255) DEFAULT '' COMMENT '组件路径',
  `type` char(1) DEFAULT '' COMMENT '菜单类型（M目录 C菜单 F按钮）',
  `icon` varchar(100) DEFAULT '#' COMMENT '菜单图标',
  `order_num` int(4) DEFAULT 0 COMMENT '显示顺序',
  `status` tinyint(1) DEFAULT 1 COMMENT '菜单状态（1正常 0停用）',
  `perms` varchar(100) DEFAULT NULL COMMENT '权限标识',
  `is_frame` tinyint(1) DEFAULT 1 COMMENT '是否为外链（1是 0否）',
  `visible` tinyint(1) DEFAULT 1 COMMENT '显示状态（1显示 0隐藏）',
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `remark` varchar(500) DEFAULT '' COMMENT '备注',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='菜单权限表';

-- 清空原有菜单数据
TRUNCATE TABLE `sys_menu`;

-- 插入更新后的菜单数据
INSERT INTO `sys_menu` (`parent_id`, `name`, `path`, `component`, `type`, `icon`, `order_num`, `status`, `perms`, `visible`) VALUES
-- 百惟数问主菜单
(0, '百惟数问', '/dataask', '', 'M', 'home', 1, 1, 'dataask:view', 1),
(1, '监控台', '/monitor', '', 'M', 'dashboard', 1, 1, 'monitor:view', 1),
(2, 'AI监控大屏', '/dashboard', 'dashboard/dashboard', 'C', 'bar-chart', 1, 1, 'dashboard:view', 1),
(1, '工作台', '/workspace', '', 'M', 'appstore', 2, 1, 'workspace:view', 1),
(4, '工作区', 'workbench', 'workspace/workbench/workbench', 'C', 'laptop', 1, 1, 'workspace:workbench:view', 1),
(4, '报表', 'report', 'workspace/report/report', 'C', 'bar-chart', 2, 1, 'workspace:report:view', 1),

-- AI引擎
(0, 'AI引擎', '/ai-engine', '', 'M', 'robot', 2, 1, 'ai-engine:view', 1),
(7, 'AI问答', 'ask-data', 'ai-engine/ask-data/ask-data', 'C', 'message', 1, 1, 'ai-engine:ask-data:view', 1),
(7, '知识库', 'knowledge-base', 'ai-engine/knowledge-base/knowledge-base', 'C', 'database', 2, 1, 'ai-engine:knowledge-base:view', 1),

-- 系统管理
(0, '系统管理', '/sys', '', 'M', 'setting', 3, 1, 'sys:view', 1),
(10, '用户管理', 'user', 'sys/user/user', 'C', 'user', 1, 1, 'sys:user:view', 1),
(10, '机构管理', 'org', 'sys/org/org', 'C', 'cluster', 2, 1, 'sys:org:view', 1),
(10, '角色管理', 'role', 'sys/role/role', 'C', 'team', 3, 1, 'sys:role:view', 1),
(10, '权限管理', 'permission', 'sys/permission/permission', 'C', 'safety', 4, 1, 'sys:permission:view', 1);

-- 创建用户菜单关联表
CREATE TABLE IF NOT EXISTS `sys_user_menu` (
  `user_id` int(11) NOT NULL COMMENT '用户ID',
  `menu_id` int(11) NOT NULL COMMENT '菜单ID',
  PRIMARY KEY (`user_id`,`menu_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户和菜单关联表';

-- 清空用户菜单关联数据
TRUNCATE TABLE `sys_user_menu`;

-- 为超级管理员分配所有菜单
INSERT INTO `sys_user_menu` (user_id, menu_id)
SELECT 1, id FROM sys_menu; 