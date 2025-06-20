# -*- coding: utf-8 -*-
"""
API路由模块
提供智能问答相关的API接口
"""
import logging
from typing import Dict, Any
from flask import Blueprint, request, jsonify, g
from AIEngine.vanna_service import get_vanna_service
from tools.database import get_database_service
from tools.redis_service import get_redis_service
from service.organization_service import get_organization_service
from service.user_service import get_user_service
from service.role_service import get_role_service
from service.permission_service import get_permission_service
from tools.auth_middleware import token_required, token_service

# License授权检查
from tools.license_middleware import require_license
# 权限验证中间件
from tools.auth_middleware import (
    permission_required, admin_required, super_admin_required,
    org_filter_required, get_current_user, get_org_filter, auth_required
)

logger = logging.getLogger(__name__)

# 创建蓝图
api_bp = Blueprint('api', __name__, url_prefix='/api')

def get_user_service_instance():
    return get_user_service()

@api_bp.route('/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    try:
        # 检查各服务状态
        db_service = get_database_service()
        redis_service = get_redis_service()
        vanna_service = get_vanna_service()
        
        health_status = {
            'status': 'healthy',
            'services': {
                'main_database': db_service.test_connection(),
                'vanna_database': db_service.test_vanna_connection(),
                'redis': redis_service.test_connection(),
                'vanna_ai': vanna_service.is_available()
            }
        }
        
        # 如果任何服务不可用，返回warning状态
        if not all(health_status['services'].values()):
            health_status['status'] = 'warning'
        
        return jsonify(health_status), 200
        
    except Exception as e:
        logger.error(f"健康检查失败: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@api_bp.route('/ask', methods=['POST'])
@require_license('ai_query')
def ask_question():
    """智能问答接口"""
    try:
        # 获取请求参数
        data = request.get_json()
        if not data or 'question' not in data:
            return jsonify({
                'success': False,
                'error': '缺少必要参数: question'
            }), 400
        
        question = data['question'].strip()
        if not question:
            return jsonify({
                'success': False,
                'error': '问题内容不能为空'
            }), 400
        
        use_cache = data.get('use_cache', True)
        
        # 使用Vanna服务处理问题
        vanna_service = get_vanna_service()
        result = vanna_service.ask_question(question, use_cache)
        
        return jsonify(result), 200 if result['success'] else 400
        
    except Exception as e:
        logger.error(f"问答处理失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/generate_sql', methods=['POST'])
@require_license('sql_generation')
def generate_sql():
    """生成SQL接口"""
    try:
        # 获取请求参数
        data = request.get_json()
        if not data or 'question' not in data:
            return jsonify({
                'success': False,
                'error': '缺少必要参数: question'
            }), 400
        
        question = data['question'].strip()
        if not question:
            return jsonify({
                'success': False,
                'error': '问题内容不能为空'
            }), 400
        
        use_cache = data.get('use_cache', True)
        
        # 使用Vanna服务生成SQL
        vanna_service = get_vanna_service()
        sql, confidence = vanna_service.generate_sql(question, use_cache)
        
        if sql:
            return jsonify({
                'success': True,
                'question': question,
                'sql': sql,
                'confidence': confidence
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': '无法生成SQL语句'
            }), 400
        
    except Exception as e:
        logger.error(f"SQL生成失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/execute_sql', methods=['POST'])
def execute_sql():
    """执行SQL接口"""
    try:
        # 获取请求参数
        data = request.get_json()
        if not data or 'sql' not in data:
            return jsonify({
                'success': False,
                'error': '缺少必要参数: sql'
            }), 400
        
        sql = data['sql'].strip()
        if not sql:
            return jsonify({
                'success': False,
                'error': 'SQL语句不能为空'
            }), 400
        
        # 安全检查 - 只允许SELECT语句
        if not sql.upper().strip().startswith('SELECT'):
            return jsonify({
                'success': False,
                'error': '仅支持SELECT查询语句'
            }), 400
        
        # 执行SQL查询
        db_service = get_database_service()
        result_data = db_service.execute_query(sql)
        
        return jsonify({
            'success': True,
            'sql': sql,
            'data': result_data,
            'count': len(result_data)
        }), 200
        
    except Exception as e:
        logger.error(f"SQL执行失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/train', methods=['POST'])
@require_license('training_enabled')
def train_model():
    """训练模型接口"""
    try:
        # 获取请求参数
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': '缺少训练数据'
            }), 400
        
        vanna_service = get_vanna_service()
        
        # 支持多种训练方式
        if 'ddl' in data:
            # DDL训练
            ddl_statements = data['ddl'] if isinstance(data['ddl'], list) else [data['ddl']]
            success = vanna_service.train_with_ddl(ddl_statements)
        elif 'documentation' in data:
            # 文档训练
            success = vanna_service.train_with_documentation(data['documentation'])
        elif 'question' in data and 'sql' in data:
            # 问题-SQL对训练
            success = vanna_service.train_with_sql(data['question'], data['sql'])
        else:
            return jsonify({
                'success': False,
                'error': '无效的训练数据格式'
            }), 400
        
        if success:
            return jsonify({
                'success': True,
                'message': '模型训练成功'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': '模型训练失败'
            }), 500
        
    except Exception as e:
        logger.error(f"模型训练失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/auto_train', methods=['POST'])  
@require_license('training_enabled')
def auto_train():
    """自动训练接口（从数据库Schema）"""
    try:
        vanna_service = get_vanna_service()
        success = vanna_service.auto_train_from_database()
        
        if success:
            return jsonify({
                'success': True,
                'message': '自动训练完成'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': '自动训练失败'
            }), 500
        
    except Exception as e:
        logger.error(f"自动训练失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/database/info', methods=['GET'])
def get_database_info():
    """获取数据库信息接口"""
    try:
        db_service = get_database_service()
        database_info = db_service.get_database_summary()
        
        return jsonify({
            'success': True,
            'data': database_info
        }), 200
        
    except Exception as e:
        logger.error(f"获取数据库信息失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/database/schema', methods=['GET'])
def get_database_schema():
    """获取数据库Schema信息"""
    try:
        db_service = get_database_service()
        schema_info = db_service.get_table_schemas()
        
        return jsonify({
            'success': True,
            'data': schema_info
        }), 200
        
    except Exception as e:
        logger.error(f"获取数据库Schema失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/cache/clear', methods=['POST'])
@require_license('cache_enabled')
def clear_cache():
    """清除缓存接口"""
    try:
        data = request.get_json() or {}
        cache_type = data.get('type', 'all')  # all, query, sql
        
        redis_service = get_redis_service()
        
        if cache_type == 'all':
            # 清除所有缓存
            redis_service.clear_vanna_cache()
            redis_service.clear_query_cache()
            message = '所有缓存已清除'
        elif cache_type == 'query':
            # 清除查询结果缓存
            redis_service.clear_query_cache()
            message = '查询结果缓存已清除'
        elif cache_type == 'sql':
            # 清除SQL生成缓存
            redis_service.clear_vanna_cache()
            message = 'SQL生成缓存已清除'
        else:
            return jsonify({
                'success': False,
                'error': '无效的缓存类型'
            }), 400
        
        return jsonify({
            'success': True,
            'message': message
        }), 200
        
    except Exception as e:
        logger.error(f"清除缓存失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ==================== 机构管理接口 ====================

@api_bp.route('/organizations', methods=['POST'])
def create_organization():
    """创建机构接口"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': '缺少请求数据'
            }), 400
        
        org_service = get_organization_service()
        result = org_service.create_organization(data)
        
        status_code = 201 if result['success'] else 400
        return jsonify(result), status_code
        
    except Exception as e:
        logger.error(f"创建机构失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'创建机构失败: {str(e)}'
        }), 500

@api_bp.route('/organizations/<int:org_id>', methods=['GET'])
def get_organization(org_id):
    """获取机构信息接口"""
    try:
        org_service = get_organization_service()
        result = org_service.get_organization_by_id(org_id)
        
        status_code = 200 if result['success'] else 404
        return jsonify(result), status_code
        
    except Exception as e:
        logger.error(f"获取机构信息失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'获取机构信息失败: {str(e)}'
        }), 500

@api_bp.route('/organizations/code/<string:org_code>', methods=['GET'])
def get_organization_by_code(org_code):
    """根据机构编码获取机构信息"""
    try:
        org_service = get_organization_service()
        result = org_service.get_organization_by_code(org_code)
        
        status_code = 200 if result['success'] else 404
        return jsonify(result), status_code
        
    except Exception as e:
        logger.error(f"根据编码获取机构信息失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'获取机构信息失败: {str(e)}'
        }), 500

@api_bp.route('/organizations', methods=['GET'])
def get_organizations_list():
    """获取机构列表接口"""
    try:
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 10, type=int)
        status = request.args.get('status', type=int)
        keyword = request.args.get('keyword')
        
        org_service = get_organization_service()
        result = org_service.get_organizations_list(
            page=page,
            page_size=page_size,
            status=status,
            keyword=keyword
        )
        
        return jsonify(result), 200 if result['success'] else 500
        
    except Exception as e:
        logger.error(f"获取机构列表失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'获取机构列表失败: {str(e)}'
        }), 500

@api_bp.route('/organizations/<int:org_id>', methods=['PUT'])
def update_organization(org_id):
    """更新机构信息接口"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': '缺少请求数据'
            }), 400
        
        org_service = get_organization_service()
        result = org_service.update_organization(org_id, data)
        
        return jsonify(result), 200 if result['success'] else 400
        
    except Exception as e:
        logger.error(f"更新机构信息失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'更新机构信息失败: {str(e)}'
        }), 500

@api_bp.route('/organizations/<int:org_id>', methods=['DELETE'])
def delete_organization(org_id):
    """删除机构接口"""
    try:
        org_service = get_organization_service()
        result = org_service.delete_organization(org_id)
        
        return jsonify(result), 200 if result['success'] else 400
        
    except Exception as e:
        logger.error(f"删除机构失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'删除机构失败: {str(e)}'
        }), 500

@api_bp.route('/organizations/cache/clear', methods=['POST'])
def clear_organization_cache():
    """清除机构缓存"""
    try:
        org_service = get_organization_service()
        # 这里可以添加清除缓存的逻辑
        
        return jsonify({
            'success': True,
            'message': '机构缓存已清除'
        }), 200
        
    except Exception as e:
        logger.error(f"清除机构缓存失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'清除缓存失败: {str(e)}'
        }), 500

@api_bp.route('/organizations/<string:org_code>/children', methods=['GET'])
def get_organization_children(org_code):
    """获取机构子机构列表"""
    try:
        include_self = request.args.get('include_self', 'false').lower() == 'true'
        
        org_service = get_organization_service()
        result = org_service.get_organization_children(org_code, include_self)
        
        return jsonify(result), 200 if result['success'] else 500
        
    except Exception as e:
        logger.error(f"获取子机构列表失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'获取子机构列表失败: {str(e)}'
        }), 500

@api_bp.route('/organizations/<string:org_code>/parents', methods=['GET'])
def get_organization_parents(org_code):
    """获取机构上级机构列表"""
    try:
        include_self = request.args.get('include_self', 'false').lower() == 'true'
        
        org_service = get_organization_service()
        result = org_service.get_organization_parents(org_code, include_self)
        
        return jsonify(result), 200 if result['success'] else 500
        
    except Exception as e:
        logger.error(f"获取上级机构列表失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'获取上级机构列表失败: {str(e)}'
        }), 500

@api_bp.route('/organizations/tree', methods=['GET'])
def get_organization_tree():
    """获取机构树形结构"""
    try:
        root_org_code = request.args.get('root_org_code')
        
        org_service = get_organization_service()
        result = org_service.get_organization_tree(root_org_code)
        
        return jsonify(result), 200 if result['success'] else 500
        
    except Exception as e:
        logger.error(f"获取机构树失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'获取机构树失败: {str(e)}'
        }), 500

