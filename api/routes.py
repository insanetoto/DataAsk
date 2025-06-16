# -*- coding: utf-8 -*-
"""
API路由模块
提供智能问答相关的API接口
"""
import logging
from typing import Dict, Any
from flask import Blueprint, request, jsonify
from services.vanna_service import get_vanna_service
from services.database import get_database_service
from services.redis_service import get_redis_service

# License授权检查
from middleware.license_middleware import require_license

logger = logging.getLogger(__name__)

# 创建蓝图
api_bp = Blueprint('api', __name__, url_prefix='/api/v1')

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
                'database': db_service.test_connection(),
                'redis': redis_service.test_connection(),
                'vanna': vanna_service.is_available()
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
                'error': '不支持的训练数据格式'
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
    """自动训练接口 - 从数据库schema自动训练"""
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
        
        # 获取数据库概要信息
        summary = db_service.get_database_summary()
        
        return jsonify({
            'success': True,
            'data': summary
        }), 200
        
    except Exception as e:
        logger.error(f"获取数据库信息失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/database/schema', methods=['GET'])
def get_database_schema():
    """获取数据库schema接口"""
    try:
        db_service = get_database_service()
        
        # 获取数据库表结构信息
        schema_info = db_service.get_table_schemas()
        
        return jsonify({
            'success': True,
            'data': schema_info
        }), 200
        
    except Exception as e:
        logger.error(f"获取数据库schema失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/cache/clear', methods=['POST'])
@require_license('cache_enabled')
def clear_cache():
    """清除缓存接口"""
    try:
        data = request.get_json()
        cache_type = data.get('type', 'all') if data else 'all'
        
        redis_service = get_redis_service()
        
        if cache_type == 'all':
            # 清除所有缓存（在实际生产环境中要谨慎使用）
            redis_service.redis_client.flushdb()
            message = '所有缓存已清除'
        elif cache_type == 'query':
            # 清除查询结果缓存
            keys = redis_service.redis_client.keys('query_result:*')
            if keys:
                redis_service.redis_client.delete(*keys)
            message = f'查询结果缓存已清除 ({len(keys)} 个)'
        elif cache_type == 'sql':
            # 清除SQL缓存
            keys = redis_service.redis_client.keys('vanna_sql:*')
            if keys:
                redis_service.redis_client.delete(*keys)
            message = f'SQL缓存已清除 ({len(keys)} 个)'
        else:
            return jsonify({
                'success': False,
                'error': '不支持的缓存类型'
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