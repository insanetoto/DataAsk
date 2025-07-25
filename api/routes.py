# -*- coding: utf-8 -*-
"""
API路由模块
"""
import logging
from typing import Any, Dict, List, Optional, Tuple
from flask import Blueprint, request, jsonify, g
from tools.auth_middleware import auth_required, permission_required
from tools.exceptions import ValidationException, DatabaseException
from tools.response import standardize_response
from tools.database import get_database_service
from tools.redis_service import get_redis_service
from service import (
    get_user_service_instance,
    get_organization_service_instance,
    get_menu_service_instance,
    get_role_service_instance,
    get_permission_service_instance
)

logger = logging.getLogger(__name__)

# 创建蓝图
api_bp = Blueprint('api', __name__)

# 导入其他路由模块
from . import auth_routes
from . import user_routes
from . import organization_routes
from . import role_permission_routes
from . import system_routes