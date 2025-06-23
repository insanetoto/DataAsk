# -*- coding: utf-8 -*-
"""
权限服务测试模块
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from service.permission_service import PermissionService
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
def mock_role_service():
    role_service = Mock()
    return role_service

@pytest.fixture
def permission_service(mock_redis_service, mock_db_service, mock_role_service):
    service = PermissionService(
        redis_service=mock_redis_service,
        db_service=mock_db_service,
        role_service=mock_role_service
    )
    return service

def test_get_user_permissions_from_cache(permission_service, mock_redis_service):
    # 准备测试数据
    user_id = 1
    cached_permissions = [
        {
            'id': 1,
            'permission_code': 'test.read',
            'permission_name': 'Test Read',
            'api_path': '/api/test',
            'api_method': 'GET',
            'status': 1
        }
    ]
    mock_redis_service.get_cache.return_value = json.dumps(cached_permissions)
    
    # 执行测试
    result = permission_service.get_user_permissions(user_id)
    
    # 验证结果
    assert result['success'] is True
    assert result['data'] == cached_permissions
    mock_redis_service.get_cache.assert_called_once()

def test_get_user_permissions_from_db(permission_service, mock_redis_service, mock_db_service):
    # 准备测试数据
    user_id = 1
    mock_permission = MagicMock()
    mock_permission.id = 1
    mock_permission.permission_code = 'test.read'
    mock_permission.permission_name = 'Test Read'
    mock_permission.api_path = '/api/test'
    mock_permission.api_method = 'GET'
    mock_permission.resource_type = 'test'
    mock_permission.description = 'Test permission'
    mock_permission.status = 1
    
    mock_redis_service.get_cache.return_value = None
    mock_db_service.session.execute.return_value.fetchall.return_value = [mock_permission]
    
    # 执行测试
    result = permission_service.get_user_permissions(user_id)
    
    # 验证结果
    assert result['success'] is True
    assert len(result['data']) == 1
    assert result['data'][0]['permission_code'] == 'test.read'
    mock_redis_service.get_cache.assert_called_once()
    mock_redis_service.set_cache.assert_called_once()

def test_check_permission_success(permission_service):
    # 准备测试数据
    user_id = 1
    permission_code = 'test.read'
    user_permissions = {
        'success': True,
        'data': [
            {
                'permission_code': 'test.read',
                'status': 1
            }
        ]
    }
    
    # Mock get_user_permissions方法
    with patch.object(permission_service, 'get_user_permissions', return_value=user_permissions):
        result = permission_service.check_permission(user_id, permission_code)
    
    # 验证结果
    assert result['success'] is True
    assert result['data']['has_permission'] is True

def test_check_permission_failure(permission_service):
    # 准备测试数据
    user_id = 1
    permission_code = 'test.write'
    user_permissions = {
        'success': True,
        'data': [
            {
                'permission_code': 'test.read',
                'status': 1
            }
        ]
    }
    
    # Mock get_user_permissions方法
    with patch.object(permission_service, 'get_user_permissions', return_value=user_permissions):
        result = permission_service.check_permission(user_id, permission_code)
    
    # 验证结果
    assert result['success'] is True
    assert result['data']['has_permission'] is False

def test_assign_permissions_to_role(permission_service, mock_db_service):
    # 准备测试数据
    role_id = 1
    permission_codes = ['test.read', 'test.write']
    
    # 模拟数据库返回
    mock_role = MagicMock()
    mock_role.id = role_id
    mock_role.role_code = 'TEST_ROLE'
    mock_role.role_name = 'Test Role'
    mock_role.permissions = []
    
    mock_permission1 = MagicMock()
    mock_permission1.permission_code = 'test.read'
    mock_permission2 = MagicMock()
    mock_permission2.permission_code = 'test.write'
    
    mock_db_service.session.get.return_value = mock_role
    mock_db_service.session.query.return_value.filter.return_value.all.return_value = [mock_permission1, mock_permission2]
    
    # 执行测试
    result = permission_service.assign_permissions_to_role(role_id, permission_codes)
    
    # 验证结果
    assert result['success'] is True
    assert result['message'] == '权限分配成功'

def test_revoke_permissions_from_role(permission_service, mock_db_service):
    # 准备测试数据
    role_id = 1
    permission_ids = [1, 2]
    
    # 模拟数据库返回
    mock_role = MagicMock()
    mock_role.id = role_id
    mock_role.role_code = 'TEST_ROLE'
    mock_role.role_name = 'Test Role'
    mock_role.permissions = []
    
    mock_permission1 = MagicMock()
    mock_permission1.id = 1
    mock_permission2 = MagicMock()
    mock_permission2.id = 2
    
    mock_db_service.session.get.return_value = mock_role
    mock_db_service.session.query.return_value.filter.return_value.all.return_value = [mock_permission1, mock_permission2]
    
    # 执行测试
    result = permission_service.revoke_permissions_from_role(role_id, permission_ids)
    
    # 验证结果
    assert result['success'] is True
    assert result['message'] == '权限移除成功' 