# -*- coding: utf-8 -*-
"""
测试客户端工具
提供API测试的便捷方法
"""

import json
import time
from typing import Dict, Any, Optional


class APITestClient:
    """API测试客户端"""
    
    def __init__(self, client, base_url='/api/v1'):
        self.client = client
        self.base_url = base_url
        self.default_headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    
    def get(self, endpoint: str, params: Optional[Dict] = None, headers: Optional[Dict] = None):
        """发送GET请求"""
        url = f"{self.base_url}{endpoint}"
        if params:
            query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
            url = f"{url}?{query_string}"
        
        request_headers = {**self.default_headers}
        if headers:
            request_headers.update(headers)
        
        return self.client.get(url, headers=request_headers)
    
    def post(self, endpoint: str, data: Any = None, headers: Optional[Dict] = None):
        """发送POST请求"""
        url = f"{self.base_url}{endpoint}"
        
        request_headers = {**self.default_headers}
        if headers:
            request_headers.update(headers)
        
        json_data = json.dumps(data) if data else None
        
        return self.client.post(
            url, 
            data=json_data, 
            headers=request_headers
        )
    
    def put(self, endpoint: str, data: Any = None, headers: Optional[Dict] = None):
        """发送PUT请求"""
        url = f"{self.base_url}{endpoint}"
        
        request_headers = {**self.default_headers}
        if headers:
            request_headers.update(headers)
        
        json_data = json.dumps(data) if data else None
        
        return self.client.put(
            url, 
            data=json_data, 
            headers=request_headers
        )
    
    def delete(self, endpoint: str, headers: Optional[Dict] = None):
        """发送DELETE请求"""
        url = f"{self.base_url}{endpoint}"
        
        request_headers = {**self.default_headers}
        if headers:
            request_headers.update(headers)
        
        return self.client.delete(url, headers=request_headers)
    
    def get_organizations(self, **params):
        """获取机构列表"""
        return self.get('/organizations', params=params)
    
    def get_organization_by_id(self, org_id: int):
        """根据ID获取机构"""
        return self.get(f'/organizations/{org_id}')
    
    def get_organization_by_code(self, org_code: str):
        """根据编码获取机构"""
        return self.get(f'/organizations/code/{org_code}')
    
    def create_organization(self, org_data: Dict):
        """创建机构"""
        return self.post('/organizations', data=org_data)
    
    def update_organization(self, org_id: int, update_data: Dict):
        """更新机构"""
        return self.put(f'/organizations/{org_id}', data=update_data)
    
    def delete_organization(self, org_id: int):
        """删除机构"""
        return self.delete(f'/organizations/{org_id}')
    
    def clear_organization_cache(self):
        """清除机构缓存"""
        return self.post('/organizations/cache/clear')


class PerformanceTestClient:
    """性能测试客户端"""
    
    def __init__(self, api_client: APITestClient):
        self.api_client = api_client
    
    def measure_response_time(self, method, *args, **kwargs):
        """测量响应时间"""
        start_time = time.time()
        response = getattr(self.api_client, method)(*args, **kwargs)
        end_time = time.time()
        
        response_time = end_time - start_time
        
        return {
            'response': response,
            'response_time': response_time,
            'status_code': response.status_code
        }
    
    def load_test(self, method, *args, concurrent_requests=10, **kwargs):
        """负载测试"""
        import threading
        import queue
        
        results = queue.Queue()
        
        def make_request():
            try:
                result = self.measure_response_time(method, *args, **kwargs)
                results.put(result)
            except Exception as e:
                results.put({'error': str(e)})
        
        # 创建并启动线程
        threads = []
        for _ in range(concurrent_requests):
            thread = threading.Thread(target=make_request)
            thread.start()
            threads.append(thread)
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        # 收集结果
        test_results = []
        while not results.empty():
            test_results.append(results.get())
        
        return self._analyze_results(test_results)
    
    def _analyze_results(self, results):
        """分析测试结果"""
        successful_requests = [r for r in results if 'error' not in r]
        failed_requests = [r for r in results if 'error' in r]
        
        if not successful_requests:
            return {
                'total_requests': len(results),
                'successful_requests': 0,
                'failed_requests': len(failed_requests),
                'success_rate': 0.0,
                'errors': [r['error'] for r in failed_requests]
            }
        
        response_times = [r['response_time'] for r in successful_requests]
        status_codes = [r['status_code'] for r in successful_requests]
        
        return {
            'total_requests': len(results),
            'successful_requests': len(successful_requests),
            'failed_requests': len(failed_requests),
            'success_rate': len(successful_requests) / len(results),
            'avg_response_time': sum(response_times) / len(response_times),
            'min_response_time': min(response_times),
            'max_response_time': max(response_times),
            'status_code_distribution': {
                code: status_codes.count(code) 
                for code in set(status_codes)
            },
            'errors': [r['error'] for r in failed_requests]
        }


