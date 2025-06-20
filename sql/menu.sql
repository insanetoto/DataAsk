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

-- 插入初始菜单数据
INSERT INTO `sys_menu` (`parent_id`, `name`, `path`, `component`, `type`, `icon`, `order_num`, `status`, `perms`, `visible`) VALUES
(0, '工作台', '/workspace', '', 'M', 'dashboard', 1, 1, 'workspace:view', 1),
(1, '仪表盘', 'dashboard', 'workspace/dashboard', 'C', 'fund', 1, 1, 'workspace:dashboard:view', 1),
(1, '工作区', 'workplace', 'workspace/workplace', 'C', 'appstore', 2, 1, 'workspace:workplace:view', 1),
(1, '报表', 'report', 'workspace/report', 'C', 'bar-chart', 3, 1, 'workspace:report:view', 1),
(0, 'AI工作区', '/ai-workspace', '', 'M', 'robot', 2, 1, 'ai:view', 1),
(0, '系统管理', '/sys', '', 'M', 'setting', 3, 1, 'sys:view', 1),
(6, '用户管理', 'user', 'sys/user', 'C', 'user', 1, 1, 'sys:user:view', 1),
(6, '角色管理', 'role', 'sys/role', 'C', 'team', 2, 1, 'sys:role:view', 1),
(6, '权限管理', 'permission', 'sys/permission', 'C', 'safety', 3, 1, 'sys:permission:view', 1),
(6, '组织管理', 'org', 'sys/org', 'C', 'cluster', 4, 1, 'sys:org:view', 1);

-- 创建用户菜单关联表
CREATE TABLE IF NOT EXISTS `sys_user_menu` (
  `user_id` int(11) NOT NULL COMMENT '用户ID',
  `menu_id` int(11) NOT NULL COMMENT '菜单ID',
  PRIMARY KEY (`user_id`,`menu_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户和菜单关联表';

-- 为超级管理员分配所有菜单
INSERT INTO `sys_user_menu` (user_id, menu_id)
SELECT 1, id FROM sys_menu; 