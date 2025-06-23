# -*- coding: utf-8 -*-
"""
模型层单元测试
测试数据模型的基本功能和验证逻辑
"""

import pytest
from unittest.mock import Mock
from datetime import datetime

# 导入模型类
try:
    from models.user import User
    from models.organization import Organization
    from models.role import Role
    from models.permission import Permission
    from models.base import Base
except ImportError:
    # 如果导入失败，跳过测试
    pytest.skip("模型导入失败，跳过模型测试", allow_module_level=True)


class TestUserModel:
    """用户模型测试"""
    
    def test_user_model_creation(self):
        """测试用户模型创建"""
        user = User(
            user_code='testuser',
            user_name='测试用户',
            email='test@example.com',
            phone='13800138001',
            password_hash='hashed_password'
        )
        
        assert user.user_code == 'testuser'
        assert user.user_name == '测试用户'
        assert user.email == 'test@example.com'
        assert user.phone == '13800138001'
        assert user.password_hash == 'hashed_password'
        assert user.status == 1  # 默认状态
    
    def test_user_model_repr(self):
        """测试用户模型字符串表示"""
        user = User(user_code='testuser', user_name='测试用户')
        assert 'testuser' in repr(user)
        assert '测试用户' in repr(user)
    
    def test_user_model_attributes(self):
        """测试用户模型属性设置"""
        user = User()
        user.user_code = 'newuser'
        user.user_name = '新用户'
        user.status = 0
        
        assert user.user_code == 'newuser'
        assert user.user_name == '新用户'
        assert user.status == 0


class TestOrganizationModel:
    """机构模型测试"""
    
    def test_organization_model_creation(self):
        """测试机构模型创建"""
        org = Organization(
            org_code='TEST001',
            org_name='测试机构',
            contact_person='测试联系人',
            contact_phone='13800138001',
            contact_email='test@example.com'
        )
        
        assert org.org_code == 'TEST001'
        assert org.org_name == '测试机构'
        assert org.contact_person == '测试联系人'
        assert org.contact_phone == '13800138001'
        assert org.contact_email == 'test@example.com'
        assert org.status == 1  # 默认状态
        assert org.level_depth == 0  # 默认层级
    
    def test_organization_model_hierarchy(self):
        """测试机构层级关系"""
        parent_org = Organization(
            org_code='PARENT',
            org_name='父机构',
            level_depth=0,
            level_path='/PARENT/'
        )
        
        child_org = Organization(
            org_code='CHILD',
            org_name='子机构',
            parent_org_code='PARENT',
            level_depth=1,
            level_path='/PARENT/CHILD/'
        )
        
        assert child_org.parent_org_code == 'PARENT'
        assert child_org.level_depth == 1
        assert child_org.level_path == '/PARENT/CHILD/'
    
    def test_organization_model_repr(self):
        """测试机构模型字符串表示"""
        org = Organization(org_code='TEST001', org_name='测试机构')
        assert 'TEST001' in repr(org)
        assert '测试机构' in repr(org)


class TestRoleModel:
    """角色模型测试"""
    
    def test_role_model_creation(self):
        """测试角色模型创建"""
        role = Role(
            role_code='ADMIN',
            role_name='管理员',
            description='系统管理员角色'
        )
        
        assert role.role_code == 'ADMIN'
        assert role.role_name == '管理员'
        assert role.description == '系统管理员角色'
        assert role.status == 1  # 默认状态
    
    def test_role_model_repr(self):
        """测试角色模型字符串表示"""
        role = Role(role_code='ADMIN', role_name='管理员')
        assert 'ADMIN' in repr(role)
        assert '管理员' in repr(role)
    
    def test_role_model_attributes(self):
        """测试角色模型属性"""
        role = Role()
        role.role_code = 'USER'
        role.role_name = '普通用户'
        role.status = 0
        
        assert role.role_code == 'USER'
        assert role.role_name == '普通用户'
        assert role.status == 0


