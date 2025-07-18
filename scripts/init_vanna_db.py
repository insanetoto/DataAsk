#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Vanna数据库初始化脚本
用于创建Vanna Text2SQL功能所需的数据库表
"""
import os
import sys
import pymysql
import logging

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_vanna_database():
    """创建vanna数据库"""
    try:
        # 连接到MySQL服务器（不指定数据库）
        connection = pymysql.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            charset='utf8mb4'
        )
        
        with connection.cursor() as cursor:
            # 创建vanna数据库
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{Config.VANNA_DATABASE}` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            logger.info(f"数据库 {Config.VANNA_DATABASE} 创建成功或已存在")
            
        connection.commit()
        connection.close()
        
    except Exception as e:
        logger.error(f"创建数据库失败: {str(e)}")
        raise

def execute_sql_file(sql_file_path):
    """执行SQL文件"""
    try:
        # 连接到vanna数据库
        connection = pymysql.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.VANNA_DATABASE,
            charset='utf8mb4'
        )
        
        # 读取SQL文件
        with open(sql_file_path, 'r', encoding='utf-8') as file:
            sql_content = file.read()
        
        # 按分号分割SQL语句
        sql_statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
        
        with connection.cursor() as cursor:
            for statement in sql_statements:
                if statement:
                    cursor.execute(statement)
                    logger.debug(f"执行SQL: {statement[:50]}...")
        
        connection.commit()
        connection.close()
        logger.info(f"SQL文件 {sql_file_path} 执行成功")
        
    except Exception as e:
        logger.error(f"执行SQL文件失败: {str(e)}")
        raise

def init_vanna_training_data():
    """初始化Vanna训练数据"""
    try:
        from service.vanna_service import get_vanna_service
        
        logger.info("开始初始化Vanna训练数据...")
        
        # 获取Vanna服务实例
        vanna_service = get_vanna_service()
        
        # 训练基础数据库结构信息
        # 这里可以根据实际的数据库表结构来训练
        basic_training_samples = [
            {
                'question': '查询所有用户信息',
                'sql': 'SELECT * FROM users'
            },
            {
                'question': '统计用户总数',
                'sql': 'SELECT COUNT(*) as user_count FROM users'
            },
            {
                'question': '查询用户数量按机构分组',
                'sql': 'SELECT org_code, COUNT(*) as user_count FROM users GROUP BY org_code'
            },
            {
                'question': '查询所有机构信息',
                'sql': 'SELECT * FROM organizations'
            },
            {
                'question': '查询所有角色信息',
                'sql': 'SELECT * FROM roles'
            }
        ]
        
        # 训练基础样本
        for sample in basic_training_samples:
            try:
                result = vanna_service.train_on_sql(
                    question=sample['question'],
                    sql=sample['sql'],
                    user_id=1  # 系统用户
                )
                if result['success']:
                    logger.info(f"训练样本成功: {sample['question']}")
                else:
                    logger.warning(f"训练样本失败: {sample['question']} - {result.get('error', '')}")
            except Exception as e:
                logger.warning(f"训练样本异常: {sample['question']} - {str(e)}")
                continue
        
        logger.info("Vanna训练数据初始化完成")
        
    except Exception as e:
        logger.error(f"初始化训练数据失败: {str(e)}")
        # 训练数据初始化失败不应该影响整体初始化
        pass

def main():
    """主函数"""
    try:
        logger.info("开始初始化Vanna数据库...")
        
        # 1. 创建vanna数据库
        create_vanna_database()
        
        # 2. 执行表结构SQL
        sql_file_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'sql',
            'vanna_tables.sql'
        )
        
        if os.path.exists(sql_file_path):
            execute_sql_file(sql_file_path)
        else:
            logger.error(f"SQL文件不存在: {sql_file_path}")
            return False
        
        # 3. 初始化训练数据（可选）
        try:
            init_vanna_training_data()
        except Exception as e:
            logger.warning(f"训练数据初始化失败，跳过: {str(e)}")
        
        logger.info("Vanna数据库初始化完成!")
        return True
        
    except Exception as e:
        logger.error(f"初始化失败: {str(e)}")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1) 