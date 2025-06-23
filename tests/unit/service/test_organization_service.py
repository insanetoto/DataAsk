import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from service.organization_service import OrganizationService
from tools.redis_service import RedisService
from tools.database import DatabaseService
import json

@pytest.fixture
def mock_redis_service():
    redis_service = Mock(spec=RedisService)
    return redis_service

@pytest.fixture
def mock_db_service():
    db_service = Mock(spec=DatabaseService)
    return db_service

@pytest.fixture
def organization_service(mock_redis_service, mock_db_service):
    service = OrganizationService(
        redis_service=mock_redis_service,
        db_service=mock_db_service
    )
    return service

def test_create_organization_success(organization_service, mock_db_service):
    # 准备测试数据
    test_org_data = {
        'org_code': 'TEST_ORG',
        'org_name': 'Test Organization',
        'contact_person': 'Test Person',
        'contact_phone': '1234567890',
        'contact_email': 'test@example.com'
    }
    
    # 模拟get_organization_by_code返回空结果
    with patch.object(organization_service, 'get_organization_by_code', return_value={'success': True, 'data': None}):
        result = organization_service.create_organization(test_org_data)
    
    assert result['success'] is True
    mock_db_service.execute_update.assert_called_once()

def test_create_organization_duplicate_code(organization_service):
    # 准备测试数据
    test_org_data = {
        'org_code': 'EXISTING_ORG',
        'org_name': 'Test Organization',
        'contact_person': 'Test Person',
        'contact_phone': '1234567890',
        'contact_email': 'test@example.com'
    }
    
    # 模拟get_organization_by_code返回已存在的组织
    with patch.object(organization_service, 'get_organization_by_code', 
                     return_value={'success': True, 'data': {'org_code': 'EXISTING_ORG'}}):
        result = organization_service.create_organization(test_org_data)
    
    assert result['success'] is False
    assert '已存在' in result['error']

def test_get_organization_by_id_from_cache(organization_service, mock_redis_service):
    # 准备缓存数据
    cached_org = {
        'id': 1,
        'org_code': 'TEST_ORG',
        'org_name': 'Test Organization',
        'status': 1
    }
    mock_redis_service.get_cache.return_value = json.dumps(cached_org)
    
    result = organization_service.get_organization_by_id(1)
    
    assert result['success'] is True
    assert result['data']['id'] == cached_org['id']
    assert result['data']['org_code'] == cached_org['org_code']
    mock_redis_service.get_cache.assert_called_once()

def test_get_organization_by_id_from_db(organization_service, mock_redis_service, mock_db_service):
    # 模拟缓存未命中
    mock_redis_service.get_cache.return_value = None
    
    # 模拟数据库返回
    db_org = {
        'id': 1,
        'org_code': 'TEST_ORG',
        'org_name': 'Test Organization',
        'status': 1,
        'created_at': datetime.now(),
        'updated_at': None
    }
    mock_db_service.execute_query.return_value = [db_org]
    
    result = organization_service.get_organization_by_id(1)
    
    assert result['success'] is True
    assert result['data']['id'] == db_org['id']
    assert result['data']['org_code'] == db_org['org_code']
    mock_redis_service.set_cache.assert_called_once()

def test_get_organizations_list(organization_service, mock_redis_service, mock_db_service):
    # 准备测试数据
    test_orgs = [
        {
            'id': 1,
            'org_code': 'ORG1',
            'org_name': 'Organization 1',
            'status': 1
        },
        {
            'id': 2,
            'org_code': 'ORG2',
            'org_name': 'Organization 2',
            'status': 1
        }
    ]
    
    # 模拟缓存未命中
    mock_redis_service.get_cache.return_value = None
    
    # 模拟数据库查询结果
    mock_db_service.execute_query.side_effect = [
        [{'total': 2}],  # 总数查询结果
        test_orgs  # 列表查询结果
    ]
    
    result = organization_service.get_organizations_list(page=1, page_size=10)
    
    assert result['success'] is True
    assert len(result['data']['list']) == 2
    assert result['data']['pagination']['total'] == 2
    mock_redis_service.set_cache.assert_called_once()

def test_update_organization(organization_service, mock_db_service):
    # 准备测试数据
    org_id = 1
    update_data = {
        'org_name': 'Updated Organization Name',
        'contact_person': 'Updated Person'
    }
    
    # 模拟_get_organization_by_id_without_status_check返回现有组织
    existing_org = {
        'success': True,
        'data': {
            'id': org_id,
            'org_code': 'TEST_ORG',
            'org_name': 'Old Name',
            'status': 1
        }
    }
    with patch.object(organization_service, '_get_organization_by_id_without_status_check', 
                     return_value=existing_org):
        result = organization_service.update_organization(org_id, update_data)
    
    assert result['success'] is True
    mock_db_service.execute_update.assert_called_once()

def test_delete_organization(organization_service, mock_db_service):
    # 准备测试数据
    org_id = 1
    
    # 模拟_get_organization_by_id_without_status_check返回现有组织
    existing_org = {
        'success': True,
        'data': {
            'id': org_id,
            'org_code': 'TEST_ORG',
            'org_name': 'Test Organization',
            'status': 1
        }
    }
    
    # 模拟数据库查询返回
    mock_db_service.execute_query.side_effect = [
        [{'count': 0}],  # 子机构查询结果
        [{'count': 0}]   # 用户查询结果
    ]
    
    # 模拟get_organization_children返回空列表
    with patch.object(organization_service, '_get_organization_by_id_without_status_check',
                     return_value=existing_org), \
         patch.object(organization_service, 'get_organization_children',
                     return_value={'success': True, 'data': []}):
        result = organization_service.delete_organization(org_id)
    
    assert result['success'] is True
    mock_db_service.execute_update.assert_called_once() 