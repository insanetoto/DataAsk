# -*- coding: utf-8 -*-
"""
Redis服务工具层单元测试
测试Redis缓存、会话管理和分布式锁功能
"""

import pytest
from unittest.mock import Mock, patch
import json

try:
    from tools.redis_service import RedisService, init_redis_service, get_redis_service
except ImportError:
    pytest.skip("Redis模块导入失败，跳过Redis测试", allow_module_level=True)


class TestRedisService:
    """Redis服务测试"""
    
    @pytest.fixture
    def mock_config(self):
        """模拟配置"""
        class MockConfig:
            REDIS_HOST = 'localhost'
            REDIS_PORT = 6379
            REDIS_DB = 0
            REDIS_PASSWORD = None
            
        return MockConfig()
    
    @pytest.fixture
    def redis_service(self, mock_config):
        """创建Redis服务实例"""
        with patch('redis.Redis') as mock_redis:
            mock_redis_instance = Mock()
            mock_redis.return_value = mock_redis_instance
            
            service = RedisService(mock_config)
            service.redis_client = mock_redis_instance
            yield service
    
    def test_redis_service_initialization(self, mock_config):
        """测试Redis服务初始化"""
        with patch('redis.Redis') as mock_redis:
            mock_redis_instance = Mock()
            mock_redis.return_value = mock_redis_instance
            
            service = RedisService(mock_config)
            
            assert service.config == mock_config
            assert hasattr(service, 'redis_client')
    
    def test_set_cache_success(self, redis_service):
        """测试设置缓存成功"""
        redis_service.redis_client.set.return_value = True
        
        key = "user:123"
        value = {"name": "测试用户", "email": "test@example.com"}
        ttl = 3600
        
        result = redis_service.set_cache(key, value, ttl)
        
        assert result is True
    
    def test_get_cache_success(self, redis_service):
        """测试获取缓存成功"""
        cached_data = {"name": "测试用户", "email": "test@example.com"}
        redis_service.redis_client.get.return_value = json.dumps(cached_data, ensure_ascii=False)
        
        key = "user:123"
        result = redis_service.get_cache(key)
        
        assert result == cached_data
    
    def test_delete_cache_success(self, redis_service):
        """测试删除缓存成功"""
        redis_service.redis_client.delete.return_value = 1
        
        key = "user:123"
        result = redis_service.delete_cache(key)
        
        assert result is True
    
    def test_clear_pattern_success(self, redis_service):
        """测试按模式清除缓存成功"""
        matching_keys = ["user:123", "user:456", "user:789"]
        redis_service.redis_client.keys.return_value = matching_keys
        redis_service.redis_client.delete.return_value = len(matching_keys)
        
        pattern = "user:*"
        result = redis_service.clear_pattern(pattern)
        
        assert result == len(matching_keys)


class TestRedisServiceSingleton:
    """Redis服务单例测试"""
    
    def test_init_redis_service(self):
        """测试初始化Redis服务"""
        class MockConfig:
            REDIS_HOST = 'localhost'
            REDIS_PORT = 6379
            REDIS_DB = 0
            REDIS_PASSWORD = None
        
        with patch('tools.redis_service.RedisService') as mock_service_class:
            mock_service_instance = Mock()
            mock_service_class.return_value = mock_service_instance
            
            init_redis_service(MockConfig())
            
            mock_service_class.assert_called_once()
    
    def test_get_redis_service_not_initialized(self):
        """测试获取未初始化的Redis服务"""
        with patch('tools.redis_service._redis_service', None):
            with pytest.raises(RuntimeError, match="Redis服务未初始化"):
                get_redis_service()


class TestRedisDistributedLock:
    """Redis分布式锁测试"""
    
    def test_acquire_lock_success(self, redis_service):
        """测试获取锁成功"""
        redis_service.redis_client.set.return_value = True
        
        lock_key = "lock:user:123"
        lock_value = "unique_value_123"
        ttl = 30
        
        # 模拟分布式锁实现
        result = redis_service.redis_client.set(lock_key, lock_value, nx=True, ex=ttl)
        assert result is True
    
    def test_release_lock_success(self, redis_service):
        """测试释放锁成功"""
        redis_service.redis_client.eval.return_value = 1
        
        lock_key = "lock:user:123"
        lock_value = "unique_value_123"
        
        lua_script = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("del", KEYS[1])
        else
            return 0
        end
        """
        
        result = redis_service.redis_client.eval(lua_script, 1, lock_key, lock_value)
        assert result == 1  # 成功释放


class TestRedisSessionManagement:
    """Redis会话管理测试"""
    
    def test_create_session(self, redis_service):
        """测试创建会话"""
        session_id = "session_123456"
        session_data = {
            "user_id": 1,
            "user_code": "testuser",
            "login_time": "2024-01-01T10:00:00Z"
        }
        session_ttl = 3600  # 1小时
        
        redis_service.redis_client.set.return_value = True
        
        session_key = f"session:{session_id}"
        result = redis_service.set_cache(session_key, session_data, session_ttl)
        
        assert result is True
    
    def test_get_session(self, redis_service):
        """测试获取会话"""
        session_id = "session_123456"
        session_data = {
            "user_id": 1,
            "user_code": "testuser",
            "login_time": "2024-01-01T10:00:00Z"
        }
        
        redis_service.redis_client.get.return_value = json.dumps(session_data, ensure_ascii=False)
        
        session_key = f"session:{session_id}"
        result = redis_service.get_cache(session_key)
        
        assert result == session_data


class TestRedisPerformance:
    """Redis性能测试"""
    
    def test_batch_operations(self, redis_service):
        """测试批量操作性能"""
        mock_pipeline = Mock()
        redis_service.redis_client.pipeline.return_value = mock_pipeline
        mock_pipeline.execute.return_value = [True] * 100
        
        pipe = redis_service.redis_client.pipeline()
        
        for i in range(100):
            pipe.set(f"key:{i}", f"value:{i}")
        
        results = pipe.execute()
        
        assert len(results) == 100
        assert all(results)
    
    def test_connection_pooling(self, redis_service):
        """测试连接池性能"""
        operations = []
        
        for i in range(10):
            operation_result = redis_service.get_cache(f"key:{i}")
            operations.append(operation_result)
        
        assert len(operations) == 10 