from flask import request, jsonify, g
from . import api_bp
from tools.auth_middleware import auth_required, permission_required
from service import get_workflow_service_instance
from service.workflow_service import get_workflow_service as get_enhanced_workflow_service
from tools.exceptions import (
    ValidationException,
    BusinessException,
    ResourceNotFoundException,
    handle_exception,
    create_error_response
)
import logging

logger = logging.getLogger(__name__)

@api_bp.route('/workflow/workspaces', methods=['GET'])
@auth_required
def get_workspaces():
    """获取工作空间列表"""
    try:
        current_user = g.current_user
        user_id = current_user.get('id')
        enhanced_service = get_enhanced_workflow_service()
        result = enhanced_service.get_workspaces(user_id)
        
        return jsonify({
            'code': 200,
            'success': True,
            'data': result.get('data', []),
            'total': result.get('total', 0),
            'message': '获取工作空间列表成功'
        })
    except Exception as e:
        logger.error(f"获取工作空间列表失败: {str(e)}")
        return handle_exception(e)

@api_bp.route('/workflow/list', methods=['GET'])
@auth_required 
def get_workflows():
    """获取工作流列表"""
    try:
        current_user = g.current_user
        user_id = current_user.get('id')
        page = request.args.get('pi', 1, type=int)
        page_size = request.args.get('ps', 10, type=int)
        workspace = request.args.get('workspace')
        category = request.args.get('category')
        status = request.args.get('status')
        
        filters = {}
        if workspace:
            filters['workspace'] = workspace
        if category:
            filters['category'] = category
        if status:
            filters['status'] = status
            
        enhanced_service = get_enhanced_workflow_service()
        # 构建过滤条件
        filters_dict = {}
        if workspace:
            filters_dict['workspace'] = workspace
        if category:
            filters_dict['category'] = category
        if status:
            filters_dict['status'] = status
        if page:
            filters_dict['page'] = page
        if page_size:
            filters_dict['page_size'] = page_size
            
        result = enhanced_service.get_workflows(
            workspace_id=workspace,
            category_id=category,
            user_id=user_id,
            filters=filters_dict
        )
        
        return jsonify({
            'code': 200,
            'success': True,
            'data': result.get('data', []),
            'total': result.get('total', 0),
            'message': '获取工作流列表成功'
        })
    except Exception as e:
        logger.error(f"获取工作流列表失败: {str(e)}")
        return handle_exception(e)

@api_bp.route('/workflow/<int:workflow_id>/activate', methods=['PUT'])
@auth_required
@permission_required('workflow:manage')
def activate_workflow(workflow_id):
    """激活工作流"""
    try:
        enhanced_service = get_enhanced_workflow_service()
        result = enhanced_service.activate_workflow(workflow_id)
        
        return jsonify({
            'code': 200,
            'success': True,
            'message': '工作流激活成功'
        })
    except Exception as e:
        logger.error(f"激活工作流失败: {str(e)}")
        return handle_exception(e)

@api_bp.route('/workflow/<int:workflow_id>', methods=['DELETE'])
@auth_required
@permission_required('workflow:delete')
def delete_workflow(workflow_id):
    """删除工作流"""
    try:
        enhanced_service = get_enhanced_workflow_service()
        result = enhanced_service.delete_workflow(workflow_id)
        
        return jsonify({
            'code': 200,
            'success': True,
            'message': '工作流删除成功'
        })
    except Exception as e:
        logger.error(f"删除工作流失败: {str(e)}")
        return handle_exception(e)

@api_bp.route('/workflow/execute/<int:workflow_id>', methods=['POST'])
@auth_required
@permission_required('workflow:execute')
def execute_workflow(workflow_id):
    """执行工作流"""
    try:
        enhanced_service = get_enhanced_workflow_service()
        result = enhanced_service.execute_workflow(workflow_id)
        
        return jsonify({
            'code': 200,
            'success': True,
            'message': '工作流执行成功'
        })
    except Exception as e:
        logger.error(f"执行工作流失败: {str(e)}")
        return handle_exception(e)

@api_bp.route('/workflow/batch/activate', methods=['PUT'])
@auth_required
@permission_required('workflow:manage')
def batch_activate_workflows():
    """批量激活工作流"""
    try:
        data = request.get_json()
        ids = data.get('ids', [])
        
        if not ids:
            raise ValidationException("请选择要激活的工作流")
        
        enhanced_service = get_enhanced_workflow_service()
        for workflow_id in ids:
            enhanced_service.activate_workflow(workflow_id)
        
        return jsonify({
            'code': 200,
            'success': True,
            'message': f'成功激活 {len(ids)} 个工作流'
        })
    except Exception as e:
        logger.error(f"批量激活工作流失败: {str(e)}")
        return handle_exception(e)

@api_bp.route('/workflow/batch/deactivate', methods=['PUT'])
@auth_required
@permission_required('workflow:manage')
def batch_deactivate_workflows():
    """批量停用工作流"""
    try:
        data = request.get_json()
        ids = data.get('ids', [])
        
        if not ids:
            raise ValidationException("请选择要停用的工作流")
        
        enhanced_service = get_enhanced_workflow_service()
        for workflow_id in ids:
            enhanced_service.deactivate_workflow(workflow_id)
        
        return jsonify({
            'code': 200,
            'success': True,
            'message': f'成功停用 {len(ids)} 个工作流'
        })
    except Exception as e:
        logger.error(f"批量停用工作流失败: {str(e)}")
        return handle_exception(e)

