# -*- coding: utf-8 -*-
"""
用户模型模块
"""
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .base import BaseModel

class User(BaseModel):
    """用户模型"""
    __tablename__ = 'users'
    
    org_code = Column(String(50), ForeignKey('organizations.org_code', onupdate='CASCADE'), nullable=False, comment='所属机构编码')
    user_code = Column(String(50), unique=True, nullable=False, comment='用户编码')
    username = Column(String(100), nullable=False, comment='用户名称')
    password_hash = Column(String(255), nullable=False, comment='密码哈希')
    phone = Column(String(20), comment='联系电话')
    address = Column(String(500), comment='联系地址')
    role_id = Column(Integer, ForeignKey('roles.id', onupdate='CASCADE'), nullable=False, comment='角色ID')
    last_login_at = Column(DateTime, comment='最后登录时间')
    login_count = Column(Integer, default=0, comment='登录次数')
    status = Column(Integer, default=1, comment='状态：1-启用，0-禁用')
    
    # 关联关系
    organization = relationship('Organization', back_populates='users')
    role = relationship('Role', back_populates='users') 