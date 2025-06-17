# -*- coding: utf-8 -*-
"""
pytest配置文件和全局fixtures
提供测试环境的setup和teardown
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch

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


@pytest.fixture(scope="session")
def app(test_config):
    """创建Flask应用fixture"""
    if create_app is not None:
        with patch('config.config', {'testing': test_config}):
            app = create_app('testing')
            app.config.from_object(test_config)
            
            # 创建应用上下文
            with app.app_context():
                yield app
    else:
        # 如果无法导入，创建简单的Mock应用
        from unittest.mock import Mock
        mock_app = Mock()
        mock_app.test_client.return_value = Mock()
        yield mock_app


@pytest.fixture(scope="session") 
def client(app):
    """Flask测试客户端fixture"""
    return app.test_client()


@pytest.fixture(scope="function")
def mock_database_service():
    """Mock数据库服务fixture"""
    mock_service = Mock()
    
    # 模拟数据库操作结果
    mock_service.execute_query.return_value = []
    mock_service.execute_update.return_value = 1
    
    with patch('service.organization_service.get_database_service', return_value=mock_service):
        yield mock_service


@pytest.fixture(scope="function")
def mock_redis_service():
    """Mock Redis服务fixture"""
    mock_service = Mock()
    
    # 模拟Redis操作
    mock_service.get_cache.return_value = None
    mock_service.set_cache.return_value = True
    mock_service.delete_cache.return_value = True
    mock_service.clear_pattern.return_value = 5
    
    with patch('service.organization_service.get_redis_service', return_value=mock_service):
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
    """修改测试项配置"""
    for item in items:
        # 为单元测试添加标记
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        # 为集成测试添加标记
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration) 