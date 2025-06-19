# -*- coding: utf-8 -*-
"""
测试数据定义
包含各种测试场景需要的数据
"""

from datetime import datetime


class OrganizationTestData:
    """机构测试数据类"""
    
    @staticmethod
    def get_valid_organization():
        """获取有效的机构数据"""
        return {
            'org_code': 'TEST001',
            'org_name': '测试机构有限公司',
            'contact_person': '张三',
            'contact_phone': '13800138001',
            'contact_email': 'zhangsan@test.com',
            'status': 1
        }
    
    @staticmethod
    def get_hierarchy_organizations():
        """获取层级机构数据"""
        return [
            {
                'id': 1,
                'org_code': 'ROOT001',
                'parent_org_code': None,
                'org_name': '根机构',
                'contact_person': '根管理员',
                'contact_phone': '13800000001',
                'contact_email': 'root@test.com',
                'status': 1,
                'level_depth': 0,
                'level_path': '/ROOT001/',
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            },
            {
                'id': 2,
                'org_code': 'SUB001',
                'parent_org_code': 'ROOT001',
                'org_name': '子机构001',
                'contact_person': '子管理员001',
                'contact_phone': '13800000002',
                'contact_email': 'sub001@test.com',
                'status': 1,
                'level_depth': 1,
                'level_path': '/ROOT001/SUB001/',
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            },
            {
                'id': 3,
                'org_code': 'SUB002',
                'parent_org_code': 'ROOT001',
                'org_name': '子机构002',
                'contact_person': '子管理员002',
                'contact_phone': '13800000003',
                'contact_email': 'sub002@test.com',
                'status': 1,
                'level_depth': 1,
                'level_path': '/ROOT001/SUB002/',
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            },
            {
                'id': 4,
                'org_code': 'SUBSUB001',
                'parent_org_code': 'SUB001',
                'org_name': '子子机构001',
                'contact_person': '子子管理员001',
                'contact_phone': '13800000004',
                'contact_email': 'subsub001@test.com',
                'status': 1,
                'level_depth': 2,
                'level_path': '/ROOT001/SUB001/SUBSUB001/',
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }
        ]
    
    @staticmethod
    def get_invalid_organization_data():
        """获取无效的机构数据（用于测试验证）"""
        return [
            {
                'description': '缺少机构编码',
                'data': {
                    'org_name': '测试机构',
                    'contact_person': '张三',
                    'contact_phone': '13800138001',
                    'contact_email': 'zhangsan@test.com'
                }
            },
            {
                'description': '机构编码为空',
                'data': {
                    'org_code': '',
                    'org_name': '测试机构',
                    'contact_person': '张三',
                    'contact_phone': '13800138001',
                    'contact_email': 'zhangsan@test.com'
                }
            },
            {
                'description': '缺少机构名称',
                'data': {
                    'org_code': 'TEST001',
                    'contact_person': '张三',
                    'contact_phone': '13800138001',
                    'contact_email': 'zhangsan@test.com'
                }
            },
            {
                'description': '缺少联系人',
                'data': {
                    'org_code': 'TEST001',
                    'org_name': '测试机构',
                    'contact_phone': '13800138001',
                    'contact_email': 'zhangsan@test.com'
                }
            },
            {
                'description': '无效的邮箱格式',
                'data': {
                    'org_code': 'TEST001',
                    'org_name': '测试机构',
                    'contact_person': '张三',
                    'contact_phone': '13800138001',
                    'contact_email': 'invalid-email'
                }
            },
            {
                'description': '无效的电话号码',
                'data': {
                    'org_code': 'TEST001',
                    'org_name': '测试机构',
                    'contact_person': '张三',
                    'contact_phone': '123',
                    'contact_email': 'zhangsan@test.com'
                }
            }
        ]
    
    @staticmethod
    def get_large_organization_list(count=100):
        """获取大量机构数据（用于性能测试）"""
        organizations = []
        for i in range(count):
            org = {
                'id': i + 1,
                'org_code': f'PERF{i+1:03d}',
                'parent_org_code': None if i == 0 else f'PERF{((i-1)//10)+1:03d}',
                'org_name': f'性能测试机构{i+1:03d}',
                'contact_person': f'测试联系人{i+1:03d}',
                'contact_phone': f'138{i+1:08d}',
                'contact_email': f'test{i+1:03d}@perf.com',
                'status': 1,
                'level_depth': 0 if i == 0 else (1 if i <= 10 else 2),
                'level_path': f'/PERF{i+1:03d}/' if i == 0 else f'/PERF{((i-1)//10)+1:03d}/PERF{i+1:03d}/',
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }
            organizations.append(org)
        return organizations


