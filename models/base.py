# -*- coding: utf-8 -*-
"""
基础模型模块
提供所有模型的基类
"""
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, DateTime, func
from datetime import datetime

# 创建基类
Base = declarative_base()

class BaseModel(Base):
    """所有模型的基类"""
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    def to_dict(self):
        """将模型转换为字典"""
        result = {}
        for c in self.__table__.columns:
            value = getattr(self, c.name)
            if isinstance(value, datetime):
                result[c.name] = value.isoformat() if value else None
            else:
                result[c.name] = value
        return result 