@api_bp.route('/workflow/batch', methods=['DELETE'])
@auth_required
@permission_required('workflow:delete')
def batch_delete_workflows():
    """批量删除工作流"""
    try:
        data = request.get_json()
        ids = data.get('ids', [])
        
        if not ids:
            raise ValidationException("请选择要删除的工作流")
        
        enhanced_service = get_enhanced_workflow_service()
        for workflow_id in ids:
            enhanced_service.delete_workflow(workflow_id)
        
        return jsonify({
            'code': 200,
            'success': True,
            'message': f'成功删除 {len(ids)} 个工作流'
        })
    except Exception as e:
        logger.error(f"批量删除工作流失败: {str(e)}")
        return handle_exception(e)

@api_bp.route('/workflow/tasks', methods=['GET'])
@auth_required
def get_tasks():
    """获取任务列表"""
    try:
        page = request.args.get('pi', request.args.get('page', 1), type=int)
        page_size = request.args.get('ps', request.args.get('page_size', 10), type=int)
        status = request.args.get('status')
        task_type = request.args.get('task_type')
        
        workflow_service = get_workflow_service_instance()
        result = workflow_service.get_tasks_list(
            page=page,
            page_size=page_size,
            status=status,
            task_type=task_type
        )
        
        if not result['success']:
            raise BusinessException(result.get('error', '获取任务列表失败'))
            
        return jsonify({
            'code': 200,
            'message': '获取任务列表成功',
            'data': result['data']
        })
            
    except Exception as e:
        logger.error(f"获取任务列表失败: {str(e)}")
        return handle_exception(e)

@api_bp.route('/workflow/tasks/<int:task_id>', methods=['GET'])
@auth_required
def get_task(task_id):
    """获取任务详情"""
    try:
        workflow_service = get_workflow_service_instance()
        result = workflow_service.get_task_by_id(task_id)
        
        if not result['success']:
            raise ResourceNotFoundException(result.get('error', '任务不存在'))
            
        return jsonify({
            'code': 200,
            'message': '获取任务详情成功',
            'data': result['data']
        })
            
    except Exception as e:
        logger.error(f"获取任务详情失败: {str(e)}")
        return handle_exception(e)

@api_bp.route('/workflow/tasks', methods=['POST'])
@auth_required
def create_task():
    """创建任务"""
    try:
        data = request.get_json()
        task_type = data.get('task_type')
        task_data = data.get('task_data')
        
        if not task_type or not task_data:
            raise ValidationException('任务类型和任务数据不能为空')
            
        workflow_service = get_workflow_service_instance()
        result = workflow_service.create_task(task_type, task_data)
        
        if not result['success']:
            raise BusinessException(result.get('error', '创建任务失败'))
            
        return jsonify({
            'code': 200,
            'message': '创建任务成功',
            'data': result['data']
        })
            
    except Exception as e:
        logger.error(f"创建任务失败: {str(e)}")
        return handle_exception(e)

@api_bp.route('/workflow/process', methods=['GET'])
@auth_required
def get_processes():
    """获取流程列表"""
    try:
        page = request.args.get('pi', request.args.get('page', 1), type=int)
        page_size = request.args.get('ps', request.args.get('page_size', 10), type=int)
        status = request.args.get('status')
        process_type = request.args.get('process_type')
        
        workflow_service = get_workflow_service_instance()
        result = workflow_service.get_processes_list(
            page=page,
            page_size=page_size,
            status=status,
            process_type=process_type
        )
        
        if not result['success']:
            raise BusinessException(result.get('error', '获取流程列表失败'))
            
        return jsonify({
            'code': 200,
            'message': '获取流程列表成功',
            'data': result['data']
        })
            
    except Exception as e:
        logger.error(f"获取流程列表失败: {str(e)}")
        return handle_exception(e)

@api_bp.route('/workflow/process/<int:process_id>', methods=['GET'])
@auth_required
def get_process(process_id):
    """获取流程详情"""
    try:
        workflow_service = get_workflow_service_instance()
        result = workflow_service.get_process_by_id(process_id)
        
        if not result['success']:
            raise ResourceNotFoundException(result.get('error', '流程不存在'))
            
        return jsonify({
            'code': 200,
            'message': '获取流程详情成功',
            'data': result['data']
        })
            
    except Exception as e:
        logger.error(f"获取流程详情失败: {str(e)}")
        return handle_exception(e)

@api_bp.route('/workflow/process', methods=['POST'])
@auth_required
@permission_required('workflow:create')
def create_process():
    """创建流程"""
    try:
        data = request.get_json()
        process_type = data.get('process_type')
        process_data = data.get('process_data')
        
        if not process_type or not process_data:
            raise ValidationException('流程类型和流程数据不能为空')
            
        workflow_service = get_workflow_service_instance()
        result = workflow_service.create_process(process_type, process_data)
        
        if not result['success']:
            raise BusinessException(result.get('error', '创建流程失败'))
            
        return jsonify({
            'code': 200,
            'message': '创建流程成功',
            'data': result['data']
        })
            
    except Exception as e:
        logger.error(f"创建流程失败: {str(e)}")
        return handle_exception(e)

@api_bp.route('/workflow/approve', methods=['POST'])
@auth_required
def approve_task():
    """审批任务"""
    try:
        data = request.get_json()
        task_id = data.get('task_id')
        action = data.get('action')  # approve/reject
        comment = data.get('comment', '')
        
        if not task_id or not action:
            raise ValidationException('任务ID和审批动作不能为空')
            
        workflow_service = get_workflow_service_instance()
        result = workflow_service.approve_task(task_id, action, comment)
        
        if not result['success']:
            raise BusinessException(result.get('error', '审批任务失败'))
            
        return jsonify({
            'code': 200,
            'message': '审批任务成功',
            'data': result['data']
        })
            
    except Exception as e:
        logger.error(f"审批任务失败: {str(e)}")
        return handle_exception(e) 