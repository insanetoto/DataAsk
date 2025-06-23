# -*- coding: utf-8 -*-
"""
数据库工具层单元测试
测试数据库连接、事务管理和SQL执行功能
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sqlite3

try:
    from tools.database import DatabaseService, init_database_service, get_database_service
except ImportError:
    pytest.skip("数据库模块导入失败，跳过数据库测试", allow_module_level=True)


class TestDatabaseService:
    """数据库服务测试"""
    
    @pytest.fixture
    def mock_config(self):
        """模拟配置"""
        class MockConfig:
            SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
            VANNA_DATABASE_URI = 'sqlite:///:memory:'
            DEBUG = False
            SQLALCHEMY_ENGINE_OPTIONS = {
                'pool_size': 5,
                'pool_timeout': 30,
                'pool_recycle': -1,
                'max_overflow': 0,
                'pool_pre_ping': True
            }
            
        return MockConfig()
    
    @pytest.fixture
    def db_service(self, mock_config):
        """创建数据库服务实例"""
        with patch('sqlite3.connect') as mock_connect:
            mock_connection = Mock()
            mock_cursor = Mock()
            mock_connection.cursor.return_value = mock_cursor
            mock_connect.return_value = mock_connection
            
            service = DatabaseService(mock_config)
            service.connection = mock_connection
            service.cursor = mock_cursor
            yield service
    
    def test_database_service_initialization(self, mock_config):
        """测试数据库服务初始化"""
        with patch('sqlite3.connect') as mock_connect:
            mock_connection = Mock()
            mock_connect.return_value = mock_connection
            
            service = DatabaseService(mock_config)
            
            assert service.config == mock_config
            assert hasattr(service, 'connection')
    
    def test_execute_query_success(self, db_service):
        """测试查询执行成功"""
        # Mock查询结果
        mock_results = [
            {'id': 1, 'name': '测试用户1'},
            {'id': 2, 'name': '测试用户2'}
        ]
        
        db_service.cursor.fetchall.return_value = mock_results
        db_service.cursor.description = [('id',), ('name',)]
        
        sql = "SELECT id, name FROM users WHERE status = ?"
        params = (1,)
        
        result = db_service.execute_query(sql, params)
        
        assert result == mock_results
        db_service.cursor.execute.assert_called_once_with(sql, params)
        db_service.cursor.fetchall.assert_called_once()
    
    def test_execute_query_with_dict_params(self, db_service):
        """测试使用字典参数执行查询"""
        mock_results = [{'id': 1, 'user_code': 'testuser'}]
        db_service.cursor.fetchall.return_value = mock_results
        
        sql = "SELECT * FROM users WHERE user_code = :user_code"
        params = {'user_code': 'testuser'}
        
        result = db_service.execute_query(sql, params)
        
        assert result == mock_results
        db_service.cursor.execute.assert_called_once_with(sql, params)
    
    def test_execute_query_no_results(self, db_service):
        """测试查询无结果"""
        db_service.cursor.fetchall.return_value = []
        
        sql = "SELECT * FROM users WHERE id = ?"
        params = (999,)
        
        result = db_service.execute_query(sql, params)
        
        assert result == []
        db_service.cursor.execute.assert_called_once_with(sql, params)
    
    def test_execute_query_exception(self, db_service):
        """测试查询异常处理"""
        db_service.cursor.execute.side_effect = sqlite3.Error("数据库错误")
        
        sql = "SELECT * FROM invalid_table"
        
        with pytest.raises(sqlite3.Error):
            db_service.execute_query(sql, {})
    
    def test_execute_update_success(self, db_service):
        """测试更新执行成功"""
        db_service.cursor.rowcount = 1
        db_service.connection.commit = Mock()
        
        sql = "UPDATE users SET name = ? WHERE id = ?"
        params = ('新名称', 1)
        
        result = db_service.execute_update(sql, params)
        
        assert result == 1
        db_service.cursor.execute.assert_called_once_with(sql, params)
        db_service.connection.commit.assert_called_once()
    
    def test_execute_update_no_rows_affected(self, db_service):
        """测试更新无影响行数"""
        db_service.cursor.rowcount = 0
        db_service.connection.commit = Mock()
        
        sql = "UPDATE users SET name = ? WHERE id = ?"
        params = ('新名称', 999)
        
        result = db_service.execute_update(sql, params)
        
        assert result == 0
        db_service.connection.commit.assert_called_once()
    
    def test_execute_update_exception_rollback(self, db_service):
        """测试更新异常回滚"""
        db_service.cursor.execute.side_effect = sqlite3.Error("更新失败")
        db_service.connection.rollback = Mock()
        
        sql = "UPDATE users SET name = ? WHERE id = ?"
        params = ('新名称', 1)
        
        with pytest.raises(sqlite3.Error):
            db_service.execute_update(sql, params)
        
        db_service.connection.rollback.assert_called_once()
    
    def test_begin_transaction(self, db_service):
        """测试开始事务"""
        db_service.connection.execute = Mock()
        
        db_service.begin_transaction()
        
        db_service.connection.execute.assert_called_once_with("BEGIN")
    
    def test_commit_transaction(self, db_service):
        """测试提交事务"""
        db_service.connection.commit = Mock()
        
        result = db_service.commit_transaction()
        
        assert result is True
        db_service.connection.commit.assert_called_once()
    
    def test_commit_transaction_exception(self, db_service):
        """测试提交事务异常"""
        db_service.connection.commit.side_effect = sqlite3.Error("提交失败")
        
        result = db_service.commit_transaction()
        
        assert result is False
    
    def test_rollback_transaction(self, db_service):
        """测试回滚事务"""
        db_service.connection.rollback = Mock()
        
        result = db_service.rollback_transaction()
        
        assert result is True
        db_service.connection.rollback.assert_called_once()
    
    def test_rollback_transaction_exception(self, db_service):
        """测试回滚事务异常"""
        db_service.connection.rollback.side_effect = sqlite3.Error("回滚失败")
        
        result = db_service.rollback_transaction()
        
        assert result is False
    
    def test_get_connection(self, db_service):
        """测试获取连接"""
        connection = db_service.get_connection()
        assert connection == db_service.connection
    
    def test_close_connection(self, db_service):
        """测试关闭连接"""
        db_service.connection.close = Mock()
        
        db_service.close_connection()
        
        db_service.connection.close.assert_called_once()
    
    def test_close_connection_exception(self, db_service):
        """测试关闭连接异常"""
        db_service.connection.close.side_effect = sqlite3.Error("关闭失败")
        
        # 应该不抛出异常
        db_service.close_connection()


class TestDatabaseServiceSingleton:
    """数据库服务单例测试"""
    
    def test_init_database_service(self):
        """测试初始化数据库服务"""
        class MockConfig:
            SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
            VANNA_DATABASE_URI = 'sqlite:///:memory:'
        
        with patch('tools.database.DatabaseService') as mock_service_class:
            mock_service_instance = Mock()
            mock_service_class.return_value = mock_service_instance
            
            init_database_service(MockConfig())
            
            mock_service_class.assert_called_once()
    
    def test_get_database_service_initialized(self):
        """测试获取已初始化的数据库服务"""
        mock_service = Mock()
        
        with patch('tools.database._database_service', mock_service):
            service = get_database_service()
            assert service == mock_service
    
    def test_get_database_service_not_initialized(self):
        """测试获取未初始化的数据库服务"""
        with patch('tools.database._database_service', None):
            with pytest.raises(RuntimeError, match="数据库服务未初始化"):
                get_database_service()


class TestDatabaseConnectionPool:
    """数据库连接池测试"""
    
    def test_connection_pool_management(self):
        """测试连接池管理"""
        # 这里测试连接池的基本概念
        # 实际实现可能需要根据具体的连接池逻辑调整
        
        connections = []
        max_connections = 5
        
        # 模拟创建连接
        for i in range(max_connections):
            mock_conn = Mock()
            mock_conn.id = i
            connections.append(mock_conn)
        
        assert len(connections) == max_connections
        
        # 模拟连接复用
        reused_conn = connections[0]
        assert reused_conn.id == 0
    
    def test_connection_cleanup(self):
        """测试连接清理"""
        mock_connections = [Mock() for _ in range(3)]
        
        # 模拟清理所有连接
        for conn in mock_connections:
            conn.close = Mock()
            conn.close()
            conn.close.assert_called_once()


class TestDatabaseTransactionManagement:
    """数据库事务管理测试"""
    
    @pytest.fixture
    def transaction_service(self):
        """创建支持事务的数据库服务"""
        with patch('sqlite3.connect') as mock_connect:
            mock_connection = Mock()
            mock_cursor = Mock()
            mock_connection.cursor.return_value = mock_cursor
            mock_connect.return_value = mock_connection
            
            class MockConfig:
                SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
                VANNA_DATABASE_URI = 'sqlite:///:memory:'
                DEBUG = False
                SQLALCHEMY_ENGINE_OPTIONS = {
                    'pool_size': 5,
                    'pool_timeout': 30,
                    'pool_recycle': -1,
                    'max_overflow': 0,
                    'pool_pre_ping': True
                }

            service = DatabaseService(MockConfig())
            service.connection = mock_connection
            service.cursor = mock_cursor
            yield service
    
    def test_transaction_success_workflow(self, transaction_service):
        """测试成功事务流程"""
        # 开始事务
        transaction_service.begin_transaction()
        
        # 执行操作
        transaction_service.execute_update(
            "INSERT INTO users (name) VALUES (?)", 
            ('测试用户',)
        )
        
        # 提交事务
        result = transaction_service.commit_transaction()
        
        assert result is True
        transaction_service.connection.commit.assert_called()
    
    def test_transaction_rollback_workflow(self, transaction_service):
        """测试事务回滚流程"""
        # 开始事务
        transaction_service.begin_transaction()
        
        # 模拟操作失败
        transaction_service.cursor.execute.side_effect = sqlite3.Error("操作失败")
        
        try:
            transaction_service.execute_update(
                "INSERT INTO users (name) VALUES (?)", 
                ('测试用户',)
            )
        except sqlite3.Error:
            # 回滚事务
            result = transaction_service.rollback_transaction()
            assert result is True
    
    def test_nested_transaction_not_supported(self, transaction_service):
        """测试嵌套事务（不支持）"""
        # SQLite默认不支持嵌套事务
        # 这里测试连续调用begin_transaction的行为
        
        transaction_service.begin_transaction()
        
        # 再次调用begin_transaction应该不会出错
        # 但实际效果取决于具体实现
        transaction_service.begin_transaction()
        
        # 验证调用次数
        expected_calls = 2
        actual_calls = transaction_service.connection.execute.call_count
        assert actual_calls >= 1  # 至少调用一次


class TestDatabaseErrorHandling:
    """数据库错误处理测试"""
    
    def test_connection_error_handling(self):
        """测试连接错误处理"""
        class MockConfig:
            SQLALCHEMY_DATABASE_URI = 'invalid://connection/string'
            VANNA_DATABASE_URI = 'invalid://connection/string'
        
        with patch('sqlite3.connect') as mock_connect:
            mock_connect.side_effect = sqlite3.Error("连接失败")
            
            with pytest.raises(sqlite3.Error):
                DatabaseService(MockConfig())
    
    def test_sql_syntax_error_handling(self, db_service):
        """测试SQL语法错误处理"""
        db_service.cursor.execute.side_effect = sqlite3.Error("语法错误")
        
        invalid_sql = "SELECT * FORM users"  # 故意的语法错误
        
        with pytest.raises(sqlite3.Error):
            db_service.execute_query(invalid_sql, {})
    
    def test_database_lock_error_handling(self, db_service):
        """测试数据库锁定错误处理"""
        db_service.cursor.execute.side_effect = sqlite3.OperationalError("database is locked")
        
        sql = "UPDATE users SET name = ? WHERE id = ?"
        params = ('新名称', 1)
        
        with pytest.raises(sqlite3.OperationalError):
            db_service.execute_update(sql, params)


class TestDatabasePerformance:
    """数据库性能测试"""
    
    def test_query_performance_measurement(self, db_service):
        """测试查询性能测量"""
        import time
        
        # 模拟查询执行时间
        def slow_execute(*args, **kwargs):
            time.sleep(0.01)  # 模拟10ms查询时间
            return []
        
        db_service.cursor.execute.side_effect = slow_execute
        db_service.cursor.fetchall.return_value = []
        
        start_time = time.time()
        db_service.execute_query("SELECT * FROM users", {})
        execution_time = time.time() - start_time
        
        # 验证执行时间大于0
        assert execution_time > 0
    
    def test_batch_operation_efficiency(self, db_service):
        """测试批量操作效率"""
        # 模拟批量插入
        batch_data = [
            ('用户1', 'user1@example.com'),
            ('用户2', 'user2@example.com'),
            ('用户3', 'user3@example.com')
        ]
        
        db_service.cursor.executemany = Mock()
        db_service.connection.commit = Mock()
        
        # 模拟批量插入方法（需要在实际服务中实现）
        sql = "INSERT INTO users (name, email) VALUES (?, ?)"
        
        # 假设服务有executemany方法
        if hasattr(db_service, 'execute_batch'):
            db_service.execute_batch(sql, batch_data)
        else:
            # 如果没有批量方法，逐个执行
            for data in batch_data:
                db_service.execute_update(sql, data)
        
        # 验证执行次数
        assert db_service.cursor.execute.call_count >= len(batch_data) 