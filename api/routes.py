# -*- coding: utf-8 -*-
"""
API路由模块
提供智能问答相关的API接口
"""
import logging
import time
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

from service.workflow_service import WorkflowService

logger = logging.getLogger(__name__)

# 创建蓝图
api_bp = Blueprint('api', __name__, url_prefix='/api')

# 初始化工作流服务
workflow_service = WorkflowService()

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

def can_manage_user(current_user: Dict[str, Any], target_user_id: int) -> bool:
    """
    检查当前用户是否可以管理目标用户
    
    Args:
        current_user: 当前用户信息
        target_user_id: 目标用户ID
    
    Returns:
        bool: 是否有权限管理
    """
    if not current_user:
        return False
    
    role_code = current_user.get('role_code', '')
    
    # 超级管理员可以管理所有用户
    if role_code == 'SUPER_ADMIN':
        return True
    
    # 机构管理员只能管理同机构用户
    if role_code == 'ORG_ADMIN':
        try:
            user_service = get_user_service_instance()
            # 使用不检查状态的方法获取用户信息，因为权限检查不应该被用户状态阻止
            target_user_result = user_service._get_user_by_id_without_status_check(target_user_id)
            
            if not target_user_result['success']:
                return False
            
            target_user = target_user_result['data']
            current_org_code = current_user.get('org_code', '')
            target_org_code = target_user.get('org_code', '')
            
            return current_org_code == target_org_code
        except Exception as e:
            logger.error(f"检查用户管理权限失败: {str(e)}")
            return False
    
    return False

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
    """创建组织机构"""
    try:
        current_user = g.current_user
        if not current_user:
            return jsonify({
                'code': 401,
                'message': '未认证用户'
            }), 401
        
        data = request.get_json()
        if not data:
            response, status = standardize_response(False, error='缺少请求数据', code=400)
            return jsonify(response), status
        
        # 验证必要字段
        required_fields = ['org_code', 'org_name', 'parent_code']
        for field in required_fields:
            if field not in data or not str(data[field]).strip():
                response, status = standardize_response(False, error=f'缺少必要字段: {field}', code=400)
                return jsonify(response), status
        
        org_service = get_organization_service()
        result = org_service.create_organization(data)
        
        if result['success']:
            # 记录审计日志
            from service.audit_service import audit_operation
            audit_operation(
                module='org',
                operation='create',
                target_type='organization',
                target_id=data['org_code'],
                target_name=data['org_name'],
                old_data=None,
                new_data=result.get('data'),
                operation_desc=f"创建机构: {data['org_name']}"
            )
            
            response, status = standardize_response(True, data=result['data'], message='机构创建成功')
        else:
            response, status = standardize_response(False, error=result['error'], code=400)
        return jsonify(response), status
        
    except Exception as e:
        logger.error(f"创建机构失败: {str(e)}")
        response, status = standardize_response(False, error=str(e), code=500)
        return jsonify(response), status

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
    """更新机构信息"""
    try:
        current_user = g.current_user
        if not current_user:
            return jsonify({
                'code': 401,
                'message': '未认证用户'
            }), 401
        
        data = request.get_json()
        if not data:
            response, status = standardize_response(False, error='缺少请求数据', code=400)
            return jsonify(response), status
        
        org_service = get_organization_service()
        
        # 获取原始数据用于审计
        old_org_result = org_service.get_organization_by_id(org_id)
        old_org_data = old_org_result.get('data') if old_org_result.get('success') else None
        
        result = org_service.update_organization(org_id, data)
        
        if result['success']:
            # 获取更新后的数据
            new_org_result = org_service.get_organization_by_id(org_id)
            new_org_data = new_org_result.get('data') if new_org_result.get('success') else None
            
            # 记录审计日志
            from service.audit_service import audit_operation
            audit_operation(
                module='org',
                operation='update',
                target_type='organization',
                target_id=str(org_id),
                target_name=old_org_data.get('org_name', '') if old_org_data else '',
                old_data=old_org_data,
                new_data=new_org_data,
                operation_desc=f"更新机构: {old_org_data.get('org_name', '') if old_org_data else ''}"
            )
            
            response, status = standardize_response(True, data=result['data'], message='机构更新成功')
        else:
            response, status = standardize_response(False, error=result['error'], code=400)
        return jsonify(response), status
        
    except Exception as e:
        logger.error(f"更新机构失败: {str(e)}")
        response, status = standardize_response(False, error=str(e), code=500)
        return jsonify(response), status

@api_bp.route('/organizations/<int:org_id>', methods=['DELETE'])
def delete_organization(org_id):
    """删除机构"""
    try:
        current_user = g.current_user
        if not current_user:
            return jsonify({
                'code': 401,
                'message': '未认证用户'
            }), 401
        
        org_service = get_organization_service()
        
        # 获取原始数据用于审计
        old_org_result = org_service.get_organization_by_id(org_id)
        old_org_data = old_org_result.get('data') if old_org_result.get('success') else None
        
        result = org_service.delete_organization(org_id)
        
        if result['success']:
            # 记录审计日志
            from service.audit_service import audit_operation
            audit_operation(
                module='org',
                operation='delete',
                target_type='organization',
                target_id=str(org_id),
                target_name=old_org_data.get('org_name', '') if old_org_data else '',
                old_data=old_org_data,
                new_data=None,
                operation_desc=f"删除机构: {old_org_data.get('org_name', '') if old_org_data else ''}"
            )
            
            response, status = standardize_response(True, message='机构删除成功')
        else:
            response, status = standardize_response(False, error=result['error'], code=400)
        return jsonify(response), status
        
    except Exception as e:
        logger.error(f"删除机构失败: {str(e)}")
        response, status = standardize_response(False, error=str(e), code=500)
        return jsonify(response), status

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
    new_tokens = token_service.refresh_access_token(refresh_token)
    
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
        org_code = request.args.get('org_code', '')
        
        # 处理undefined字符串值
        status_str = request.args.get('status')
        if status_str and status_str != 'undefined':
            status = int(status_str)
        else:
            status = None
        
        # 权限控制：根据当前用户角色决定可见的用户范围
        current_user = get_current_user()
        current_user_org = None
        
        if current_user:
            role_code = current_user.get('role_code', '')
            
            # 如果是机构管理员，只能查看本机构用户
            if role_code == 'ORG_ADMIN':
                current_user_org = current_user.get('org_code', '')
                # 强制设置org_code过滤条件为当前用户的机构
                if current_user_org:
                    org_code = current_user_org
            # 超级管理员可以查看所有用户，不需要额外限制
        
        user_service = get_user_service_instance()
        result = user_service.get_users_list(
            page=page, 
            page_size=page_size, 
            keyword=keyword, 
            status=status,
            org_code=org_code,
            current_user_org=current_user_org
        )
        
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
    try:
        # 权限控制：检查是否可以查看该用户
        current_user = get_current_user()
        if not can_manage_user(current_user, user_id):
            response, status = standardize_response(False, error='权限不足：无法查看该用户信息', code=403)
            return jsonify(response), status
        
        user_service = get_user_service_instance()
        result = user_service.get_user_by_id(user_id)
        
        # 转换服务层响应为标准格式
        if result['success']:
            response, status = standardize_response(True, data=result['data'], message='获取用户信息成功')
        else:
            response, status = standardize_response(False, error=result.get('error', '获取用户信息失败'), code=400)
        return jsonify(response), status
        
    except Exception as e:
        logger.error(f"获取用户信息失败: {str(e)}")
        response, status = standardize_response(False, error=str(e), code=500)
        return jsonify(response), status

