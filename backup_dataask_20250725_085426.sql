-- MySQL dump 10.13  Distrib 8.0.42, for Linux (aarch64)
--
-- Host: localhost    Database: dataask
-- ------------------------------------------------------
-- Server version	8.0.42

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `enhanced_workflows`
--

DROP TABLE IF EXISTS `enhanced_workflows`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `enhanced_workflows` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '工作流ID',
  `workspace_id` bigint NOT NULL COMMENT '所属工作域ID',
  `category_id` bigint NOT NULL COMMENT '所属分类ID',
  `name` varchar(200) NOT NULL COMMENT '工作流名称',
  `code` varchar(100) NOT NULL COMMENT '工作流代码',
  `description` text COMMENT '工作流描述',
  `version` varchar(20) DEFAULT '1.0.0' COMMENT '版本号',
  `type` enum('sequential','parallel','conditional','loop') DEFAULT 'sequential' COMMENT '流程类型',
  `trigger_type` enum('manual','automatic','scheduled','event') DEFAULT 'manual' COMMENT '触发方式',
  `status` enum('draft','active','inactive','disabled','archived') NOT NULL DEFAULT 'draft' COMMENT '状态',
  `priority` enum('low','normal','high','urgent') DEFAULT 'normal' COMMENT '优先级',
  `dag_id` varchar(200) NOT NULL COMMENT 'Airflow DAG ID',
  `config` json DEFAULT NULL COMMENT '工作流配置(JSON格式)',
  `variables` json DEFAULT NULL COMMENT '工作流变量',
  `schedule_expression` varchar(100) DEFAULT NULL COMMENT '调度表达式(Cron)',
  `timeout_minutes` int DEFAULT '60' COMMENT '超时时间(分钟)',
  `retry_count` int DEFAULT '1' COMMENT '重试次数',
  `retry_delay_minutes` int DEFAULT '5' COMMENT '重试间隔(分钟)',
  `auto_rollback` tinyint(1) DEFAULT '0' COMMENT '是否自动回滚',
  `notification_enabled` tinyint(1) DEFAULT '1' COMMENT '是否启用通知',
  `notification_config` json DEFAULT NULL COMMENT '通知配置',
  `creator_id` bigint NOT NULL COMMENT '创建人ID',
  `updater_id` bigint DEFAULT NULL COMMENT '最后修改人ID',
  `published_at` timestamp NULL DEFAULT NULL COMMENT '发布时间',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_workflow_code_workspace` (`code`,`workspace_id`),
  UNIQUE KEY `uk_dag_id` (`dag_id`),
  KEY `idx_workflow_workspace` (`workspace_id`),
  KEY `idx_workflow_category` (`category_id`),
  KEY `idx_workflow_status` (`status`),
  KEY `idx_workflow_type` (`type`),
  KEY `idx_workflow_creator` (`creator_id`),
  CONSTRAINT `enhanced_workflows_ibfk_1` FOREIGN KEY (`workspace_id`) REFERENCES `workflow_workspaces` (`id`) ON DELETE CASCADE,
  CONSTRAINT `enhanced_workflows_ibfk_2` FOREIGN KEY (`category_id`) REFERENCES `workflow_categories` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='增强版工作流定义表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `enhanced_workflows`
--

LOCK TABLES `enhanced_workflows` WRITE;
/*!40000 ALTER TABLE `enhanced_workflows` DISABLE KEYS */;
/*!40000 ALTER TABLE `enhanced_workflows` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `operation_audit`
--

DROP TABLE IF EXISTS `operation_audit`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `operation_audit` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '审计记录ID',
  `user_id` int NOT NULL COMMENT '操作用户ID',
  `username` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '操作用户名',
  `user_code` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '操作用户编码',
  `org_code` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '操作用户机构编码',
  `module` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '操作模块（user/org/role/permission）',
  `operation` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '操作类型（create/update/delete/disable/enable）',
  `target_type` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '目标对象类型',
  `target_id` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '目标对象ID',
  `target_name` varchar(200) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '目标对象名称',
  `old_data` text COLLATE utf8mb4_unicode_ci COMMENT '操作前数据（JSON格式）',
  `new_data` text COLLATE utf8mb4_unicode_ci COMMENT '操作后数据（JSON格式）',
  `operation_desc` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '操作描述',
  `ip_address` varchar(45) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '操作IP地址',
  `user_agent` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '用户代理信息',
  `request_id` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '请求ID',
  `operation_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '操作时间',
  `result` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'success' COMMENT '操作结果（success/failure）',
  `error_message` text COLLATE utf8mb4_unicode_ci COMMENT '错误信息（操作失败时）',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_operation_time` (`operation_time`),
  KEY `idx_module_operation` (`module`,`operation`),
  KEY `idx_target` (`target_type`,`target_id`)
) ENGINE=InnoDB AUTO_INCREMENT=32 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='操作审计表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `operation_audit`
--

LOCK TABLES `operation_audit` WRITE;
/*!40000 ALTER TABLE `operation_audit` DISABLE KEYS */;
INSERT INTO `operation_audit` VALUES (1,2,'admin','admin','0501','user','update','user','4','testuser','{\"id\": 4, \"org_code\": \"0501\", \"user_code\": \"testuser\", \"username\": \"testuser\", \"role_id\": 3, \"role_code\": \"NORMAL_USER\", \"org_name\": \"测试分部\", \"status\": 0, \"created_at\": \"2025-07-04 01:25:49\", \"updated_at\": \"2025-07-04 01:51:11\"}','{\"id\": 4, \"org_code\": \"0501\", \"user_code\": \"testuser\", \"username\": \"testuser\", \"role_id\": 3, \"role_code\": \"NORMAL_USER\", \"org_name\": \"测试分部\", \"status\": 1, \"created_at\": \"2025-07-04 01:25:49\", \"updated_at\": \"2025-07-04 01:52:14\"}','更新用户: testuser','127.0.0.1','curl/8.7.1','ec61dcfb-5494-4aa6-ba16-cc09bceec489','2025-07-04 09:52:14','success',NULL,'2025-07-04 01:52:14'),(2,2,'admin','admin','0501','user','delete','user','4','testuser','{\"id\": 4, \"org_code\": \"0501\", \"user_code\": \"testuser\", \"username\": \"testuser\", \"role_id\": 3, \"role_code\": \"NORMAL_USER\", \"org_name\": \"测试分部\", \"status\": 1, \"created_at\": \"2025-07-04 01:25:49\", \"updated_at\": \"2025-07-04 01:52:14\"}',NULL,'永久删除用户: testuser','127.0.0.1','curl/8.7.1','a1251128-6bfb-44f3-8dba-68e757fb8092','2025-07-04 09:53:52','success',NULL,'2025-07-04 01:53:52'),(3,2,'admin','admin','0501','user','create','user','5','测试用户001',NULL,'{\"id\": 5, \"org_code\": \"0501\", \"user_code\": \"testuser001\", \"username\": \"测试用户001\", \"role_id\": 3, \"role_code\": \"NORMAL_USER\", \"org_name\": \"测试分部\", \"status\": 1, \"created_at\": \"2025-07-04 01:57:28\", \"updated_at\": \"2025-07-04 01:57:28\"}','创建用户: 测试用户001','127.0.0.1','curl/8.7.1','68d883d8-5c9d-4f82-851e-14cbe5844080','2025-07-04 09:57:28','success',NULL,'2025-07-04 01:57:28'),(4,2,'admin','admin','0501','user','create','user','6','测试用户002',NULL,'{\"id\": 6, \"org_code\": \"0501\", \"user_code\": \"testuser002\", \"username\": \"测试用户002\", \"role_id\": 3, \"role_code\": \"NORMAL_USER\", \"org_name\": \"测试分部\", \"status\": 1, \"created_at\": \"2025-07-04 01:57:39\", \"updated_at\": \"2025-07-04 01:57:39\"}','创建用户: 测试用户002','127.0.0.1','curl/8.7.1','a1da0cf6-c9e3-495d-aa9a-cf07f0a7a87a','2025-07-04 09:57:39','success',NULL,'2025-07-04 01:57:39'),(5,2,'admin','admin','0501','user','disable','user','5','测试用户001','{\"id\": 5, \"org_code\": \"0501\", \"user_code\": \"testuser001\", \"username\": \"测试用户001\", \"role_id\": 3, \"role_code\": \"NORMAL_USER\", \"org_name\": \"测试分部\", \"status\": 1, \"created_at\": \"2025-07-04 01:57:28\", \"updated_at\": \"2025-07-04 01:57:28\"}','{\"id\": 5, \"org_code\": \"0501\", \"user_code\": \"testuser001\", \"username\": \"测试用户001\", \"role_id\": 3, \"role_code\": \"NORMAL_USER\", \"org_name\": \"测试分部\", \"status\": 0, \"created_at\": \"2025-07-04 01:57:28\", \"updated_at\": \"2025-07-04 02:02:16\"}','停用用户: 测试用户001','127.0.0.1','curl/8.7.1','5614bd3c-9ec9-470e-a096-4c6eaec744b9','2025-07-04 10:02:17','success',NULL,'2025-07-04 02:02:16'),(6,2,'admin','admin','0501','user','disable','user','6','测试用户002','{\"id\": 6, \"org_code\": \"0501\", \"user_code\": \"testuser002\", \"username\": \"测试用户002\", \"role_id\": 3, \"role_code\": \"NORMAL_USER\", \"org_name\": \"测试分部\", \"status\": 1, \"created_at\": \"2025-07-04 01:57:39\", \"updated_at\": \"2025-07-04 01:57:39\"}','{\"id\": 6, \"org_code\": \"0501\", \"user_code\": \"testuser002\", \"username\": \"测试用户002\", \"role_id\": 3, \"role_code\": \"NORMAL_USER\", \"org_name\": \"测试分部\", \"status\": 0, \"created_at\": \"2025-07-04 01:57:39\", \"updated_at\": \"2025-07-04 02:04:11\"}','停用用户: 测试用户002','127.0.0.1','Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36','01821949-0fad-419c-a0d3-f4e4ac35cbda','2025-07-04 10:04:12','success',NULL,'2025-07-04 02:04:11'),(7,2,'admin','admin','0501','user','disable','user','5','测试用户001','{\"id\": 5, \"org_code\": \"0501\", \"user_code\": \"testuser001\", \"username\": \"测试用户001\", \"role_id\": 3, \"role_code\": \"NORMAL_USER\", \"org_name\": \"测试分部\", \"status\": 0, \"created_at\": \"2025-07-04 01:57:28\", \"updated_at\": \"2025-07-04 02:02:16\"}','{\"id\": 5, \"org_code\": \"0501\", \"user_code\": \"testuser001\", \"username\": \"测试用户001\", \"role_id\": 3, \"role_code\": \"NORMAL_USER\", \"org_name\": \"测试分部\", \"status\": 0, \"created_at\": \"2025-07-04 01:57:28\", \"updated_at\": \"2025-07-04 02:04:32\"}','停用用户: 测试用户001','127.0.0.1','Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36','206db605-2e47-48c5-86b5-55d6498807ba','2025-07-04 10:04:33','success',NULL,'2025-07-04 02:04:32'),(8,2,'admin','admin','0501','user','disable','user','6','测试用户002','{\"id\": 6, \"org_code\": \"0501\", \"user_code\": \"testuser002\", \"username\": \"测试用户002\", \"role_id\": 3, \"role_code\": \"NORMAL_USER\", \"org_name\": \"测试分部\", \"status\": 1, \"created_at\": \"2025-07-04 01:57:39\", \"updated_at\": \"2025-07-04 02:10:27\"}','{\"id\": 6, \"org_code\": \"0501\", \"user_code\": \"testuser002\", \"username\": \"测试用户002\", \"role_id\": 3, \"role_code\": \"NORMAL_USER\", \"org_name\": \"测试分部\", \"status\": 0, \"created_at\": \"2025-07-04 01:57:39\", \"updated_at\": \"2025-07-04 02:10:36\"}','停用用户: 测试用户002','127.0.0.1','Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36','54599f0f-f68c-4aec-a614-fc1df3ac43e3','2025-07-04 10:10:36','success',NULL,'2025-07-04 02:10:36'),(9,2,'admin','admin','0501','user','disable','user','5','测试用户001','{\"id\": 5, \"org_code\": \"0501\", \"user_code\": \"testuser001\", \"username\": \"测试用户001\", \"role_id\": 3, \"role_code\": \"NORMAL_USER\", \"org_name\": \"测试分部\", \"status\": 1, \"created_at\": \"2025-07-04 01:57:28\", \"updated_at\": \"2025-07-04 02:10:25\"}','{\"id\": 5, \"org_code\": \"0501\", \"user_code\": \"testuser001\", \"username\": \"测试用户001\", \"role_id\": 3, \"role_code\": \"NORMAL_USER\", \"org_name\": \"测试分部\", \"status\": 0, \"created_at\": \"2025-07-04 01:57:28\", \"updated_at\": \"2025-07-04 02:10:40\"}','停用用户: 测试用户001','127.0.0.1','Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36','6b6f958f-61f8-426b-841b-7f8b37b48aff','2025-07-04 10:10:41','success',NULL,'2025-07-04 02:10:40'),(10,2,'admin','admin','0501','user','disable','user','6','测试用户002','{\"id\": 6, \"org_code\": \"0501\", \"user_code\": \"testuser002\", \"username\": \"测试用户002\", \"role_id\": 3, \"role_code\": \"NORMAL_USER\", \"org_name\": \"测试分部\", \"status\": 0, \"created_at\": \"2025-07-04 01:57:39\", \"updated_at\": \"2025-07-04 02:10:36\"}','{\"id\": 6, \"org_code\": \"0501\", \"user_code\": \"testuser002\", \"username\": \"测试用户002\", \"role_id\": 3, \"role_code\": \"NORMAL_USER\", \"org_name\": \"测试分部\", \"status\": 0, \"created_at\": \"2025-07-04 01:57:39\", \"updated_at\": \"2025-07-04 02:15:26\"}','停用用户: 测试用户002','127.0.0.1','Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36','cf6a539e-904b-4630-8678-60a587b4b3e2','2025-07-04 10:15:26','success',NULL,'2025-07-04 02:15:26'),(11,2,'admin','admin','0501','user','delete','user','6','测试用户002','{\"id\": 6, \"org_code\": \"0501\", \"user_code\": \"testuser002\", \"username\": \"测试用户002\", \"role_id\": 3, \"role_code\": \"NORMAL_USER\", \"org_name\": \"测试分部\", \"status\": 0, \"created_at\": \"2025-07-04 01:57:39\", \"updated_at\": \"2025-07-04 02:15:26\"}',NULL,'永久删除用户: 测试用户002','127.0.0.1','Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36','2114b67a-d5af-4255-ac35-2556b4ab09f0','2025-07-04 10:15:49','success',NULL,'2025-07-04 02:15:49'),(12,2,'admin','admin','0501','user','delete','user','5','测试用户001','{\"id\": 5, \"org_code\": \"0501\", \"user_code\": \"testuser001\", \"username\": \"测试用户001\", \"role_id\": 3, \"role_code\": \"NORMAL_USER\", \"org_name\": \"测试分部\", \"status\": 0, \"created_at\": \"2025-07-04 01:57:28\", \"updated_at\": \"2025-07-04 02:10:40\"}',NULL,'永久删除用户: 测试用户001','127.0.0.1','Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36','b4e34a9a-5a04-44b1-99d0-4cd4ef8cf68c','2025-07-04 10:16:03','success',NULL,'2025-07-04 02:16:03'),(13,2,'admin','admin','0501','user','create','user','7','测试用户2',NULL,'{\"id\": 7, \"org_code\": \"0501\", \"user_code\": \"0501000000000004\", \"username\": \"测试用户2\", \"role_id\": 2, \"role_code\": \"ORG_ADMIN\", \"org_name\": \"测试分部\", \"status\": 1, \"created_at\": \"2025-07-07 01:06:18\", \"updated_at\": \"2025-07-07 01:06:18\"}','创建用户: 测试用户2 (编码: 0501000000000004)','127.0.0.1','Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36','0caaf114-ad15-4623-a087-28ddc1391f56','2025-07-07 09:06:18','success',NULL,'2025-07-07 01:06:18'),(14,2,'admin','admin','0501','user','create','user','8','测试用户2',NULL,'{\"id\": 8, \"org_code\": \"0501\", \"user_code\": \"0501000000000005\", \"username\": \"测试用户2\", \"role_id\": 2, \"role_code\": \"ORG_ADMIN\", \"org_name\": \"测试分部\", \"status\": 1, \"created_at\": \"2025-07-07 01:06:33\", \"updated_at\": \"2025-07-07 01:06:33\"}','创建用户: 测试用户2 (编码: 0501000000000005)','127.0.0.1','Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36','d932d588-d0e1-4aa0-a3a6-c34f99fafc58','2025-07-07 09:06:33','success',NULL,'2025-07-07 01:06:33'),(15,2,'admin','admin','0501','user','create','user','9','测试用户2',NULL,'{\"id\": 9, \"org_code\": \"0501\", \"user_code\": \"0501000000000006\", \"username\": \"测试用户2\", \"role_id\": 2, \"role_code\": \"ORG_ADMIN\", \"org_name\": \"测试分部\", \"status\": 1, \"created_at\": \"2025-07-07 01:07:12\", \"updated_at\": \"2025-07-07 01:07:12\"}','创建用户: 测试用户2 (编码: 0501000000000006)','127.0.0.1','Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36','713a9fd8-d046-4652-b8b4-b767d5dd533e','2025-07-07 09:07:13','success',NULL,'2025-07-07 01:07:12'),(16,2,'admin','admin','0501','user','create','user','10','测试用户2',NULL,'{\"id\": 10, \"org_code\": \"0501\", \"user_code\": \"0501000000000007\", \"username\": \"测试用户2\", \"role_id\": 2, \"role_code\": \"ORG_ADMIN\", \"org_name\": \"测试分部\", \"status\": 1, \"created_at\": \"2025-07-07 01:10:54\", \"updated_at\": \"2025-07-07 01:10:54\"}','创建用户: 测试用户2 (编码: 0501000000000007)','127.0.0.1','Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36','1bdcbd42-e55a-41b6-a95c-db754220fb78','2025-07-07 09:10:55','success',NULL,'2025-07-07 01:10:54'),(17,2,'admin','admin','0501','user','delete','user','7','测试用户2','{\"id\": 7, \"org_code\": \"0501\", \"user_code\": \"0501000000000004\", \"username\": \"测试用户2\", \"role_id\": 2, \"role_code\": \"ORG_ADMIN\", \"org_name\": \"测试分部\", \"status\": 1, \"created_at\": \"2025-07-07 01:06:18\", \"updated_at\": \"2025-07-07 01:06:18\"}',NULL,'永久删除用户: 测试用户2','127.0.0.1','Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36','1e175eec-388a-404d-848b-3d3eac339429','2025-07-07 09:11:28','success',NULL,'2025-07-07 01:11:28'),(18,2,'admin','admin','0501','user','disable','user','9','测试用户2','{\"id\": 9, \"org_code\": \"0501\", \"user_code\": \"0501000000000006\", \"username\": \"测试用户2\", \"role_id\": 2, \"role_code\": \"ORG_ADMIN\", \"org_name\": \"测试分部\", \"status\": 1, \"created_at\": \"2025-07-07 01:07:12\", \"updated_at\": \"2025-07-07 01:07:12\"}','{\"id\": 9, \"org_code\": \"0501\", \"user_code\": \"0501000000000006\", \"username\": \"测试用户2\", \"role_id\": 2, \"role_code\": \"ORG_ADMIN\", \"org_name\": \"测试分部\", \"status\": 0, \"created_at\": \"2025-07-07 01:07:12\", \"updated_at\": \"2025-07-07 01:11:31\"}','停用用户: 测试用户2','127.0.0.1','Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36','543025bc-084b-4b4f-b1ae-d72d9930a274','2025-07-07 09:11:31','success',NULL,'2025-07-07 01:11:31'),(19,2,'admin','admin','0501','user','delete','user','10','测试用户2','{\"id\": 10, \"org_code\": \"0501\", \"user_code\": \"0501000000000007\", \"username\": \"测试用户2\", \"role_id\": 2, \"role_code\": \"ORG_ADMIN\", \"org_name\": \"测试分部\", \"status\": 1, \"created_at\": \"2025-07-07 01:10:54\", \"updated_at\": \"2025-07-07 01:10:54\"}',NULL,'永久删除用户: 测试用户2','127.0.0.1','Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36','70abcceb-74bd-47eb-915f-f62e2ac597b5','2025-07-07 09:11:35','success',NULL,'2025-07-07 01:11:35'),(20,2,'admin','admin','0501','user','delete','user','9','测试用户2','{\"id\": 9, \"org_code\": \"0501\", \"user_code\": \"0501000000000006\", \"username\": \"测试用户2\", \"role_id\": 2, \"role_code\": \"ORG_ADMIN\", \"org_name\": \"测试分部\", \"status\": 0, \"created_at\": \"2025-07-07 01:07:12\", \"updated_at\": \"2025-07-07 01:11:31\"}',NULL,'永久删除用户: 测试用户2','127.0.0.1','Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36','b7b8c6b7-e069-4216-873a-7180735e0c6c','2025-07-07 09:11:39','success',NULL,'2025-07-07 01:11:38'),(21,2,'admin','admin','0501','user','delete','user','8','测试用户2','{\"id\": 8, \"org_code\": \"0501\", \"user_code\": \"0501000000000005\", \"username\": \"测试用户2\", \"role_id\": 2, \"role_code\": \"ORG_ADMIN\", \"org_name\": \"测试分部\", \"status\": 1, \"created_at\": \"2025-07-07 01:06:33\", \"updated_at\": \"2025-07-07 01:06:33\"}',NULL,'永久删除用户: 测试用户2','127.0.0.1','Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36','c29441ed-fcf2-4fd1-8466-024b6c12ded6','2025-07-07 09:11:42','success',NULL,'2025-07-07 01:11:42'),(22,2,'admin','admin','0501','user','create','user','11','测试用户2',NULL,'{\"id\": 11, \"org_code\": \"0501\", \"user_code\": \"0501000000000008\", \"username\": \"测试用户2\", \"role_id\": 2, \"role_code\": \"ORG_ADMIN\", \"org_name\": \"测试分部\", \"status\": 1, \"created_at\": \"2025-07-07 01:12:35\", \"updated_at\": \"2025-07-07 01:12:35\"}','创建用户: 测试用户2 (编码: 0501000000000008)','127.0.0.1','Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36','96682f9e-b7a0-489c-a55a-34200d6e5fd1','2025-07-07 09:12:36','success',NULL,'2025-07-07 01:12:35'),(23,2,'admin','admin','0501','user','delete','user','11','测试用户2','{\"id\": 11, \"org_code\": \"0501\", \"user_code\": \"0501000000000008\", \"username\": \"测试用户2\", \"role_id\": 2, \"role_code\": \"ORG_ADMIN\", \"org_name\": \"测试分部\", \"status\": 1, \"created_at\": \"2025-07-07 01:12:35\", \"updated_at\": \"2025-07-07 01:12:35\"}',NULL,'永久删除用户: 测试用户2','127.0.0.1','Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36','0412daae-e58d-4c8f-a9dd-371785ac9659','2025-07-07 09:17:46','success',NULL,'2025-07-07 01:17:45'),(24,2,'admin','admin','0501','org','create','organization','050103','测试部门',NULL,'{\"id\": 9, \"org_code\": \"050103\", \"parent_org_code\": \"0501\", \"org_name\": \"测试部门\", \"contact_person\": \"测试\", \"contact_phone\": \"13000000000\", \"contact_email\": \"test@test.com\", \"status\": 1, \"level_depth\": 0, \"level_path\": null, \"created_at\": \"2025-07-07 06:30:00\", \"updated_at\": \"2025-07-07 06:30:00\"}','创建机构: 测试部门','127.0.0.1','Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36','2418adff-3634-4c36-8ed6-3d606481438d','2025-07-07 14:30:01','success',NULL,'2025-07-07 06:30:00'),(25,2,'admin','admin','0501','org','create','organization','050104','测试部门',NULL,'{\"id\": 10, \"org_code\": \"050104\", \"parent_org_code\": \"0501\", \"org_name\": \"测试部门\", \"contact_person\": \"xin zhang\", \"contact_phone\": \"15808875472\", \"contact_email\": \"test@test.com\", \"status\": 1, \"level_depth\": 0, \"level_path\": null, \"created_at\": \"2025-07-07 06:30:53\", \"updated_at\": \"2025-07-07 06:30:53\"}','创建机构: 测试部门','127.0.0.1','Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36','2d48b4f0-fa12-48ca-ad65-578afa0ef204','2025-07-07 14:30:54','success',NULL,'2025-07-07 06:30:53'),(26,2,'admin','admin','0501','org','delete','organization','9','测试部门','{\"id\": 9, \"org_code\": \"050103\", \"parent_org_code\": \"0501\", \"org_name\": \"测试部门\", \"contact_person\": \"测试\", \"contact_phone\": \"13000000000\", \"contact_email\": \"test@test.com\", \"status\": 1, \"level_depth\": 2, \"level_path\": \"/05/0501/050103/\", \"created_at\": \"2025-07-07 06:30:00\", \"updated_at\": \"2025-07-07 06:40:35\"}',NULL,'删除机构: 测试部门','127.0.0.1','Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36','d64e1ba6-0f33-49a2-81b6-0c02a365d63f','2025-07-07 14:41:47','success',NULL,'2025-07-07 06:41:47'),(27,2,'admin','admin','0501','org','delete','organization','10','测试部门','{\"id\": 10, \"org_code\": \"050104\", \"parent_org_code\": \"0501\", \"org_name\": \"测试部门\", \"contact_person\": \"xin zhang\", \"contact_phone\": \"15808875472\", \"contact_email\": \"test@test.com\", \"status\": 1, \"level_depth\": 2, \"level_path\": \"/05/0501/050104/\", \"created_at\": \"2025-07-07 06:30:53\", \"updated_at\": \"2025-07-07 06:40:35\"}',NULL,'删除机构: 测试部门','127.0.0.1','Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36','6a558a82-97d1-4a1a-871c-6801a9b3e26b','2025-07-07 14:42:05','success',NULL,'2025-07-07 06:42:05'),(28,2,'admin','admin','0501','org','delete','organization','10','测试部门','{\"id\": 10, \"org_code\": \"050104\", \"parent_org_code\": \"0501\", \"org_name\": \"测试部门\", \"contact_person\": \"xin zhang\", \"contact_phone\": \"15808875472\", \"contact_email\": \"test@test.com\", \"status\": 1, \"level_depth\": 2, \"level_path\": \"/05/0501/050104/\", \"created_at\": \"2025-07-07 06:30:53\", \"updated_at\": \"2025-07-07 06:48:50\"}',NULL,'删除机构: 测试部门','127.0.0.1','Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36','3552581a-8939-470c-aa0a-e2fa311b8edf','2025-07-07 14:50:01','success',NULL,'2025-07-07 06:50:00'),(29,2,'admin','admin','0501','org','delete','organization','9','测试部门','{\"id\": 9, \"org_code\": \"050103\", \"parent_org_code\": \"0501\", \"org_name\": \"测试部门\", \"contact_person\": \"测试\", \"contact_phone\": \"13000000000\", \"contact_email\": \"test@test.com\", \"status\": 1, \"level_depth\": 2, \"level_path\": \"/05/0501/050103/\", \"created_at\": \"2025-07-07 06:30:00\", \"updated_at\": \"2025-07-07 06:48:52\"}',NULL,'删除机构: 测试部门','127.0.0.1','Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36','f20cf730-cf9b-46ca-9934-1c81b33fb747','2025-07-07 14:50:08','success',NULL,'2025-07-07 06:50:08'),(30,2,'admin','admin','0501','org','delete','organization','10','测试部门','{\"id\": 10, \"org_code\": \"050104\", \"parent_org_code\": \"0501\", \"org_name\": \"测试部门\", \"contact_person\": \"xin zhang\", \"contact_phone\": \"15808875472\", \"contact_email\": \"test@test.com\", \"status\": 1, \"level_depth\": 2, \"level_path\": \"/05/0501/050104/\", \"created_at\": \"2025-07-07 06:30:53\", \"updated_at\": \"2025-07-07 06:54:18\"}',NULL,'删除机构: 测试部门','127.0.0.1','Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36','1c8c6805-d120-4a07-9f74-2a8f97d92d0d','2025-07-07 14:55:25','success',NULL,'2025-07-07 06:55:24'),(31,2,'admin','admin','0501','org','delete','organization','9','测试部门','{\"id\": 9, \"org_code\": \"050103\", \"parent_org_code\": \"0501\", \"org_name\": \"测试部门\", \"contact_person\": \"测试\", \"contact_phone\": \"13000000000\", \"contact_email\": \"test@test.com\", \"status\": 1, \"level_depth\": 2, \"level_path\": \"/05/0501/050103/\", \"created_at\": \"2025-07-07 06:30:00\", \"updated_at\": \"2025-07-07 06:54:20\"}',NULL,'删除机构: 测试部门','127.0.0.1','Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36','0606303c-0c34-4c08-be78-d10f0183473d','2025-07-07 14:55:48','success',NULL,'2025-07-07 06:55:47');
/*!40000 ALTER TABLE `operation_audit` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `organizations`
--

DROP TABLE IF EXISTS `organizations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `organizations` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `org_code` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '机构编码',
  `parent_org_code` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '上级机构编码',
  `level_depth` int DEFAULT '0' COMMENT '层级深度：0-顶级机构，1-二级机构，以此类推',
  `level_path` text COLLATE utf8mb4_unicode_ci COMMENT '层级路径，如：/ORG001/ORG001-01/ORG001-01-01/',
  `org_name` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '机构名称',
  `contact_person` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '负责人姓名',
  `contact_phone` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '负责人联系电话',
  `contact_email` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '负责人邮箱',
  `status` tinyint DEFAULT '1' COMMENT '状态：1-启用，0-禁用',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `org_code` (`org_code`),
  KEY `idx_org_code` (`org_code`),
  KEY `idx_org_name` (`org_name`),
  KEY `idx_status` (`status`),
  KEY `idx_created_at` (`created_at`),
  KEY `idx_parent_org_code` (`parent_org_code`),
  CONSTRAINT `fk_parent_org_code` FOREIGN KEY (`parent_org_code`) REFERENCES `organizations` (`org_code`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='机构管理表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `organizations`
--

LOCK TABLES `organizations` WRITE;
/*!40000 ALTER TABLE `organizations` DISABLE KEYS */;
INSERT INTO `organizations` VALUES (1,'05',NULL,0,'/05/','测试总部','张三','13800138001','zhangsan@test.com',1,'2025-06-20 00:38:58','2025-07-07 01:23:51'),(2,'0501','05',1,'/05/0501/','测试分部','李四','13800138002','lisi@test.com',1,'2025-06-20 00:38:58','2025-07-07 01:24:21'),(3,'050101','0501',2,'/05/0501/050101/','测试部门','王五','13800138003','wangwu@test.com',1,'2025-06-20 00:38:58','2025-07-07 01:24:21'),(4,'01',NULL,0,'/01/','中国南方电网集团','张三','13800138001','zhangsan@example.com',1,'2025-06-20 02:35:08','2025-07-07 01:23:51'),(5,'0101','01',1,'/01/0101/','广东电网公司','李四','13800138002','lisi@example.com',1,'2025-06-20 02:35:08','2025-07-07 01:24:21'),(6,'010101','0101',2,'/01/0101/010101/','广州供电局','王五','13800138003','wangwu@example.com',1,'2025-06-20 02:35:08','2025-07-07 01:24:21'),(8,'050102','0501',2,'/05/0501/050102/','测试部门','测试','13000000000','test@test.com',1,'2025-07-07 06:27:49','2025-07-07 06:40:35'),(9,'050103','0501',2,'/05/0501/050103/','测试部门','测试','13000000000','test@test.com',0,'2025-07-07 06:30:00','2025-07-07 06:55:47'),(10,'050104','0501',2,'/05/0501/050104/','测试部门','xin zhang','15808875472','test@test.com',0,'2025-07-07 06:30:53','2025-07-07 06:55:24');
/*!40000 ALTER TABLE `organizations` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `permissions`
--

DROP TABLE IF EXISTS `permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `permissions` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `permission_code` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '权限编码',
  `permission_name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '权限名称',
  `api_path` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'API路径',
  `api_method` varchar(10) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'HTTP方法',
  `resource_type` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '资源类型',
  `description` text COLLATE utf8mb4_unicode_ci COMMENT '权限描述',
  `status` tinyint DEFAULT '1' COMMENT '状态：1-启用，0-禁用',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `permission_code` (`permission_code`),
  KEY `idx_permission_code` (`permission_code`),
  KEY `idx_api_path` (`api_path`),
  KEY `idx_resource_type` (`resource_type`),
  KEY `idx_status` (`status`)
) ENGINE=InnoDB AUTO_INCREMENT=32 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='权限表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `permissions`
--

LOCK TABLES `permissions` WRITE;
/*!40000 ALTER TABLE `permissions` DISABLE KEYS */;
INSERT INTO `permissions` VALUES (1,'SYSTEM_HEALTH','系统健康检查','/api/v1/health','GET','system','查看系统健康状态',1,'2025-06-17 03:43:35','2025-06-17 03:43:35'),(2,'SYSTEM_CACHE_CLEAR','清除系统缓存','/api/v1/cache/clear','POST','system','清除系统缓存',1,'2025-06-17 03:43:35','2025-06-17 03:43:35'),(3,'ORG_CREATE','创建机构','/api/v1/organizations','POST','organization','创建新机构',1,'2025-06-17 03:43:35','2025-06-17 03:43:35'),(4,'ORG_READ','查看机构','/api/v1/organizations/*','GET','organization','查看机构信息',1,'2025-06-17 03:43:35','2025-06-17 03:43:35'),(5,'ORG_UPDATE','更新机构','/api/v1/organizations/*','PUT','organization','更新机构信息',1,'2025-06-17 03:43:35','2025-06-17 03:43:35'),(6,'ORG_DELETE','删除机构','/api/v1/organizations/*','DELETE','organization','删除机构',1,'2025-06-17 03:43:35','2025-06-17 03:43:35'),(7,'ORG_LIST','机构列表','/api/v1/organizations','GET','organization','查看机构列表',1,'2025-06-17 03:43:35','2025-06-17 03:43:35'),(8,'USER_CREATE','创建用户','/api/v1/users','POST','user','创建新用户',1,'2025-06-17 03:43:35','2025-06-17 03:43:35'),(9,'USER_READ','查看用户','/api/v1/users/*','GET','user','查看用户信息',1,'2025-06-17 03:43:35','2025-06-17 03:43:35'),(10,'USER_UPDATE','更新用户','/api/v1/users/*','PUT','user','更新用户信息',1,'2025-06-17 03:43:35','2025-06-17 03:43:35'),(11,'USER_DELETE','删除用户','/api/v1/users/*','DELETE','user','删除用户',1,'2025-06-17 03:43:35','2025-06-17 03:43:35'),(12,'USER_LIST','用户列表','/api/v1/users','GET','user','查看用户列表',1,'2025-06-17 03:43:35','2025-06-17 03:43:35'),(13,'ROLE_CREATE','创建角色','/api/v1/roles','POST','role','创建新角色',1,'2025-06-17 03:43:35','2025-06-17 03:43:35'),(14,'ROLE_READ','查看角色','/api/v1/roles/*','GET','role','查看角色信息',1,'2025-06-17 03:43:35','2025-06-17 03:43:35'),(15,'ROLE_UPDATE','更新角色','/api/v1/roles/*','PUT','role','更新角色信息',1,'2025-06-17 03:43:35','2025-06-17 03:43:35'),(16,'ROLE_DELETE','删除角色','/api/v1/roles/*','DELETE','role','删除角色',1,'2025-06-17 03:43:35','2025-06-17 03:43:35'),(17,'ROLE_LIST','角色列表','/api/v1/roles','GET','role','查看角色列表',1,'2025-06-17 03:43:35','2025-06-17 03:43:35'),(18,'PERMISSION_READ','查看权限','/api/v1/permissions/*','GET','permission','查看权限信息',1,'2025-06-17 03:43:35','2025-06-17 03:43:35'),(19,'PERMISSION_LIST','权限列表','/api/v1/permissions','GET','permission','查看权限列表',1,'2025-06-17 03:43:35','2025-06-17 03:43:35'),(20,'AI_ASK','AI问答','/api/v1/ask','POST','ai','AI智能问答',1,'2025-06-17 03:43:35','2025-06-17 03:43:35'),(21,'AI_SQL_GENERATE','SQL生成','/api/v1/generate_sql','POST','ai','生成SQL语句',1,'2025-06-17 03:43:35','2025-06-17 03:43:35'),(22,'AI_SQL_EXECUTE','SQL执行','/api/v1/execute_sql','POST','ai','执行SQL语句',1,'2025-06-17 03:43:35','2025-06-17 03:43:35'),(23,'AI_TRAIN','AI训练','/api/v1/train','POST','ai','AI模型训练',1,'2025-06-17 03:43:35','2025-06-17 03:43:35'),(24,'AI_AUTO_TRAIN','AI自动训练','/api/v1/auto_train','POST','ai','AI自动训练',1,'2025-06-17 03:43:35','2025-06-17 03:43:35'),(25,'DB_INFO','数据库信息','/api/v1/database/info','GET','database','查看数据库信息',1,'2025-06-17 03:43:35','2025-06-17 03:43:35'),(26,'DB_SCHEMA','数据库架构','/api/v1/database/schema','GET','database','查看数据库架构',1,'2025-06-17 03:43:35','2025-06-17 03:43:35');
/*!40000 ALTER TABLE `permissions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `role_permissions`
--

DROP TABLE IF EXISTS `role_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `role_permissions` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `role_id` bigint NOT NULL COMMENT '角色ID',
  `permission_id` bigint NOT NULL COMMENT '权限ID',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_role_permission` (`role_id`,`permission_id`),
  KEY `idx_role_id` (`role_id`),
  KEY `idx_permission_id` (`permission_id`),
  CONSTRAINT `role_permissions_ibfk_1` FOREIGN KEY (`role_id`) REFERENCES `roles` (`id`) ON DELETE CASCADE,
  CONSTRAINT `role_permissions_ibfk_2` FOREIGN KEY (`permission_id`) REFERENCES `permissions` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=89 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='角色权限关联表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `role_permissions`
--

LOCK TABLES `role_permissions` WRITE;
/*!40000 ALTER TABLE `role_permissions` DISABLE KEYS */;
/*!40000 ALTER TABLE `role_permissions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `roles`
--

DROP TABLE IF EXISTS `roles`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `roles` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `role_code` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '角色编码',
  `role_name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '角色名称',
  `role_level` tinyint NOT NULL COMMENT '角色等级：1-超级管理员，2-机构管理员，3-普通用户',
  `org_code` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '所属机构编码（机构管理员专用）',
  `description` text COLLATE utf8mb4_unicode_ci COMMENT '角色描述',
  `status` tinyint DEFAULT '1' COMMENT '状态：1-启用，0-禁用',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `role_code` (`role_code`),
  UNIQUE KEY `uk_org_admin` (`org_code`,`role_level`),
  KEY `idx_role_code` (`role_code`),
  KEY `idx_role_level` (`role_level`),
  KEY `idx_org_code` (`org_code`),
  KEY `idx_status` (`status`),
  CONSTRAINT `roles_ibfk_1` FOREIGN KEY (`org_code`) REFERENCES `organizations` (`org_code`) ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='角色表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `roles`
--

LOCK TABLES `roles` WRITE;
/*!40000 ALTER TABLE `roles` DISABLE KEYS */;
INSERT INTO `roles` VALUES (1,'SUPER_ADMIN','超级管理员',1,'05','系统超级管理员',1,'2025-06-20 00:38:58','2025-06-20 00:38:58'),(2,'ORG_ADMIN','机构管理员',2,'0501','机构管理员',1,'2025-06-20 00:38:58','2025-06-20 00:38:58'),(3,'NORMAL_USER','普通用户',3,'050101','普通用户',1,'2025-06-20 00:38:58','2025-06-20 00:38:58');
/*!40000 ALTER TABLE `roles` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `sys_menu`
--

DROP TABLE IF EXISTS `sys_menu`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `sys_menu` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'èœå•ID',
  `parent_id` int DEFAULT '0' COMMENT 'çˆ¶èœå•ID',
  `name` varchar(50) NOT NULL COMMENT 'èœå•åç§°',
  `path` varchar(200) DEFAULT '' COMMENT 'è·¯ç”±åœ°å€',
  `component` varchar(255) DEFAULT '' COMMENT 'ç»„ä»¶è·¯å¾„',
  `type` char(1) DEFAULT '' COMMENT 'èœå•ç±»åž‹ï¼ˆMç›®å½• Cèœå• FæŒ‰é’®ï¼‰',
  `icon` varchar(100) DEFAULT '#' COMMENT 'èœå•å›¾æ ‡',
  `order_num` int DEFAULT '0' COMMENT 'æ˜¾ç¤ºé¡ºåº',
  `status` tinyint(1) DEFAULT '1' COMMENT 'èœå•çŠ¶æ€ï¼ˆ1æ­£å¸¸ 0åœç”¨ï¼‰',
  `perms` varchar(100) DEFAULT NULL COMMENT 'æƒé™æ ‡è¯†',
  `is_frame` tinyint(1) DEFAULT '1' COMMENT 'æ˜¯å¦ä¸ºå¤–é“¾ï¼ˆ1æ˜¯ 0å¦ï¼‰',
  `visible` tinyint(1) DEFAULT '1' COMMENT 'æ˜¾ç¤ºçŠ¶æ€ï¼ˆ1æ˜¾ç¤º 0éšè—ï¼‰',
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT 'åˆ›å»ºæ—¶é—´',
  `update_time` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'æ›´æ–°æ—¶é—´',
  `remark` varchar(500) DEFAULT '' COMMENT 'å¤‡æ³¨',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=30 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='èœå•æƒé™è¡¨';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `sys_menu`
--

LOCK TABLES `sys_menu` WRITE;
/*!40000 ALTER TABLE `sys_menu` DISABLE KEYS */;
INSERT INTO `sys_menu` VALUES (1,0,'洞察魔方','/dataask','','M','home',1,1,'dataask:view',1,1,'2025-06-24 03:11:06','2025-06-24 03:11:06',''),(2,1,'监控台','/monitor','','M','dashboard',1,1,'monitor:view',1,1,'2025-06-24 03:11:06','2025-06-24 03:11:06',''),(3,2,'AI监控大屏','/dashboard','dashboard/dashboard','C','bar-chart',1,1,'dashboard:view',1,1,'2025-06-24 03:11:06','2025-06-24 03:11:06',''),(4,1,'工作台','/workspace','','M','appstore',2,1,'workspace:view',1,1,'2025-06-24 03:11:06','2025-06-24 03:11:06',''),(5,4,'个人工作台','workbench','workspace/workbench/workbench','C','laptop',1,1,'workspace:workbench:view',1,1,'2025-06-24 03:11:06','2025-06-24 03:11:06',''),(6,4,'工作报表','report','workspace/report/report','C','bar-chart',2,1,'workspace:report:view',1,1,'2025-06-24 03:11:06','2025-06-24 03:11:06',''),(7,4,'系统监控','monitor','workspace/monitor/monitor','C','monitor',3,1,'workspace:monitor:view',1,1,'2025-06-24 03:11:06','2025-06-24 03:11:06',''),(8,1,'AI引擎','/ai-engine','','M','robot',4,1,'ai-engine:view',1,1,'2025-06-24 03:11:06','2025-07-09 01:01:06',''),(9,8,'AI问答','ask-data','ai-engine/ask-data/ask-data','C','message',1,1,'ai-engine:ask-data:view',1,1,'2025-06-24 03:11:06','2025-06-24 03:11:06',''),(10,8,'知识库','knowledge-base','ai-engine/knowledge-base/knowledge-base','C','database',2,1,'ai-engine:knowledge-base:view',1,1,'2025-06-24 03:11:06','2025-06-24 03:11:06',''),(11,8,'数据源管理','datasource','ai-engine/datasource/datasource','C','table',3,1,'ai-engine:datasource:view',1,1,'2025-06-24 03:11:06','2025-06-24 03:11:06',''),(12,8,'大模型管理','llmmanage','ai-engine/llmmanage/llmmanage','C','deployment-unit',4,1,'ai-engine:llmmanage:view',1,1,'2025-06-24 03:11:06','2025-06-24 03:11:06',''),(13,8,'多模态管理','multimodal','ai-engine/multimodal/multimodal','C','experiment',5,1,'ai-engine:multimodal:view',1,1,'2025-06-24 03:11:06','2025-06-24 03:11:06',''),(14,1,'系统管理','/sys','','M','setting',5,1,'sys:view',1,1,'2025-06-24 03:11:06','2025-07-09 01:01:06',''),(15,14,'用户管理','user','sys/user/user','C','user',1,1,'sys:user:view',1,1,'2025-06-24 03:11:06','2025-06-24 03:11:21',''),(16,14,'机构管理','org','sys/org/org','C','cluster',2,1,'sys:org:view',1,1,'2025-06-24 03:11:06','2025-06-24 03:11:21',''),(17,14,'角色管理','role','sys/role/role','C','team',3,1,'sys:role:view',1,1,'2025-06-24 03:11:06','2025-06-24 03:11:21',''),(18,14,'权限管理','permission','sys/permission/permission','C','safety',4,1,'sys:permission:view',1,1,'2025-06-24 03:11:06','2025-06-24 03:11:21',''),(19,14,'工作流管理','workflow','sys/workflow/workflow','C','apartment',5,1,'sys:workflow:view',1,1,'2025-06-24 03:11:06','2025-06-24 03:11:21',''),(20,14,'消息管理','message','sys/message/message','C','message',6,1,'sys:message:view',1,1,'2025-06-24 03:11:06','2025-06-24 03:11:21',''),(23,1,'AI应用','/ai-app','','M','experiment',3,1,'ai-app:view',1,1,'2025-07-09 00:58:10','2025-07-09 01:01:06',''),(25,23,'Text2SQL','text2sql','ai-app/text2sql/text2sql','C','table',1,1,'ai-app:text2sql:view',1,1,'2025-07-09 00:58:45','2025-07-09 01:24:02',''),(26,1,'客服服务','/customer-service','','M','team',4,1,'customer-service:view',1,1,'2025-07-18 02:31:10','2025-07-18 02:39:38',''),(27,26,'客服仪表板','dashboard','customer-service/service-dashboard/service-dashboard','C','dashboard',1,1,'customer-service:dashboard:view',1,1,'2025-07-18 02:31:10','2025-07-18 02:39:41',''),(28,26,'客服工作台','workbench','customer-service/service-workbench/service-workbench','C','monitor',2,1,'customer-service:workbench:view',1,1,'2025-07-18 02:31:10','2025-07-18 02:39:43',''),(29,26,'服务工单详情','order-detail','customer-service/service-order-detail/service-order-detail','C','file-text',3,1,'customer-service:order-detail:view',1,1,'2025-07-18 02:31:10','2025-07-18 02:31:10','');
/*!40000 ALTER TABLE `sys_menu` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `sys_user_menu`
--

DROP TABLE IF EXISTS `sys_user_menu`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `sys_user_menu` (
  `user_id` int NOT NULL COMMENT 'ç”¨æˆ·ID',
  `menu_id` int NOT NULL COMMENT 'èœå•ID',
  PRIMARY KEY (`user_id`,`menu_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='ç”¨æˆ·å’Œèœå•å…³è”è¡¨';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `sys_user_menu`
--

LOCK TABLES `sys_user_menu` WRITE;
/*!40000 ALTER TABLE `sys_user_menu` DISABLE KEYS */;
INSERT INTO `sys_user_menu` VALUES (1,1),(1,2),(1,3),(1,4),(1,5),(1,6),(1,7),(1,8),(1,9),(1,10),(1,11),(1,12),(1,13),(1,14),(1,15),(1,16),(1,17),(1,18),(1,19),(1,20),(1,23),(1,25),(1,26),(1,27),(1,28),(1,29);
/*!40000 ALTER TABLE `sys_user_menu` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `sys_workflow`
--

DROP TABLE IF EXISTS `sys_workflow`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `sys_workflow` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '工作流ID',
  `name` varchar(100) NOT NULL COMMENT '工作流名称',
  `description` text COMMENT '工作流描述',
  `category` varchar(50) NOT NULL DEFAULT 'general' COMMENT '工作流分类',
  `workspace` varchar(50) DEFAULT 'default' COMMENT '所属工作域',
  `sub_category` varchar(50) DEFAULT NULL COMMENT '子分类',
  `status` enum('active','inactive','disabled','deleted') NOT NULL DEFAULT 'inactive' COMMENT '状态',
  `trigger_type` enum('manual','automatic','scheduled','event') DEFAULT 'manual' COMMENT '触发方式',
  `version` varchar(20) DEFAULT '1.0.0' COMMENT '版本号',
  `dag_id` varchar(100) NOT NULL COMMENT 'Airflow DAG ID',
  `config` json DEFAULT NULL COMMENT '工作流配置(JSON格式)',
  `schedule` varchar(100) DEFAULT NULL COMMENT '调度表达式',
  `priority` int DEFAULT '0' COMMENT '优先级',
  `timeout` int DEFAULT '3600' COMMENT '超时时间(秒)',
  `retry_count` int DEFAULT '1' COMMENT '重试次数',
  `creator_id` bigint NOT NULL COMMENT '创建人ID',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_dag_id` (`dag_id`),
  KEY `idx_name` (`name`),
  KEY `idx_category` (`category`),
  KEY `idx_status` (`status`),
  KEY `idx_creator` (`creator_id`),
  CONSTRAINT `sys_workflow_ibfk_1` FOREIGN KEY (`creator_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='工作流定义表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `sys_workflow`
--

LOCK TABLES `sys_workflow` WRITE;
/*!40000 ALTER TABLE `sys_workflow` DISABLE KEYS */;
INSERT INTO `sys_workflow` VALUES (1,'客户服务','市场营销域客户服务业务流程，包含坐席受理、服务处理、完结审批、客服回访等环节','customer_service','marketing','service_process','active','manual','1.0.0','workflow_marketing_customer_service_001','{\"timeout\": 3600, \"max_retry\": 3, \"description\": \"客户服务流程\", \"notification\": {\"sms\": false, \"email\": true}}',NULL,1,3600,3,1,'2025-07-18 04:40:14','2025-07-18 04:40:14');
/*!40000 ALTER TABLE `sys_workflow` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `user_code_seq`
--

DROP TABLE IF EXISTS `user_code_seq`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `user_code_seq` (
  `id` int NOT NULL AUTO_INCREMENT,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `user_code_seq`
--

LOCK TABLES `user_code_seq` WRITE;
/*!40000 ALTER TABLE `user_code_seq` DISABLE KEYS */;
INSERT INTO `user_code_seq` VALUES (1),(2),(3),(4),(5),(6),(7),(8);
/*!40000 ALTER TABLE `user_code_seq` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `user_sessions`
--

DROP TABLE IF EXISTS `user_sessions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `user_sessions` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `user_id` bigint NOT NULL COMMENT '用户ID',
  `session_token` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '会话令牌',
  `expires_at` timestamp NOT NULL COMMENT '过期时间',
  `ip_address` varchar(45) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'IP地址',
  `user_agent` text COLLATE utf8mb4_unicode_ci COMMENT '用户代理',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `session_token` (`session_token`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_session_token` (`session_token`),
  KEY `idx_expires_at` (`expires_at`),
  CONSTRAINT `user_sessions_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户会话表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `user_sessions`
--

LOCK TABLES `user_sessions` WRITE;
/*!40000 ALTER TABLE `user_sessions` DISABLE KEYS */;
/*!40000 ALTER TABLE `user_sessions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `org_code` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '所属机构编码',
  `user_code` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '用户编码',
  `username` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '用户名称',
  `password_hash` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '密码哈希',
  `phone` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '联系电话',
  `address` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '联系地址',
  `role_id` bigint NOT NULL COMMENT '角色ID',
  `last_login_at` timestamp NULL DEFAULT NULL COMMENT '最后登录时间',
  `login_count` int DEFAULT '0' COMMENT '登录次数',
  `status` tinyint DEFAULT '1' COMMENT '状态：1-启用，0-禁用',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_code` (`user_code`),
  KEY `idx_user_code` (`user_code`),
  KEY `idx_org_code` (`org_code`),
  KEY `idx_username` (`username`),
  KEY `idx_role_id` (`role_id`),
  KEY `idx_status` (`status`),
  CONSTRAINT `users_ibfk_1` FOREIGN KEY (`org_code`) REFERENCES `organizations` (`org_code`) ON UPDATE CASCADE,
  CONSTRAINT `users_ibfk_2` FOREIGN KEY (`role_id`) REFERENCES `roles` (`id`) ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
INSERT INTO `users` VALUES (1,'05','superadmin','superadmin','$2b$12$WnGjtg4Kuu8L6rklVuWK1.i3md62IW8kfu0JuoGIMlqv.Pt64S2ZC','13000000000','',1,NULL,0,1,'2025-06-20 00:38:58','2025-07-03 02:51:21'),(2,'0501','admin','admin','$2b$12$SViucHGJubfZQ6a8JTRgsuywVmqzeIOCdy1PU5nR2vSMG/nshS8Lq','13000000000','',2,'2025-07-24 14:22:10',5,1,'2025-06-20 00:38:58','2025-07-24 14:22:10'),(3,'050101','user','user','$2b$12$lEUdCmFJMP5eeknZvAi0gukADLWVqova8GmRXBA2FwPHYWKpTwCM6','13000000000','',3,NULL,0,1,'2025-06-20 00:38:58','2025-07-03 02:54:55');
/*!40000 ALTER TABLE `users` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `workflow_approvals`
--

DROP TABLE IF EXISTS `workflow_approvals`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `workflow_approvals` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '审批记录ID',
  `instance_id` bigint NOT NULL COMMENT '工作流实例ID',
  `node_id` bigint NOT NULL COMMENT '审批节点ID',
  `approver_id` bigint NOT NULL COMMENT '审批人ID',
  `approval_type` enum('approve','reject','delegate','withdraw') NOT NULL COMMENT '审批类型',
  `approval_result` enum('pending','approved','rejected','delegated','withdrawn','timeout') NOT NULL DEFAULT 'pending' COMMENT '审批结果',
  `comments` text COMMENT '审批意见',
  `attachments` json DEFAULT NULL COMMENT '附件信息',
  `delegate_to_id` bigint DEFAULT NULL COMMENT '委托给用户ID',
  `delegate_reason` text COMMENT '委托原因',
  `approval_data` json DEFAULT NULL COMMENT '审批数据',
  `deadline` timestamp NULL DEFAULT NULL COMMENT '审批截止时间',
  `approved_at` timestamp NULL DEFAULT NULL COMMENT '审批时间',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_approval_instance` (`instance_id`),
  KEY `idx_approval_node` (`node_id`),
  KEY `idx_approval_approver` (`approver_id`),
  KEY `idx_approval_result` (`approval_result`),
  KEY `idx_approval_deadline` (`deadline`),
  CONSTRAINT `workflow_approvals_ibfk_1` FOREIGN KEY (`instance_id`) REFERENCES `workflow_instances` (`id`) ON DELETE CASCADE,
  CONSTRAINT `workflow_approvals_ibfk_2` FOREIGN KEY (`node_id`) REFERENCES `workflow_nodes` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='审批节点记录表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `workflow_approvals`
--

LOCK TABLES `workflow_approvals` WRITE;
/*!40000 ALTER TABLE `workflow_approvals` DISABLE KEYS */;
/*!40000 ALTER TABLE `workflow_approvals` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `workflow_categories`
--

DROP TABLE IF EXISTS `workflow_categories`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `workflow_categories` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '分类ID',
  `workspace_id` bigint NOT NULL COMMENT '所属工作域ID',
  `name` varchar(100) NOT NULL COMMENT '分类名称',
  `code` varchar(50) NOT NULL COMMENT '分类代码',
  `description` text COMMENT '分类描述',
  `icon` varchar(50) DEFAULT 'folder' COMMENT '分类图标',
  `color` varchar(20) DEFAULT '#52c41a' COMMENT '分类颜色',
  `parent_id` bigint DEFAULT NULL COMMENT '父分类ID',
  `level` int DEFAULT '1' COMMENT '分类层级',
  `path` varchar(500) DEFAULT '/' COMMENT '分类路径',
  `status` enum('active','disabled') NOT NULL DEFAULT 'active' COMMENT '状态',
  `order_num` int DEFAULT '0' COMMENT '排序号',
  `creator_id` bigint NOT NULL COMMENT '创建人ID',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_category_code_workspace` (`code`,`workspace_id`),
  KEY `idx_category_workspace` (`workspace_id`),
  KEY `idx_category_parent` (`parent_id`),
  KEY `idx_category_path` (`path`),
  CONSTRAINT `workflow_categories_ibfk_1` FOREIGN KEY (`workspace_id`) REFERENCES `workflow_workspaces` (`id`) ON DELETE CASCADE,
  CONSTRAINT `workflow_categories_ibfk_2` FOREIGN KEY (`parent_id`) REFERENCES `workflow_categories` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='业务流程分类表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `workflow_categories`
--

LOCK TABLES `workflow_categories` WRITE;
/*!40000 ALTER TABLE `workflow_categories` DISABLE KEYS */;
/*!40000 ALTER TABLE `workflow_categories` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `workflow_executions`
--

DROP TABLE IF EXISTS `workflow_executions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `workflow_executions` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '执行记录ID',
  `workflow_id` bigint NOT NULL COMMENT '工作流ID',
  `execution_id` varchar(100) NOT NULL COMMENT '执行ID(对应Airflow dag_run_id)',
  `status` enum('running','success','failed','cancelled','timeout') NOT NULL DEFAULT 'running' COMMENT '执行状态',
  `trigger_type` enum('manual','scheduled','api','webhook') NOT NULL DEFAULT 'manual' COMMENT '触发方式',
  `input_data` json DEFAULT NULL COMMENT '输入数据',
  `output_data` json DEFAULT NULL COMMENT '输出数据',
  `error_message` text COMMENT '错误信息',
  `started_at` timestamp NULL DEFAULT NULL COMMENT '开始时间',
  `finished_at` timestamp NULL DEFAULT NULL COMMENT '结束时间',
  `duration` int DEFAULT NULL COMMENT '执行时长(秒)',
  `executor_id` bigint DEFAULT NULL COMMENT '执行人ID',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_execution_id` (`execution_id`),
  KEY `idx_workflow_id` (`workflow_id`),
  KEY `idx_status` (`status`),
  KEY `idx_started_at` (`started_at`),
  KEY `idx_executor_id` (`executor_id`),
  CONSTRAINT `workflow_executions_ibfk_1` FOREIGN KEY (`workflow_id`) REFERENCES `sys_workflow` (`id`),
  CONSTRAINT `workflow_executions_ibfk_2` FOREIGN KEY (`executor_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='工作流执行记录表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `workflow_executions`
--

LOCK TABLES `workflow_executions` WRITE;
/*!40000 ALTER TABLE `workflow_executions` DISABLE KEYS */;
/*!40000 ALTER TABLE `workflow_executions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `workflow_instances`
--

DROP TABLE IF EXISTS `workflow_instances`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `workflow_instances` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '实例ID',
  `workflow_id` bigint NOT NULL COMMENT '工作流ID',
  `instance_code` varchar(100) NOT NULL COMMENT '实例代码',
  `dag_run_id` varchar(200) NOT NULL COMMENT 'Airflow DAG运行ID',
  `status` enum('pending','running','paused','completed','failed','cancelled','timeout') NOT NULL DEFAULT 'pending' COMMENT '执行状态',
  `trigger_type` enum('manual','scheduled','api','webhook','event') NOT NULL DEFAULT 'manual' COMMENT '触发方式',
  `trigger_user_id` bigint DEFAULT NULL COMMENT '触发用户ID',
  `trigger_data` json DEFAULT NULL COMMENT '触发数据',
  `context_data` json DEFAULT NULL COMMENT '上下文数据',
  `current_node_id` bigint DEFAULT NULL COMMENT '当前执行节点ID',
  `progress_percentage` decimal(5,2) DEFAULT '0.00' COMMENT '执行进度百分比',
  `error_message` text COMMENT '错误信息',
  `error_stack` text COMMENT '错误堆栈',
  `started_at` timestamp NULL DEFAULT NULL COMMENT '开始时间',
  `completed_at` timestamp NULL DEFAULT NULL COMMENT '完成时间',
  `duration_seconds` int DEFAULT NULL COMMENT '执行时长(秒)',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_instance_code` (`instance_code`),
  UNIQUE KEY `uk_dag_run_id` (`dag_run_id`),
  KEY `idx_instance_workflow` (`workflow_id`),
  KEY `idx_instance_status` (`status`),
  KEY `idx_instance_trigger` (`trigger_type`),
  KEY `idx_instance_user` (`trigger_user_id`),
  KEY `idx_instance_started` (`started_at`),
  KEY `current_node_id` (`current_node_id`),
  CONSTRAINT `workflow_instances_ibfk_1` FOREIGN KEY (`workflow_id`) REFERENCES `enhanced_workflows` (`id`) ON DELETE CASCADE,
  CONSTRAINT `workflow_instances_ibfk_2` FOREIGN KEY (`current_node_id`) REFERENCES `workflow_nodes` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='工作流执行实例表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `workflow_instances`
--

LOCK TABLES `workflow_instances` WRITE;
/*!40000 ALTER TABLE `workflow_instances` DISABLE KEYS */;
/*!40000 ALTER TABLE `workflow_instances` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `workflow_node_connections`
--

DROP TABLE IF EXISTS `workflow_node_connections`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `workflow_node_connections` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '连接ID',
  `workflow_id` bigint NOT NULL COMMENT '工作流ID',
  `from_node_id` bigint NOT NULL COMMENT '源节点ID',
  `to_node_id` bigint NOT NULL COMMENT '目标节点ID',
  `condition_type` enum('always','success','failure','condition') DEFAULT 'always' COMMENT '连接条件类型',
  `condition_expression` text COMMENT '条件表达式',
  `condition_config` json DEFAULT NULL COMMENT '条件配置',
  `order_num` int DEFAULT '0' COMMENT '连接排序',
  `style_config` json DEFAULT NULL COMMENT '连接样式配置',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_connection` (`from_node_id`,`to_node_id`,`condition_type`),
  KEY `idx_connection_workflow` (`workflow_id`),
  KEY `idx_connection_from` (`from_node_id`),
  KEY `idx_connection_to` (`to_node_id`),
  CONSTRAINT `workflow_node_connections_ibfk_1` FOREIGN KEY (`workflow_id`) REFERENCES `enhanced_workflows` (`id`) ON DELETE CASCADE,
  CONSTRAINT `workflow_node_connections_ibfk_2` FOREIGN KEY (`from_node_id`) REFERENCES `workflow_nodes` (`id`) ON DELETE CASCADE,
  CONSTRAINT `workflow_node_connections_ibfk_3` FOREIGN KEY (`to_node_id`) REFERENCES `workflow_nodes` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='节点连接关系表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `workflow_node_connections`
--

LOCK TABLES `workflow_node_connections` WRITE;
/*!40000 ALTER TABLE `workflow_node_connections` DISABLE KEYS */;
/*!40000 ALTER TABLE `workflow_node_connections` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `workflow_node_executions`
--

DROP TABLE IF EXISTS `workflow_node_executions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `workflow_node_executions` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '执行记录ID',
  `instance_id` bigint NOT NULL COMMENT '工作流实例ID',
  `node_id` bigint NOT NULL COMMENT '节点ID',
  `execution_code` varchar(100) NOT NULL COMMENT '执行代码',
  `task_id` varchar(200) DEFAULT NULL COMMENT 'Airflow任务ID',
  `status` enum('pending','running','success','failed','skipped','retry','timeout') NOT NULL DEFAULT 'pending' COMMENT '执行状态',
  `attempt_count` int DEFAULT '1' COMMENT '尝试次数',
  `input_data` json DEFAULT NULL COMMENT '输入数据',
  `output_data` json DEFAULT NULL COMMENT '输出数据',
  `error_message` text COMMENT '错误信息',
  `error_details` json DEFAULT NULL COMMENT '错误详情',
  `execution_logs` longtext COMMENT '执行日志',
  `started_at` timestamp NULL DEFAULT NULL COMMENT '开始时间',
  `completed_at` timestamp NULL DEFAULT NULL COMMENT '完成时间',
  `duration_seconds` int DEFAULT NULL COMMENT '执行时长(秒)',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_execution_code` (`execution_code`),
  KEY `idx_execution_instance` (`instance_id`),
  KEY `idx_execution_node` (`node_id`),
  KEY `idx_execution_status` (`status`),
  KEY `idx_execution_started` (`started_at`),
  CONSTRAINT `workflow_node_executions_ibfk_1` FOREIGN KEY (`instance_id`) REFERENCES `workflow_instances` (`id`) ON DELETE CASCADE,
  CONSTRAINT `workflow_node_executions_ibfk_2` FOREIGN KEY (`node_id`) REFERENCES `workflow_nodes` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='节点执行记录表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `workflow_node_executions`
--

LOCK TABLES `workflow_node_executions` WRITE;
/*!40000 ALTER TABLE `workflow_node_executions` DISABLE KEYS */;
/*!40000 ALTER TABLE `workflow_node_executions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `workflow_nodes`
--

DROP TABLE IF EXISTS `workflow_nodes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `workflow_nodes` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '节点ID',
  `workflow_id` bigint NOT NULL COMMENT '工作流ID',
  `name` varchar(200) NOT NULL COMMENT '节点名称',
  `code` varchar(100) NOT NULL COMMENT '节点代码',
  `description` text COMMENT '节点描述',
  `type` enum('page','button','api','condition','timer','notification','script','approval') NOT NULL COMMENT '节点类型',
  `subtype` varchar(50) DEFAULT NULL COMMENT '节点子类型',
  `step_order` int NOT NULL COMMENT '执行顺序',
  `x_position` decimal(10,2) DEFAULT '0.00' COMMENT 'X坐标(流程图)',
  `y_position` decimal(10,2) DEFAULT '0.00' COMMENT 'Y坐标(流程图)',
  `icon` varchar(50) DEFAULT 'play-circle' COMMENT '节点图标',
  `color` varchar(20) DEFAULT '#1890ff' COMMENT '节点颜色',
  `config` json NOT NULL COMMENT '节点配置',
  `input_schema` json DEFAULT NULL COMMENT '输入数据结构',
  `output_schema` json DEFAULT NULL COMMENT '输出数据结构',
  `validation_rules` json DEFAULT NULL COMMENT '数据验证规则',
  `timeout_minutes` int DEFAULT '30' COMMENT '节点超时时间(分钟)',
  `retry_count` int DEFAULT '1' COMMENT '重试次数',
  `retry_delay_minutes` int DEFAULT '2' COMMENT '重试间隔(分钟)',
  `skip_on_failure` tinyint(1) DEFAULT '0' COMMENT '失败时是否跳过',
  `rollback_enabled` tinyint(1) DEFAULT '0' COMMENT '是否支持回滚',
  `rollback_config` json DEFAULT NULL COMMENT '回滚配置',
  `conditions` json DEFAULT NULL COMMENT '执行条件',
  `status` enum('active','disabled') NOT NULL DEFAULT 'active' COMMENT '状态',
  `creator_id` bigint NOT NULL COMMENT '创建人ID',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_node_code_workflow` (`code`,`workflow_id`),
  KEY `idx_node_workflow` (`workflow_id`),
  KEY `idx_node_type` (`type`),
  KEY `idx_node_order` (`step_order`),
  KEY `idx_node_status` (`status`),
  CONSTRAINT `workflow_nodes_ibfk_1` FOREIGN KEY (`workflow_id`) REFERENCES `enhanced_workflows` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='工作流节点定义表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `workflow_nodes`
--

LOCK TABLES `workflow_nodes` WRITE;
/*!40000 ALTER TABLE `workflow_nodes` DISABLE KEYS */;
/*!40000 ALTER TABLE `workflow_nodes` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `workflow_permissions`
--

DROP TABLE IF EXISTS `workflow_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `workflow_permissions` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '权限ID',
  `resource_type` enum('workspace','category','workflow','node') NOT NULL COMMENT '资源类型',
  `resource_id` bigint NOT NULL COMMENT '资源ID',
  `subject_type` enum('user','role','organization') NOT NULL COMMENT '主体类型',
  `subject_id` bigint NOT NULL COMMENT '主体ID',
  `permission_type` enum('view','edit','execute','delete','manage') NOT NULL COMMENT '权限类型',
  `granted` tinyint(1) NOT NULL DEFAULT '1' COMMENT '是否授权',
  `conditions` json DEFAULT NULL COMMENT '权限条件',
  `granted_by` bigint NOT NULL COMMENT '授权人ID',
  `granted_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '授权时间',
  `expires_at` timestamp NULL DEFAULT NULL COMMENT '过期时间',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_permission` (`resource_type`,`resource_id`,`subject_type`,`subject_id`,`permission_type`),
  KEY `idx_permission_resource` (`resource_type`,`resource_id`),
  KEY `idx_permission_subject` (`subject_type`,`subject_id`),
  KEY `idx_permission_type` (`permission_type`),
  KEY `idx_permission_granted` (`granted`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='工作流权限控制表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `workflow_permissions`
--

LOCK TABLES `workflow_permissions` WRITE;
/*!40000 ALTER TABLE `workflow_permissions` DISABLE KEYS */;
/*!40000 ALTER TABLE `workflow_permissions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `workflow_step_executions`
--

DROP TABLE IF EXISTS `workflow_step_executions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `workflow_step_executions` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '步骤执行记录ID',
  `execution_id` bigint NOT NULL COMMENT '工作流执行记录ID',
  `step_id` bigint NOT NULL COMMENT '步骤ID',
  `task_id` varchar(100) NOT NULL COMMENT 'Airflow任务ID',
  `status` enum('running','success','failed','skipped','retry') NOT NULL DEFAULT 'running' COMMENT '执行状态',
  `input_data` json DEFAULT NULL COMMENT '输入数据',
  `output_data` json DEFAULT NULL COMMENT '输出数据',
  `error_message` text COMMENT '错误信息',
  `logs` longtext COMMENT '执行日志',
  `started_at` timestamp NULL DEFAULT NULL COMMENT '开始时间',
  `finished_at` timestamp NULL DEFAULT NULL COMMENT '结束时间',
  `duration` int DEFAULT NULL COMMENT '执行时长(秒)',
  `retry_count` int DEFAULT '0' COMMENT '重试次数',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_execution_id` (`execution_id`),
  KEY `idx_step_id` (`step_id`),
  KEY `idx_task_id` (`task_id`),
  KEY `idx_status` (`status`),
  CONSTRAINT `workflow_step_executions_ibfk_1` FOREIGN KEY (`execution_id`) REFERENCES `workflow_executions` (`id`) ON DELETE CASCADE,
  CONSTRAINT `workflow_step_executions_ibfk_2` FOREIGN KEY (`step_id`) REFERENCES `workflow_steps` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='工作流步骤执行记录表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `workflow_step_executions`
--

LOCK TABLES `workflow_step_executions` WRITE;
/*!40000 ALTER TABLE `workflow_step_executions` DISABLE KEYS */;
/*!40000 ALTER TABLE `workflow_step_executions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `workflow_steps`
--

DROP TABLE IF EXISTS `workflow_steps`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `workflow_steps` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '步骤ID',
  `workflow_id` bigint NOT NULL COMMENT '工作流ID',
  `step_name` varchar(100) NOT NULL COMMENT '步骤名称',
  `step_type` varchar(50) NOT NULL COMMENT '步骤类型(python,bash,sql,http,etc.)',
  `step_order` int NOT NULL COMMENT '执行顺序',
  `depends_on` json DEFAULT NULL COMMENT '依赖的步骤ID列表',
  `config` json NOT NULL COMMENT '步骤配置',
  `timeout` int DEFAULT '1800' COMMENT '步骤超时时间(秒)',
  `retry_count` int DEFAULT '1' COMMENT '重试次数',
  `condition` varchar(500) DEFAULT NULL COMMENT '执行条件',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_workflow_id` (`workflow_id`),
  KEY `idx_step_order` (`step_order`),
  CONSTRAINT `workflow_steps_ibfk_1` FOREIGN KEY (`workflow_id`) REFERENCES `sys_workflow` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='工作流步骤定义表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `workflow_steps`
--

LOCK TABLES `workflow_steps` WRITE;
/*!40000 ALTER TABLE `workflow_steps` DISABLE KEYS */;
INSERT INTO `workflow_steps` VALUES (1,1,'坐席受理','manual',1,NULL,'{\"icon\": \"phone\", \"color\": \"#1890ff\", \"route\": \"/customer-service/reception\", \"node_type\": \"page\", \"description\": \"客服坐席接收客户服务请求，进行初步处理和分类\"}',1800,1,NULL,'2025-07-18 04:40:14','2025-07-18 04:40:14'),(2,1,'服务处理','manual',2,'[1]','{\"icon\": \"tool\", \"color\": \"#52c41a\", \"route\": \"/customer-service/processing\", \"node_type\": \"page\", \"description\": \"根据客户需求进行具体的服务处理和问题解决\"}',3600,2,NULL,'2025-07-18 04:40:14','2025-07-18 04:40:14'),(3,1,'完结审批','approval',3,'[2]','{\"icon\": \"check-circle\", \"color\": \"#fa8c16\", \"route\": \"/customer-service/approval\", \"node_type\": \"approval\", \"description\": \"主管或质检人员对服务处理结果进行审批确认\"}',1800,1,'status == \"completed\"','2025-07-18 04:40:14','2025-07-18 04:40:14'),(4,1,'客服回访','manual',4,'[3]','{\"icon\": \"message\", \"color\": \"#722ed1\", \"route\": \"/customer-service/followup\", \"node_type\": \"page\", \"description\": \"服务完成后对客户进行回访，收集满意度反馈\"}',1800,1,'approval_status == \"approved\"','2025-07-18 04:40:14','2025-07-18 04:40:14');
/*!40000 ALTER TABLE `workflow_steps` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `workflow_templates`
--

DROP TABLE IF EXISTS `workflow_templates`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `workflow_templates` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '模板ID',
  `name` varchar(100) NOT NULL COMMENT '模板名称',
  `description` text COMMENT '模板描述',
  `category` varchar(50) NOT NULL COMMENT '模板分类',
  `icon` varchar(100) DEFAULT NULL COMMENT '图标',
  `template_config` json NOT NULL COMMENT '模板配置',
  `usage_count` int DEFAULT '0' COMMENT '使用次数',
  `is_public` tinyint(1) DEFAULT '1' COMMENT '是否公开',
  `creator_id` bigint NOT NULL COMMENT '创建人ID',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_name` (`name`),
  KEY `idx_category` (`category`),
  KEY `idx_creator` (`creator_id`),
  CONSTRAINT `workflow_templates_ibfk_1` FOREIGN KEY (`creator_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='工作流模板表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `workflow_templates`
--

LOCK TABLES `workflow_templates` WRITE;
/*!40000 ALTER TABLE `workflow_templates` DISABLE KEYS */;
/*!40000 ALTER TABLE `workflow_templates` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `workflow_variables`
--

DROP TABLE IF EXISTS `workflow_variables`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `workflow_variables` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '变量ID',
  `workflow_id` bigint NOT NULL COMMENT '工作流ID',
  `var_name` varchar(100) NOT NULL COMMENT '变量名称',
  `var_type` enum('string','number','boolean','json','secret') NOT NULL DEFAULT 'string' COMMENT '变量类型',
  `var_value` text COMMENT '变量值',
  `description` varchar(500) DEFAULT NULL COMMENT '变量描述',
  `is_required` tinyint(1) DEFAULT '0' COMMENT '是否必需',
  `default_value` text COMMENT '默认值',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_workflow_var` (`workflow_id`,`var_name`),
  KEY `idx_var_name` (`var_name`),
  CONSTRAINT `workflow_variables_ibfk_1` FOREIGN KEY (`workflow_id`) REFERENCES `sys_workflow` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='工作流变量表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `workflow_variables`
--

LOCK TABLES `workflow_variables` WRITE;
/*!40000 ALTER TABLE `workflow_variables` DISABLE KEYS */;
INSERT INTO `workflow_variables` VALUES (1,1,'customer_info','json','{\"customer_id\": \"\", \"customer_name\": \"\", \"contact_phone\": \"\", \"service_type\": \"\"}','客户基本信息',1,NULL,'2025-07-18 04:40:14','2025-07-18 04:40:14'),(2,1,'service_result','json','{\"status\": \"\", \"solution\": \"\", \"processing_time\": \"\", \"agent_notes\": \"\"}','服务处理结果记录',1,NULL,'2025-07-18 04:40:14','2025-07-18 04:40:14'),(3,1,'approval_result','json','{\"approval_status\": \"\", \"approver_id\": \"\", \"approval_notes\": \"\", \"approval_time\": \"\"}','审批结果记录',0,NULL,'2025-07-18 04:40:14','2025-07-18 04:40:14'),(4,1,'followup_result','json','{\"satisfaction_score\": \"\", \"feedback_comments\": \"\", \"followup_agent\": \"\", \"followup_time\": \"\"}','客服回访结果',0,NULL,'2025-07-18 04:40:14','2025-07-18 04:40:14');
/*!40000 ALTER TABLE `workflow_variables` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `workflow_workspaces`
--

DROP TABLE IF EXISTS `workflow_workspaces`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `workflow_workspaces` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `code` varchar(50) NOT NULL,
  `name` varchar(100) NOT NULL,
  `description` text,
  `icon` varchar(50) DEFAULT 'folder',
  `color` varchar(20) DEFAULT '#1890ff',
  `status` enum('active','disabled') NOT NULL DEFAULT 'active',
  `order_num` int DEFAULT '0',
  `creator_id` bigint NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_workspace_code` (`code`)
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `workflow_workspaces`
--

LOCK TABLES `workflow_workspaces` WRITE;
/*!40000 ALTER TABLE `workflow_workspaces` DISABLE KEYS */;
INSERT INTO `workflow_workspaces` VALUES (6,'marketing','市场营销域','市场营销相关的业务流程和工作流管理','team','#ff6b35','active',6,1,'2025-07-18 04:38:00','2025-07-18 04:38:00');
/*!40000 ALTER TABLE `workflow_workspaces` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-07-25  0:54:26
