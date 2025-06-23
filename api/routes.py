# -*- coding: utf-8 -*-
"""
API路由模块
提供智能问答相关的API接口
"""
import logging
from typing import Dict, Any
from flask import Blueprint, request, jsonify, g, current_app
from AIEngine.vanna_service import get_vanna_service
from tools.database import get_database_service
from tools.redis_service import get_redis_service
from service.organization_service import get_organization_service
from service.user_service import get_user_service
from service.role_service import get_role_service
from service.permission_service import get_permission_service
from service.menu_service import get_menu_service
from tools.auth_middleware import token_required, token_service, auth_required, generate_token

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

def standardize_response(success: bool, data: Any = None, message: str = None, error: str = None, code: int = None) -> tuple:
    """
    标准化API响应格式
    
    Args:
        success: 操作是否成功
        data: 响应数据
        message: 成功消息
        error: 错误消息
        code: HTTP状态码
    
    Returns:
        (response_dict, status_code)
    """
    if success:
        status_code = code or 200
        return {
            'code': status_code,
            'message': message or '操作成功',
            'data': data
        }, status_code
    else:
        status_code = code or 400
        return {
            'code': status_code,
            'message': error or '操作失败',
            'data': None
        }, status_code

def get_user_service_instance():
    return get_user_service()

def get_menu_service_instance():
    return get_menu_service()

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
            response, status = standardize_response(False, error='缺少必要参数: question', code=400)
            return jsonify(response), status
        
        question = data['question'].strip()
        if not question:
            response, status = standardize_response(False, error='问题内容不能为空', code=400)
            return jsonify(response), status
        
        use_cache = data.get('use_cache', True)
        
        # 使用Vanna服务处理问题
        vanna_service = get_vanna_service()
        result = vanna_service.ask_question(question, use_cache)
        
        # 转换服务层响应为标准格式
        if result.get('success'):
            response, status = standardize_response(True, data=result.get('data'), message='问答处理成功')
        else:
            response, status = standardize_response(False, error=result.get('error', '问答处理失败'), code=400)
        return jsonify(response), status
        
    except Exception as e:
        logger.error(f"问答处理失败: {str(e)}")
        response, status = standardize_response(False, error=str(e), code=500)
        return jsonify(response), status

@api_bp.route('/generate_sql', methods=['POST'])
@require_license('sql_generation')
def generate_sql():
    """生成SQL接口"""
    try:
        # 获取请求参数
        data = request.get_json()
        if not data or 'question' not in data:
            response, status = standardize_response(False, error='缺少必要参数: question', code=400)
            return jsonify(response), status
        
        question = data['question'].strip()
        if not question:
            response, status = standardize_response(False, error='问题内容不能为空', code=400)
            return jsonify(response), status
        
        use_cache = data.get('use_cache', True)
        
        # 使用Vanna服务生成SQL
        vanna_service = get_vanna_service()
        sql, confidence = vanna_service.generate_sql(question, use_cache)
        
        if sql:
            response_data = {
                'question': question,
                'sql': sql,
                'confidence': confidence
            }
            response, status = standardize_response(True, data=response_data, message='SQL生成成功')
            return jsonify(response), status
        else:
            response, status = standardize_response(False, error='无法生成SQL语句', code=400)
            return jsonify(response), status
        
    except Exception as e:
        logger.error(f"SQL生成失败: {str(e)}")
        response, status = standardize_response(False, error=str(e), code=500)
        return jsonify(response), status