@api_bp.route('/users', methods=['POST'], endpoint='create_new_user')
@auth_required
def create_user():
    """创建用户"""
    try:
        data = request.get_json()
        current_user = get_current_user()
        
        # 获取当前操作员的机构编码
        current_user_org = None
        if current_user:
            current_user_org = current_user.get('org_code')
        
        # 权限控制：机构管理员只能在自己的机构下创建用户
        role_code = current_user.get('role_code') if current_user else None
        if role_code == 'ORG_ADMIN' and current_user_org:
            # 强制设置新用户的机构编码为当前用户的机构编码
            data['org_code'] = current_user_org
        
        user_service = get_user_service_instance()
        result = user_service.create_user(data, current_user_org)
        
        # 转换服务层响应为标准格式
        if result['success']:
            response, status = standardize_response(True, data=result['data'], message='创建用户成功', code=201)
        else:
            response, status = standardize_response(False, error=result.get('error', '创建用户失败'), code=400)
        return jsonify(response), status
    
    except Exception as e:
        logger.error(f"创建用户API失败: {str(e)}")
        response, status = standardize_response(False, error=f'创建用户失败: {str(e)}', code=500)
        return jsonify(response), status

@api_bp.route('/users/<int:user_id>', methods=['PUT'], endpoint='update_user_by_id')
@auth_required
def update_user(user_id):
    """更新用户信息"""
    try:
        # 权限控制：检查是否可以编辑该用户
        current_user = get_current_user()
        if not can_manage_user(current_user, user_id):
            response, status = standardize_response(False, error='权限不足：无法编辑该用户信息', code=403)
            return jsonify(response), status
        
        data = request.get_json()
        user_service = get_user_service_instance()
        result = user_service.update_user(user_id, data)
        
        # 转换服务层响应为标准格式
        if result['success']:
            response, status = standardize_response(True, message=result.get('message', '更新用户成功'))
        else:
            response, status = standardize_response(False, error=result.get('error', '更新用户失败'), code=400)
        return jsonify(response), status
        
    except Exception as e:
        logger.error(f"更新用户信息失败: {str(e)}")
        response, status = standardize_response(False, error=str(e), code=500)
        return jsonify(response), status

@api_bp.route('/users/<int:user_id>', methods=['DELETE'], endpoint='delete_user_by_id')
@auth_required
def delete_user(user_id):
    """删除用户"""
    try:
        # 权限控制：检查是否可以删除该用户
        current_user = get_current_user()
        
        # 不能删除自己
        if current_user and current_user.get('id') == user_id:
            response, status = standardize_response(False, error='不能删除自己的账户', code=400)
            return jsonify(response), status
        
        if not can_manage_user(current_user, user_id):
            response, status = standardize_response(False, error='权限不足：无法删除该用户', code=403)
            return jsonify(response), status
        
        user_service = get_user_service_instance()
        result = user_service.delete_user(user_id)
        
        # 转换服务层响应为标准格式
        if result['success']:
            response, status = standardize_response(True, message=result.get('message', '删除用户成功'))
        else:
            response, status = standardize_response(False, error=result.get('error', '删除用户失败'), code=400)
        return jsonify(response), status
        
    except Exception as e:
        logger.error(f"删除用户失败: {str(e)}")
        response, status = standardize_response(False, error=str(e), code=500)
        return jsonify(response), status

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

@api_bp.route('/users/<int:user_id>/password', methods=['PUT'], endpoint='reset_user_password_by_id')
@auth_required
def reset_user_password(user_id):
    """重置用户密码"""
    try:
        data = request.get_json()
        new_password = data.get('password')
        
        if not new_password:
            return jsonify({
                'success': False,
                'error': '新密码不能为空'
            }), 400
            
        # 获取当前操作用户信息
        operator_user = request.user
        
        user_service = get_user_service_instance()
        result = user_service.reset_user_password(user_id, new_password, operator_user)
        
        if result['success']:
            response, status = standardize_response(True, message=result['message'])
        else:
            response, status = standardize_response(False, error=result['error'], code=403 if '权限不足' in result['error'] else 400)
        
        return jsonify(response), status
        
    except Exception as e:
        logger.error(f"重置用户密码API失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'重置密码失败: {str(e)}'
        }), 500

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
    try:
        current_user = g.current_user
        data = request.get_json()
        
        role_service = get_role_service()
        result = role_service.create_role(data)
        
        if result['success']:
            # 记录审计日志
            from service.audit_service import audit_operation
            audit_operation(
                module='role',
                operation='create',
                target_type='role',
                target_id=str(result.get('data', {}).get('id', '')),
                target_name=data.get('role_name', ''),
                old_data=None,
                new_data=result.get('data'),
                operation_desc=f"创建角色: {data.get('role_name', '')}"
            )
            
        response, status = standardize_response(result['success'], data=result.get('data'), error=result.get('error'))
        return jsonify(response), status
        
    except Exception as e:
        logger.error(f"创建角色失败: {str(e)}")
        response, status = standardize_response(False, error=str(e), code=500)
        return jsonify(response), status

@api_bp.route('/roles/<int:role_id>', methods=['PUT'], endpoint='update_role_by_id')
@auth_required
def update_role(role_id):
    """更新角色"""
    try:
        current_user = g.current_user
        data = request.get_json()
        
        role_service = get_role_service()
        
        # 获取原始数据用于审计
        old_role_result = role_service.get_role_by_id(role_id)
        old_role_data = old_role_result.get('data') if old_role_result.get('success') else None
        
        result = role_service.update_role(role_id, data)
        
        if result['success']:
            # 获取更新后的数据
            new_role_result = role_service.get_role_by_id(role_id)
            new_role_data = new_role_result.get('data') if new_role_result.get('success') else None
            
            # 记录审计日志
            from service.audit_service import audit_operation
            audit_operation(
                module='role',
                operation='update',
                target_type='role',
                target_id=str(role_id),
                target_name=old_role_data.get('role_name', '') if old_role_data else '',
                old_data=old_role_data,
                new_data=new_role_data,
                operation_desc=f"更新角色: {old_role_data.get('role_name', '') if old_role_data else ''}"
            )
            
        response, status = standardize_response(result['success'], data=result.get('data'), error=result.get('error'))
        return jsonify(response), status
        
    except Exception as e:
        logger.error(f"更新角色失败: {str(e)}")
        response, status = standardize_response(False, error=str(e), code=500)
        return jsonify(response), status

