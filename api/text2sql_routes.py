# -*- coding: utf-8 -*-
"""
Text2SQL API路由模块
提供自然语言转SQL的HTTP接口
"""
import json
from datetime import datetime
from flask import Blueprint, request, jsonify, g
from service.vanna_service import get_vanna_service
from tools.auth_middleware import auth_required
import logging

logger = logging.getLogger(__name__)

# 创建蓝图
text2sql_bp = Blueprint('text2sql', __name__, url_prefix='/api/text2sql')

@text2sql_bp.route('/generate', methods=['POST'])
@auth_required
def generate_sql():
    """生成SQL查询"""
    try:
        data = request.get_json()
        question = data.get('question', '').strip()
        
        if not question:
            return jsonify({'error': '请输入查询问题'}), 400
        
        # 获取当前用户ID
        current_user = getattr(g, 'current_user', None)
        user_id = current_user.get('id') if current_user else None
        
        # 记录用户查询
        logger.info(f"用户查询: {question} (用户ID: {user_id})")
        
        # 调用Vanna服务
        vanna_service = get_vanna_service()
        result = vanna_service.generate_sql(question, user_id)
        
        if result['success']:
            return jsonify({
                'success': True,
                'sql': result['sql'],
                'confidence': result['confidence'],
                'timestamp': result['timestamp']
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 400
            
    except Exception as e:
        logger.error(f"生成SQL失败: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500

@text2sql_bp.route('/execute', methods=['POST'])
@auth_required
def execute_sql():
    """执行SQL查询"""
    try:
        data = request.get_json()
        sql = data.get('sql', '').strip()
        
        if not sql:
            return jsonify({'error': 'SQL语句不能为空'}), 400
        
        # 获取当前用户ID
        current_user = getattr(g, 'current_user', None)
        user_id = current_user.get('id') if current_user else None
        
        # 记录SQL执行
        logger.info(f"执行SQL: {sql} (用户ID: {user_id})")
        
        # 调用Vanna服务
        vanna_service = get_vanna_service()
        result = vanna_service.execute_sql(sql, user_id)
        
        if result['success']:
            return jsonify({
                'success': True,
                'data': result['data'],
                'columns': result['columns'],
                'row_count': result['row_count'],
                'execution_time': result['execution_time'],
                'timestamp': result['timestamp']
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 400
            
    except Exception as e:
        logger.error(f"执行SQL失败: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500

@text2sql_bp.route('/train', methods=['POST'])
@auth_required
def train_sql():
    """训练SQL样本"""
    try:
        data = request.get_json()
        question = data.get('question', '').strip()
        sql = data.get('sql', '').strip()
        
        if not question or not sql:
            return jsonify({'error': '问题和SQL都不能为空'}), 400
        
        # 获取当前用户ID
        current_user = getattr(g, 'current_user', None)
        user_id = current_user.get('id') if current_user else None
        
        # 记录训练
        logger.info(f"训练样本: {question} -> {sql} (用户ID: {user_id})")
        
        # 调用Vanna服务
        vanna_service = get_vanna_service()
        result = vanna_service.train_on_sql(question, sql, user_id)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"训练失败: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500

@text2sql_bp.route('/sessions', methods=['GET'])
@auth_required
def get_sessions():
    """获取用户的Text2SQL会话列表"""
    try:
        # 获取当前用户ID
        current_user = getattr(g, 'current_user', None)
        user_id = current_user.get('id') if current_user else None
        
        if not user_id:
            return jsonify({'error': '用户身份验证失败'}), 401
        
        # 使用Vanna服务获取会话列表
        vanna_service = get_vanna_service()
        result = vanna_service.get_user_sessions(user_id)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"获取会话列表失败: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500

@text2sql_bp.route('/sessions', methods=['POST'])
@auth_required
def create_session():
    """创建新的Text2SQL会话"""
    try:
        data = request.get_json()
        title = data.get('title', '新的Text2SQL对话')
        
        # 获取当前用户ID
        current_user = getattr(g, 'current_user', None)
        user_id = current_user.get('id') if current_user else None
        
        if not user_id:
            return jsonify({'error': '用户身份验证失败'}), 401
        
        # 使用Vanna服务创建会话
        vanna_service = get_vanna_service()
        result = vanna_service.create_session(user_id, title)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"创建会话失败: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500

@text2sql_bp.route('/sessions/<session_id>', methods=['DELETE'])
@auth_required
def delete_session(session_id):
    """删除Text2SQL会话"""
    try:
        # 获取当前用户ID
        current_user = getattr(g, 'current_user', None)
        user_id = current_user.get('id') if current_user else None
        
        if not user_id:
            return jsonify({'error': '用户身份验证失败'}), 401
        
        # 使用Vanna服务删除会话
        vanna_service = get_vanna_service()
        result = vanna_service.delete_session(user_id, session_id)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"删除会话失败: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500

@text2sql_bp.route('/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    try:
        vanna_service = get_vanna_service()
        return jsonify({
            'success': True,
            'message': 'Text2SQL服务运行正常',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"健康检查失败: {str(e)}")
        return jsonify({'error': '服务异常'}), 500

@text2sql_bp.route('/train-samples', methods=['POST'])
@auth_required
def train_initial_samples():
    """训练初始SQL样本"""
    try:
        # 获取当前用户ID
        current_user = getattr(g, 'current_user', None)
        user_id = current_user.get('id') if current_user else None
        
        # 记录训练操作
        logger.info(f"开始训练初始SQL样本 (用户ID: {user_id})")
        
        # 调用Vanna服务
        vanna_service = get_vanna_service()
        result = vanna_service.train_initial_samples()
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"训练初始样本失败: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500 