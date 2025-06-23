"""
用户服务的单元测试
"""
import pytest
import json
from datetime import datetime
from unittest.mock import Mock, patch
from service.user_service import UserService
from tools.redis_service import RedisService
from tools.database import DatabaseService
from service.permission_service import PermissionService
from sqlalchemy import Row, Column

@pytest.fixture
def mock_redis_service():
    redis = Mock(spec=RedisService)
    redis.get_cache.return_value = None
    redis.set_cache.return_value = True
    redis.delete_cache.return_value = True
    return redis

@pytest.fixture
def mock_session():
    session = Mock()
    session.__enter__ = Mock(return_value=session)
    session.__exit__ = Mock(return_value=None)
    return session

@pytest.fixture
def mock_db_service(mock_session):
    db = Mock(spec=DatabaseService)
    db.get_session.return_value = mock_session
    return db

@pytest.fixture
def mock_permission_service():
    permission = Mock(spec=PermissionService)
    permission.get_user_permissions.return_value = []
    return permission

@pytest.fixture
def user_service(mock_redis_service, mock_db_service, mock_permission_service):
    service = UserService(
        redis_service=mock_redis_service,
        db_service=mock_db_service,
        permission_service=mock_permission_service
    )
    # Mock the get_user_by_code method to return no existing user
    service.get_user_by_code = Mock(return_value={'success': False, 'error': 'User not found'})
    return service

def test_create_user_success(user_service, mock_session):
    # Arrange
    user_data = {
        'org_code': 'ORG001',
        'user_code': 'USER001',
        'username': 'testuser',
        'password': 'password123',
        'role_id': 1,
        'phone': '1234567890',
        'address': 'Test Address',
        'status': 1
    }
    
    mock_result = Mock()
    mock_result.lastrowid = 1
    mock_session.execute.return_value = mock_result
    
    # Act
    result = user_service.create_user(user_data)
    
    # Assert
    assert result['success'] is True
    assert result['data']['id'] == 1
    assert result['data']['user_code'] == user_data['user_code']
    assert result['data']['username'] == user_data['username']
    mock_session.commit.assert_called_once()

def test_create_user_missing_fields(user_service):
    # Arrange
    user_data = {
        'org_code': 'ORG001',
        'username': 'testuser',  # missing user_code and other required fields
    }
    
    # Act
    result = user_service.create_user(user_data)
    
    # Assert
    assert result['success'] is False
    assert 'error' in result
    assert '缺少必要字段' in result['error']

def test_get_user_by_id_from_cache(user_service, mock_redis_service):
    # Arrange
    user_id = 1
    cached_user = {
        'id': user_id,
        'user_code': 'USER001',
        'username': 'testuser',
        'status': 1
    }
    mock_redis_service.get_cache.return_value = json.dumps(cached_user)
    
    # Act
    result = user_service.get_user_by_id(user_id)
    
    # Assert
    assert result['success'] is True
    assert result['data'] == cached_user
    mock_redis_service.get_cache.assert_called_once()

def test_get_user_by_id_from_db(user_service, mock_session, mock_redis_service):
    # Arrange
    user_id = 1
    mock_user = Mock()
    mock_user.id = user_id
    mock_user.org_code = 'ORG001'
    mock_user.user_code = 'USER001'
    mock_user.username = 'testuser'
    mock_user.role_id = 1
    mock_user.role_code = 'ROLE001'
    mock_user.org_name = 'Test Org'
    mock_user.status = 1
    mock_user.created_at = datetime.now()
    mock_user.updated_at = None
    
    mock_result = Mock()
    mock_result.fetchone.return_value = mock_user
    mock_session.execute.return_value = mock_result
    mock_redis_service.get_cache.return_value = None
    
    # Act
    result = user_service.get_user_by_id(user_id)
    
    # Assert
    assert result['success'] is True
    assert result['data']['id'] == user_id
    assert result['data']['user_code'] == mock_user.user_code
    mock_redis_service.set_cache.assert_called_once()

def test_verify_password_success(user_service, mock_session):
    # Arrange
    username = 'testuser'
    password = 'password123'
    hashed_password = user_service._hash_password(password)
    
    mock_user = Mock()
    mock_user.id = 1
    mock_user.username = username
    mock_user.password = hashed_password
    mock_user.status = 1
    
    mock_result = Mock()
    mock_result.fetchone.return_value = mock_user
    mock_session.execute.return_value = mock_result
    
    # Act
    result = user_service.verify_password(username, password)
    
    # Assert
    assert result is not None
    assert result['id'] == mock_user.id
    assert result['username'] == mock_user.username

