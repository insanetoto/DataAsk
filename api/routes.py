# -*- coding: utf-8 -*-
"""
API路由模块
提供智能问答相关的API接口
"""
import logging
from typing import Dict, Any
from flask import Blueprint, request, jsonify
from AIEngine.vanna_service import get_vanna_service
from tools.database import get_database_service
from tools.redis_service import get_redis_service
from service.organization_service import get_organization_service
from service.user_service import get_user_service
from service.role_service import get_role_service
from service.permission_service import get_permission_service

# License授权检查
from tools.license_middleware import require_license
# 权限验证中间件
from tools.auth_middleware import (
    token_required, permission_required, admin_required, super_admin_required,
    org_filter_required, generate_token, get_current_user, get_org_filter
)

logger = logging.getLogger(__name__)

# 创建蓝图
api_bp = Blueprint('api', __name__, url_prefix='/api')

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
    """用户登录接口"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': '缺少请求数据'
            }), 400
        
        # 验证必要字段
        required_fields = ['user_code', 'password']
        for field in required_fields:
            if field not in data or not str(data[field]).strip():
                return jsonify({
                    'success': False,
                    'error': f'缺少必要字段: {field}'
                }), 400
        
        user_service = get_user_service()
        
        # 用户认证
        auth_result = user_service.authenticate_user(
            data['user_code'].strip(), 
            data['password']
        )
        
        if not auth_result['success']:
            return jsonify(auth_result), 401
        
        # 生成JWT令牌
        token = generate_token(auth_result['data'])
        
        return jsonify({
            'success': True,
            'message': '登录成功',
            'data': {
                'user': auth_result['data'],
                'token': token
            }
        }), 200
        
    except Exception as e:
        logger.error(f"用户登录失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'登录失败: {str(e)}'
        }), 500

# 为前端兼容添加的简化登录接口
@api_bp.route('/login/account', methods=['POST'])
def frontend_login():
    """前端兼容的登录接口"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'msg': '缺少请求数据'
            }), 400
        
        # 支持前端发送的字段名
        user_code = data.get('userName') or data.get('user_code', '').strip()
        password = data.get('password', '').strip()
        
        if not user_code or not password:
            return jsonify({
                'msg': '用户名和密码不能为空'
            }), 400
        
        user_service = get_user_service()
        
        # 用户认证
        auth_result = user_service.authenticate_user(user_code, password)
        
        if not auth_result['success']:
            return jsonify({
                'msg': auth_result['error']
            }), 200  # 前端期望200状态码
        
        # 生成JWT令牌
        token = generate_token(auth_result['data'])
        
        # 返回前端期望的格式
        user_data = auth_result['data']
        response_data = {
            'msg': 'ok',
            'user': {
                'token': token,
                'name': user_data['username'],
                'avatar': './assets/tmp/img.jpg',
                'email': user_data['user_code'],
                'id': user_data['id'],
                'user': user_data
            }
        }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"前端登录失败: {str(e)}")
        return jsonify({
            'msg': f'登录失败: {str(e)}'
        }), 200