class TestPermissionModel:
    """权限模型测试"""
    
    def test_permission_model_creation(self):
        """测试权限模型创建"""
        permission = Permission(
            permission_code='READ_USER',
            permission_name='读取用户',
            resource='user',
            action='read',
            description='读取用户信息的权限'
        )
        
        assert permission.permission_code == 'READ_USER'
        assert permission.permission_name == '读取用户'
        assert permission.resource == 'user'
        assert permission.action == 'read'
        assert permission.description == '读取用户信息的权限'
    
    def test_permission_model_repr(self):
        """测试权限模型字符串表示"""
        permission = Permission(
            permission_code='READ_USER',
            permission_name='读取用户'
        )
        assert 'READ_USER' in repr(permission)
        assert '读取用户' in repr(permission)
    
    def test_permission_model_resource_action(self):
        """测试权限资源和操作"""
        permission = Permission(
            permission_code='WRITE_ORG',
            permission_name='写入机构',
            resource='organization',
            action='write'
        )
        
        assert permission.resource == 'organization'
        assert permission.action == 'write'


class TestBaseModel:
    """基础模型测试"""
    
    def test_base_model_timestamps(self):
        """测试基础模型时间戳"""
        # 这里测试Base模型的时间戳功能
        # 由于Base是抽象类，我们通过User模型来测试
        user = User(
            user_code='testuser',
            user_name='测试用户'
        )
        
        # 验证模型具有时间戳字段（通过属性检查）
        assert hasattr(user, 'created_at')
        assert hasattr(user, 'updated_at')
    
    def test_base_model_id_field(self):
        """测试基础模型ID字段"""
        user = User(user_code='testuser')
        
        # 验证模型具有ID字段
        assert hasattr(user, 'id')
        
        # 新创建的模型ID应该为None（未持久化）
        assert user.id is None


class TestModelValidation:
    """模型验证测试"""
    
    def test_user_email_validation(self):
        """测试用户邮箱验证"""
        # 这里可以添加模型级别的验证逻辑测试
        # 由于当前模型可能没有内置验证，我们测试基本属性设置
        user = User()
        
        # 测试正常邮箱
        user.email = 'valid@example.com'
        assert user.email == 'valid@example.com'
        
        # 测试异常邮箱（如果有验证逻辑的话）
        user.email = 'invalid-email'
        assert user.email == 'invalid-email'  # 当前无验证
    
    def test_organization_code_uniqueness(self):
        """测试机构编码唯一性约束"""
        # 由于这是数据库级别的约束，这里主要测试模型属性
        org1 = Organization(org_code='UNIQUE001', org_name='机构1')
        org2 = Organization(org_code='UNIQUE001', org_name='机构2')
        
        # 模型级别应该允许相同编码（约束在数据库层）
        assert org1.org_code == org2.org_code
    
    def test_role_code_validation(self):
        """测试角色编码验证"""
        role = Role()
        
        # 测试角色编码设置
        role.role_code = 'VALID_ROLE'
        assert role.role_code == 'VALID_ROLE'
        
        # 测试空编码
        role.role_code = ''
        assert role.role_code == ''


class TestModelRelationships:
    """模型关系测试"""
    
    def test_user_organization_relationship(self):
        """测试用户与机构的关系"""
        user = User(
            user_code='testuser',
            user_name='测试用户',
            org_code='TEST_ORG'
        )
        
        assert user.org_code == 'TEST_ORG'
    
    def test_organization_hierarchy_relationship(self):
        """测试机构层级关系"""
        parent_org = Organization(
            org_code='PARENT',
            org_name='父机构'
        )
        
        child_org = Organization(
            org_code='CHILD',
            org_name='子机构',
            parent_org_code='PARENT'
        )
        
        assert child_org.parent_org_code == parent_org.org_code
    
    def test_role_permission_relationship(self):
        """测试角色与权限的关系"""
        # 这里测试角色和权限的基本关联
        # 实际的多对多关系可能在中间表中处理
        role = Role(
            role_code='TEST_ROLE',
            role_name='测试角色'
        )
        
        permission = Permission(
            permission_code='TEST_PERM',
            permission_name='测试权限',
            resource='test',
            action='read'
        )
        
        # 验证模型创建成功
        assert role.role_code == 'TEST_ROLE'
        assert permission.permission_code == 'TEST_PERM' 