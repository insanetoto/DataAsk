"""
依赖注入容器的单元测试
"""
import pytest
from tools.di_container import DIContainer

class DummyService:
    def __init__(self, name: str = "dummy"):
        self.name = name
        
    def get_name(self) -> str:
        return self.name

def test_register_and_get_instance():
    """测试注册和获取服务实例"""
    container = DIContainer()
    service = DummyService()
    
    # 注册实例
    container.register("dummy", instance=service)
    
    # 获取实例
    retrieved = container.get("dummy")
    assert retrieved is service
    assert retrieved.get_name() == "dummy"

def test_register_and_get_factory():
    """测试注册和获取工厂函数"""
    container = DIContainer()
    
    # 注册工厂函数
    container.register("dummy", factory=lambda: DummyService("factory"))
    
    # 获取实例
    service = container.get("dummy")
    assert isinstance(service, DummyService)
    assert service.get_name() == "factory"
    
    # 验证工厂函数只被调用一次（返回相同实例）
    service2 = container.get("dummy")
    assert service2 is service

def test_register_invalid_args():
    """测试无效的注册参数"""
    container = DIContainer()
    
    # 测试同时提供instance和factory
    with pytest.raises(ValueError):
        container.register("dummy", 
                         instance=DummyService(), 
                         factory=lambda: DummyService())
    
    # 测试既不提供instance也不提供factory
    with pytest.raises(ValueError):
        container.register("dummy")

def test_get_unregistered_service():
    """测试获取未注册的服务"""
    container = DIContainer()
    
    with pytest.raises(KeyError):
        container.get("not_exists")

def test_remove_service():
    """测试移除服务"""
    container = DIContainer()
    service = DummyService()
    
    # 注册服务
    container.register("dummy", instance=service)
    assert container.has_service("dummy")
    
    # 移除服务
    container.remove("dummy")
    assert not container.has_service("dummy")
    
    # 尝试获取已移除的服务
    with pytest.raises(KeyError):
        container.get("dummy")

def test_clear_services():
    """测试清空所有服务"""
    container = DIContainer()
    
    # 注册多个服务
    container.register("service1", instance=DummyService("1"))
    container.register("service2", factory=lambda: DummyService("2"))
    
    assert container.has_service("service1")
    assert container.has_service("service2")
    
    # 清空所有服务
    container.clear()
    
    assert not container.has_service("service1")
    assert not container.has_service("service2")

def test_thread_safety():
    """测试线程安全性"""
    import threading
    import time
    
    container = DIContainer()
    counter = {"value": 0}
    
    def factory():
        counter["value"] += 1
        time.sleep(0.1)  # 模拟耗时操作
        return DummyService(f"service_{counter['value']}")
    
    container.register("dummy", factory=factory)
    
    def get_service():
        return container.get("dummy")
    
    # 创建多个线程同时获取服务
    threads = [threading.Thread(target=get_service) for _ in range(10)]
    
    # 启动所有线程
    for t in threads:
        t.start()
    
    # 等待所有线程完成
    for t in threads:
        t.join()
    
    # 验证工厂函数只被调用一次
    assert counter["value"] == 1
    
    # 验证所有线程获取到的是同一个实例
    service = container.get("dummy")
    assert service.get_name() == "service_1" 