@api_bp.route('/organizations/hierarchy', methods=['GET'])
def get_organization_hierarchy():
    """获取机构层级视图"""
    try:
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 10, type=int)
        keyword = request.args.get('keyword')
        
        org_service = get_organization_service()
        result = org_service.get_organization_hierarchy_view(
            page=page,
            page_size=page_size,
            keyword=keyword
        )
        
        return jsonify(result), 200 if result['success'] else 500
        
    except Exception as e:
        logger.error(f"获取机构层级视图失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'获取机构层级视图失败: {str(e)}'
        }), 500

@api_bp.route('/organizations/<string:org_code>/move', methods=['PUT'])
def move_organization(org_code):
    """移动机构到新的上级机构"""
    try:
        data = request.get_json()
        new_parent_code = data.get('new_parent_code') if data else None
        
        org_service = get_organization_service()
        result = org_service.move_organization(org_code, new_parent_code)
        
        return jsonify(result), 200 if result['success'] else 400
        
    except Exception as e:
        logger.error(f"移动机构失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'移动机构失败: {str(e)}'
        }), 500

# ==================== 用户认证接口 ====================

@api_bp.route('/auth/login', methods=['POST'])
def login():
    """用户登录"""
    try:
        logger.info("收到登录请求")
        data = request.get_json()
        if not data:
            logger.warning("请求数据为空")
            return jsonify({
                'success': False,
                'error': '无效的请求数据'
            }), 400
            
        logger.info(f"登录请求数据: {data}")
        
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            logger.warning("用户名或密码为空")
            return jsonify({
                'success': False,
                'error': '用户名和密码不能为空'
            }), 400

        logger.info(f"开始验证用户: {username}")
        # 验证用户
        user = get_user_service_instance().authenticate_user(username, password)
        if not user:
            logger.warning(f"用户验证失败: {username}")
            return jsonify({
                'success': False,
                'error': '用户名或密码错误'
            }), 401

        logger.info(f"用户验证成功，开始生成令牌: {username}")
        # 生成令牌
        tokens = get_user_service_instance().create_tokens(user)
        if not tokens:
            logger.error(f"令牌生成失败: {username}")
            return jsonify({
                'success': False,
                'error': '生成令牌失败'
            }), 500
        
        logger.info(f"登录成功: {username}")
        return jsonify({
            'success': True,
            'data': tokens,
            'message': '登录成功'
        }), 200
        
    except Exception as e:
        logger.error(f"登录过程出错: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'登录失败: {str(e)}'
        }), 500

