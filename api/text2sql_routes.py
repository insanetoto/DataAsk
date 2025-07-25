# -*- coding: utf-8 -*-
"""
Text2SQL API路由模块
提供自然语言转SQL的HTTP接口
"""
import json
from datetime import datetime
from flask import Blueprint, request, jsonify, g
from AIEngine.vanna_service import get_vanna_service
from tools.auth_middleware import auth_required
from tools.exceptions import (
    ValidationException, BusinessException,
    DatabaseException, ExternalServiceException
)
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
        session_id = data.get('session_id')  # 添加会话ID参数
        
        if not question:
            raise ValidationException('请输入查询问题')
        
        # 获取当前用户ID
        current_user = getattr(g, 'current_user', None)
        user_id = current_user.get('id') if current_user else None
        
        # 记录用户查询
        logger.info(f"用户查询: {question} (用户ID: {user_id})")
        
        # 调用Vanna服务
        vanna_service = get_vanna_service()
        result = vanna_service.generate_sql(question)
        
        if result['success']:
            return jsonify({
                'code': 200,
                'success': True,
                'data': result['data'],
                'message': 'SQL生成成功'
            })
        else:
            raise BusinessException(result.get('error', 'SQL生成失败'))
            
    except (ValidationException, BusinessException):
        raise
    except Exception as e:
        logger.error(f"生成SQL失败: {str(e)}")
        raise ExternalServiceException('SQL生成服务异常')

@text2sql_bp.route('/execute', methods=['POST'])
@auth_required
def execute_sql():
    """执行SQL查询"""
    try:
        data = request.get_json()
        sql = data.get('sql', '').strip()
        session_id = data.get('session_id')  # 添加会话ID参数
        
        if not sql:
            raise ValidationException('SQL语句不能为空')
        
        # 获取当前用户ID
        current_user = getattr(g, 'current_user', None)
        user_id = current_user.get('id') if current_user else None
        
        # 记录SQL执行
        logger.info(f"执行SQL: {sql} (用户ID: {user_id})")
        
        start_time = datetime.now()
        
        # 调用Vanna服务
        vanna_service = get_vanna_service()
        result = vanna_service.execute_sql(sql)
        
        execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
        
        if result['success']:
            # 如果提供了会话ID，记录执行结果
            if session_id:
                vanna_service.add_message_to_session(
                    session_id=session_id,
                    user_id=user_id,
                    message_type='assistant',
                    content=f"SQL执行成功，返回{len(result['data'])}条记录",
                    sql_query=sql,
                    query_result=result['data'],
                    execution_time=execution_time
                )
            
            return jsonify({
                'code': 200,
                'success': True,
                'data': {
                    'records': result['data'],
                    'columns': result['columns'],
                    'row_count': result['row_count'],
                    'execution_time': execution_time,
                    'timestamp': datetime.now().isoformat()
                },
                'message': 'SQL执行成功'
            })
        else:
            error_message = result.get('error', 'SQL执行失败')
            
            # 如果提供了会话ID，记录执行失败
            if session_id:
                vanna_service.add_message_to_session(
                    session_id=session_id,
                    user_id=user_id,
                    message_type='assistant',
                    content=f"SQL执行失败：{error_message}",
                    sql_query=sql,
                    execution_time=execution_time
                )
            
            raise DatabaseException(error_message)
            
    except (ValidationException, DatabaseException):
        raise
    except Exception as e:
        logger.error(f"执行SQL失败: {str(e)}")
        raise ExternalServiceException('SQL执行服务异常')

@text2sql_bp.route('/train', methods=['POST'])
@auth_required
def train_model():
    """训练模型"""
    try:
        data = request.get_json()
        if not data:
            raise ValidationException('缺少训练数据')
        
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
            raise ValidationException('无效的训练数据格式')
        
        if success:
            return jsonify({
                'code': 200,
                'success': True,
                'message': '模型训练成功'
            })
        else:
            raise BusinessException('模型训练失败')
            
    except (ValidationException, BusinessException):
        raise
    except Exception as e:
        logger.error(f"模型训练失败: {str(e)}")
        raise ExternalServiceException('训练服务异常')

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
        
        if result['success']:
            # 添加欢迎消息
            session_id = result['data']['id']
            vanna_service.add_message_to_session(
                session_id=session_id,
                user_id=user_id,
                message_type='system',
                content='欢迎使用Text2SQL对话功能！请输入您的问题，我会帮您生成相应的SQL查询。'
            )
        
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