# -*- coding: utf-8 -*-
"""
机构模型模块
"""
from sqlalchemy import Column, String, Integer, Text, ForeignKey
from sqlalchemy.orm import relationship
from .base import BaseModel

class Organization(BaseModel):
    """机构模型"""
    __tablename__ = 'organizations'
    
    org_code = Column(String(50), unique=True, nullable=False, comment='机构编码')
    org_name = Column(String(200), nullable=False, comment='机构名称')
    parent_org_code = Column(String(50), ForeignKey('organizations.org_code', onupdate='CASCADE', ondelete='SET NULL'), comment='上级机构编码')
    level_depth = Column(Integer, default=0, comment='层级深度：0-顶级机构，1-二级机构，以此类推')
    contact_person = Column(String(100), nullable=False, comment='负责人姓名')
    contact_phone = Column(String(20), nullable=False, comment='负责人联系电话')
    contact_email = Column(String(100), nullable=False, comment='负责人邮箱')
    status = Column(Integer, default=1, comment='状态：1-启用，0-禁用')
    
    # 关联关系
    parent = relationship('Organization', remote_side=[org_code], backref='children')
    users = relationship('User', back_populates='organization')
 