# -*- coding: utf-8 -*-
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """基础配置类"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'zkbw-key'
    
        # MySQL配置
    MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
    MYSQL_PORT = int(os.environ.get('MYSQL_PORT', '3306'))
    MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', 'llmstudy')
    MYSQL_DATABASE = os.environ.get('MYSQL_DATABASE', 'dataask')
    VANNA_DATABASE = os.environ.get('VANNA_DATABASE', 'vanna')
    
    # SQLAlchemy配置 - 主数据库（用于机构管理等业务数据）
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}?charset=utf8mb4"
    
    # Vanna专用数据库配置
    VANNA_DATABASE_URI = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{VANNA_DATABASE}?charset=utf8mb4"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 120,
        'pool_pre_ping': True
    }
    
    # Redis配置
    REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.environ.get('REDIS_PORT', '6379'))
    REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD', '')
    REDIS_DB = int(os.environ.get('REDIS_DB', '0'))
    
    # Vanna AI配置 - 支持阿里云百炼平台
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
    OPENAI_API_BASE = os.environ.get('OPENAI_API_BASE', 'https://dashscope.aliyuncs.com/compatible-mode/v1')
    VANNA_MODEL = os.environ.get('VANNA_MODEL', 'qwen-turbo')  # 默认使用阿里云qwen-turbo模型
    
    # 应用配置
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    HOST = os.environ.get('FLASK_HOST', '0.0.0.0')
    PORT = int(os.environ.get('FLASK_PORT', '9000'))

    # License配置
    LICENSE_KEY = os.getenv('LICENSE_KEY', '')
    LICENSE_FEATURES = {}
    LICENSE_ENABLED = os.getenv('LICENSE_ENABLED', 'false').lower() == 'true'  # 默认关闭license校验

    # JWT配置
    SECRET_KEY = os.getenv('SECRET_KEY', 'zkbw-key-production')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', SECRET_KEY)

    # Vanna AI 数据库配置
    VANNA_DATABASE_URI = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/vanna"

class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    LICENSE_ENABLED = False  # 开发环境默认关闭license校验

class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    LICENSE_ENABLED = True  # 生产环境强制启用license校验

class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    DEBUG = False
    LICENSE_ENABLED = False  # 测试环境禁用license校验
    
    # 使用内存SQLite数据库进行测试
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    VANNA_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Redis配置 - 使用测试专用DB
    REDIS_HOST = 'localhost'
    REDIS_PORT = 6379
    REDIS_DB = 15  # 使用测试专用DB
    
    # 其他测试配置
    SECRET_KEY = 'test-secret-key'
    JWT_SECRET_KEY = 'test-jwt-secret'

# 配置字典
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
} 