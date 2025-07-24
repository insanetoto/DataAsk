-- Text2SQL会话管理相关表
USE vanna;

-- 删除现有的表（如果存在）
DROP TABLE IF EXISTS `text2sql_session_history`;
DROP TABLE IF EXISTS `text2sql_sessions`;

-- Text2SQL会话表
CREATE TABLE IF NOT EXISTS `text2sql_sessions` (
  `id` varchar(36) NOT NULL DEFAULT (uuid()) COMMENT '会话ID',
  `user_id` int NOT NULL COMMENT '用户ID',
  `title` varchar(200) NOT NULL DEFAULT '新的Text2SQL对话' COMMENT '会话标题',
  `status` enum('active','archived','deleted') NOT NULL DEFAULT 'active' COMMENT '状态',
  `last_question` varchar(500) DEFAULT NULL COMMENT '最后一次提问',
  `last_sql` text DEFAULT NULL COMMENT '最后一次生成的SQL',
  `question_count` int DEFAULT 0 COMMENT '提问次数',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_status` (`status`),
  KEY `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Text2SQL会话表';

-- Text2SQL会话历史记录表
CREATE TABLE IF NOT EXISTS `text2sql_session_history` (
  `id` varchar(36) NOT NULL DEFAULT (uuid()) COMMENT '历史记录ID',
  `session_id` varchar(36) NOT NULL COMMENT '会话ID',
  `user_id` int NOT NULL COMMENT '用户ID',
  `question` varchar(500) NOT NULL COMMENT '用户问题',
  `generated_sql` text NOT NULL COMMENT '生成的SQL',
  `execution_result` json DEFAULT NULL COMMENT '执行结果',
  `confidence` decimal(3,2) DEFAULT 0.00 COMMENT '置信度',
  `execution_time` int DEFAULT 0 COMMENT '执行时间(毫秒)',
  `status` enum('success','failed') NOT NULL DEFAULT 'success' COMMENT '状态',
  `error_message` text DEFAULT NULL COMMENT '错误信息',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_session_id` (`session_id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_created_at` (`created_at`),
  FOREIGN KEY (`session_id`) REFERENCES `text2sql_sessions` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Text2SQL会话历史记录表'; 