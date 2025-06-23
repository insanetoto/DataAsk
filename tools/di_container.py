"""
依赖注入容器
用于管理和注入服务依赖
"""
from typing import Dict, Any, TypeVar, Optional, Callable
from threading import Lock

T = TypeVar('T')

class DIContainer:
    """
    依赖注入容器
    负责管理服务的注册、获取和生命周期
    """
    
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, Callable[[], Any]] = {}
        self._lock = Lock()
    
    def register(self, key: str, instance: Any = None, factory: Callable[[], Any] = None) -> None:
        """
        注册服务到容器
        
        Args:
            key: 服务标识符
            instance: 服务实例（可选）
            factory: 服务工厂函数（可选）
            
        注意：必须提供 instance 或 factory 其中之一
        """
        if instance is not None and factory is not None:
            raise ValueError("不能同时提供 instance 和 factory")
        if instance is None and factory is None:
            raise ValueError("必须提供 instance 或 factory 其中之一")
            
        with self._lock:
            if instance is not None:
                self._services[key] = instance
            else:
                self._factories[key] = factory
                # 确保服务不在_services中
                if key in self._services:
                    del self._services[key]
    
    def get(self, key: str) -> Any:
        """
        获取服务实例
        
        Args:
            key: 服务标识符
            
        Returns:
            服务实例
            
        Raises:
            KeyError: 如果服务未注册
        """
        # 先检查是否已有实例
        with self._lock:
            if key in self._services:
                return self._services[key]
                
            # 检查是否有工厂函数
            if key in self._factories:
                # 使用工厂函数创建实例并缓存
                instance = self._factories[key]()
                self._services[key] = instance
                return instance
                
        raise KeyError(f"服务未注册: {key}")
    
    def remove(self, key: str) -> None:
        """
        移除已注册的服务
        
        Args:
            key: 服务标识符
        """
        with self._lock:
            self._services.pop(key, None)
            self._factories.pop(key, None)
    
    def clear(self) -> None:
        """清空所有注册的服务"""
        with self._lock:
            self._services.clear()
            self._factories.clear()
    
    def has_service(self, key: str) -> bool:
        """
        检查服务是否已注册
        
        Args:
            key: 服务标识符
            
        Returns:
            bool: 服务是否已注册
        """
        with self._lock:
            return key in self._services or key in self._factories 