@api_bp.route('/auth/refresh', methods=['POST'])
def refresh_token():
    """刷新访问令牌"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({
            'code': 401,
            'message': '无效的认证头'
        }), 401

    refresh_token = auth_header.split(' ')[1]
    new_tokens = get_user_service_instance().refresh_access_token(refresh_token)
    
    if not new_tokens:
        return jsonify({
            'code': 401,
            'message': '无效或过期的刷新令牌'
        }), 401

    return jsonify({
        'code': 200,
        'message': '令牌刷新成功',
        'data': new_tokens
    })

@api_bp.route('/auth/logout', methods=['POST'])
@auth_required
def logout():
    """用户登出"""
    user_id = request.user.get('user_id')
    get_user_service_instance().revoke_tokens(user_id)
    
    return jsonify({
        'code': 200,
        'message': '登出成功'
    })

@api_bp.route('/auth/profile', methods=['GET'])
@token_required
def get_profile():
    """获取当前用户信息"""
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({
                'success': False,
                'error': '获取用户信息失败'
            }), 401
            
        return jsonify({
            'success': True,
            'data': {
                'id': current_user['id'],
                'name': current_user['username'],
                'avatar': current_user.get('avatar', ''),
                'email': current_user.get('email', ''),
                'role_code': current_user['role_code'],
                'org_code': current_user['org_code'],
                'permissions': current_user.get('permissions', [])
            }
        }), 200
        
    except Exception as e:
        logger.error(f"获取用户信息失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'获取用户信息失败: {str(e)}'
        }), 500

@api_bp.route('/auth/permissions', methods=['GET'])
@token_required
def get_user_permissions():
    """获取当前用户权限列表"""
    try:
        current_user = get_current_user()
        permission_service = get_permission_service()
        
        permissions_result = permission_service.get_user_permissions(current_user['id'])
        
        if not permissions_result['success']:
            return jsonify(permissions_result), 500
            
        return jsonify({
            'success': True,
            'data': permissions_result['data']
        }), 200
        
    except Exception as e:
        logger.error(f"获取用户权限失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'获取用户权限失败: {str(e)}'
        }), 500

# ==================== 用户管理接口 ====================

@api_bp.route('/users', methods=['GET'], endpoint='list_users')
@auth_required
def get_users():
    """获取用户列表"""
    try:
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 10, type=int)
        keyword = request.args.get('keyword', '')
        status = request.args.get('status', None, type=int)
        
        user_service = get_user_service()
        result = user_service.get_users_list(page, page_size, keyword=keyword, status=status)
        
        return jsonify(result), 200 if result['success'] else 400
        
    except Exception as e:
        logger.error(f"获取用户列表失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/users/<int:user_id>', methods=['GET'], endpoint='get_user_by_id')
@auth_required
def get_user(user_id):
    """获取用户信息"""
    user_service = get_user_service()
    result = user_service.get_user_by_id(user_id)
    return jsonify(result), 200 if result['success'] else 400

@api_bp.route('/users', methods=['POST'], endpoint='create_new_user')
@auth_required
def create_user():
    """创建用户"""
    data = request.get_json()
    user_service = get_user_service()
    result = user_service.create_user(data)
    return jsonify(result), 200 if result['success'] else 400

@api_bp.route('/users/<int:user_id>', methods=['PUT'], endpoint='update_user_by_id')
@auth_required
def update_user(user_id):
    """更新用户信息"""
    data = request.get_json()
    user_service = get_user_service()
    result = user_service.update_user(user_id, data)
    return jsonify(result), 200 if result['success'] else 400

@api_bp.route('/users/<int:user_id>', methods=['DELETE'], endpoint='delete_user_by_id')
@auth_required
def delete_user(user_id):
    """删除用户"""
    user_service = get_user_service()
    result = user_service.delete_user(user_id)
    return jsonify(result), 200 if result['success'] else 400

@api_bp.route('/users/<int:user_id>/roles', methods=['GET'], endpoint='get_user_roles_by_id')
@auth_required
def get_user_roles(user_id):
    """获取用户角色"""
    user_service = get_user_service()
    roles = user_service.get_user_roles(user_id)
    return jsonify({'success': True, 'data': roles}), 200

@api_bp.route('/users/<int:user_id>/roles', methods=['POST'], endpoint='set_user_roles_by_id')
@auth_required
def set_user_roles(user_id):
    """设置用户角色"""
    data = request.get_json()
    role_ids = data.get('role_ids', [])
    user_service = get_user_service()
    success = user_service.set_user_roles(user_id, role_ids)
    return jsonify({'success': success}), 200 if success else 400

@api_bp.route('/users/<int:user_id>/permissions', methods=['GET'], endpoint='get_user_permissions_by_id')
@auth_required
def get_user_permissions(user_id):
    """获取用户权限"""
    user_service = get_user_service()
    permissions = user_service.get_user_permissions(user_id)
    return jsonify({'success': True, 'data': permissions}), 200

# ==================== 角色管理接口 ====================

@api_bp.route('/roles', methods=['GET'], endpoint='list_roles')
@auth_required
def get_roles():
    """获取角色列表"""
    try:
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 10, type=int)
        keyword = request.args.get('keyword', '')
        status = request.args.get('status', None, type=int)
        
        role_service = get_role_service()
        result = role_service.get_roles_list(page, page_size, keyword=keyword, status=status)
        
        return jsonify(result), 200 if result['success'] else 400
        
    except Exception as e:
        logger.error(f"获取角色列表失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/roles/<int:role_id>', methods=['GET'], endpoint='get_role_by_id')
@auth_required
def get_role(role_id):
    """获取角色信息"""
    role_service = get_role_service()
    result = role_service.get_role_by_id(role_id)
    return jsonify(result), 200 if result['success'] else 400

@api_bp.route('/roles', methods=['POST'], endpoint='create_new_role')
@auth_required
def create_role():
    """创建角色"""
    data = request.get_json()
    role_service = get_role_service()
    result = role_service.create_role(data)
    return jsonify(result), 200 if result['success'] else 400

@api_bp.route('/roles/<int:role_id>', methods=['PUT'], endpoint='update_role_by_id')
@auth_required
def update_role(role_id):
    """更新角色信息"""
    data = request.get_json()
    role_service = get_role_service()
    result = role_service.update_role(role_id, data)
    return jsonify(result), 200 if result['success'] else 400

@api_bp.route('/roles/<int:role_id>', methods=['DELETE'], endpoint='delete_role_by_id')
@auth_required
def delete_role(role_id):
    """删除角色"""
    role_service = get_role_service()
    result = role_service.delete_role(role_id)
    return jsonify(result), 200 if result['success'] else 400

@api_bp.route('/roles/<int:role_id>/permissions', methods=['GET'], endpoint='get_role_permissions_by_id')
@auth_required
def get_role_permissions(role_id):
    """获取角色权限"""
    role_service = get_role_service()
    result = role_service.get_role_permissions(role_id)
    return jsonify(result), 200 if result['success'] else 400

@api_bp.route('/roles/<int:role_id>/permissions', methods=['POST'], endpoint='set_role_permissions_by_id')
@auth_required
def set_role_permissions(role_id):
    """设置角色权限"""
    data = request.get_json()
    permission_codes = data.get('permission_codes', [])
    permission_service = get_permission_service()
    result = permission_service.assign_permissions_to_role(role_id, permission_codes)
    return jsonify(result), 200 if result['success'] else 400

# ==================== 权限管理接口 ====================

@api_bp.route('/permissions', methods=['GET'], endpoint='list_permissions')
@auth_required
def get_permissions():
    """获取权限列表"""
    try:
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 10, type=int)
        keyword = request.args.get('keyword', '')
        status = request.args.get('status', None, type=int)
        
        permission_service = get_permission_service()
        result = permission_service.get_permissions_list(page, page_size, keyword=keyword, status=status)
        
        return jsonify(result), 200 if result['success'] else 400
        
    except Exception as e:
        logger.error(f"获取权限列表失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/permissions/<int:permission_id>', methods=['GET'], endpoint='get_permission_by_id')
@auth_required
def get_permission(permission_id):
    """获取权限信息"""
    permission_service = get_permission_service()
    result = permission_service.get_permission_by_id(permission_id)
    return jsonify(result), 200 if result['success'] else 400

@api_bp.route('/permissions', methods=['POST'], endpoint='create_new_permission')
@auth_required
def create_permission():
    """创建权限"""
    data = request.get_json()
    permission_service = get_permission_service()
    result = permission_service.create_permission(data)
    return jsonify(result), 200 if result['success'] else 400

@api_bp.route('/permissions/<int:permission_id>', methods=['PUT'], endpoint='update_permission_by_id')
@auth_required
def update_permission(permission_id):
    """更新权限信息"""
    data = request.get_json()
    permission_service = get_permission_service()
    result = permission_service.update_permission(permission_id, data)
    return jsonify(result), 200 if result['success'] else 400

@api_bp.route('/permissions/<int:permission_id>', methods=['DELETE'], endpoint='delete_permission_by_id')
@auth_required
def delete_permission(permission_id):
    """删除权限"""
    permission_service = get_permission_service()
    result = permission_service.delete_permission(permission_id)
    return jsonify(result), 200 if result['success'] else 400

@api_bp.route('/permissions/tree', methods=['GET'], endpoint='get_permission_tree_view')
@auth_required
def get_permission_tree():
    """获取权限树"""
    permission_service = get_permission_service()
    result = permission_service.get_permission_tree()
    return jsonify(result), 200 if result['success'] else 400

@api_bp.route('/notice', methods=['GET'])
def get_notice():
    """获取通知列表"""
    notices = [
        {
            "id": "xxx1",
            "title": "智能问答模型训练",
            "logo": "https://gw.alipayobjects.com/zos/rmsportal/WdGqmHpayyMjiEhcKoVE.png",
            "description": "基于最新数据集进行的智能问答模型训练任务",
            "updatedAt": "2025-06-17T07:16:50.587Z",
            "member": "张工",
            "href": "",
            "memberLink": ""
        },
        {
            "id": "xxx2",
            "title": "知识库更新",
            "logo": "https://gw.alipayobjects.com/zos/rmsportal/zOsKZmFRdUtvpqCImOVY.png",
            "description": "金融领域知识库的定期更新维护",
            "updatedAt": "2025-06-17T07:16:50.587Z",
            "member": "李工",
            "href": "",
            "memberLink": ""
        },
        {
            "id": "xxx3",
            "title": "系统性能优化",
            "logo": "https://gw.alipayobjects.com/zos/rmsportal/dURIMkkrRFpPgTuzkwnB.png",
            "description": "对系统进行性能调优和资源优化",
            "updatedAt": "2025-06-17T07:16:50.587Z",
            "member": "王工",
            "href": "",
            "memberLink": ""
        },
        {
            "id": "xxx4",
            "title": "用户反馈分析",
            "logo": "https://gw.alipayobjects.com/zos/rmsportal/sfjbOqnsXXJgNCjCzDBL.png",
            "description": "收集和分析用户使用反馈，优化系统体验",
            "updatedAt": "2025-06-17T07:16:50.587Z",
            "member": "赵工",
            "href": "",
            "memberLink": ""
        }
    ]
    return jsonify(notices)

@api_bp.route('/activities', methods=['GET'])
def get_activities():
    """获取活动列表"""
    activities = [
        {
            "id": "trend-1",
            "updatedAt": "2025-06-17T07:16:50.587Z",
            "user": {
                "name": "张工",
                "avatar": "https://gw.alipayobjects.com/zos/rmsportal/BiazfanxmamNRoxxVxka.png"
            },
            "group": {
                "name": "AI研发组",
                "link": "http://github.com/"
            },
            "project": {
                "name": "智能问答系统",
                "link": "http://github.com/"
            },
            "template": "在 @{group} 新建项目 @{project}"
        },
        {
            "id": "trend-2",
            "updatedAt": "2025-06-17T07:16:50.587Z",
            "user": {
                "name": "李工",
                "avatar": "https://gw.alipayobjects.com/zos/rmsportal/jZUIxmJycoymBprLOUbT.png"
            },
            "group": {
                "name": "数据处理组",
                "link": "http://github.com/"
            },
            "project": {
                "name": "知识库管理",
                "link": "http://github.com/"
            },
            "template": "在 @{group} 更新了 @{project}"
        },
        {
            "id": "trend-3",
            "updatedAt": "2025-06-17T07:16:50.587Z",
            "user": {
                "name": "王工",
                "avatar": "https://gw.alipayobjects.com/zos/rmsportal/dURIMkkrRFpPgTuzkwnB.png"
            },
            "group": {
                "name": "产品设计组",
                "link": "http://github.com/"
            },
            "project": {
                "name": "用户界面",
                "link": "http://github.com/"
            },
            "template": "在 @{group} 发布了 @{project}"
        }
    ]
    return jsonify(activities)

@api_bp.route('/chart', methods=['GET'])
def get_chart():
    """获取图表数据"""
    data = {
        "radarData": [
            {
                "name": "个人",
                "label": "引用",
                "value": 10
            },
            {
                "name": "个人",
                "label": "口碑",
                "value": 8
            },
            {
                "name": "个人",
                "label": "产量",
                "value": 4
            },
            {
                "name": "个人",
                "label": "贡献",
                "value": 5
            },
            {
                "name": "个人",
                "label": "热度",
                "value": 7
            },
            {
                "name": "团队",
                "label": "引用",
                "value": 3
            },
            {
                "name": "团队",
                "label": "口碑",
                "value": 9
            },
            {
                "name": "团队",
                "label": "产量",
                "value": 6
            },
            {
                "name": "团队",
                "label": "贡献",
                "value": 3
            },
            {
                "name": "团队",
                "label": "热度",
                "value": 1
            },
            {
                "name": "部门",
                "label": "引用",
                "value": 4
            },
            {
                "name": "部门",
                "label": "口碑",
                "value": 3
            },
            {
                "name": "部门",
                "label": "产量",
                "value": 8
            },
            {
                "name": "部门",
                "label": "贡献",
                "value": 7
            },
            {
                "name": "部门",
                "label": "热度",
                "value": 2
            }
        ]
    }
    return jsonify(data)

@api_bp.route('/user/info', methods=['GET'])
@auth_required
def get_user_info():
    """获取当前登录用户信息"""
    try:
        current_user = g.current_user
        if not current_user:
            return jsonify({
                'success': False,
                'error': '用户未登录'
            }), 401

        # 获取用户菜单
        from service.menu_service import get_menu_service
        menu_service = get_menu_service()
        menu_result = menu_service.get_user_menus(current_user['id'])
        
        if not menu_result['success']:
            return jsonify({
                'success': False,
                'error': menu_result['error']
            }), 500

        # 构建用户信息响应
        user_info = {
            'success': True,
            'data': {
                'user': {
                    'id': current_user['id'],
                    'username': current_user['username'],
                    'name': current_user['username'],
                    'avatar': current_user.get('avatar', './assets/tmp/img/avatar.jpg'),
                    'email': current_user.get('email', ''),
                    'status': current_user['status'],
                    'orgCode': current_user['org_code'],
                    'roleCode': current_user['role_code'],
                    'permissions': current_user.get('permissions', [])
                },
                'menus': menu_result['data']
            }
        }
        
        return jsonify(user_info), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'获取用户信息失败: {str(e)}'
        }), 500 