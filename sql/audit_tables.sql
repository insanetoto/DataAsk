-- 操作审计表
DROP TABLE IF EXISTS `operation_audit`;
CREATE TABLE `operation_audit` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '审计记录ID',
  `user_id` int NOT NULL COMMENT '操作用户ID',
  `username` varchar(50) NOT NULL COMMENT '操作用户名',
  `user_code` varchar(50) NOT NULL COMMENT '操作用户编码',
  `org_code` varchar(50) NOT NULL COMMENT '操作用户机构编码',
  `module` varchar(50) NOT NULL COMMENT '操作模块（user/org/role/permission）',
  `operation` varchar(20) NOT NULL COMMENT '操作类型（create/update/delete/disable/enable）',
  `target_type` varchar(50) NOT NULL COMMENT '目标对象类型',
  `target_id` varchar(50) DEFAULT NULL COMMENT '目标对象ID',
  `target_name` varchar(200) DEFAULT NULL COMMENT '目标对象名称',
  `old_data` text COMMENT '操作前数据（JSON格式）',
  `new_data` text COMMENT '操作后数据（JSON格式）',
  `operation_desc` varchar(500) DEFAULT NULL COMMENT '操作描述',
  `ip_address` varchar(45) DEFAULT NULL COMMENT '操作IP地址',
  `user_agent` varchar(500) DEFAULT NULL COMMENT '用户代理信息',
  `request_id` varchar(100) DEFAULT NULL COMMENT '请求ID',
  `operation_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '操作时间',
  `result` varchar(20) NOT NULL DEFAULT 'success' COMMENT '操作结果（success/failure）',
  `error_message` text COMMENT '错误信息（操作失败时）',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_operation_time` (`operation_time`),
  KEY `idx_module_operation` (`module`, `operation`),
  KEY `idx_target` (`target_type`, `target_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='操作审计表';

-- 审计表分区（按月分区，提高查询性能）
-- ALTER TABLE operation_audit PARTITION BY RANGE (YEAR(operation_time) * 100 + MONTH(operation_time)) (
--   PARTITION p202501 VALUES LESS THAN (202502),
--   PARTITION p202502 VALUES LESS THAN (202503),
--   PARTITION p202503 VALUES LESS THAN (202504),
--   PARTITION p202504 VALUES LESS THAN (202505),
--   PARTITION p202505 VALUES LESS THAN (202506),
--   PARTITION p202506 VALUES LESS THAN (202507),
--   PARTITION p202507 VALUES LESS THAN (202508),
--   PARTITION p202508 VALUES LESS THAN (202509),
--   PARTITION p202509 VALUES LESS THAN (202510),
--   PARTITION p202510 VALUES LESS THAN (202511),
--   PARTITION p202511 VALUES LESS THAN (202512),
--   PARTITION p202512 VALUES LESS THAN (202513),
--   PARTITION p_future VALUES LESS THAN MAXVALUE
-- ); 