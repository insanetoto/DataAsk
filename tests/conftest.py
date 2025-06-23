# -*- coding: utf-8 -*-
"""
pytest配置文件和全局fixtures
提供测试环境的setup和teardown
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from flask import Flask
from tools.di_container import DIContainer

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 设置测试环境变量
os.environ['FLASK_ENV'] = 'testing'

try:
    from config import config
    from app import create_app
    from tools.database import init_database_service, get_database_service
    from tools.redis_service import init_redis_service, get_redis_service
except ImportError as e:
    # 如果导入失败，创建mock对象
    print(f"导入警告: {e}")
    config = None
    create_app = None


@pytest.fixture(scope="session")
def test_config():
    """测试配置fixture"""
    class TestConfig:
        TESTING = True
        DEBUG = False
        LICENSE_ENABLED = False  # 测试环境禁用license校验
        
        # 使用内存SQLite数据库进行测试
        SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
        VANNA_DATABASE_URI = 'sqlite:///:memory:'
        SQLALCHEMY_TRACK_MODIFICATIONS = False
        
        # Redis配置 - 使用mock
        REDIS_HOST = 'localhost'
        REDIS_PORT = 6379
        REDIS_DB = 15  # 使用测试专用DB
        
        # 其他配置
        SECRET_KEY = 'test-secret-key'
        JWT_SECRET_KEY = 'test-jwt-secret'
        
    return TestConfig()


@pytest.fixture
def app():
    """创建测试用的Flask应用"""
    app = Flask(__name__)
    app.config['TESTING'] = True
    
    # 创建DI容器
    container = DIContainer()
    app.container = container
    
    return app


@pytest.fixture
def client(app):
    """创建测试客户端"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """创建测试命令运行器"""
    return app.test_cli_runner()


@pytest.fixture(scope="function", autouse=True)
def mock_redis_service():
    """自动Mock Redis服务fixture - 解决Redis未初始化问题"""
    mock_service = Mock()
    
    # 模拟Redis操作
    mock_service.get_cache.return_value = None
    mock_service.set_cache.return_value = True
    mock_service.delete_cache.return_value = True
    mock_service.clear_pattern.return_value = 5
    mock_service.ping.return_value = True
    
    # Mock Redis服务的初始化状态
    with patch('tools.redis_service._redis_service', mock_service):
        with patch('tools.redis_service.get_redis_service', return_value=mock_service):
            with patch('service.organization_service.get_redis_service', return_value=mock_service):
                with patch('service.user_service.get_redis_service', return_value=mock_service):
                    with patch('service.role_service.get_redis_service', return_value=mock_service):
                        with patch('service.permission_service.get_redis_service', return_value=mock_service):
                            yield mock_service


@pytest.fixture(scope="function")
def mock_database_service():
    """Mock数据库服务fixture"""
    mock_service = Mock()
    
    # 模拟数据库操作结果
    mock_service.execute_query.return_value = []
    mock_service.execute_update.return_value = 1
    mock_service.get_connection.return_value = Mock()
    mock_service.begin_transaction.return_value = Mock()
    mock_service.commit_transaction.return_value = True
    mock_service.rollback_transaction.return_value = True
    
    # 添加更详细的查询模拟
    def mock_execute_query(sql, params=None):
        if 'SELECT' in sql and 'organizations' in sql:
            if 'org_code' in sql and params and params.get('org_code'):
                return [{
                    'id': 1,
                    'org_code': params['org_code'],
                    'org_name': '测试机构',
                    'contact_person': '测试人员',
                    'contact_phone': '13800138001',
                    'contact_email': 'test@example.com',
                    'status': 1,
                    'created_at': '2024-01-01 00:00:00',
                    'updated_at': '2024-01-01 00:00:00'
                }]
            return []
        elif 'SELECT' in sql and 'users' in sql:
            return [{
                'id': 1,
                'user_code': 'testuser',
                'user_name': '测试用户',
                'email': 'test@example.com',
                'phone': '13800138001',
                'status': 1,
                'role_name': '测试角色',
                'org_name': '测试机构'
            }]
        return []
    
    mock_service.execute_query.side_effect = mock_execute_query
    
    with patch('service.organization_service.get_database_service', return_value=mock_service):
        with patch('service.user_service.get_database_service', return_value=mock_service):
            with patch('service.role_service.get_database_service', return_value=mock_service):
                with patch('service.permission_service.get_database_service', return_value=mock_service):
                    yield mock_service


@pytest.fixture(scope="function")
def organization_test_data():
    """机构测试数据fixture"""
    return {
        'valid_org': {
            'org_code': 'TEST001',
            'org_name': '测试机构',
            'contact_person': '测试联系人',
            'contact_phone': '13800138001',
            'contact_email': 'test@example.com',
            'status': 1
        },
        'hierarchy_orgs': [
            {
                'org_code': 'ROOT',
                'parent_org_code': None,
                'org_name': '根机构',
                'contact_person': '根管理员',
                'contact_phone': '13800000001',
                'contact_email': 'root@example.com',
                'level_depth': 0,
                'level_path': '/ROOT/'
            },
            {
                'org_code': 'SUB01',
                'parent_org_code': 'ROOT',
                'org_name': '子机构01',
                'contact_person': '子管理员01',
                'contact_phone': '13800000002',
                'contact_email': 'sub01@example.com',
                'level_depth': 1,
                'level_path': '/ROOT/SUB01/'
            }
        ],
        'invalid_org': {
            'org_code': '',  # 无效的机构编码
            'org_name': '无效机构',
            'contact_person': '',  # 缺少联系人
            'contact_phone': '138',  # 无效电话
            'contact_email': 'invalid-email'  # 无效邮箱
        }
    }


@pytest.fixture(scope="function")
def user_test_data():
    """用户测试数据fixture"""
    return {
        'valid_user': {
            'user_code': 'testuser001',
            'user_name': '测试用户',
            'email': 'testuser@example.com',
            'phone': '13800138001',
            'password': 'Test@123456',
            'org_code': 'TEST001',
            'role_codes': ['ROLE001'],
            'status': 1
        },
        'invalid_user': {
            'user_code': '',
            'user_name': '',
            'email': 'invalid-email',
            'phone': '138',
            'password': '123',  # 密码太简单
            'org_code': '',
            'role_codes': []
        }
    }


@pytest.fixture(scope="function")
def role_test_data():
    """角色测试数据fixture"""
    return {
        'valid_role': {
            'role_code': 'ROLE001',
            'role_name': '测试角色',
            'description': '用于测试的角色',
            'permission_codes': ['PERM001', 'PERM002'],
            'status': 1
        },
        'invalid_role': {
            'role_code': '',
            'role_name': '',
            'description': '',
            'permission_codes': []
        }
    }


@pytest.fixture(scope="function")
def permission_test_data():
    """权限测试数据fixture"""
    return {
        'valid_permission': {
            'permission_code': 'PERM001',
            'permission_name': '测试权限',
            'resource': 'test_resource',
            'action': 'read',
            'description': '测试权限描述'
        },
        'permission_list': [
            {
                'permission_code': 'PERM001',
                'permission_name': '读取权限',
                'resource': 'test_resource',
                'action': 'read'
            },
            {
                'permission_code': 'PERM002',
                'permission_name': '写入权限',
                'resource': 'test_resource',
                'action': 'write'
            }
        ]
    }


@pytest.fixture(scope="function")
def db_session(app, test_config):
    """数据库会话fixture"""
    with app.app_context():
        # 初始化数据库服务
        init_database_service(test_config)
        db_service = get_database_service()
        
        # 创建测试表
        create_test_tables(db_service)
        
        yield db_service
        
        # 清理测试数据
        cleanup_test_data(db_service)


def create_test_tables(db_service):
    """创建测试表"""
    sql_create_org_table = """
    CREATE TABLE IF NOT EXISTS organizations (
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
    db_service.execute_update(sql_create_org_table, {})


def cleanup_test_data(db_service):
    """清理测试数据"""
    try:
        db_service.execute_update("DELETE FROM organizations", {})
        db_service.execute_update("DELETE FROM users", {})
        db_service.execute_update("DELETE FROM roles", {})
        db_service.execute_update("DELETE FROM permissions", {})
    except:
        pass  # 忽略清理错误


# pytest配置
def pytest_configure(config):
    """pytest配置"""
    config.addinivalue_line(
        "markers", "unit: 单元测试标记"
    )
    config.addinivalue_line(
        "markers", "integration: 集成测试标记"
    )
    config.addinivalue_line(
        "markers", "slow: 慢速测试标记"
    )


def pytest_collection_modifyitems(config, items):
    """修改pytest收集的测试项，添加标记"""
    for item in items:
        # 根据测试文件路径添加标记
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        
        # 根据测试名称添加标记
        if "slow" in item.name or "performance" in item.name:
            item.add_marker(pytest.mark.slow) 