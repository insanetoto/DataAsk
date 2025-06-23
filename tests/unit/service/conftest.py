"""
服务测试的配置文件
"""
import pytest
from unittest.mock import MagicMock, Mock
from contextlib import contextmanager

class MockSession:
    def __init__(self):
        self.execute = Mock()
        self.commit = Mock()
        self.rollback = Mock()
        self.close = Mock()
        self.get = Mock()
        self.query = Mock()
        self.add = Mock()
        self.refresh = Mock()
        self.scalar = Mock()
        self.scalars = Mock()
        self.delete = Mock()
        self.merge = Mock()
        self.flush = Mock()

class MockContextManager:
    def __init__(self, session):
        self.session = session
        
    def __enter__(self):
        return self.session
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.session.rollback()
        else:
            self.session.commit()
        self.session.close()

class MockDatabaseService:
    def __init__(self):
        self.session = MockSession()
        self.execute_query = Mock()
        self.execute_update = Mock()
        
    def get_session(self):
        return MockContextManager(self.session)

@pytest.fixture
def db_service():
    """创建模拟数据库服务"""
    return MockDatabaseService()

@pytest.fixture
def redis_service():
    """创建模拟Redis服务"""
    mock_redis = MagicMock()
    mock_redis.get_cache.return_value = None
    mock_redis.set_cache.return_value = True
    mock_redis.delete_cache.return_value = True
    mock_redis.delete_pattern.return_value = True
    mock_redis.get_keys_by_pattern.return_value = []
    return mock_redis 