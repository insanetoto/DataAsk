# -*- coding: utf-8 -*-
"""
权限模型模块
"""
from sqlalchemy import Column, String, Integer, Text, Table, ForeignKey
from sqlalchemy.orm import relationship
from .base import BaseModel

# 角色权限关联表
role_permissions = Table(
    'role_permissions',
    BaseModel.metadata,
    Column('id', Integer, primary_key=True, autoincrement=True, comment='主键ID'),
    Column('role_id', Integer, ForeignKey('roles.id', ondelete='CASCADE'), nullable=False, comment='角色ID'),
    Column('permission_id', Integer, ForeignKey('permissions.id', ondelete='CASCADE'), nullable=False, comment='权限ID')
)

class Permission(BaseModel):
    """权限模型"""
    __tablename__ = 'permissions'
    
    permission_code = Column(String(100), unique=True, nullable=False, comment='权限编码')
    permission_name = Column(String(100), nullable=False, comment='权限名称')
    api_path = Column(String(200), nullable=False, comment='API路径')
    api_method = Column(String(10), nullable=False, comment='HTTP方法')
    resource_type = Column(String(50), comment='资源类型')
    description = Column(Text, comment='权限描述')
    status = Column(Integer, default=1, comment='状态：1-启用，0-禁用')
    
    # 关联关系
    roles = relationship('Role', secondary='role_permissions', back_populates='permissions') 