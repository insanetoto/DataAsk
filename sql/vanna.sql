-- ============================================================
-- 百惟数问 - 智能数据问答平台
-- Vanna AI引擎数据库初始化脚本
-- ============================================================

-- 创建Vanna AI专用数据库
CREATE DATABASE IF NOT EXISTS vanna CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE vanna;

-- ============================================================
-- 第一部分：基础表结构
-- ============================================================

-- AI训练记录表
CREATE TABLE IF NOT EXISTS ai_training_records (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    training_type ENUM('ddl', 'documentation', 'question_sql') NOT NULL COMMENT '训练类型',
    content TEXT NOT NULL COMMENT '训练内容',
    question VARCHAR(500) NULL COMMENT '问题（仅question_sql类型）',
    sql_statement TEXT NULL COMMENT 'SQL语句（仅question_sql类型）',
    status TINYINT DEFAULT 1 COMMENT '状态：1-有效，0-无效',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_training_type (training_type),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='AI训练记录表';

-- 问答历史记录表
CREATE TABLE IF NOT EXISTS qa_history (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    question VARCHAR(500) NOT NULL COMMENT '用户问题',
    generated_sql TEXT NULL COMMENT '生成的SQL',
    execution_result JSON NULL COMMENT '执行结果',
    confidence DECIMAL(3,2) DEFAULT 0.00 COMMENT '置信度',
    success TINYINT DEFAULT 0 COMMENT '是否成功：1-成功，0-失败',
    error_message TEXT NULL COMMENT '错误信息',
    execution_time INT DEFAULT 0 COMMENT '执行时间（毫秒）',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_question (question(100)),
    INDEX idx_success (success),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='问答历史记录表';

-- SQL生成统计表
CREATE TABLE IF NOT EXISTS sql_generation_stats (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    date_key DATE NOT NULL COMMENT '日期',
    total_requests INT DEFAULT 0 COMMENT '总请求数',
    successful_requests INT DEFAULT 0 COMMENT '成功请求数',
    failed_requests INT DEFAULT 0 COMMENT '失败请求数',
    avg_confidence DECIMAL(3,2) DEFAULT 0.00 COMMENT '平均置信度',
    avg_execution_time INT DEFAULT 0 COMMENT '平均执行时间（毫秒）',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY uk_date (date_key),
    INDEX idx_date (date_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='SQL生成统计表';

-- Text2SQL会话表
CREATE TABLE IF NOT EXISTS `text2sql_sessions` (
  `id` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT (uuid()),
  `user_id` int NOT NULL,
  `title` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '新的Text2SQL对话',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `is_deleted` tinyint(1) DEFAULT '0',
  PRIMARY KEY (`id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Text2SQL会话表';

-- Text2SQL消息表
CREATE TABLE IF NOT EXISTS `text2sql_messages` (
  `id` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT (uuid()),
  `session_id` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL,
  `user_id` int NOT NULL,
  `message_type` enum('user','assistant','system') COLLATE utf8mb4_unicode_ci NOT NULL,
  `content` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `sql_query` text COLLATE utf8mb4_unicode_ci,
  `query_result` json DEFAULT NULL,
  `confidence_score` decimal(3,2) DEFAULT NULL,
  `execution_time` int DEFAULT NULL COMMENT '执行时间(毫秒)',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_session_id` (`session_id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_created_at` (`created_at`),
  CONSTRAINT `text2sql_messages_ibfk_1` FOREIGN KEY (`session_id`) REFERENCES `text2sql_sessions` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Text2SQL消息表';

-- ============================================================
-- 第二部分：初始化基础数据
-- ============================================================

-- 插入初始示例训练数据
INSERT INTO ai_training_records (training_type, content) VALUES
('ddl', 'CREATE TABLE users (id INT PRIMARY KEY, name VARCHAR(100), email VARCHAR(255), created_at TIMESTAMP)'),
('ddl', 'CREATE TABLE orders (id INT PRIMARY KEY, user_id INT, amount DECIMAL(10,2), status VARCHAR(20), created_at TIMESTAMP)'),
('documentation', '用户表包含用户的基本信息，包括姓名和邮箱。订单表记录用户的购买订单，包含金额和状态信息。');

-- 创建示例问答记录
INSERT INTO qa_history (question, generated_sql, success, confidence) VALUES
('查询用户总数', 'SELECT COUNT(*) as total_users FROM users', 1, 0.95),
('查询今天的订单数量', 'SELECT COUNT(*) as today_orders FROM orders WHERE DATE(created_at) = CURDATE()', 1, 0.88);

-- 初始化统计数据
INSERT INTO sql_generation_stats (date_key, total_requests, successful_requests, failed_requests) VALUES
(CURDATE(), 0, 0, 0); 