@api_bp.route('/auth/profile', methods=['GET'])
@token_required
def get_profile():
    """获取当前用户信息"""
    try:
        current_user = get_current_user()
        
        return jsonify({
            'success': True,
            'data': current_user
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

@api_bp.route('/users', methods=['POST'])
@token_required
@admin_required
def create_user():
    """创建用户接口"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': '缺少请求数据'
            }), 400
        
        user_service = get_user_service()
        result = user_service.create_user(data)
        
        status_code = 201 if result['success'] else 400
        return jsonify(result), status_code
        
    except Exception as e:
        logger.error(f"创建用户失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'创建用户失败: {str(e)}'
        }), 500

@api_bp.route('/users/<int:user_id>', methods=['GET'])
@token_required
@org_filter_required()
def get_user(user_id):
    """获取用户信息接口"""
    try:
        user_service = get_user_service()
        result = user_service.get_user_by_id(user_id)
        
        if not result['success']:
            return jsonify(result), 404 if '不存在' in result.get('error', '') else 500
        
        # 检查机构权限
        current_user = get_current_user()
        user_data = result['data']
        
        # 非超级管理员只能查看同机构用户
        if current_user['role_level'] != 1 and current_user['org_code'] != user_data['org_code']:
            return jsonify({
                'success': False,
                'error': '无权访问其他机构的用户信息'
            }), 403
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"获取用户信息失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'获取用户信息失败: {str(e)}'
        }), 500

@api_bp.route('/users', methods=['GET'])
@token_required
@org_filter_required()
def get_users_list():
    """获取用户列表接口"""
    try:
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 10, type=int)
        status = request.args.get('status', type=int)
        org_code = request.args.get('org_code')
        role_level = request.args.get('role_level', type=int)
        keyword = request.args.get('keyword')
        
        # 应用机构过滤
        current_user = get_current_user()
        org_filter = get_org_filter()
        
        # 如果不是超级管理员，强制过滤为当前用户机构
        current_user_org = None
        if org_filter['type'] == 'org':
            current_user_org = current_user['org_code']
            # 如果指定了机构编码，确保只能查询自己机构的数据
            if org_code and org_code != current_user['org_code']:
                return jsonify({
                    'success': False,
                    'error': '无权查询其他机构的用户数据'
                }), 403
        
        user_service = get_user_service()
        result = user_service.get_users_list(
            page=page,
            page_size=page_size,
            status=status,
            org_code=org_code,
            role_level=role_level,
            keyword=keyword,
            current_user_org=current_user_org
        )
        
        return jsonify(result), 200 if result['success'] else 500
        
    except Exception as e:
        logger.error(f"获取用户列表失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'获取用户列表失败: {str(e)}'
        }), 500

# ==================== 角色管理接口 ====================

@api_bp.route('/roles', methods=['POST'])
@token_required
@super_admin_required
def create_role():
    """创建角色接口"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': '缺少请求数据'
            }), 400
        
        role_service = get_role_service()
        result = role_service.create_role(data)
        
        status_code = 201 if result['success'] else 400
        return jsonify(result), status_code
        
    except Exception as e:
        logger.error(f"创建角色失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'创建角色失败: {str(e)}'
        }), 500

@api_bp.route('/roles/<int:role_id>', methods=['GET'])
@token_required
def get_role(role_id):
    """获取角色信息接口"""
    try:
        role_service = get_role_service()
        result = role_service.get_role_by_id(role_id)
        
        status_code = 200 if result['success'] else 404
        return jsonify(result), status_code
        
    except Exception as e:
        logger.error(f"获取角色信息失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'获取角色信息失败: {str(e)}'
        }), 500

@api_bp.route('/roles', methods=['GET'])
@token_required
def get_roles_list():
    """获取角色列表接口"""
    try:
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 10, type=int)
        status = request.args.get('status', type=int)
        role_level = request.args.get('role_level', type=int)
        keyword = request.args.get('keyword')
        
        role_service = get_role_service()
        result = role_service.get_roles_list(
            page=page,
            page_size=page_size,
            status=status,
            role_level=role_level,
            keyword=keyword
        )
        
        return jsonify(result), 200 if result['success'] else 500
        
    except Exception as e:
        logger.error(f"获取角色列表失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'获取角色列表失败: {str(e)}'
        }), 500

@api_bp.route('/roles/<int:role_id>/permissions', methods=['GET'])
@token_required
def get_role_permissions(role_id):
    """获取角色权限列表"""
    try:
        permission_service = get_permission_service()
        result = permission_service.get_role_permissions(role_id)
        
        return jsonify(result), 200 if result['success'] else 500
        
    except Exception as e:
        logger.error(f"获取角色权限失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'获取角色权限失败: {str(e)}'
        }), 500

@api_bp.route('/permissions', methods=['GET'])
@token_required
def get_permissions_list():
    """获取权限列表接口"""
    try:
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 10, type=int)
        category = request.args.get('category')
        keyword = request.args.get('keyword')
        
        permission_service = get_permission_service()
        result = permission_service.get_permissions_list(
            page=page,
            page_size=page_size,
            category=category,
            keyword=keyword
        )
        
        return jsonify(result), 200 if result['success'] else 500
        
    except Exception as e:
        logger.error(f"获取权限列表失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'获取权限列表失败: {str(e)}'
        }), 500

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