def test_verify_password_failure(user_service, mock_session):
    # Arrange
    username = 'testuser'
    password = 'wrongpassword'
    hashed_password = user_service._hash_password('correctpassword')
    
    mock_user = Mock()
    mock_user.id = 1
    mock_user.username = username
    mock_user.password = hashed_password
    mock_user.status = 1
    
    mock_result = Mock()
    mock_result.fetchone.return_value = mock_user
    mock_session.execute.return_value = mock_result
    
    # Act
    result = user_service.verify_password(username, password)
    
    # Assert
    assert result is None

def test_authenticate_user_success(user_service):
    # Arrange
    username = 'testuser'
    password = 'password123'
    mock_user = {
        'id': 1,
        'username': username,
        'status': 1,
        'user_code': 'USER001',
        'org_code': 'ORG001',
        'role_code': 'ROLE001'
    }
    
    mock_tokens = {
        'access_token': 'test_access_token',
        'refresh_token': 'test_refresh_token',
        'token_type': 'Bearer',
        'expires_in': 1800
    }
    
    with patch.object(user_service, 'verify_password', return_value=mock_user), \
         patch.object(user_service, 'create_tokens', return_value=mock_tokens):
        # Act
        result = user_service.authenticate_user(username, password)
        
        # Assert
        assert result['success'] is True
        assert result['data']['user'] == mock_user
        assert result['data']['access_token'] == mock_tokens['access_token']
        assert result['data']['refresh_token'] == mock_tokens['refresh_token']

def test_authenticate_user_failure(user_service):
    # Arrange
    username = 'testuser'
    password = 'wrongpassword'
    
    with patch.object(user_service, 'verify_password', return_value=None):
        # Act
        result = user_service.authenticate_user(username, password)
        
        # Assert
        assert result['success'] is False
        assert 'error' in result

def test_update_user_success(user_service, mock_session):
    # Arrange
    user_id = 1
    update_data = {
        'username': 'newusername',
        'phone': '9876543210'
    }
    
    # Mock the get_user_by_id method
    user_service._get_user_by_id_without_status_check = Mock(return_value={
        'success': True,
        'data': {
            'id': user_id,
            'user_code': 'USER001',
            'username': 'oldusername'
        }
    })
    
    mock_result = Mock()
    mock_result.rowcount = 1
    mock_session.execute.return_value = mock_result
    
    # Act
    result = user_service.update_user(user_id, update_data)
    
    # Assert
    assert result['success'] is True
    mock_session.commit.assert_called_once()

def test_delete_user_success(user_service, mock_session):
    # Arrange
    user_id = 1
    
    # Mock the get_user_by_id method
    user_service._get_user_by_id_without_status_check = Mock(return_value={
        'success': True,
        'data': {
            'id': user_id,
            'user_code': 'USER001',
            'username': 'testuser'
        }
    })
    
    mock_result = Mock()
    mock_result.rowcount = 1
    mock_session.execute.return_value = mock_result
    
    # Act
    result = user_service.delete_user(user_id)
    
    # Assert
    assert result['success'] is True
    mock_session.commit.assert_called_once()

def test_get_users_list(user_service, mock_session):
    # Arrange
    now = datetime.now()
    
    # Create mock users using SQLAlchemy Row
    def create_row(**kwargs):
        row = Mock(spec=Row)
        for key, value in kwargs.items():
            setattr(row, key, value)
        return row
    
    mock_users = [
        create_row(
            id=1,
            username='user1',
            user_code='USER001',
            org_code='ORG001',
            role_id=1,
            role_code='ROLE001',
            org_name='Test Org',
            status=1,
            created_at=now,
            updated_at=None
        ),
        create_row(
            id=2,
            username='user2',
            user_code='USER002',
            org_code='ORG001',
            role_id=1,
            role_code='ROLE001',
            org_name='Test Org',
            status=1,
            created_at=now,
            updated_at=None
        )
    ]
    
    # Create a list-like object that also has fetchall
    class ListWithFetchall(list):
        def fetchall(self):
            return self
    
    # Create the list result object
    list_result = ListWithFetchall(mock_users)
    
    # Create the count result object
    count_result = Mock()
    count_result.scalar.return_value = 2
    
    # Mock the Redis service
    mock_redis = Mock()
    mock_redis.get_cache.return_value = None
    mock_redis.set_cache.return_value = True
    
    # Patch the get_redis_service function
    with patch('service.user_service.get_redis_service', return_value=mock_redis):
        # Set up the side effect sequence for execute
        mock_session.execute.side_effect = [count_result, list_result]  # Swap the order since count is queried first
        
        # Act
        result = user_service.get_users_list(page=1, page_size=10)
        
        # Assert
        assert result['success'] is True
        assert result['data']['total'] == 2
        assert len(result['data']['items']) == 2
        assert result['data']['items'][0]['username'] == 'user1'
        assert result['data']['items'][1]['username'] == 'user2' 