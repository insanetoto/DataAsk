import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from service.role_service import RoleService
from tools.redis_service import RedisService
from tools.database import DatabaseService
import json

@pytest.fixture
def mock_redis_service():
    redis_service = Mock()
    redis_service.get_cache.return_value = None
    redis_service.set_cache.return_value = True
    redis_service.delete_cache.return_value = True
    redis_service.delete_pattern.return_value = True
    return redis_service

@pytest.fixture
def mock_db_service(db_service):
    """使用conftest.py中定义的db_service"""
    return db_service

@pytest.fixture
def role_service(mock_redis_service, mock_db_service):
    service = RoleService(
        redis_service=mock_redis_service,
        db_service=mock_db_service
    )
    return service

def test_create_role_success(role_service, mock_db_service, mock_redis_service):
    # 准备测试数据
    test_role_data = {
        'role_code': 'TEST_ROLE',
        'role_name': 'Test Role',
        'role_level': 3,  # 普通角色
        'description': 'Test role description'
    }
    
    # 模拟get_role_by_code返回空结果
    with patch.object(role_service, 'get_role_by_code', return_value={'success': True, 'data': None}):
        result = role_service.create_role(test_role_data)
    
    assert result['success'] is True
    mock_db_service.session.add.assert_called_once()
    mock_db_service.session.commit.assert_called()

def test_create_role_duplicate_code(role_service):
    # 准备测试数据
    test_role_data = {
        'role_code': 'EXISTING_ROLE',
        'role_name': 'Test Role',
        'role_level': 3
    }
    
    # 模拟get_role_by_code返回已存在的角色
    with patch.object(role_service, 'get_role_by_code', 
                     return_value={'success': True, 'data': {'role_code': 'EXISTING_ROLE'}}):
        result = role_service.create_role(test_role_data)
    
    assert result['success'] is False
    assert '已存在' in result['error']

def test_get_role_by_id_from_cache(role_service, mock_redis_service):
    # 准备缓存数据
    cached_role = {
        'id': 1,
        'role_code': 'TEST_ROLE',
        'role_name': 'Test Role',
        'role_level': 3,
        'status': 1
    }
    mock_redis_service.get_cache.return_value = json.dumps(cached_role)
    
    result = role_service.get_role_by_id(1)
    
    assert result['success'] is True
    assert result['data']['id'] == cached_role['id']
    assert result['data']['role_code'] == cached_role['role_code']
    mock_redis_service.get_cache.assert_called_once()

def test_get_role_by_id_from_db(role_service, mock_redis_service, mock_db_service):
    # 模拟缓存未命中
    mock_redis_service.get_cache.return_value = None
    
    # 模拟数据库返回
    mock_role = Mock()
    mock_role.to_dict.return_value = {
        'id': 1,
        'role_code': 'TEST_ROLE',
        'role_name': 'Test Role',
        'role_level': 3,
        'status': 1
    }
    
    mock_db_service.session.get.return_value = mock_role
    
    result = role_service.get_role_by_id(1)
    
    assert result['success'] is True
    assert result['data']['id'] == 1
    assert result['data']['role_code'] == 'TEST_ROLE'
    mock_redis_service.set_cache.assert_called_once()

def test_get_roles_list(role_service, mock_redis_service, mock_db_service):
    # 准备测试数据
    test_roles = [
        Mock(to_dict=lambda: {
            'id': 1,
            'role_code': 'ROLE1',
            'role_name': 'Role 1',
            'role_level': 3,
            'status': 1
        }),
        Mock(to_dict=lambda: {
            'id': 2,
            'role_code': 'ROLE2',
            'role_name': 'Role 2',
            'role_level': 3,
            'status': 1
        })
    ]
    
    # 模拟缓存未命中
    mock_redis_service.get_cache.return_value = None
    
    # 模拟数据库查询结果 - 需要正确设置scalars和scalar方法
    mock_result = Mock()
    mock_result.all.return_value = test_roles
    mock_db_service.session.scalars.return_value = mock_result
    mock_db_service.session.scalar.return_value = len(test_roles)
    
    result = role_service.get_roles_list(page=1, page_size=10)
    
    assert result['success'] is True
    assert len(result['data']['list']) == 2
    assert result['data']['pagination']['total'] == 2
    mock_redis_service.set_cache.assert_called_once()

def test_update_role(role_service, mock_db_service, mock_redis_service):
    # 准备测试数据
    role_id = 1
    update_data = {
        'role_name': 'Updated Role Name',
        'description': 'Updated description'
    }
    
    # 模拟数据库返回
    mock_role = Mock()
    mock_role.to_dict.return_value = {
        'id': role_id,
        'role_code': 'TEST_ROLE',
        'role_name': update_data['role_name'],
        'description': update_data['description'],
        'status': 1
    }
    
    mock_db_service.session.get.return_value = mock_role
    
    result = role_service.update_role(role_id, update_data)
    
    assert result['success'] is True
    assert result['data']['role_name'] == update_data['role_name']
    assert result['data']['description'] == update_data['description']
    mock_db_service.session.commit.assert_called() 