@api_bp.route('/roles/<int:role_id>', methods=['DELETE'], endpoint='delete_role_by_id')
@auth_required
def delete_role(role_id):
    """删除角色"""
    try:
        current_user = g.current_user
        
        role_service = get_role_service()
        
        # 获取原始数据用于审计
        old_role_result = role_service.get_role_by_id(role_id)
        old_role_data = old_role_result.get('data') if old_role_result.get('success') else None
        
        result = role_service.delete_role(role_id)
        
        if result['success']:
            # 记录审计日志
            from service.audit_service import audit_operation
            audit_operation(
                module='role',
                operation='delete',
                target_type='role',
                target_id=str(role_id),
                target_name=old_role_data.get('role_name', '') if old_role_data else '',
                old_data=old_role_data,
                new_data=None,
                operation_desc=f"删除角色: {old_role_data.get('role_name', '') if old_role_data else ''}"
            )
            
        response, status = standardize_response(result['success'], data=result.get('data'), error=result.get('error'))
        return jsonify(response), status
        
    except Exception as e:
        logger.error(f"删除角色失败: {str(e)}")
        response, status = standardize_response(False, error=str(e), code=500)
        return jsonify(response), status

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
            'text': '洞察魔方',
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
                            'text': '个人工作台',
                            'icon': {'type': 'icon', 'value': 'laptop'},
                            'link': '/workspace/workbench'
                        },
                        {
                            'text': '工作报表',
                            'icon': {'type': 'icon', 'value': 'bar-chart'},
                            'link': '/workspace/report'
                        },
                        {
                            'text': '系统监控',
                            'icon': {'type': 'icon', 'value': 'monitor'},
                            'link': '/workspace/monitor'
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
                        },
                        {
                            'text': '数据源管理',
                            'icon': {'type': 'icon', 'value': 'api'},
                            'link': '/ai-engine/datasource'
                        },
                        {
                            'text': '大模型管理',
                            'icon': {'type': 'icon', 'value': 'deployment-unit'},
                            'link': '/ai-engine/llmmanage'
                        },
                        {
                            'text': '多模态管理',
                            'icon': {'type': 'icon', 'value': 'experiment'},
                            'link': '/ai-engine/multimodal'
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
                        },
                        {
                            'text': '工作流管理',
                            'icon': {'type': 'icon', 'value': 'apartment'},
                            'link': '/sys/workflow'
                        },
                        {
                            'text': '消息管理',
                            'icon': {'type': 'icon', 'value': 'message'},
                            'link': '/sys/message'
                        }
                    ]
                }
            ]
        }
    ]

# ============ 多模态管理接口 ============

@api_bp.route('/multimodal', methods=['GET'])
def get_multimodal_configs():
    """获取多模态配置列表"""
    try:
        # 获取分页参数
        page = int(request.args.get('pi', 1))
        page_size = int(request.args.get('ps', 10))
        search = request.args.get('search', '').strip()
        
        # 模拟多模态配置数据
        all_configs = [
            {
                'id': 1,
                'name': 'GPT-4V 视觉模型',
                'type': 'vision',
                'provider': 'OpenAI',
                'model': 'gpt-4-vision-preview',
                'description': '支持图像理解和分析的多模态模型',
                'status': 'active',
                'config': {
                    'max_tokens': 4096,
                    'temperature': 0.7,
                    'supports_images': True,
                    'image_formats': ['png', 'jpg', 'jpeg', 'gif', 'webp']
                },
                'created_at': '2024-01-15 10:30:00',
                'updated_at': '2024-01-20 14:45:00'
            },
            {
                'id': 2,
                'name': 'Claude-3 Sonnet',
                'type': 'vision',
                'provider': 'Anthropic',
                'model': 'claude-3-sonnet-20240229',
                'description': '强大的视觉理解和文档分析能力',
                'status': 'active',
                'config': {
                    'max_tokens': 4096,
                    'temperature': 0.5,
                    'supports_images': True,
                    'image_formats': ['png', 'jpg', 'jpeg', 'pdf']
                },
                'created_at': '2024-02-01 09:15:00',
                'updated_at': '2024-02-15 16:20:00'
            },
            {
                'id': 3,
                'name': '通义千问VL',
                'type': 'vision',
                'provider': 'Alibaba',
                'model': 'qwen-vl-plus',
                'description': '阿里云通义千问视觉语言模型',
                'status': 'inactive',
                'config': {
                    'max_tokens': 2048,
                    'temperature': 0.8,
                    'supports_images': True,
                    'image_formats': ['png', 'jpg', 'jpeg']
                },
                'created_at': '2024-01-10 11:20:00',
                'updated_at': '2024-01-25 13:30:00'
            },
            {
                'id': 4,
                'name': 'DALL-E 3',
                'type': 'generation',
                'provider': 'OpenAI',
                'model': 'dall-e-3',
                'description': '先进的AI图像生成模型',
                'status': 'active',
                'config': {
                    'sizes': ['1024x1024', '1792x1024', '1024x1792'],
                    'quality': 'hd',
                    'style': 'natural'
                },
                'created_at': '2024-01-05 08:45:00',
                'updated_at': '2024-01-18 10:15:00'
            }
        ]
        
        # 根据搜索条件过滤
        if search:
            all_configs = [
                config for config in all_configs 
                if search.lower() in config['name'].lower() or 
                   search.lower() in config['description'].lower() or
                   search.lower() in config['provider'].lower()
            ]
        
        # 计算分页
        total = len(all_configs)
        start = (page - 1) * page_size
        end = start + page_size
        configs = all_configs[start:end]
        
        response_data = {
            'list': configs,
            'total': total,
            'pi': page,
            'ps': page_size
        }
        
        response, status = standardize_response(True, data=response_data, message='获取多模态配置成功')
        return jsonify(response), status
        
    except Exception as e:
        logger.error(f"获取多模态配置失败: {str(e)}")
        response, status = standardize_response(False, error=str(e), code=500)
        return jsonify(response), status

