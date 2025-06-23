"""
菜单服务的单元测试
"""
import pytest
from unittest.mock import Mock, MagicMock
from service.menu_service import MenuService

class MockSession:
    def __init__(self):
        self.execute = MagicMock()
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

class MockDatabaseService:
    def __init__(self):
        self.session = MockSession()
        
    def get_session(self):
        return self.session

@pytest.fixture
def db_service():
    return MockDatabaseService()

@pytest.fixture
def menu_service(db_service):
    return MenuService(db_service)

def test_get_user_menus_empty(menu_service, db_service):
    """测试获取空的用户菜单列表"""
    # 设置模拟返回值
    mock_result = MagicMock()
    mock_result.__iter__.return_value = iter([])
    db_service.session.execute.return_value = mock_result
    
    # 调用服务方法
    result = menu_service.get_user_menus(1)
    
    # 验证结果
    assert result['success'] is False
    assert '未找到用户菜单' in result['error']

def test_get_user_menus_success(menu_service, db_service):
    """测试成功获取用户菜单列表"""
    # 创建模拟数据
    mock_row1 = MagicMock()
    mock_row1._mapping = {
        'id': 1,
        'parent_id': 0,
        'name': '系统管理',
        'path': '/system',
        'component': 'Layout',
        'type': 'M',
        'icon': 'system',
        'order_num': 1,
        'perms': None,
        'is_frame': 0,
        'visible': 1,
        'status': 1
    }
    for key, value in mock_row1._mapping.items():
        setattr(mock_row1, key, value)
    
    mock_row2 = MagicMock()
    mock_row2._mapping = {
        'id': 2,
        'parent_id': 1,
        'name': '用户管理',
        'path': 'user',
        'component': 'system/user/index',
        'type': 'C',
        'icon': 'user',
        'order_num': 1,
        'perms': 'system:user:list',
        'is_frame': 0,
        'visible': 1,
        'status': 1
    }
    for key, value in mock_row2._mapping.items():
        setattr(mock_row2, key, value)
    
    # 设置模拟返回值
    mock_result = MagicMock()
    mock_result.__iter__.return_value = iter([mock_row1, mock_row2])
    db_service.session.execute.return_value = mock_result
    
    # 调用服务方法
    result = menu_service.get_user_menus(1)
    
    # 验证结果
    assert result['success'] is True
    assert 'data' in result
    
    menu_tree = result['data']
    assert len(menu_tree) == 1
    
    root_menu = menu_tree[0]
    assert root_menu['id'] == 1
    assert root_menu['name'] == '系统管理'
    assert root_menu['path'] == '/system'
    
    assert 'children' in root_menu
    assert len(root_menu['children']) == 1
    
    child_menu = root_menu['children'][0]
    assert child_menu['id'] == 2
    assert child_menu['name'] == '用户管理'
    assert child_menu['path'] == 'user'
    assert child_menu['perms'] == 'system:user:list'

def test_get_user_menus_error(menu_service, db_service):
    """测试获取用户菜单时发生错误"""
    # 设置模拟异常
    db_service.session.execute.side_effect = Exception("数据库错误")
    
    # 调用服务方法
    result = menu_service.get_user_menus(1)
    
    # 验证结果
    assert result['success'] is False
    assert '获取用户菜单失败' in result['error']
    assert '数据库错误' in result['error'] 