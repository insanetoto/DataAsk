# -*- coding: utf-8 -*-
"""
服务层模块
提供业务逻辑处理服务
"""
from typing import Optional
from .user_service import UserService
from .organization_service import OrganizationService
from .menu_service import MenuService
from .role_service import RoleService
from .permission_service import PermissionService
from .ai_service import AIService
from .workflow_service import WorkflowService
from .audit_service import AuditService
from .enhanced_permission_service import EnhancedPermissionService

# 服务实例缓存
_user_service: Optional[UserService] = None
_organization_service: Optional[OrganizationService] = None
_menu_service: Optional[MenuService] = None
_role_service: Optional[RoleService] = None
_permission_service: Optional[PermissionService] = None
_ai_service: Optional[AIService] = None
_workflow_service: Optional[WorkflowService] = None
_audit_service: Optional[AuditService] = None
_enhanced_permission_service: Optional[EnhancedPermissionService] = None

def get_user_service_instance() -> UserService:
    """获取用户服务实例"""
    global _user_service
    if _user_service is None:
        _user_service = UserService()
    return _user_service

def get_organization_service_instance() -> OrganizationService:
    """获取机构服务实例"""
    global _organization_service
    if _organization_service is None:
        _organization_service = OrganizationService()
    return _organization_service

def get_menu_service_instance() -> MenuService:
    """获取菜单服务实例"""
    global _menu_service
    if _menu_service is None:
        _menu_service = MenuService()
    return _menu_service

def get_role_service_instance() -> RoleService:
    """获取角色服务实例"""
    global _role_service
    if _role_service is None:
        _role_service = RoleService()
    return _role_service

def get_permission_service_instance() -> PermissionService:
    """获取权限服务实例"""
    global _permission_service
    if _permission_service is None:
        _permission_service = PermissionService()
    return _permission_service

def get_ai_service_instance() -> AIService:
    """获取AI服务实例"""
    global _ai_service
    if _ai_service is None:
        _ai_service = AIService()
    return _ai_service

def get_workflow_service_instance() -> WorkflowService:
    """获取工作流服务实例"""
    global _workflow_service
    if _workflow_service is None:
        _workflow_service = WorkflowService()
    return _workflow_service

def get_enhanced_workflow_service_instance() -> WorkflowService:
    """获取增强版工作流服务实例（向后兼容）"""
    return get_workflow_service_instance()

def get_audit_service_instance() -> AuditService:
    """获取审计服务实例"""
    global _audit_service
    if _audit_service is None:
        _audit_service = AuditService()
    return _audit_service

def get_enhanced_permission_service_instance() -> EnhancedPermissionService:
    """获取增强权限服务实例"""
    global _enhanced_permission_service
    if _enhanced_permission_service is None:
        _enhanced_permission_service = EnhancedPermissionService()
    return _enhanced_permission_service

__all__ = [
    'get_user_service_instance',
    'get_organization_service_instance',
    'get_menu_service_instance',
    'get_role_service_instance',
    'get_permission_service_instance',
    'get_ai_service_instance',
    'get_workflow_service_instance',
    'get_enhanced_workflow_service_instance',
    'get_audit_service_instance',
    'get_enhanced_permission_service_instance'
] 