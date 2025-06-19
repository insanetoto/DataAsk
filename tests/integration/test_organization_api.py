# -*- coding: utf-8 -*-
"""
机构管理API集成测试
测试完整的API请求响应流程
"""

import pytest
import json
from unittest.mock import patch
from flask import url_for


class TestOrganizationAPI:
    """机构管理API测试类"""

    def test_create_organization_api_success(self, client, organization_test_data):
        """测试创建机构API成功"""
        org_data = organization_test_data['valid_org']
        
        with patch('service.organization_service.OrganizationService') as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.create_organization.return_value = {
                'success': True,
                'data': {**org_data, 'id': 1},
                'message': '机构创建成功'
            }
            
            response = client.post(
                '/api/v1/organizations',
                data=json.dumps(org_data),
                content_type='application/json'
            )
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            assert data['message'] == '机构创建成功'
            assert data['data']['org_code'] == org_data['org_code']

    def test_create_organization_api_invalid_data(self, client):
        """测试创建机构API - 无效数据"""
        invalid_data = {'org_code': ''}  # 空机构编码
        
        response = client.post(
            '/api/v1/organizations',
            data=json.dumps(invalid_data),
            content_type='application/json'
        )
        
        # 应该返回400状态码或错误响应
        data = json.loads(response.data)
        assert data['success'] is False

    def test_create_organization_api_missing_content_type(self, client, organization_test_data):
        """测试创建机构API - 缺少Content-Type"""
        org_data = organization_test_data['valid_org']
        
        response = client.post(
            '/api/v1/organizations',
            data=json.dumps(org_data)
            # 不设置content_type
        )
        
        # 应该返回400状态码
        assert response.status_code == 400

    def test_get_organization_by_id_api_success(self, client, organization_test_data):
        """测试根据ID获取机构API成功"""
        org_data = organization_test_data['valid_org']
        org_id = 1
        
        with patch('service.organization_service.OrganizationService') as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.get_organization_by_id.return_value = {
                'success': True,
                'data': org_data
            }
            
            response = client.get(f'/api/v1/organizations/{org_id}')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            assert data['data']['org_code'] == org_data['org_code']

    def test_get_organization_by_id_api_not_found(self, client):
        """测试根据ID获取机构API - 机构不存在"""
        org_id = 999
        
        with patch('service.organization_service.OrganizationService') as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.get_organization_by_id.return_value = {
                'success': False,
                'error': '机构不存在'
            }
            
            response = client.get(f'/api/v1/organizations/{org_id}')
            
            assert response.status_code == 404
            data = json.loads(response.data)
            assert data['success'] is False
            assert data['error'] == '机构不存在'

    def test_get_organization_by_code_api_success(self, client, organization_test_data):
        """测试根据编码获取机构API成功"""
        org_data = organization_test_data['valid_org']
        org_code = org_data['org_code']
        
        with patch('service.organization_service.OrganizationService') as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.get_organization_by_code.return_value = {
                'success': True,
                'data': org_data
            }
            
            response = client.get(f'/api/v1/organizations/code/{org_code}')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            assert data['data']['org_code'] == org_code

    def test_get_organizations_list_api_success(self, client, organization_test_data):
        """测试获取机构列表API成功"""
        org_list = [organization_test_data['valid_org']]
        
        with patch('service.organization_service.OrganizationService') as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.get_organizations_list.return_value = {
                'success': True,
                'data': {
                    'list': org_list,
                    'pagination': {
                        'page': 1,
                        'page_size': 10,
                        'total': 1,
                        'total_pages': 1,
                        'has_next': False,
                        'has_prev': False
                    }
                }
            }
            
            response = client.get('/api/v1/organizations')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            assert len(data['data']['list']) == 1
            assert data['data']['pagination']['total'] == 1

    def test_get_organizations_list_api_with_params(self, client):
        """测试获取机构列表API - 带查询参数"""
        with patch('service.organization_service.OrganizationService') as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.get_organizations_list.return_value = {
                'success': True,
                'data': {
                    'list': [],
                    'pagination': {
                        'page': 2,
                        'page_size': 5,
                        'total': 0,
                        'total_pages': 0,
                        'has_next': False,
                        'has_prev': True
                    }
                }
            }
            
            response = client.get(
                '/api/v1/organizations?page=2&page_size=5&status=1&keyword=测试'
            )
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            
            # 验证服务被正确调用
            mock_service.get_organizations_list.assert_called_once_with(
                page=2,
                page_size=5,
                status=1,
                keyword='测试'
            )

    def test_update_organization_api_success(self, client, organization_test_data):
        """测试更新机构API成功"""
        org_data = organization_test_data['valid_org']
        org_id = 1
        update_data = {'org_name': '更新后的机构名称'}
        
        with patch('service.organization_service.OrganizationService') as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.update_organization.return_value = {
                'success': True,
                'data': {**org_data, **update_data},
                'message': '机构更新成功'
            }
            
            response = client.put(
                f'/api/v1/organizations/{org_id}',
                data=json.dumps(update_data),
                content_type='application/json'
            )
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            assert data['message'] == '机构更新成功'
            assert data['data']['org_name'] == update_data['org_name']

    def test_delete_organization_api_success(self, client):
        """测试删除机构API成功"""
        org_id = 1
        
        with patch('service.organization_service.OrganizationService') as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.delete_organization.return_value = {
                'success': True,
                'message': '机构删除成功'
            }
            
            response = client.delete(f'/api/v1/organizations/{org_id}')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            assert data['message'] == '机构删除成功'

    def test_clear_organization_cache_api_success(self, client):
        """测试清除机构缓存API成功"""
        with patch('service.organization_service.OrganizationService') as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.clear_organization_cache.return_value = {
                'success': True,
                'message': '机构缓存已清除 (10 个缓存键)'
            }
            
            response = client.post('/api/v1/organizations/cache/clear')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            assert '缓存已清除' in data['message']

    def test_api_error_handling(self, client):
        """测试API错误处理"""
        with patch('service.organization_service.OrganizationService') as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.get_organization_by_id.side_effect = Exception("服务异常")
            
            response = client.get('/api/v1/organizations/1')
            
            assert response.status_code == 500
            data = json.loads(response.data)
            assert data['success'] is False
            assert 'error' in data

    def test_api_validation_error(self, client):
        """测试API参数验证错误"""
        # 测试无效的机构ID
        response = client.get('/api/v1/organizations/invalid-id')
        
        # 应该返回400状态码
        assert response.status_code == 400

    def test_api_method_not_allowed(self, client):
        """测试不支持的HTTP方法"""
        response = client.patch('/api/v1/organizations/1')
        
        assert response.status_code == 405

    @pytest.mark.slow
    def test_api_performance(self, client, organization_test_data):
        """测试API性能"""
        import time
        
        org_list = [organization_test_data['valid_org']] * 100  # 模拟大量数据
        
        with patch('service.organization_service.OrganizationService') as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.get_organizations_list.return_value = {
                'success': True,
                'data': {
                    'list': org_list,
                    'pagination': {
                        'page': 1,
                        'page_size': 100,
                        'total': 100,
                        'total_pages': 1,
                        'has_next': False,
                        'has_prev': False
                    }
                }
            }
            
            start_time = time.time()
            response = client.get('/api/v1/organizations?page_size=100')
            end_time = time.time()
            
            assert response.status_code == 200
            # 响应时间应该小于1秒
            assert (end_time - start_time) < 1.0

    def test_api_pagination_edge_cases(self, client):
        """测试API分页边界情况"""
        test_cases = [
            {'page': 0, 'page_size': 10},  # 页码为0
            {'page': 1, 'page_size': 0},   # 每页数量为0
            {'page': 1, 'page_size': 1000}, # 每页数量过大
            {'page': -1, 'page_size': 10},  # 负页码
        ]
        
        for params in test_cases:
            with patch('service.organization_service.OrganizationService') as mock_service_class:
                mock_service = mock_service_class.return_value
                mock_service.get_organizations_list.return_value = {
                    'success': True,
                    'data': {
                        'list': [],
                        'pagination': {
                            'page': max(1, params['page']),
                            'page_size': min(100, max(1, params['page_size'])),
                            'total': 0,
                            'total_pages': 0,
                            'has_next': False,
                            'has_prev': False
                        }
                    }
                }
                
                response = client.get(
                    f"/api/v1/organizations?page={params['page']}&page_size={params['page_size']}"
                )
                
                # 应该处理边界情况并返回合理的响应
                assert response.status_code == 200 