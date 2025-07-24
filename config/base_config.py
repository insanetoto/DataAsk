# -*- coding: utf-8 -*-
import os
from datetime import timedelta

class Config:
    """应用配置"""
    
    # 基础配置
    SECRET_KEY = 'dev-secret-key'
    DEBUG = True
    PORT = 9000  # 后端服务端口号，固定为9000
    
    # 数据库配置
    DB_HOST = '127.0.0.1'
    DB_PORT = 3306
    DB_USER = 'root'
    DB_PASSWORD = 'llmstudy'
    DB_NAME = 'dataask'
    VANNA_DATABASE = 'vanna'
    
    # SQLAlchemy配置
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
    VANNA_DATABASE_URI = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{VANNA_DATABASE}?charset=utf8mb4"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 120,
        'pool_pre_ping': True
    }
    
    # Redis配置
    REDIS_HOST = 'localhost'
    REDIS_PORT = 6379
    REDIS_DB = 0
    REDIS_PASSWORD = None
    
    # JWT配置
    JWT_SECRET_KEY = 'jwt-secret-key'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    
    # OpenAI配置
    OPENAI_API_KEY = ''
    OPENAI_API_BASE = 'https://api.openai.com/v1'
    OPENAI_MODEL = 'gpt-3.5-turbo'
    
    # Vanna配置
    VANNA_MODEL = 'qwen-turbo'
    VANNA_API_KEY = ''
    VANNA_API_BASE = 'https://dashscope.aliyuncs.com/compatible-mode/v1'
    
    # 跨域配置
    CORS_ORIGINS = [
        'http://localhost:4200',  # Angular开发服务器
        'http://localhost:9000',  # Flask开发服务器
    ]
    
    # 文件上传配置
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    
    # 日志配置
    LOG_LEVEL = 'INFO'
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs/app.log')
    
    @staticmethod
    def init_app(app):
        """初始化应用配置"""
        # 确保上传目录存在
        if not os.path.exists(Config.UPLOAD_FOLDER):
            os.makedirs(Config.UPLOAD_FOLDER)
        
        # 确保日志目录存在
        log_dir = os.path.dirname(Config.LOG_FILE)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    DEBUG = True
    
    # 使用测试数据库
    DB_NAME = 'dataask_test'
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{Config.DB_USER}:{Config.DB_PASSWORD}@{Config.DB_HOST}:{Config.DB_PORT}/{DB_NAME}?charset=utf8mb4"
    
    # 使用测试Redis数据库
    REDIS_DB = 1

class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    
    # 生产环境应该使用更强的密钥
    SECRET_KEY = 'production-secret-key'  # 请在部署时修改为强密钥
    JWT_SECRET_KEY = 'production-jwt-secret-key'  # 请在部署时修改为强密钥
    
    # 生产环境跨域配置
    CORS_ORIGINS = [
        'https://localhost:9000'  # 请在部署时修改为实际域名
    ]

config = {
    'development': Config,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': Config
} 