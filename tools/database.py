# -*- coding: utf-8 -*-
"""
数据库服务模块
提供MySQL连接池管理和基础查询服务
"""
import logging
from typing import Optional, Dict, Any, List
import pymysql
from sqlalchemy import create_engine, text
from sqlalchemy.pool import QueuePool
from config import Config
from contextlib import contextmanager
from sqlalchemy.orm import sessionmaker, scoped_session

logger = logging.getLogger(__name__)

config = Config()
# 数据库连接配置
DATABASE_URL = f"mysql+pymysql://{config.DB_USER}:{config.DB_PASSWORD}@{config.DB_HOST}:{config.DB_PORT}/{config.DB_NAME}"

# 创建数据库引擎
engine = create_engine(DATABASE_URL)

# 创建会话工厂
SessionFactory = sessionmaker(bind=engine)
Session = scoped_session(SessionFactory)

@contextmanager
def get_db_session():
    """获取数据库会话的上下文管理器"""
    session = Session()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

class DatabaseService:
    """数据库服务类"""
    
    def __init__(self, config: Config):
        self.config = config
        # 主数据库引擎（用于业务数据）
        self.engine = self._create_engine(config.SQLALCHEMY_DATABASE_URI, "主数据库")
        # Vanna数据库引擎（用于AI训练数据）
        self.vanna_engine = self._create_engine(config.VANNA_DATABASE_URI, "Vanna数据库")
        self.Session = Session
        
    def _create_engine(self, database_uri: str, db_name: str):
        """创建数据库引擎"""
        try:
            engine = create_engine(
                database_uri,
                poolclass=QueuePool,
                **self.config.SQLALCHEMY_ENGINE_OPTIONS,
                echo=self.config.DEBUG
            )
            logger.info(f"{db_name}引擎创建成功")
            return engine
        except Exception as e:
            logger.error(f"{db_name}引擎创建失败: {str(e)}")
            raise
    
    def test_connection(self) -> bool:
        """测试主数据库连接"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                return result.fetchone() is not None
        except Exception as e:
            logger.error(f"主数据库连接测试失败: {str(e)}")
            return False
    
    def test_vanna_connection(self) -> bool:
        """测试Vanna数据库连接"""
        try:
            with self.vanna_engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                return result.fetchone() is not None
        except Exception as e:
            logger.error(f"Vanna数据库连接测试失败: {str(e)}")
            return False
    
    def execute_query(self, sql: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """执行查询SQL"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(sql), params or {})
                columns = result.keys()
                rows = result.fetchall()
                return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            logger.error(f"查询执行失败: {str(e)}")
            raise
    
    def execute_update(self, sql: str, params: Optional[Dict[str, Any]] = None) -> int:
        """执行更新SQL（主数据库）"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(sql), params or {})
                conn.commit()
                return result.rowcount
        except Exception as e:
            logger.error(f"主数据库更新执行失败: {str(e)}")
            raise
    
    def execute_vanna_query(self, sql: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """执行查询SQL（Vanna数据库）"""
        try:
            with self.vanna_engine.connect() as conn:
                result = conn.execute(text(sql), params or {})
                columns = result.keys()
                rows = result.fetchall()
                return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            logger.error(f"Vanna数据库查询执行失败: {str(e)}")
            raise
    
    def execute_vanna_update(self, sql: str, params: Optional[Dict[str, Any]] = None) -> int:
        """执行更新SQL（Vanna数据库）"""
        try:
            with self.vanna_engine.connect() as conn:
                result = conn.execute(text(sql), params or {})
                conn.commit()
                return result.rowcount
        except Exception as e:
            logger.error(f"Vanna数据库更新执行失败: {str(e)}")
            raise
    
    def get_table_schemas(self) -> List[Dict[str, Any]]:
        """获取数据库表结构信息"""
        try:
            sql = """
            SELECT 
                TABLE_NAME as table_name,
                COLUMN_NAME as column_name,
                DATA_TYPE as data_type,
                IS_NULLABLE as is_nullable,
                COLUMN_DEFAULT as default_value,
                COLUMN_COMMENT as comment
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = :database_name
            ORDER BY TABLE_NAME, ORDINAL_POSITION
            """
            return self.execute_query(sql, {'database_name': self.config.MYSQL_DATABASE})
        except Exception as e:
            logger.error(f"获取表结构失败: {str(e)}")
            raise
    
    def get_database_summary(self) -> Dict[str, Any]:
        """获取数据库概要信息"""
        try:
            # 获取表数量
            tables_sql = """
            SELECT COUNT(*) as table_count 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_SCHEMA = :database_name
            """
            table_count = self.execute_query(tables_sql, {'database_name': self.config.MYSQL_DATABASE})[0]['table_count']
            
            # 获取表名列表
            table_names_sql = """
            SELECT TABLE_NAME as table_name
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_SCHEMA = :database_name
            ORDER BY TABLE_NAME
            """
            table_names = [row['table_name'] for row in self.execute_query(table_names_sql, {'database_name': self.config.MYSQL_DATABASE})]
            
            return {
                'database_name': self.config.MYSQL_DATABASE,
                'table_count': table_count,
                'table_names': table_names
            }
        except Exception as e:
            logger.error(f"获取数据库概要失败: {str(e)}")
            raise

# 全局数据库服务实例
db_service = None

def init_database_service(config: Config) -> DatabaseService:
    """初始化数据库服务"""
    global db_service
    db_service = DatabaseService(config)
    return db_service

def get_database_service() -> DatabaseService:
    """获取数据库服务实例"""
    if db_service is None:
        raise RuntimeError("数据库服务未初始化")
    return db_service 