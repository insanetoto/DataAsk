# -*- coding: utf-8 -*-
"""
API模块包
提供RESTful API接口
"""
from flask import Blueprint

# 创建蓝图
api_bp = Blueprint('api', __name__)

# 导入路由模块
from . import auth_routes
from . import user_routes
from . import organization_routes
from . import role_permission_routes
from . import system_routes
from . import ai_routes
from . import workflow_routes
from . import audit_routes
from . import text2sql_routes
from . import message_routes

# 注册所有路由模块
def init_app(app):
    """初始化所有路由"""
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # 注册text2sql专用蓝图
    from .text2sql_routes import text2sql_bp
    app.register_blueprint(text2sql_bp) 