@api_bp.route('/multimodal/<int:config_id>', methods=['GET'])
def get_multimodal_config(config_id):
    """获取单个多模态配置详情"""
    try:
        # 模拟获取配置详情
        config = {
            'id': config_id,
            'name': f'多模态配置 {config_id}',
            'type': 'vision',
            'provider': 'OpenAI',
            'model': 'gpt-4-vision-preview',
            'description': '示例多模态配置',
            'status': 'active',
            'config': {
                'max_tokens': 4096,
                'temperature': 0.7,
                'supports_images': True
            },
            'created_at': '2024-01-15 10:30:00',
            'updated_at': '2024-01-20 14:45:00'
        }
        
        response, status = standardize_response(True, data=config, message='获取配置详情成功')
        return jsonify(response), status
        
    except Exception as e:
        logger.error(f"获取配置详情失败: {str(e)}")
        response, status = standardize_response(False, error=str(e), code=500)
        return jsonify(response), status

@api_bp.route('/multimodal', methods=['POST'])
def create_multimodal_config():
    """创建多模态配置"""
    try:
        data = request.get_json()
        
        # 验证必要字段
        required_fields = ['name', 'type', 'provider', 'model']
        for field in required_fields:
            if not data.get(field):
                response, status = standardize_response(False, error=f'缺少必要字段: {field}', code=400)
                return jsonify(response), status
        
        # 模拟创建配置
        new_config = {
            'id': 999,  # 模拟生成的ID
            'name': data['name'],
            'type': data['type'],
            'provider': data['provider'],
            'model': data['model'],
            'description': data.get('description', ''),
            'status': data.get('status', 'inactive'),
            'config': data.get('config', {}),
            'created_at': '2024-01-25 16:00:00',
            'updated_at': '2024-01-25 16:00:00'
        }
        
        response, status = standardize_response(True, data=new_config, message='创建配置成功')
        return jsonify(response), status
        
    except Exception as e:
        logger.error(f"创建配置失败: {str(e)}")
        response, status = standardize_response(False, error=str(e), code=500)
        return jsonify(response), status

@api_bp.route('/multimodal/<int:config_id>', methods=['PUT'])
def update_multimodal_config(config_id):
    """更新多模态配置"""
    try:
        data = request.get_json()
        
        # 模拟更新配置
        updated_config = {
            'id': config_id,
            'name': data.get('name', f'更新的配置 {config_id}'),
            'type': data.get('type', 'vision'),
            'provider': data.get('provider', 'OpenAI'),
            'model': data.get('model', 'gpt-4-vision-preview'),
            'description': data.get('description', ''),
            'status': data.get('status', 'active'),
            'config': data.get('config', {}),
            'updated_at': '2024-01-25 16:30:00'
        }
        
        response, status = standardize_response(True, data=updated_config, message='更新配置成功')
        return jsonify(response), status
        
    except Exception as e:
        logger.error(f"更新配置失败: {str(e)}")
        response, status = standardize_response(False, error=str(e), code=500)
        return jsonify(response), status

@api_bp.route('/multimodal/<int:config_id>', methods=['DELETE'])
def delete_multimodal_config(config_id):
    """删除多模态配置"""
    try:
        # 模拟删除操作
        response, status = standardize_response(True, message=f'删除配置 {config_id} 成功')
        return jsonify(response), status
        
    except Exception as e:
        logger.error(f"删除配置失败: {str(e)}")
        response, status = standardize_response(False, error=str(e), code=500)
        return jsonify(response), status

@api_bp.route('/multimodal/<int:config_id>/test', methods=['POST'])
def test_multimodal_config(config_id):
    """测试多模态配置"""
    try:
        data = request.get_json()
        test_data = data.get('test_data', {})
        
        # 模拟测试结果
        test_result = {
            'config_id': config_id,
            'test_status': 'success',
            'response_time': '1.2s',
            'test_message': '模型连接正常，功能测试通过',
            'test_output': {
                'model_response': '测试成功，模型运行正常',
                'latency': 1200,  # ms
                'tokens_used': 150
            }
        }
        
        response, status = standardize_response(True, data=test_result, message='测试完成')
        return jsonify(response), status
        
    except Exception as e:
        logger.error(f"测试配置失败: {str(e)}")
        response, status = standardize_response(False, error=str(e), code=500)
        return jsonify(response), status

# ============ 消息管理接口 ============

@api_bp.route('/message', methods=['GET'])
def get_messages():
    """获取消息列表"""
    try:
        # 获取分页参数
        page = int(request.args.get('pi', 1))
        page_size = int(request.args.get('ps', 10))
        title = request.args.get('title', '').strip()
        msg_type = request.args.get('type', '').strip()
        status = request.args.get('status', '').strip()
        
        # 模拟消息数据
        all_messages = [
            {
                'id': 1,
                'title': '系统维护通知',
                'content': '系统将于今晚23:00-02:00进行维护，期间服务可能暂时不可用。',
                'type': 'system',
                'status': 'sent',
                'recipient': '全体用户',
                'sender': '系统管理员',
                'sent_at': '2024-01-20 10:30:00',
                'created_at': '2024-01-20 10:25:00',
                'read_count': 128,
                'total_recipients': 150
            },
            {
                'id': 2,
                'title': '数据分析报告已生成',
                'content': '您请求的月度数据分析报告已经生成完成，请及时查看。',
                'type': 'business',
                'status': 'sent',
                'recipient': '张三',
                'sender': 'AI引擎',
                'sent_at': '2024-01-20 14:15:00',
                'created_at': '2024-01-20 14:10:00',
                'read_count': 1,
                'total_recipients': 1
            },
            {
                'id': 3,
                'title': '存储空间不足告警',
                'content': '数据库存储空间使用率已达到85%，请及时清理或扩容。',
                'type': 'alert',
                'status': 'sent',
                'recipient': '运维团队',
                'sender': '监控系统',
                'sent_at': '2024-01-20 16:45:00',
                'created_at': '2024-01-20 16:40:00',
                'read_count': 3,
                'total_recipients': 5
            },
            {
                'id': 4,
                'title': '新功能发布通知',
                'content': '多模态AI功能已正式发布，欢迎体验图像分析和生成功能。',
                'type': 'system',
                'status': 'draft',
                'recipient': '全体用户',
                'sender': '产品团队',
                'sent_at': None,
                'created_at': '2024-01-21 09:30:00',
                'read_count': 0,
                'total_recipients': 150
            },
            {
                'id': 5,
                'title': '用户权限变更通知',
                'content': '您的账户权限已更新，新增了报表导出功能的访问权限。',
                'type': 'business',
                'status': 'read',
                'recipient': '李四',
                'sender': '系统管理员',
                'sent_at': '2024-01-19 11:20:00',
                'created_at': '2024-01-19 11:15:00',
                'read_count': 1,
                'total_recipients': 1
            }
        ]
        
        # 根据条件过滤
        filtered_messages = all_messages
        if title:
            filtered_messages = [msg for msg in filtered_messages if title.lower() in msg['title'].lower()]
        if msg_type:
            filtered_messages = [msg for msg in filtered_messages if msg['type'] == msg_type]
        if status:
            filtered_messages = [msg for msg in filtered_messages if msg['status'] == status]
        
        # 计算分页
        total = len(filtered_messages)
        start = (page - 1) * page_size
        end = start + page_size
        messages = filtered_messages[start:end]
        
        response_data = {
            'list': messages,
            'total': total,
            'pi': page,
            'ps': page_size
        }
        
        response, status = standardize_response(True, data=response_data, message='获取消息列表成功')
        return jsonify(response), status
        
    except Exception as e:
        logger.error(f"获取消息列表失败: {str(e)}")
        response, status = standardize_response(False, error=str(e), code=500)
        return jsonify(response), status