@api_bp.route('/execute_sql', methods=['POST'])
def execute_sql():
    """执行SQL接口"""
    try:
        # 获取请求参数
        data = request.get_json()
        if not data or 'sql' not in data:
            response, status = standardize_response(False, error='缺少必要参数: sql', code=400)
            return jsonify(response), status
        
        sql = data['sql'].strip()
        if not sql:
            response, status = standardize_response(False, error='SQL语句不能为空', code=400)
            return jsonify(response), status
        
        # 安全检查 - 只允许SELECT语句
        if not sql.upper().strip().startswith('SELECT'):
            response, status = standardize_response(False, error='仅支持SELECT查询语句', code=400)
            return jsonify(response), status
        
        # 执行SQL查询
        db_service = get_database_service()
        result_data = db_service.execute_query(sql)
        
        response_data = {
            'sql': sql,
            'data': result_data,
            'count': len(result_data)
        }
        response, status = standardize_response(True, data=response_data, message='SQL执行成功')
        return jsonify(response), status
        
    except Exception as e:
        logger.error(f"SQL执行失败: {str(e)}")
        response, status = standardize_response(False, error=str(e), code=500)
        return jsonify(response), status

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
            response, status = standardize_response(True, message='模型训练成功')
            return jsonify(response), status
        else:
            response, status = standardize_response(False, error='模型训练失败', code=500)
            return jsonify(response), status
        
    except Exception as e:
        logger.error(f"模型训练失败: {str(e)}")
        response, status = standardize_response(False, error=str(e), code=500)
        return jsonify(response), status

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
                'code': 400,
                'message': '缺少请求数据',
                'data': None
            }), 400
        
        org_service = get_organization_service()
        result = org_service.create_organization(data)
        
        # 转换为标准格式
        if result['success']:
            return jsonify({
                'code': 201,
                'message': '创建机构成功',
                'data': result['data']
            }), 201
        else:
            return jsonify({
                'code': 400,
                'message': result.get('error', '创建机构失败'),
                'data': None
            }), 400
        
    except Exception as e:
        logger.error(f"创建机构失败: {str(e)}")
        return jsonify({
            'code': 500,
            'message': f'创建机构失败: {str(e)}',
            'data': None
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
        page = request.args.get('pi', 1, type=int)  # 前端使用pi参数
        page_size = request.args.get('ps', 10, type=int)  # 前端使用ps参数
        status = request.args.get('status', type=int)
        keyword = request.args.get('keyword')
        
        org_service = get_organization_service()
        result = org_service.get_organizations_list(
            page=page,
            page_size=page_size,
            status=status,
            keyword=keyword
        )
        
        # 转换为标准格式
        if result['success']:
            return jsonify({
                'code': 200,
                'message': '获取机构列表成功',
                'data': result['data']
            }), 200
        else:
            return jsonify({
                'code': 500,
                'message': result.get('error', '获取机构列表失败'),
                'data': None
            }), 500
        
    except Exception as e:
        logger.error(f"获取机构列表失败: {str(e)}")
        return jsonify({
            'code': 500,
            'message': f'获取机构列表失败: {str(e)}',
            'data': None
        }), 500

@api_bp.route('/organizations/<int:org_id>', methods=['PUT'])
def update_organization(org_id):
    """更新机构信息接口"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'code': 400,
                'message': '缺少请求数据',
                'data': None
            }), 400
        
        org_service = get_organization_service()
        result = org_service.update_organization(org_id, data)
        
        # 转换为标准格式
        if result['success']:
            return jsonify({
                'code': 200,
                'message': '更新机构成功',
                'data': result['data']
            }), 200
        else:
            return jsonify({
                'code': 400,
                'message': result.get('error', '更新机构失败'),
                'data': None
            }), 400
        
    except Exception as e:
        logger.error(f"更新机构信息失败: {str(e)}")
        return jsonify({
            'code': 500,
            'message': f'更新机构信息失败: {str(e)}',
            'data': None
        }), 500

@api_bp.route('/organizations/<int:org_id>', methods=['DELETE'])
def delete_organization(org_id):
    """删除机构接口"""
    try:
        org_service = get_organization_service()
        result = org_service.delete_organization(org_id)
        
        # 转换为标准格式
        if result['success']:
            return jsonify({
                'code': 200,
                'message': '删除机构成功',
                'data': result.get('data')
            }), 200
        else:
            return jsonify({
                'code': 400,
                'message': result.get('error', '删除机构失败'),
                'data': None
            }), 400
        
    except Exception as e:
        logger.error(f"删除机构失败: {str(e)}")
        return jsonify({
            'code': 500,
            'message': f'删除机构失败: {str(e)}',
            'data': None
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
        
        # 转换为标准响应格式
        if result['success']:
            response, status = standardize_response(True, data=result['data'], message='获取机构树成功')
        else:
            response, status = standardize_response(False, error=result.get('error', '获取机构树失败'), code=500)
        return jsonify(response), status
        
    except Exception as e:
        logger.error(f"获取机构树失败: {str(e)}")
        response, status = standardize_response(False, error=f'获取机构树失败: {str(e)}', code=500)
        return jsonify(response), status

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
    """
    用户登录接口
    """
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({
                'code': 400,
                'message': '用户名和密码不能为空',
                'data': None
            }), 400
        
        # 验证用户名和密码
        user = get_user_service_instance().verify_password(username, password)
        if not user:
            return jsonify({
                'code': 401,
                'message': '用户名或密码错误',
                'data': None
            }), 401
        
        # 生成token
        token_info = generate_token(user['id'])
        
        return jsonify({
            'code': 200,
            'message': '登录成功',
            'data': token_info
        })
        
    except Exception as e:
        current_app.logger.error(f"Error in login: {str(e)}")
        return jsonify({
            'code': 500,
            'message': '登录失败',
            'data': None
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
            response, status = standardize_response(False, error='获取用户信息失败', code=401)
            return jsonify(response), status
            
        user_data = {
            'id': current_user['id'],
            'name': current_user['username'],
            'avatar': current_user.get('avatar', ''),
            'email': current_user.get('email', ''),
            'role_code': current_user['role_code'],
            'org_code': current_user['org_code'],
            'permissions': current_user.get('permissions', [])
        }
        response, status = standardize_response(True, data=user_data, message='获取用户信息成功')
        return jsonify(response), status
        
    except Exception as e:
        logger.error(f"获取用户信息失败: {str(e)}")
        response, status = standardize_response(False, error=f'获取用户信息失败: {str(e)}', code=500)
        return jsonify(response), status

@api_bp.route('/auth/permissions', methods=['GET'])
@token_required
def get_user_permissions():
    """获取当前用户权限列表"""
    try:
        current_user = get_current_user()
        permission_service = get_permission_service()
        
        permissions_result = permission_service.get_user_permissions(current_user['id'])
        
        if not permissions_result['success']:
            response, status = standardize_response(False, error=permissions_result.get('error', '获取权限失败'), code=500)
            return jsonify(response), status
            
        response, status = standardize_response(True, data=permissions_result['data'], message='获取用户权限成功')
        return jsonify(response), status
        
    except Exception as e:
        logger.error(f"获取用户权限失败: {str(e)}")
        response, status = standardize_response(False, error=f'获取用户权限失败: {str(e)}', code=500)
        return jsonify(response), status

# ==================== 用户管理接口 ====================

@api_bp.route('/users', methods=['GET'], endpoint='list_users')
@auth_required
def get_users():
    """获取用户列表"""
    try:
        # 支持ng-alain表格组件的参数格式：pi, ps
        page = request.args.get('pi', request.args.get('page', 1), type=int)
        page_size = request.args.get('ps', request.args.get('page_size', 10), type=int)
        keyword = request.args.get('keyword', '')
        
        # 处理undefined字符串值
        status_str = request.args.get('status')
        if status_str and status_str != 'undefined':
            status = int(status_str)
        else:
            status = None
        
        user_service = get_user_service_instance()
        result = user_service.get_users_list(page, page_size, keyword=keyword, status=status)
        
        # 转换服务层响应为标准格式
        if result['success']:
            response, status_code = standardize_response(True, data=result['data'], message='获取用户列表成功')
        else:
            response, status_code = standardize_response(False, error=result.get('error', '获取用户列表失败'), code=400)
        return jsonify(response), status_code
        
    except Exception as e:
        logger.error(f"获取用户列表失败: {str(e)}")
        response, status = standardize_response(False, error=str(e), code=500)
        return jsonify(response), status

@api_bp.route('/users/<int:user_id>', methods=['GET'], endpoint='get_user_by_id')
@auth_required
def get_user(user_id):
    """获取用户信息"""
    user_service = get_user_service_instance()
    result = user_service.get_user_by_id(user_id)
    
    # 转换服务层响应为标准格式
    if result['success']:
        response, status = standardize_response(True, data=result['data'], message='获取用户信息成功')
    else:
        response, status = standardize_response(False, error=result.get('error', '获取用户信息失败'), code=400)
    return jsonify(response), status

@api_bp.route('/users', methods=['POST'], endpoint='create_new_user')
@auth_required
def create_user():
    """创建用户"""
    data = request.get_json()
    user_service = get_user_service_instance()
    result = user_service.create_user(data)
    
    # 转换服务层响应为标准格式
    if result['success']:
        response, status = standardize_response(True, data=result['data'], message='创建用户成功', code=201)
    else:
        response, status = standardize_response(False, error=result.get('error', '创建用户失败'), code=400)
    return jsonify(response), status

@api_bp.route('/users/<int:user_id>', methods=['PUT'], endpoint='update_user_by_id')
@auth_required
def update_user(user_id):
    """更新用户信息"""
    data = request.get_json()
    user_service = get_user_service_instance()
    result = user_service.update_user(user_id, data)
    
    # 转换服务层响应为标准格式
    if result['success']:
        response, status = standardize_response(True, data=result['data'], message='更新用户成功')
    else:
        response, status = standardize_response(False, error=result.get('error', '更新用户失败'), code=400)
    return jsonify(response), status

@api_bp.route('/users/<int:user_id>', methods=['DELETE'], endpoint='delete_user_by_id')
@auth_required
def delete_user(user_id):
    """删除用户"""
    user_service = get_user_service_instance()
    result = user_service.delete_user(user_id)
    return jsonify(result), 200 if result['success'] else 400

@api_bp.route('/users/<int:user_id>/roles', methods=['GET'], endpoint='get_user_roles_by_id')
@auth_required
def get_user_roles(user_id):
    """获取用户角色"""
    user_service = get_user_service_instance()
    roles = user_service.get_user_roles(user_id)
    return jsonify({'success': True, 'data': roles}), 200

@api_bp.route('/users/<int:user_id>/roles', methods=['POST'], endpoint='set_user_roles_by_id')
@auth_required
def set_user_roles(user_id):
    """设置用户角色"""
    data = request.get_json()
    role_ids = data.get('role_ids', [])
    user_service = get_user_service_instance()
    success = user_service.set_user_roles(user_id, role_ids)
    return jsonify({'success': success}), 200 if success else 400

@api_bp.route('/users/<int:user_id>/permissions', methods=['GET'], endpoint='get_user_permissions_by_id')
@auth_required
def get_user_permissions(user_id):
    """获取用户权限"""
    user_service = get_user_service_instance()
    permissions = user_service.get_user_permissions(user_id)
    return jsonify({'success': True, 'data': permissions}), 200

# ==================== 角色管理接口 ====================

@api_bp.route('/roles', methods=['GET'], endpoint='list_roles')
@auth_required
def get_roles():
    """获取角色列表"""
    try:
        # 支持ng-alain表格组件的参数格式：pi, ps
        page = request.args.get('pi', request.args.get('page', 1), type=int)
        page_size = request.args.get('ps', request.args.get('page_size', 10), type=int)
        keyword = request.args.get('keyword', '')
        
        # 处理undefined字符串值
        status_str = request.args.get('status')
        if status_str and status_str != 'undefined':
            status = int(status_str)
        else:
            status = None
            
        role_level_str = request.args.get('role_level')
        if role_level_str and role_level_str != 'undefined':
            role_level = int(role_level_str)
        else:
            role_level = None
            

        
        role_service = get_role_service()
        result = role_service.get_roles_list(
            page=page, 
            page_size=page_size, 
            keyword=keyword, 
            status=status, 
            role_level=role_level, 

        )
        
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
        # 支持ng-alain表格组件的参数格式：pi, ps
        page = request.args.get('pi', request.args.get('page', 1), type=int)
        page_size = request.args.get('ps', request.args.get('page_size', 10), type=int)
        keyword = request.args.get('keyword', '')
        
        # 处理undefined字符串值
        status_str = request.args.get('status')
        if status_str and status_str != 'undefined':
            status = int(status_str)
        else:
            status = None
        
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
    """获取图表数据 - Dashboard页面使用"""
    # 为Dashboard组件提供所需的数据格式
    data = {
        # 网站访问数据 - 用于mini-bar图表
        "visitData": [
            {"x": "2024-01", "y": 123},
            {"x": "2024-02", "y": 234},
            {"x": "2024-03", "y": 345},
            {"x": "2024-04", "y": 456},
            {"x": "2024-05", "y": 567},
            {"x": "2024-06", "y": 678},
            {"x": "2024-07", "y": 789},
            {"x": "2024-08", "y": 890},
            {"x": "2024-09", "y": 901},
            {"x": "2024-10", "y": 823}
        ],
        
        # 销售数据 - 用于bar图表
        "salesData": [
            {"x": "1月", "y": 2800},
            {"x": "2月", "y": 3200},
            {"x": "3月", "y": 3600},
            {"x": "4月", "y": 3800},
            {"x": "5月", "y": 4200},
            {"x": "6月", "y": 4600},
            {"x": "7月", "y": 5000},
            {"x": "8月", "y": 5200},
            {"x": "9月", "y": 4800},
            {"x": "10月", "y": 5400},
            {"x": "11月", "y": 5800},
            {"x": "12月", "y": 6200}
        ],
        
        # 离线数据 - 用于timeline图表
        "offlineChartData": [
            {"x": 1577836800000, "y1": 7, "y2": 9},
            {"x": 1577923200000, "y1": 8, "y2": 12},
            {"x": 1578009600000, "y1": 12, "y2": 15},
            {"x": 1578096000000, "y1": 15, "y2": 18},
            {"x": 1578182400000, "y1": 18, "y2": 21},
            {"x": 1578268800000, "y1": 21, "y2": 24},
            {"x": 1578355200000, "y1": 24, "y2": 27},
            {"x": 1578441600000, "y1": 27, "y2": 30},
            {"x": 1578528000000, "y1": 30, "y2": 33},
            {"x": 1578614400000, "y1": 33, "y2": 36},
            {"x": 1578700800000, "y1": 36, "y2": 39},
            {"x": 1578787200000, "y1": 39, "y2": 42},
            {"x": 1578873600000, "y1": 42, "y2": 45},
            {"x": 1578960000000, "y1": 45, "y2": 48}
        ],
        
        # 保留原雷达图数据（备用）
        "radarData": [
            {"name": "个人", "label": "引用", "value": 10},
            {"name": "个人", "label": "口碑", "value": 8},
            {"name": "个人", "label": "产量", "value": 4},
            {"name": "个人", "label": "贡献", "value": 5},
            {"name": "个人", "label": "热度", "value": 7},
            {"name": "团队", "label": "引用", "value": 3},
            {"name": "团队", "label": "口碑", "value": 9},
            {"name": "团队", "label": "产量", "value": 6},
            {"name": "团队", "label": "贡献", "value": 3},
            {"name": "团队", "label": "热度", "value": 1},
            {"name": "部门", "label": "引用", "value": 4},
            {"name": "部门", "label": "口碑", "value": 3},
            {"name": "部门", "label": "产量", "value": 8},
            {"name": "部门", "label": "贡献", "value": 7},
            {"name": "部门", "label": "热度", "value": 2}
        ]
    }
    
    # 返回标准格式：{code: 200, data: ...}
    return jsonify({
        "code": 200,
        "message": "获取图表数据成功",
        "data": data
    })

@api_bp.route('/user/info', methods=['GET'])
@auth_required
def get_user_info():
    """获取当前登录用户信息"""
    try:
        current_user = g.current_user
        if not current_user:
            response, status = standardize_response(False, error='用户未登录', code=401)
            return jsonify(response), status

        # 获取用户菜单
        menu_result = get_menu_service_instance().get_user_menus(current_user['id'])
        
        if not menu_result['success']:
            response, status = standardize_response(False, error=menu_result['error'], code=500)
            return jsonify(response), status

        # 获取用户权限
        permissions_result = get_user_service_instance().get_user_permissions(current_user['id'])
        
        if not permissions_result['success']:
            response, status = standardize_response(False, error=permissions_result.get('error', '获取权限失败'), code=500)
            return jsonify(response), status

        # 构建用户信息响应数据
        user_data = {
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
            'menus': menu_result['data'],
            'permissions': permissions_result['data']
        }
        
        response, status = standardize_response(True, data=user_data, message='获取用户信息成功')
        return jsonify(response), status
        
    except Exception as e:
        response, status = standardize_response(False, error=f'获取用户信息失败: {str(e)}', code=500)
        return jsonify(response), status

@api_bp.route('/app/init', methods=['GET'])
def app_init():
    """
    系统初始化接口
    返回应用信息，如果有token则返回用户信息、菜单和权限
    """
    try:
        # 默认响应数据
        response_data = {
            'app': {
                'name': '洞察魔方',
                'description': '数据分析问答系统'
            },
            'user': {
                'id': 1,
                'name': 'admin',
                'avatar': './assets/tmp/img/avatar.jpg',
                'email': 'admin@dataask.com',
                'orgCode': 'ORG001',
                'roleCode': 'ADMIN'
            },
            'menus': [],
            'permissions': []
        }
        
        # 获取用户菜单数据
        try:
            # 使用超级管理员用户ID=1获取菜单
            menu_service = get_menu_service_instance()
            menu_result = menu_service.get_user_menus(1)
            
            if menu_result and menu_result['success']:
                # 将数据库菜单转换为前端格式
                response_data['menus'] = convert_menus_to_frontend_format(menu_result['data'])

            else:
                current_app.logger.warning(f"Failed to load menus: {menu_result.get('error', 'Unknown error')}")
                # 如果菜单服务失败，使用基本的默认菜单
                response_data['menus'] = get_default_menus()
        except Exception as menu_error:
            current_app.logger.error(f"Menu service error: {str(menu_error)}")
            response_data['menus'] = get_default_menus()
        
        # 尝试获取当前用户（如果有token的话）
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            try:
                token = auth_header.split(' ')[1]
                user_service = get_user_service_instance()
                user_result = user_service.verify_token(token)
                
                if user_result and user_result['success']:
                    current_user = user_result['data']
                    
                    # 获取该用户的菜单
                    user_menu_result = menu_service.get_user_menus(current_user['id'])
                    if user_menu_result and user_menu_result['success']:
                        response_data['menus'] = convert_menus_to_frontend_format(user_menu_result['data'])
                    
                    # 获取用户权限
                    permissions_result = user_service.get_user_permissions(current_user['id'])
                    
                    # 更新响应数据
                    response_data.update({
                        'user': {
                            'id': current_user['id'],
                            'name': current_user.get('username', current_user.get('name', 'admin')),
                            'avatar': current_user.get('avatar', './assets/tmp/img/avatar.jpg'),
                            'email': current_user.get('email', ''),
                            'orgCode': current_user['org_code'],
                            'roleCode': current_user['role_code']
                        },
                        'permissions': permissions_result['data'] if permissions_result['success'] else []
                    })
            except Exception as token_error:
                # Token验证失败，使用默认数据
                pass
        
        return jsonify({
            'code': 200,
            'data': response_data,
            'message': '获取成功'
        })
        
    except Exception as e:
        current_app.logger.error(f"Error in app_init: {str(e)}")
        return jsonify({
            'code': 500,
            'message': '系统初始化失败',
            'data': None
        }), 500

def convert_menus_to_frontend_format(menus):
    """将数据库菜单格式转换为前端需要的格式"""
    def convert_menu_item(menu, parent_path=''):
        # 基本菜单项
        item = {
            'text': menu['name'],
            'icon': {'type': 'icon', 'value': menu['icon']}
        }
        
        # 构建完整路径
        if menu['type'] == 'C' and menu['path']:
            # 如果是子菜单，需要拼接父路径
            if parent_path and not menu['path'].startswith('/'):
                full_path = f"{parent_path}/{menu['path']}"
            else:
                full_path = menu['path']
            item['link'] = full_path
        
        # 如果有子菜单，递归处理
        if 'children' in menu and menu['children']:
            # 为子菜单传递当前菜单的路径作为父路径
            current_path = menu['path'] if menu['path'] else ''
            item['children'] = [convert_menu_item(child, current_path) for child in menu['children']]
        
        return item
    
    return [convert_menu_item(menu) for menu in menus]

def get_default_menus():
    """获取默认菜单（当菜单服务失败时使用）"""
    return [
        {
            'text': '百惟数问',
            'icon': {'type': 'icon', 'value': 'home'},
            'children': [
                {
                    'text': '监控台',
                    'icon': {'type': 'icon', 'value': 'dashboard'},
                    'children': [
                        {
                            'text': 'AI监控大屏',
                            'icon': {'type': 'icon', 'value': 'bar-chart'},
                            'link': '/dashboard'
                        }
                    ]
                },
                {
                    'text': '工作台',
                    'icon': {'type': 'icon', 'value': 'appstore'},
                    'children': [
                        {
                            'text': '工作区',
                            'icon': {'type': 'icon', 'value': 'laptop'},
                            'link': '/workspace/workplace'
                        },
                        {
                            'text': '工作报表',
                            'icon': {'type': 'icon', 'value': 'bar-chart'},
                            'link': '/workspace/report'
                        }
                    ]
                }
            ]
        },
        {
            'text': 'AI引擎',
            'icon': {'type': 'icon', 'value': 'robot'},
            'children': [
                {
                    'text': 'AI问答',
                    'icon': {'type': 'icon', 'value': 'message'},
                    'link': '/ai-engine/ask-data'
                },
                {
                    'text': '知识库',
                    'icon': {'type': 'icon', 'value': 'database'},
                    'link': '/ai-engine/knowledge-base'
                }
            ]
        },
        {
            'text': '系统管理',
            'icon': {'type': 'icon', 'value': 'setting'},
            'children': [
                {
                    'text': '用户管理',
                    'icon': {'type': 'icon', 'value': 'user'},
                    'link': '/sys/user'
                },
                {
                    'text': '角色管理',
                    'icon': {'type': 'icon', 'value': 'team'},
                    'link': '/sys/role'
                },
                {
                    'text': '权限管理',
                    'icon': {'type': 'icon', 'value': 'safety'},
                    'link': '/sys/permission'
                },
                {
                    'text': '机构管理',
                    'icon': {'type': 'icon', 'value': 'cluster'},
                    'link': '/sys/org'
                }
            ]
        }
    ] 