from flask import jsonify, g
from . import api_bp
from tools.auth_middleware import auth_required
from tools.exceptions import (
    ValidationException,
    BusinessException,
    AuthenticationException,
    handle_exception,
    create_error_response
)
from service import get_menu_service_instance, get_permission_service_instance
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def get_default_menus():
    """获取默认菜单（当菜单服务失败时使用）"""
    return [
        {
            'text': '洞察魔方',
            'group': True,
            'hideInBreadcrumb': True,
            'children': [
                {
                    'text': 'AI监控大屏',
                    'i18n': 'menu.dashboard',
                    'icon': { 'type': 'icon', 'value': 'dashboard' },
                    'link': '/dashboard'
                },
                {
                    'text': '系统管理',
                    'i18n': 'menu.sys',
                    'icon': { 'type': 'icon', 'value': 'setting' },
                    'children': [
                        {
                            'text': '用户管理',
                            'i18n': 'menu.sys.user',
                            'link': '/sys/user',
                            'icon': { 'type': 'icon', 'value': 'user' }
                        },
                        {
                            'text': '角色管理',
                            'i18n': 'menu.sys.role',
                            'link': '/sys/role',
                            'icon': { 'type': 'icon', 'value': 'team' }
                        },
                        {
                            'text': '权限管理',
                            'i18n': 'menu.sys.permission',
                            'link': '/sys/permission',
                            'icon': { 'type': 'icon', 'value': 'safety' }
                        },
                        {
                            'text': '机构管理',
                            'i18n': 'menu.sys.org',
                            'link': '/sys/org',
                            'icon': { 'type': 'icon', 'value': 'cluster' }
                        }
                    ]
                }
            ]
        }
    ]

@api_bp.route('/app/init', methods=['GET'])
@auth_required
def app_init():
    """
    系统初始化接口
    返回完全兼容ACL框架的配置
    """
    try:
        # 获取当前用户信息
        current_user = g.current_user
        if not current_user:
            raise AuthenticationException('用户未登录')
        
        user_id = current_user.get('user_id') or current_user.get('id')
        if not user_id:
            raise AuthenticationException('无效的用户信息')

        # 获取增强权限服务
        from service.enhanced_permission_service import get_enhanced_permission_service_instance
        permission_service = get_enhanced_permission_service_instance()
        
        # 获取用户详细信息
        user_info = permission_service.get_user_with_role(user_id)
        if not user_info:
            raise BusinessException('获取用户信息失败')
        
        # 获取ACL配置
        acl_config = permission_service.get_user_acl_config(user_id)
        
        # 获取过滤后的菜单数据
        menus = permission_service.get_filtered_menus(acl_config['ability'])

        # 构建响应数据，完全兼容ACL框架
        response_data = {
            'app': {
                'name': '洞察魔方',
                'description': '智能数据问答平台'
            },
            'user': {
                'id': user_info['id'],
                'name': user_info['username'],
                'username': user_info['username'],
                'avatar': './assets/tmp/img/avatar.jpg',
                'email': current_user.get('email', ''),
                'orgCode': user_info['org_code'],
                'roleCode': user_info['role_code'],
                'dataScope': acl_config.get('dataScope', 'SELF')
            },
            'menus': menus,
            'permissions': acl_config['ability'],  # 前端ACL使用的权限列表
            'acl': acl_config  # 完整的ACL配置
        }
        
        return jsonify({
            'code': 200,
            'message': '获取成功',
            'data': response_data
        })
        
    except Exception as e:
        logger.error(f"系统初始化失败: {str(e)}")
        return handle_exception(e)

@api_bp.route('/chart', methods=['GET'])
def get_chart():
    """获取图表数据"""
    try:
        data = {
            'visitData': [
                {"x": "2024-01", "y": 123}, {"x": "2024-02", "y": 234},
                {"x": "2024-03", "y": 345}, {"x": "2024-04", "y": 456},
                {"x": "2024-05", "y": 567}
            ],
            'salesData': [
                {"x": "1月", "y": 2800}, {"x": "2月", "y": 3200},
                {"x": "3月", "y": 3600}, {"x": "4月", "y": 3800},
                {"x": "5月", "y": 4200}
            ]
        }
        return jsonify({
            'code': 200,
            'message': '获取图表数据成功',
            'data': data
        })
    except Exception as e:
        logger.error(f"获取图表数据失败: {str(e)}")
        return handle_exception(e)

@api_bp.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    try:
        return jsonify({
            'code': 200,
            'message': 'Service is healthy',
            'data': {
                'status': 'UP',
                'timestamp': datetime.now().isoformat()
            }
        })
    except Exception as e:
        logger.error(f"健康检查失败: {str(e)}")
        return handle_exception(e)

@api_bp.route('/notice', methods=['GET'])
def get_notice():
    """获取通知列表"""
    try:
        notices = [
            {
                'id': '000000001',
                'avatar': 'https://gw.alipayobjects.com/zos/rmsportal/ThXAXghbEsBCCSDihZxY.png',
                'title': '你收到了 14 份新周报',
                'datetime': '2024-01-09',
                'type': 'notification'
            }
        ]
        return jsonify({
            'code': 200,
            'message': '获取通知列表成功',
            'data': notices
        })
    except Exception as e:
        logger.error(f"获取通知列表失败: {str(e)}")
        return handle_exception(e)

@api_bp.route('/activities', methods=['GET'])
def get_activities():
    """获取活动列表"""
    try:
        activities = [
            {
                'id': 'trend-1',
                'updatedAt': '2024-01-09T08:22:54.445Z',
                'user': {
                    'name': '曲丽丽',
                    'avatar': 'https://gw.alipayobjects.com/zos/rmsportal/BiazfanxmamNRoxxVxka.png'
                },
                'group': {
                    'name': '高逼格设计天团',
                    'link': 'http://github.com/'
                },
                'project': {
                    'name': '六月迭代',
                    'link': 'http://github.com/'
                },
                'template': '在 @{group} 新建项目 @{project}'
            }
        ]
        return jsonify({
            'code': 200,
            'message': '获取活动列表成功',
            'data': activities
        })
    except Exception as e:
        logger.error(f"获取活动列表失败: {str(e)}")
        return handle_exception(e)

@api_bp.route('/permission/test', methods=['GET'])
@auth_required
def test_permission():
    """测试权限系统"""
    try:
        from tools.permission_middleware import PermissionMiddleware
        current_user = g.current_user
        if not current_user:
            raise AuthenticationException("用户未登录")
        
        user_id = current_user.get('user_id') or current_user.get('id')
        middleware = PermissionMiddleware()
        user_acl_info = middleware.get_user_acl_info(user_id)
        
        return jsonify({
            'code': 200,
            'message': '权限测试成功',
            'data': {
                'user_info': current_user,
                'acl_info': user_acl_info,
                'has_user_list_permission': 'USER_LIST' in user_acl_info.get('ability', []),
                'has_super_admin_permission': '*' in user_acl_info.get('ability', [])
            }
        })
    except Exception as e:
        logger.error(f"权限测试失败: {str(e)}")
        return handle_exception(e) 