@api_bp.route('/message/<int:message_id>', methods=['GET'])
def get_message(message_id):
    """获取单个消息详情"""
    try:
        # 模拟获取消息详情
        message = {
            'id': message_id,
            'title': f'消息标题 {message_id}',
            'content': f'这是消息 {message_id} 的详细内容...',
            'type': 'system',
            'status': 'sent',
            'recipient': '全体用户',
            'sender': '系统管理员',
            'sent_at': '2024-01-20 10:30:00',
            'created_at': '2024-01-20 10:25:00',
            'read_count': 50,
            'total_recipients': 100
        }
        
        response, status = standardize_response(True, data=message, message='获取消息详情成功')
        return jsonify(response), status
        
    except Exception as e:
        logger.error(f"获取消息详情失败: {str(e)}")
        response, status = standardize_response(False, error=str(e), code=500)
        return jsonify(response), status

@api_bp.route('/message', methods=['POST'])
def create_message():
    """创建新消息"""
    try:
        data = request.get_json()
        
        # 验证必要字段
        required_fields = ['title', 'content', 'type', 'recipient']
        for field in required_fields:
            if not data.get(field):
                response, status = standardize_response(False, error=f'缺少必要字段: {field}', code=400)
                return jsonify(response), status
        
        # 模拟创建消息
        new_message = {
            'id': 999,  # 模拟生成的ID
            'title': data['title'],
            'content': data['content'],
            'type': data['type'],
            'status': data.get('status', 'draft'),
            'recipient': data['recipient'],
            'sender': '当前用户',  # 实际应该从认证信息获取
            'sent_at': None if data.get('status', 'draft') == 'draft' else '2024-01-25 16:00:00',
            'created_at': '2024-01-25 16:00:00',
            'read_count': 0,
            'total_recipients': 1
        }
        
        response, status = standardize_response(True, data=new_message, message='创建消息成功')
        return jsonify(response), status
        
    except Exception as e:
        logger.error(f"创建消息失败: {str(e)}")
        response, status = standardize_response(False, error=str(e), code=500)
        return jsonify(response), status

@api_bp.route('/message/<int:message_id>', methods=['PUT'])
def update_message(message_id):
    """更新消息"""
    try:
        data = request.get_json()
        
        # 模拟更新消息
        updated_message = {
            'id': message_id,
            'title': data.get('title', f'更新的消息 {message_id}'),
            'content': data.get('content', '更新的内容'),
            'type': data.get('type', 'system'),
            'status': data.get('status', 'draft'),
            'recipient': data.get('recipient', '全体用户'),
            'sender': '当前用户',
            'updated_at': '2024-01-25 16:30:00'
        }
        
        response, status = standardize_response(True, data=updated_message, message='更新消息成功')
        return jsonify(response), status
        
    except Exception as e:
        logger.error(f"更新消息失败: {str(e)}")
        response, status = standardize_response(False, error=str(e), code=500)
        return jsonify(response), status

@api_bp.route('/message/<int:message_id>', methods=['DELETE'])
def delete_message(message_id):
    """删除消息"""
    try:
        # 模拟删除操作
        response, status = standardize_response(True, message=f'删除消息 {message_id} 成功')
        return jsonify(response), status
        
    except Exception as e:
        logger.error(f"删除消息失败: {str(e)}")
        response, status = standardize_response(False, error=str(e), code=500)
        return jsonify(response), status

@api_bp.route('/message/<int:message_id>/send', methods=['POST'])
def send_message(message_id):
    """发送消息"""
    try:
        # 模拟发送操作
        result = {
            'message_id': message_id,
            'send_status': 'success',
            'sent_at': '2024-01-25 16:45:00',
            'recipients_count': 150,
            'success_count': 148,
            'failed_count': 2
        }
        
        response, status = standardize_response(True, data=result, message='消息发送成功')
        return jsonify(response), status
        
    except Exception as e:
        logger.error(f"发送消息失败: {str(e)}")
        response, status = standardize_response(False, error=str(e), code=500)
        return jsonify(response), status 

# ================== 消息订阅和批量操作 API ==================

@api_bp.route('/message/batch/delete', methods=['POST'])
@auth_required
def batch_delete_messages():
    """批量删除消息"""
    try:
        data = request.get_json()
        ids = data.get('ids', [])
        
        if not ids:
            response, status = standardize_response(False, error='请提供要删除的消息ID列表', code=400)
            return jsonify(response), status
        
        # 模拟批量删除操作
        result = {
            'success_count': len(ids),
            'failed_count': 0,
            'deleted_ids': ids
        }
        
        response, status = standardize_response(True, data=result, message=f'成功删除 {len(ids)} 条消息')
        return jsonify(response), status
        
    except Exception as e:
        logger.error(f"批量删除消息失败: {str(e)}")
        response, status = standardize_response(False, error=str(e), code=500)
        return jsonify(response), status

@api_bp.route('/message/batch/send', methods=['POST'])
@auth_required
def batch_send_messages():
    """批量发送消息"""
    try:
        data = request.get_json()
        ids = data.get('ids', [])
        
        if not ids:
            response, status = standardize_response(False, error='请提供要发送的消息ID列表', code=400)
            return jsonify(response), status
        
        # 模拟批量发送操作
        result = {
            'success_count': len(ids) - 1,  # 模拟一个失败
            'failed_count': 1,
            'sent_ids': ids[:-1],
            'failed_ids': [ids[-1]] if ids else []
        }
        
        response, status = standardize_response(True, data=result, message=f'成功发送 {result["success_count"]} 条消息')
        return jsonify(response), status
        
    except Exception as e:
        logger.error(f"批量发送消息失败: {str(e)}")
        response, status = standardize_response(False, error=str(e), code=500)
        return jsonify(response), status