class DatabaseTestData:
    """数据库测试数据类"""
    
    @staticmethod
    def get_db_connection_config():
        """获取测试数据库连接配置"""
        return {
            'host': 'localhost',
            'port': 3306,
            'user': 'test_user',
            'password': 'test_password',
            'database': 'test_dataask',
            'charset': 'utf8mb4'
        }
    
    @staticmethod
    def get_create_table_sql():
        """获取创建测试表的SQL"""
        return """
        CREATE TABLE IF NOT EXISTS test_organizations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            org_code VARCHAR(50) NOT NULL UNIQUE,
            parent_org_code VARCHAR(50) NULL,
            org_name VARCHAR(200) NOT NULL,
            contact_person VARCHAR(100) NOT NULL,
            contact_phone VARCHAR(20) NOT NULL,
            contact_email VARCHAR(100) NOT NULL,
            status INTEGER DEFAULT 1,
            level_depth INTEGER DEFAULT 0,
            level_path TEXT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """


class APITestData:
    """API测试数据类"""
    
    @staticmethod
    def get_api_headers():
        """获取API请求头"""
        return {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'DataAsk-Test-Client/1.0'
        }
    
    @staticmethod
    def get_pagination_test_cases():
        """获取分页测试用例"""
        return [
            {
                'description': '正常分页',
                'params': {'page': 1, 'page_size': 10},
                'expected_status': 200
            },
            {
                'description': '大页面尺寸',
                'params': {'page': 1, 'page_size': 100},
                'expected_status': 200
            },
            {
                'description': '第一页',
                'params': {'page': 1, 'page_size': 5},
                'expected_status': 200
            },
            {
                'description': '页码为0',
                'params': {'page': 0, 'page_size': 10},
                'expected_status': 400
            },
            {
                'description': '负页码',
                'params': {'page': -1, 'page_size': 10},
                'expected_status': 400
            },
            {
                'description': '页面尺寸为0',
                'params': {'page': 1, 'page_size': 0},
                'expected_status': 400
            },
            {
                'description': '页面尺寸过大',
                'params': {'page': 1, 'page_size': 1000},
                'expected_status': 400
            }
        ]
    
    @staticmethod
    def get_search_test_cases():
        """获取搜索测试用例"""
        return [
            {
                'description': '搜索机构名称',
                'keyword': '测试机构',
                'expected_count': 1
            },
            {
                'description': '搜索机构编码',
                'keyword': 'TEST001',
                'expected_count': 1
            },
            {
                'description': '搜索联系人',
                'keyword': '张三',
                'expected_count': 1
            },
            {
                'description': '搜索不存在的关键词',
                'keyword': '不存在的机构',
                'expected_count': 0
            },
            {
                'description': '空搜索关键词',
                'keyword': '',
                'expected_count': 'all'  # 返回所有结果
            },
            {
                'description': '特殊字符搜索',
                'keyword': '%_test',
                'expected_count': 0
            }
        ]


class MockTestData:
    """Mock测试数据类"""
    
    @staticmethod
    def get_database_service_mock_responses():
        """获取数据库服务Mock响应"""
        return {
            'query_success': [{'id': 1, 'org_code': 'TEST001', 'org_name': '测试机构'}],
            'query_empty': [],
            'query_multiple': [
                {'id': 1, 'org_code': 'TEST001', 'org_name': '测试机构1'},
                {'id': 2, 'org_code': 'TEST002', 'org_name': '测试机构2'}
            ],
            'update_success': 1,
            'update_failure': 0,
            'exception': Exception('数据库连接失败')
        }
    
    @staticmethod
    def get_redis_service_mock_responses():
        """获取Redis服务Mock响应"""
        return {
            'cache_hit': '{"id": 1, "org_code": "TEST001", "org_name": "测试机构"}',
            'cache_miss': None,
            'set_success': True,
            'set_failure': False,
            'delete_success': True,
            'clear_success': 5,  # 清除了5个缓存键
            'exception': Exception('Redis连接失败')
        } 