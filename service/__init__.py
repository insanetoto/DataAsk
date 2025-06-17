# -*- coding: utf-8 -*-
"""
业务服务模块
包含机构管理、用户管理、角色管理、权限管理服务
"""

# 业务服务
from .organization_service import get_organization_service, init_organization_service
from .user_service import get_user_service, init_user_service
from .role_service import get_role_service, init_role_service
from .permission_service import get_permission_service, init_permission_service

__all__ = [
    # 业务服务
    'get_organization_service', 'init_organization_service',
    'get_user_service', 'init_user_service',
    'get_role_service', 'init_role_service',
    'get_permission_service', 'init_permission_service'
] 