@api_bp.route('/message/stats', methods=['GET'])
@auth_required
def get_message_stats():
    """获取消息统计信息"""
    try:
        # 模拟统计数据
        stats = {
            'total': 150,
            'sent': 120,
            'draft': 25,
            'read': 95,
            'today_sent': 15,
            'this_week_sent': 45,
            'this_month_sent': 120,
            'success_rate': '95.5%',
            'avg_read_rate': '79.2%'
        }
        
        response, status = standardize_response(True, data=stats, message='获取统计信息成功')
        return jsonify(response), status
        
    except Exception as e:
        logger.error(f"获取消息统计失败: {str(e)}")
        response, status = standardize_response(False, error=str(e), code=500)
        return jsonify(response), status

@api_bp.route('/message/types', methods=['GET'])
def get_message_types():
    """获取消息类型列表"""
    try:
        # 消息类型配置
        types = [
            {
                'value': 'system',
                'label': '系统通知',
                'description': '系统维护、更新等通知',
                'color': 'blue',
                'icon': 'setting'
            },
            {
                'value': 'business',
                'label': '业务消息',
                'description': '业务流程、数据处理相关消息',
                'color': 'green',
                'icon': 'dollar'
            },
            {
                'value': 'alert',
                'label': '告警消息',
                'description': '系统异常、错误告警',
                'color': 'red',
                'icon': 'warning'
            }
        ]
        
        response, status = standardize_response(True, data=types, message='获取消息类型成功')
        return jsonify(response), status
        
    except Exception as e:
        logger.error(f"获取消息类型失败: {str(e)}")
        response, status = standardize_response(False, error=str(e), code=500)
        return jsonify(response), status

@api_bp.route('/message/subscriptions/<int:user_id>', methods=['GET'])
@auth_required
def get_user_subscriptions(user_id):
    """获取用户消息订阅设置"""
    try:
        # 模拟用户订阅设置
        subscriptions = [
            {
                'id': 1,
                'user_id': user_id,
                'message_type': 'system',
                'channel': 'email',
                'enabled': True,
                'created_at': '2024-01-15 10:30:00'
            },
            {
                'id': 2,
                'user_id': user_id,
                'message_type': 'business',
                'channel': 'system',
                'enabled': True,
                'created_at': '2024-01-15 10:30:00'
            },
            {
                'id': 3,
                'user_id': user_id,
                'message_type': 'alert',
                'channel': 'sms',
                'enabled': False,
                'created_at': '2024-01-15 10:30:00'
            }
        ]
        
        response, status = standardize_response(True, data=subscriptions, message='获取订阅设置成功')
        return jsonify(response), status
        
    except Exception as e:
        logger.error(f"获取用户订阅设置失败: {str(e)}")
        response, status = standardize_response(False, error=str(e), code=500)
        return jsonify(response), status

@api_bp.route('/message/subscriptions/<int:user_id>', methods=['PUT'])
@auth_required
def update_user_subscription(user_id):
    """更新用户消息订阅设置"""
    try:
        data = request.get_json()
        
        # 验证必要字段
        required_fields = ['message_type', 'channel', 'enabled']
        for field in required_fields:
            if field not in data:
                response, status = standardize_response(False, error=f'缺少必要字段: {field}', code=400)
                return jsonify(response), status
        
        # 模拟更新订阅设置
        updated_subscription = {
            'id': data.get('id', 999),
            'user_id': user_id,
            'message_type': data['message_type'],
            'channel': data['channel'],
            'enabled': data['enabled'],
            'updated_at': '2024-01-25 16:30:00'
        }
        
        response, status = standardize_response(True, data=updated_subscription, message='更新订阅设置成功')
        return jsonify(response), status
        
    except Exception as e:
        logger.error(f"更新用户订阅设置失败: {str(e)}")
        response, status = standardize_response(False, error=str(e), code=500)
        return jsonify(response), status

@api_bp.route('/message/publish', methods=['POST'])
@auth_required
def publish_message():
    """发布消息到指定频道"""
    try:
        data = request.get_json()
        
        # 验证必要字段
        required_fields = ['title', 'content', 'type', 'channels']
        for field in required_fields:
            if not data.get(field):
                response, status = standardize_response(False, error=f'缺少必要字段: {field}', code=400)
                return jsonify(response), status
        
        # 模拟发布操作
        publish_result = {
            'message_id': 999,
            'title': data['title'],
            'channels': data['channels'],
            'publish_time': '2024-01-25 16:45:00',
            'total_subscribers': 150,
            'successful_deliveries': 148,
            'failed_deliveries': 2,
            'delivery_channels': {
                'email': {'sent': 100, 'failed': 1},
                'sms': {'sent': 30, 'failed': 1},
                'system': {'sent': 18, 'failed': 0}
            }
        }
        
        response, status = standardize_response(True, data=publish_result, message='消息发布成功')
        return jsonify(response), status
        
    except Exception as e:
        logger.error(f"发布消息失败: {str(e)}")
        response, status = standardize_response(False, error=str(e), code=500)
        return jsonify(response), status

@api_bp.route('/message/subscribe', methods=['POST'])
@auth_required
def subscribe_message():
    """订阅消息"""
    try:
        data = request.get_json()
        
        # 验证必要字段
        required_fields = ['user_id', 'message_type', 'channel']
        for field in required_fields:
            if not data.get(field):
                response, status = standardize_response(False, error=f'缺少必要字段: {field}', code=400)
                return jsonify(response), status
        
        # 模拟订阅操作
        subscription = {
            'id': 999,
            'user_id': data['user_id'],
            'message_type': data['message_type'],
            'channel': data['channel'],
            'enabled': True,
            'created_at': '2024-01-25 16:50:00'
        }
        
        response, status = standardize_response(True, data=subscription, message='订阅成功')
        return jsonify(response), status
        
    except Exception as e:
        logger.error(f"订阅消息失败: {str(e)}")
        response, status = standardize_response(False, error=str(e), code=500)
        return jsonify(response), status

@api_bp.route('/message/unsubscribe', methods=['POST'])
@auth_required
def unsubscribe_message():
    """取消订阅消息"""
    try:
        data = request.get_json()
        
        # 验证必要字段
        required_fields = ['user_id', 'message_type']
        for field in required_fields:
            if not data.get(field):
                response, status = standardize_response(False, error=f'缺少必要字段: {field}', code=400)
                return jsonify(response), status
        
        # 模拟取消订阅操作
        result = {
            'user_id': data['user_id'],
            'message_type': data['message_type'],
            'unsubscribed_at': '2024-01-25 16:55:00'
        }
        
        response, status = standardize_response(True, data=result, message='取消订阅成功')
        return jsonify(response), status
        
    except Exception as e:
        logger.error(f"取消订阅消息失败: {str(e)}")
        response, status = standardize_response(False, error=str(e), code=500)
        return jsonify(response), status

# ================== 消息发布订阅管理 API ==================

