from flask import request, jsonify, g
from . import api_bp
from tools.auth_middleware import auth_required, permission_required
from service import get_ai_service_instance
from tools.exceptions import (
    ValidationException,
    BusinessException,
    handle_exception,
    create_error_response
)
import logging

logger = logging.getLogger(__name__)

@api_bp.route('/ask', methods=['POST'])
@auth_required
def ask_question():
    """AI问答接口"""
    try:
        data = request.get_json()
        question = data.get('question')
        context = data.get('context', '')
        
        if not question:
            raise ValidationException('问题不能为空')
            
        ai_service = get_ai_service_instance()
        result = ai_service.ask_question(question, context)
        
        if not result['success']:
            raise BusinessException(result.get('error', 'AI回答失败'))
            
        return jsonify({
            'code': 200,
            'message': '获取回答成功',
            'data': result['data']
        })
            
    except Exception as e:
        logger.error(f"AI回答失败: {str(e)}")
        return handle_exception(e)

@api_bp.route('/generate_sql', methods=['POST'])
@auth_required
def generate_sql():
    """生成SQL语句"""
    try:
        data = request.get_json()
        question = data.get('question')
        database_info = data.get('database_info', {})
        
        if not question:
            raise ValidationException('问题不能为空')
            
        ai_service = get_ai_service_instance()
        result = ai_service.generate_sql(question, database_info)
        
        if not result['success']:
            raise BusinessException(result.get('error', '生成SQL失败'))
            
        return jsonify({
            'code': 200,
            'message': '生成SQL成功',
            'data': result['data']
        })
            
    except Exception as e:
        logger.error(f"生成SQL失败: {str(e)}")
        return handle_exception(e)

@api_bp.route('/train', methods=['POST'])
@auth_required
@permission_required('ai:train')
def train_model():
    """训练模型"""
    try:
        data = request.get_json()
        model_type = data.get('model_type')
        training_data = data.get('training_data')
        parameters = data.get('parameters', {})
        
        if not model_type or not training_data:
            raise ValidationException('模型类型和训练数据不能为空')
            
        ai_service = get_ai_service_instance()
        result = ai_service.train_model(model_type, training_data, parameters)
        
        if not result['success']:
            raise BusinessException(result.get('error', '模型训练失败'))
            
        return jsonify({
            'code': 200,
            'message': '开始训练模型',
            'data': result['data']
        })
            
    except Exception as e:
        logger.error(f"模型训练失败: {str(e)}")
        return handle_exception(e)

@api_bp.route('/auto_train', methods=['POST'])
@auth_required
@permission_required('ai:train')
def auto_train():
    """自动训练模型"""
    try:
        data = request.get_json()
        model_type = data.get('model_type')
        data_source = data.get('data_source')
        parameters = data.get('parameters', {})
        
        if not model_type or not data_source:
            raise ValidationException('模型类型和数据源不能为空')
            
        ai_service = get_ai_service_instance()
        result = ai_service.auto_train(model_type, data_source, parameters)
        
        if not result['success']:
            raise BusinessException(result.get('error', '自动训练失败'))
            
        return jsonify({
            'code': 200,
            'message': '开始自动训练',
            'data': result['data']
        })
            
    except Exception as e:
        logger.error(f"自动训练失败: {str(e)}")
        return handle_exception(e)

@api_bp.route('/train/status/<task_id>', methods=['GET'])
@auth_required
def get_train_status(task_id):
    """获取训练状态"""
    try:
        if not task_id:
            raise ValidationException('任务ID不能为空')
            
        ai_service = get_ai_service_instance()
        result = ai_service.get_train_status(task_id)
        
        if not result['success']:
            raise BusinessException(result.get('error', '获取训练状态失败'))
            
        return jsonify({
            'code': 200,
            'message': '获取训练状态成功',
            'data': result['data']
        })
            
    except Exception as e:
        logger.error(f"获取训练状态失败: {str(e)}")
        return handle_exception(e)

@api_bp.route('/models', methods=['GET'])
@auth_required
def get_models():
    """获取模型列表"""
    try:
        model_type = request.args.get('model_type')
        status = request.args.get('status')
        
        ai_service = get_ai_service_instance()
        result = ai_service.get_models(model_type, status)
        
        if not result['success']:
            raise BusinessException(result.get('error', '获取模型列表失败'))
            
        return jsonify({
            'code': 200,
            'message': '获取模型列表成功',
            'data': result['data']
        })
            
    except Exception as e:
        logger.error(f"获取模型列表失败: {str(e)}")
        return handle_exception(e) 