class ResponseValidator:
    """响应验证器"""
    
    @staticmethod
    def validate_json_response(response, expected_status=200):
        """验证JSON响应"""
        assert response.status_code == expected_status, f"期望状态码 {expected_status}，实际 {response.status_code}"
        
        try:
            data = json.loads(response.data)
            return data
        except json.JSONDecodeError:
            raise AssertionError("响应不是有效的JSON格式")
    
    @staticmethod
    def validate_success_response(response, expected_status=200):
        """验证成功响应"""
        data = ResponseValidator.validate_json_response(response, expected_status)
        assert data.get('success') is True, f"响应不成功: {data.get('error', '未知错误')}"
        return data
    
    @staticmethod
    def validate_error_response(response, expected_status=400):
        """验证错误响应"""
        data = ResponseValidator.validate_json_response(response, expected_status)
        assert data.get('success') is False, "错误响应应该包含 success: false"
        assert 'error' in data, "错误响应应该包含错误信息"
        return data
    
    @staticmethod
    def validate_pagination_response(response, expected_status=200):
        """验证分页响应"""
        data = ResponseValidator.validate_success_response(response, expected_status)
        assert 'data' in data, "分页响应应该包含data字段"
        assert 'list' in data['data'], "分页响应应该包含list字段"
        assert 'pagination' in data['data'], "分页响应应该包含pagination字段"
        
        pagination = data['data']['pagination']
        required_fields = ['page', 'page_size', 'total', 'total_pages', 'has_next', 'has_prev']
        for field in required_fields:
            assert field in pagination, f"分页信息缺少字段: {field}"
        
        return data
    
    @staticmethod
    def validate_organization_data(org_data):
        """验证机构数据"""
        required_fields = ['org_code', 'org_name', 'contact_person', 'contact_phone', 'contact_email']
        for field in required_fields:
            assert field in org_data, f"机构数据缺少必要字段: {field}"
            assert org_data[field], f"机构数据字段 {field} 不能为空"
        
        # 验证邮箱格式
        email = org_data['contact_email']
        assert '@' in email and '.' in email, f"无效的邮箱格式: {email}"
        
        return True


class TestDataGenerator:
    """测试数据生成器"""
    
    @staticmethod
    def generate_organization_data(org_code=None, **overrides):
        """生成机构测试数据"""
        if not org_code:
            import uuid
            org_code = f"TEST_{uuid.uuid4().hex[:8].upper()}"
        
        default_data = {
            'org_code': org_code,
            'org_name': f'测试机构_{org_code}',
            'contact_person': '测试联系人',
            'contact_phone': '13800138000',
            'contact_email': f'test_{org_code.lower()}@example.com',
            'status': 1
        }
        
        default_data.update(overrides)
        return default_data
    
    @staticmethod
    def generate_multiple_organizations(count=5):
        """生成多个机构测试数据"""
        return [
            TestDataGenerator.generate_organization_data(f"TEST{i+1:03d}")
            for i in range(count)
        ]
    
    @staticmethod
    def generate_invalid_organization_data(invalid_type='missing_required'):
        """生成无效的机构数据"""
        base_data = TestDataGenerator.generate_organization_data()
        
        if invalid_type == 'missing_required':
            del base_data['org_code']
        elif invalid_type == 'empty_required':
            base_data['org_code'] = ''
        elif invalid_type == 'invalid_email':
            base_data['contact_email'] = 'invalid-email'
        elif invalid_type == 'invalid_phone':
            base_data['contact_phone'] = '123'
        
        return base_data 