@api_bp.route('/message/channels', methods=['GET'])
def get_message_channels():
    """获取消息推送渠道列表"""
    try:
        channels = [
            {
                'value': 'email',
                'label': '邮件',
                'description': '通过邮件发送消息',
                'icon': 'mail',
                'enabled': True
            },
            {
                'value': 'sms',
                'label': '短信',
                'description': '通过短信发送消息',
                'icon': 'message',
                'enabled': True
            },
            {
                'value': 'system',
                'label': '系统通知',
                'description': '系统内部消息通知',
                'icon': 'notification',
                'enabled': True
            },
            {
                'value': 'webhook',
                'label': 'Webhook',
                'description': '通过Webhook推送消息',
                'icon': 'api',
                'enabled': False
            }
        ]
        
        response, status = standardize_response(True, data=channels, message='获取推送渠道成功')
        return jsonify(response), status
        
    except Exception as e:
        logger.error(f"获取推送渠道失败: {str(e)}")
        response, status = standardize_response(False, error=str(e), code=500)
        return jsonify(response), status

# ============ 工作流管理接口 ============

@api_bp.route('/workflow', methods=['GET'])
def get_workflows():
    """获取工作流列表"""
    try:
        # 获取分页参数
        page = int(request.args.get('pi', 1))
        page_size = int(request.args.get('ps', 10))
        name = request.args.get('name', '').strip()
        status = request.args.get('status', '').strip()
        category = request.args.get('category', '').strip()
        
        # 模拟工作流数据
        all_workflows = [
            {
                'id': 1,
                'name': '用户注册审批流程',
                'description': '新用户注册后的审批和权限分配流程',
                'category': 'approval',
                'status': 'active',
                'steps_count': 5,
                'execution_count': 245,
                'success_rate': '98.8%',
                'creator': '系统管理员',
                'created_at': '2024-01-10 09:30:00',
                'updated_at': '2024-01-20 14:15:00',
                'last_execution': '2024-01-25 16:20:00',
                'average_duration': '1.5小时'
            },
            {
                'id': 2,
                'name': '数据处理自动化',
                'description': '每日数据清洗、转换和导入流程',
                'category': 'data_processing',
                'status': 'active',
                'steps_count': 8,
                'execution_count': 87,
                'success_rate': '95.4%',
                'creator': '数据工程师',
                'created_at': '2024-01-15 11:45:00',
                'updated_at': '2024-01-23 10:30:00',
                'last_execution': '2024-01-25 02:00:00',
                'average_duration': '45分钟'
            },
            {
                'id': 3,
                'name': '系统监控告警通知',
                'description': '系统异常检测和告警通知流程',
                'category': 'notification',
                'status': 'active',
                'steps_count': 3,
                'execution_count': 1523,
                'success_rate': '99.9%',
                'creator': '运维工程师',
                'created_at': '2024-01-08 14:20:00',
                'updated_at': '2024-01-24 09:45:00',
                'last_execution': '2024-01-25 16:30:00',
                'average_duration': '2分钟'
            },
            {
                'id': 4,
                'name': '报表生成任务',
                'description': '定时生成各类业务报表的任务调度流程',
                'category': 'task_scheduling',
                'status': 'paused',
                'steps_count': 6,
                'execution_count': 156,
                'success_rate': '92.3%',
                'creator': '业务分析师',
                'created_at': '2024-01-12 16:00:00',
                'updated_at': '2024-01-22 11:30:00',
                'last_execution': '2024-01-22 23:00:00',
                'average_duration': '20分钟'
            },
            {
                'id': 5,
                'name': '文档审核流程',
                'description': '技术文档和用户手册的审核发布流程',
                'category': 'approval',
                'status': 'disabled',
                'steps_count': 4,
                'execution_count': 34,
                'success_rate': '100%',
                'creator': '技术写作员',
                'created_at': '2024-01-05 13:15:00',
                'updated_at': '2024-01-18 15:45:00',
                'last_execution': '2024-01-18 14:30:00',
                'average_duration': '2.5小时'
            }
        ]
        
        # 根据条件过滤
        filtered_workflows = all_workflows
        if name:
            filtered_workflows = [wf for wf in filtered_workflows if name.lower() in wf['name'].lower()]
        if status:
            filtered_workflows = [wf for wf in filtered_workflows if wf['status'] == status]
        if category:
            filtered_workflows = [wf for wf in filtered_workflows if wf['category'] == category]
        
        # 计算分页
        total = len(filtered_workflows)
        start = (page - 1) * page_size
        end = start + page_size
        workflows = filtered_workflows[start:end]
        
        response_data = {
            'list': workflows,
            'total': total,
            'pi': page,
            'ps': page_size
        }
        
        response, status = standardize_response(True, data=response_data, message='获取工作流列表成功')
        return jsonify(response), status
        
    except Exception as e:
        logger.error(f"获取工作流列表失败: {str(e)}")
        response, status = standardize_response(False, error=str(e), code=500)
        return jsonify(response), status



# ================== 工作流管理 API ==================

@api_bp.route('/workflow/list', methods=['GET'])
@token_required
def get_workflow_list():
    """获取工作流列表"""
    try:
        # 获取查询参数
        user_id = request.args.get('user_id', type=int)
        category = request.args.get('category')
        status = request.args.get('status')
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)
        
        # 获取工作流列表
        result = workflow_service.get_workflow_list(
            user_id=user_id,
            category=category,
            status=status,
            page=page,
            page_size=page_size
        )
        
        if result['success']:
            return response_success(result['data'], "获取工作流列表成功")
        else:
            return response_error(result['message'], result.get('error'))
            
    except Exception as e:
        return response_error(f"获取工作流列表失败: {str(e)}")

@api_bp.route('/workflow/create', methods=['POST'])
@token_required
def create_workflow():
    """创建工作流"""
    try:
        data = request.get_json()
        
        # 验证必需字段
        required_fields = ['name', 'creator_id']
        for field in required_fields:
            if field not in data:
                return response_error(f"缺少必需字段: {field}")
        
        # 创建工作流
        result = workflow_service.create_workflow(data)
        
        if result['success']:
            return response_success({
                'workflow_id': result['workflow_id'],
                'dag_id': result['dag_id']
            }, "工作流创建成功")
        else:
            return response_error(result['message'], result.get('error'))
            
    except Exception as e:
        return response_error(f"创建工作流失败: {str(e)}")

@api_bp.route('/workflow/<int:workflow_id>', methods=['GET'])
@token_required
def get_workflow_detail(workflow_id):
    """获取工作流详情"""
    try:
        result = workflow_service.get_workflow_detail(workflow_id)
        
        if result['success']:
            return response_success(result['data'], "获取工作流详情成功")
        else:
            return response_error(result['message'], result.get('error'))
            
    except Exception as e:
        return response_error(f"获取工作流详情失败: {str(e)}")

