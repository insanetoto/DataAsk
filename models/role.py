# -*- coding: utf-8 -*-
"""
角色模型模块
"""
from sqlalchemy import Column, String, Integer, Text, ForeignKey
from sqlalchemy.orm import relationship
from .base import BaseModel

class Role(BaseModel):
    """角色模型"""
    __tablename__ = 'roles'
    
    role_code = Column(String(50), unique=True, nullable=False, comment='角色编码')
    role_name = Column(String(100), nullable=False, comment='角色名称')
    role_level = Column(Integer, nullable=False, comment='角色等级：1-超级管理员，2-机构管理员，3-普通用户')

    description = Column(Text, comment='角色描述')
    status = Column(Integer, default=1, comment='状态：1-启用，0-禁用')
    
    # 关联关系
    users = relationship('User', back_populates='role')
    permissions = relationship('Permission', secondary='role_permissions', back_populates='roles') 