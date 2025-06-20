# -*- coding: utf-8 -*-
"""
服务层模块
提供各种业务服务的实现
"""

# 业务服务
from .organization_service import get_organization_service, init_organization_service
from .permission_service import get_permission_service, init_permission_service
from .role_service import get_role_service, init_role_service
from .user_service import get_user_service, get_user_service_instance

__all__ = [
    # 业务服务
    'get_organization_service', 'init_organization_service',
    'get_user_service', 'get_user_service_instance',
    'get_role_service', 'init_role_service',
    'get_permission_service', 'init_permission_service'
] 