@api_bp.route('/workflow/<int:workflow_id>/execute', methods=['POST'])
@token_required
def execute_workflow(workflow_id):
    """执行工作流"""
    try:
        data = request.get_json()
        input_data = data.get('input_data', {})
        user_id = data.get('user_id')
        
        # 执行工作流
        result = workflow_service.execute_workflow(
            workflow_id=workflow_id,
            input_data=input_data,
            user_id=user_id
        )
        
        if result['success']:
            return response_success({
                'execution_id': result['execution_id'],
                'dag_run_id': result.get('dag_run_id')
            }, "工作流执行已启动")
        else:
            return response_error(result['message'], result.get('error'))
            
    except Exception as e:
        return response_error(f"执行工作流失败: {str(e)}")

@api_bp.route('/workflow/executions', methods=['GET'])
@token_required
def get_execution_history():
    """获取工作流执行历史"""
    try:
        # 获取查询参数
        workflow_id = request.args.get('workflow_id', type=int)
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)
        
        # 获取执行历史
        result = workflow_service.get_execution_history(
            workflow_id=workflow_id,
            page=page,
            page_size=page_size
        )
        
        if result['success']:
            return response_success(result['data'], "获取执行历史成功")
        else:
            return response_error(result['message'], result.get('error'))
            
    except Exception as e:
        return response_error(f"获取执行历史失败: {str(e)}")

@api_bp.route('/workflow/templates', methods=['GET'])
@token_required
def get_workflow_templates():
    """获取工作流模板列表"""
    try:
        category = request.args.get('category')
        
        # 获取模板列表
        result = workflow_service.get_workflow_templates(category=category)
        
        if result['success']:
            return response_success(result['data'], "获取工作流模板成功")
        else:
            return response_error(result['message'], result.get('error'))
            
    except Exception as e:
        return response_error(f"获取工作流模板失败: {str(e)}")

@api_bp.route('/workflow/<int:workflow_id>/dag/status', methods=['GET'])
@token_required
def get_dag_status(workflow_id):
    """获取DAG状态"""
    try:
        # 获取工作流详情以获取dag_id
        workflow_result = workflow_service.get_workflow_detail(workflow_id)
        if not workflow_result['success']:
            return response_error(workflow_result['message'], workflow_result.get('error'))
        
        dag_id = workflow_result['data']['dag_id']
        
        # 获取DAG状态
        result = workflow_service.get_dag_status(dag_id)
        
        if result['success']:
            return response_success(result['data'], "获取DAG状态成功")
        else:
            return response_error(result['message'], result.get('error'))
            
    except Exception as e:
        return response_error(f"获取DAG状态失败: {str(e)}")

# ================== 工作流模板 API ==================

@api_bp.route('/workflow/template/<int:template_id>/create', methods=['POST'])
@token_required
def create_workflow_from_template(template_id):
    """从模板创建工作流"""
    try:
        data = request.get_json()
        
        # 获取模板详情
        templates_result = workflow_service.get_workflow_templates()
        if not templates_result['success']:
            return response_error("获取模板失败")
        
        # 查找指定模板
        template = None
        for t in templates_result['data']:
            if t['id'] == template_id:
                template = t
                break
        
        if not template:
            return response_error("模板不存在")
        
        # 构建工作流数据
        workflow_data = {
            'name': data.get('name', template['name']),
            'description': data.get('description', template['description']),
            'category': template['category'],
            'creator_id': data['creator_id'],
            'config': template['template_config'].get('config', {}),
            'schedule': data.get('schedule', ''),
            'steps': template['template_config'].get('steps', [])
        }
        
        # 创建工作流
        result = workflow_service.create_workflow(workflow_data)
        
        if result['success']:
            return response_success({
                'workflow_id': result['workflow_id'],
                'dag_id': result['dag_id']
            }, "从模板创建工作流成功")
        else:
            return response_error(result['message'], result.get('error'))
            
    except Exception as e:
        return response_error(f"从模板创建工作流失败: {str(e)}")

@api_bp.route('/audit/logs', methods=['GET'])
@auth_required
def get_audit_logs():
    """获取审计日志列表"""
    try:
        # 获取查询参数
        page = int(request.args.get('pi', 1))
        page_size = int(request.args.get('ps', 10))
        module = request.args.get('module')
        operation = request.args.get('operation')
        user_id = request.args.get('user_id')
        start_time = request.args.get('start_time')
        end_time = request.args.get('end_time')
        org_code = request.args.get('org_code')
        
        # 权限检查：普通用户只能查看自己的审计日志
        current_user = g.current_user
        role_code = current_user.get('role_code', '')
        
        if role_code == 'NORMAL_USER':
            user_id = current_user.get('id')  # 强制只查看自己的日志
        elif role_code == 'ORG_ADMIN':
            org_code = current_user.get('org_code')  # 强制只查看本机构的日志
        # SUPER_ADMIN 可以查看所有日志
        
        from service.audit_service import get_audit_service
        audit_service = get_audit_service()
        
        result = audit_service.get_audit_logs(
            page=page,
            page_size=page_size,
            module=module,
            operation=operation,
            user_id=int(user_id) if user_id else None,
            start_time=start_time,
            end_time=end_time,
            org_code=org_code
        )
        
        if result['success']:
            response, status = standardize_response(True, data=result['data'], message='获取审计日志成功')
        else:
            response, status = standardize_response(False, error=result['error'], code=400)
        return jsonify(response), status
        
    except Exception as e:
        logger.error(f"获取审计日志失败: {str(e)}")
        response, status = standardize_response(False, error=str(e), code=500)
        return jsonify(response), status

@api_bp.route('/audit/logs/<int:audit_id>', methods=['GET'])
@auth_required
def get_audit_detail(audit_id):
    """获取审计日志详情"""
    try:
        from service.audit_service import get_audit_service
        audit_service = get_audit_service()
        
        result = audit_service.get_audit_detail(audit_id)
        
        if result['success']:
            # 权限检查：普通用户只能查看自己的审计日志
            current_user = g.current_user
            role_code = current_user.get('role_code', '')
            audit_data = result['data']
            
            if role_code == 'NORMAL_USER' and audit_data['user_id'] != current_user.get('id'):
                response, status = standardize_response(False, error='权限不足', code=403)
                return jsonify(response), status
            elif role_code == 'ORG_ADMIN' and audit_data['org_code'] != current_user.get('org_code'):
                response, status = standardize_response(False, error='权限不足', code=403)
                return jsonify(response), status
            
            response, status = standardize_response(True, data=result['data'], message='获取审计日志详情成功')
        else:
            response, status = standardize_response(False, error=result['error'], code=400)
        return jsonify(response), status
        
    except Exception as e:
        logger.error(f"获取审计日志详情失败: {str(e)}")
        response, status = standardize_response(False, error=str(e), code=500)
        return jsonify(response), status