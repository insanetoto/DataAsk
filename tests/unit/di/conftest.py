"""
DI容器测试的配置文件
"""
import pytest
from tools.di_container import DIContainer

@pytest.fixture
def container():
    """创建一个新的DI容器实例"""
    return DIContainer() 