import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from service.user_service import UserService
from tools.redis_service import RedisService
from tools.database import DatabaseService
import json

@pytest.fixture
def mock_redis_service():
    redis_service = Mock(spec=RedisService)
    return redis_service

@pytest.fixture
def mock_db_service(db_service):
    """使用conftest.py中定义的db_service"""
    return db_service

@pytest.fixture
def mock_permission_service():
    permission_service = Mock()
    return permission_service

@pytest.fixture
def user_service(mock_redis_service, mock_db_service, mock_permission_service):
    service = UserService(
        redis_service=mock_redis_service,
        db_service=mock_db_service,
        permission_service=mock_permission_service
    )
    return service

def test_create_user_success(user_service, mock_db_service):
    # 准备测试数据
    test_user_data = {
        'org_code': 'TEST_ORG',
        'user_code': 'TEST_USER',
        'username': 'Test User',
        'password': 'test_password',
        'role_id': 1
    }
    
    # 模拟数据库返回
    mock_result = Mock()
    mock_result.lastrowid = 1
    mock_db_service.session.execute.return_value = mock_result
    
    # 模拟get_user_by_code返回空结果
    with patch.object(user_service, 'get_user_by_code', return_value={'success': True, 'data': None}):
        result = user_service.create_user(test_user_data)
    
    assert result['success'] is True
    assert result['data']['id'] == 1
    assert result['data']['user_code'] == test_user_data['user_code']
    assert result['data']['username'] == test_user_data['username']

def test_create_user_duplicate_code(user_service):
    # 准备测试数据
    test_user_data = {
        'org_code': 'TEST_ORG',
        'user_code': 'EXISTING_USER',
        'username': 'Test User',
        'password': 'test_password',
        'role_id': 1
    }
    
    # 模拟get_user_by_code返回已存在的用户
    with patch.object(user_service, 'get_user_by_code', 
                     return_value={'success': True, 'data': {'user_code': 'EXISTING_USER'}}):
        result = user_service.create_user(test_user_data)
    
    assert result['success'] is False
    assert '已存在' in result['error']

def test_get_user_by_id_from_cache(user_service, mock_redis_service):
    # 准备缓存数据
    cached_user = {
        'id': 1,
        'user_code': 'TEST_USER',
        'username': 'Test User',
        'status': 1
    }
    mock_redis_service.get_cache.return_value = json.dumps(cached_user)
    
    result = user_service.get_user_by_id(1)
    
    assert result['success'] is True
    assert result['data']['id'] == cached_user['id']
    assert result['data']['user_code'] == cached_user['user_code']
    mock_redis_service.get_cache.assert_called_once()

def test_get_user_by_id_from_db(user_service, mock_redis_service, mock_db_service):
    # 模拟缓存未命中
    mock_redis_service.get_cache.return_value = None
    
    # 模拟数据库返回
    mock_db_result = Mock()
    mock_db_result.id = 1
    mock_db_result.org_code = 'TEST_ORG'
    mock_db_result.user_code = 'TEST_USER'
    mock_db_result.username = 'Test User'
    mock_db_result.role_id = 1
    mock_db_result.role_code = 'ADMIN'
    mock_db_result.org_name = 'Test Org'
    mock_db_result.status = 1
    mock_db_result.created_at = datetime.now()
    mock_db_result.updated_at = None
    
    mock_db_service.session.execute.return_value.fetchone.return_value = mock_db_result
    
    result = user_service.get_user_by_id(1)
    
    assert result['success'] is True
    assert result['data']['id'] == mock_db_result.id
    assert result['data']['user_code'] == mock_db_result.user_code
    mock_redis_service.set_cache.assert_called_once() 