# -*- coding: utf-8 -*-
"""
增强权限服务模块
提供完全兼容ACL框架的权限控制服务
"""
import logging
import json
from typing import Dict, Any, List, Optional
from tools.database import get_database_service
from tools.exceptions import (
    ValidationException, BusinessException,
    DatabaseException
)

logger = logging.getLogger(__name__)

class EnhancedPermissionService:
    """增强的权限服务，完全兼容ACL框架"""
    
    def __init__(self):
        self.db = get_database_service()
    
    def get_user_acl_config(self, user_id: int) -> Dict[str, Any]:
        """
        获取用户的ACL配置，完全兼容ng-alain ACL格式
        返回格式：{role: [], ability: [], mode: 'oneOf'}
        """
        try:
            # 获取用户角色信息
            user_info = self.get_user_with_role(user_id)
            if not user_info:
                return {'role': [], 'ability': [], 'mode': 'oneOf'}
            
            role_code = user_info['role_code']
            role_level = user_info['role_level']
            data_scope = user_info['data_scope']
            
            # 构建ACL配置
            acl_config = {
                'role': [role_code],
                'ability': [],
                'mode': 'oneOf'
            }
            
            # 根据角色等级获取权限
            if role_level == 1:  # 超级管理员
                acl_config['ability'] = ['*']  # 拥有所有权限
            elif role_level == 2:  # 机构管理员
                acl_config['ability'] = self.get_org_admin_permissions()
            else:  # 普通用户
                acl_config['ability'] = self.get_normal_user_permissions()
            
            # 添加数据范围信息（用于后端数据过滤）
            acl_config['dataScope'] = data_scope
            acl_config['orgCode'] = user_info.get('org_code')
            
            return acl_config
            
        except Exception as e:
            logger.error(f"获取用户ACL配置失败: {str(e)}")
            return {'role': [], 'ability': [], 'mode': 'oneOf'}
    
    def get_user_with_role(self, user_id: int) -> Optional[Dict[str, Any]]:
        """获取用户及其角色信息"""
        try:
            sql = """
                SELECT u.id, u.user_code, u.username, u.org_code,
                       r.role_code, r.role_name, r.role_level, r.data_scope
                FROM users u
                JOIN roles r ON u.role_id = r.id
                WHERE u.id = :user_id AND u.status = 1 AND r.status = 1
            """
            results = self.db.execute_query(sql, {'user_id': user_id})
            return results[0] if results else None
            
        except Exception as e:
            logger.error(f"获取用户角色信息失败: {str(e)}")
            return None
    
    def get_org_admin_permissions(self) -> List[str]:
        """获取机构管理员权限列表"""
        try:
            sql = """
                SELECT DISTINCT p.permission_code 
                FROM permission_templates pt
                JOIN permissions p ON pt.permission_code = p.permission_code 
                    AND pt.permission_type = p.permission_type
                WHERE pt.role_level = 2 AND p.status = 1
            """
            results = self.db.execute_query(sql)
            return [row['permission_code'] for row in results]
            
        except Exception as e:
            logger.error(f"获取机构管理员权限失败: {str(e)}")
            return []
    
    def get_normal_user_permissions(self) -> List[str]:
        """获取普通用户权限列表"""
        try:
            sql = """
                SELECT DISTINCT p.permission_code 
                FROM permission_templates pt
                JOIN permissions p ON pt.permission_code = p.permission_code 
                    AND pt.permission_type = p.permission_type
                WHERE pt.role_level = 3 AND p.status = 1
            """
            results = self.db.execute_query(sql)
            return [row['permission_code'] for row in results]
            
        except Exception as e:
            logger.error(f"获取普通用户权限失败: {str(e)}")
            return []
    
    def get_all_permissions(self) -> List[str]:
        """获取所有权限列表（用于超级管理员）"""
        try:
            sql = "SELECT permission_code FROM permissions WHERE status = 1"
            results = self.db.execute_query(sql)
            permissions = [row['permission_code'] for row in results]
            permissions.append('*')  # 添加通配符权限
            return permissions
            
        except Exception as e:
            logger.error(f"获取所有权限失败: {str(e)}")
            return ['*']
    
    def apply_data_scope_filter(self, base_sql: str, user_info: dict, table_alias: str = '') -> str:
        """
        应用数据范围过滤
        在WHERE子句中添加过滤条件，而不是外层包装
        """
        try:
            data_scope = user_info.get('dataScope', 'SELF')
            org_code = user_info.get('orgCode') 
            user_id = user_info.get('user_id')
            
            if data_scope == 'ALL':
                # 超级管理员，不过滤
                return base_sql
            
            # 构建过滤条件
            alias = f"{table_alias}." if table_alias else ""
            
            if data_scope == 'ORG':
                # 机构管理员，只能看本机构数据
                filter_condition = f"{alias}org_code = '{org_code}'"
            else:
                # 普通用户，只能看自己的数据  
                filter_condition = f"{alias}created_by = {user_id}"
            
            # 在WHERE子句中添加过滤条件
            if 'WHERE' in base_sql.upper():
                # 已有WHERE子句，用AND连接
                return f"{base_sql} AND {filter_condition}"
            else:
                # 没有WHERE子句，添加WHERE
                return f"{base_sql} WHERE {filter_condition}"
                
        except Exception as e:
            logger.error(f"应用数据范围过滤失败: {str(e)}")
            return base_sql
    
    def get_permission_by_api(self, api_path: str, method: str) -> Optional[str]:
        """根据API路径和方法获取对应的权限编码"""
        try:
            sql = """
                SELECT permission_code FROM permissions 
                WHERE api_path = :api_path AND api_method = :method AND status = 1
                LIMIT 1
            """
            results = self.db.execute_query(sql, {
                'api_path': api_path,
                'method': method
            })
            return results[0]['permission_code'] if results else None
            
        except Exception as e:
            logger.error(f"获取API权限编码失败: {str(e)}")
            return None
    
    def check_user_permission(self, user_id: int, permission_code: str) -> bool:
        """检查用户是否具有指定权限"""
        try:
            acl_config = self.get_user_acl_config(user_id)
            abilities = acl_config.get('ability', [])
            
            # 超级管理员拥有所有权限
            if '*' in abilities:
                return True
                
            return permission_code in abilities
            
        except Exception as e:
            logger.error(f"检查用户权限失败: {str(e)}")
            return False
    
    def get_filtered_menus(self, abilities: List[str]) -> List[Dict[str, Any]]:
        """根据权限过滤菜单数据"""
        try:
            # 获取菜单数据 - 优先使用数据库菜单，降级到静态菜单
            menus = self.get_database_menus()
            if not menus:
                logger.warning("数据库菜单为空，使用静态菜单结构")
                menus = self.get_static_menu_structure()
            
            def filter_menu_recursive(menu_items: List[Dict], user_abilities: List[str]) -> List[Dict]:
                filtered_menus = []
                
                for menu in menu_items:
                    # 检查菜单权限
                    menu_permission = self.get_menu_permission_code(menu.get('link', ''))
                    
                    # 超级管理员或具有菜单权限的用户可以访问
                    if '*' in user_abilities or not menu_permission or menu_permission in user_abilities:
                        filtered_menu = menu.copy()
                        
                        # 递归过滤子菜单
                        if 'children' in menu and menu['children']:
                            filtered_children = filter_menu_recursive(menu['children'], user_abilities)
                            filtered_menu['children'] = filtered_children
                        
                        filtered_menus.append(filtered_menu)
                
                return filtered_menus
            
            return filter_menu_recursive(menus, abilities)
            
        except Exception as e:
            logger.error(f"过滤菜单数据失败: {str(e)}")
            return self.get_default_menus()
    
    def get_default_menus(self) -> List[Dict[str, Any]]:
        """获取默认菜单（当数据库菜单无法获取时的降级方案）"""
        return [
            {
                'text': 'AI监控大屏',
                'i18n': 'menu.dashboard',
                'link': '/dashboard',
                'icon': { 'type': 'icon', 'value': 'dashboard' }
            }
        ]
    
    def get_database_menus(self) -> List[Dict[str, Any]]:
        """从数据库获取菜单结构，完全符合ng-alain标准格式"""
        try:
            # 获取所有启用的菜单
            sql = """
                SELECT * FROM sys_menu 
                WHERE status = 1 AND visible = 1
                ORDER BY order_num
            """
            menus = self.db.execute_query(sql, {})
            
            if not menus:
                return []
            
            # 构建菜单树
            menu_map = {}
            
            # 第一遍：创建所有菜单项
            for menu in menus:
                menu_item = {
                    'text': menu['name'],  # 直接使用数据库中的中文名称，不使用国际化
                    'children': []
                }
                
                # 设置图标（使用字符串格式，符合ng-alain标准）
                if menu.get('icon') and menu['icon'] != '#':
                    menu_item['icon'] = menu['icon']
                
                # 设置路径
                if menu.get('path'):
                    menu_item['link'] = menu['path']
                
                # 顶级菜单设置为group（除非有路径）
                if menu.get('parent_id') is None and not menu.get('path'):
                    menu_item['group'] = True
                    menu_item['hideInBreadcrumb'] = True
                
                menu_map[menu['id']] = menu_item
            
            # 第二遍：构建树形结构
            tree = []
            for menu in menus:
                menu_item = menu_map[menu['id']]
                parent_id = menu['parent_id']
                
                if parent_id and parent_id in menu_map:
                    menu_map[parent_id]['children'].append(menu_item)
                else:
                    tree.append(menu_item)
            
            # 第三遍：清理空的children
            def clean_empty_children(items):
                for item in items:
                    if item['children']:
                        clean_empty_children(item['children'])
                    else:
                        del item['children']
            
            for item in tree:
                if item.get('children'):
                    clean_empty_children([item])
                elif not item.get('link'):
                    # 没有子菜单且没有链接的菜单项，移除children属性
                    if 'children' in item:
                        del item['children']
            
            # 包装在主导航分组中，符合ng-alain标准
            if tree:
                wrapped_tree = [
                    {
                        'text': '洞察魔方',
                        'group': True,
                        'hideInBreadcrumb': True,
                        'children': tree
                    }
                ]
                return wrapped_tree
            
            return tree
            
        except Exception as e:
            logger.error(f"从数据库获取菜单失败: {str(e)}")
            return []
    
    def get_menu_permission_code(self, menu_path: str) -> Optional[str]:
        """根据菜单路径获取权限编码"""
        menu_permission_map = {
            '/dashboard': 'MENU_DASHBOARD',
            '/workspace': 'MENU_WORKSPACE',
            '/workspace/workbench': 'MENU_WORKSPACE_WORKBENCH',
            '/workspace/report': 'MENU_WORKSPACE_REPORT',
            '/workspace/monitor': 'MENU_WORKSPACE_MONITOR',
            '/ai-engine': 'MENU_AI_ENGINE',
            '/ai-engine/ask-data': 'MENU_AI_ENGINE_ASK_DATA',
            '/ai-engine/knowledge-base': 'MENU_AI_ENGINE_KNOWLEDGE_BASE',
            '/ai-engine/datasource': 'MENU_AI_ENGINE_DATASOURCE',
            '/ai-engine/llmmanage': 'MENU_AI_ENGINE_LLMMANAGE',
            '/ai-engine/multimodal': 'MENU_AI_ENGINE_MULTIMODAL',
            '/sys': 'MENU_SYS',
            '/sys/user': 'MENU_SYS_USER',
            '/sys/org': 'MENU_SYS_ORG',
            '/sys/role': 'MENU_SYS_ROLE',
            '/sys/permission': 'MENU_SYS_PERMISSION',
            '/sys/workflow': 'MENU_SYS_WORKFLOW',
            '/sys/message': 'MENU_SYS_MESSAGE'
        }
        return menu_permission_map.get(menu_path)
    
    def get_static_menu_structure(self) -> List[Dict[str, Any]]:
        """获取静态菜单结构，符合ng-alain Menu接口标准"""
        return [
            {
                'text': '洞察魔方',
                'group': True,
                'hideInBreadcrumb': True,
                'children': [
                    {
                        'text': 'AI监控大屏',
                        'i18n': 'menu.dashboard',
                        'link': '/dashboard',
                        'icon': { 'type': 'icon', 'value': 'dashboard' }
                    },
                    {
                        'text': '工作台',
                        'i18n': 'menu.workspace',
                        'icon': { 'type': 'icon', 'value': 'appstore' },
                        'children': [
                            {
                                'text': '个人工作台',
                                'i18n': 'menu.workspace.workbench',
                                'link': '/workspace/workbench',
                                'icon': { 'type': 'icon', 'value': 'laptop' }
                            },
                            {
                                'text': '工作报表',
                                'i18n': 'menu.workspace.report',
                                'link': '/workspace/report',
                                'icon': { 'type': 'icon', 'value': 'bar-chart' }
                            },
                            {
                                'text': '系统监控',
                                'i18n': 'menu.workspace.monitor',
                                'link': '/workspace/monitor',
                                'icon': { 'type': 'icon', 'value': 'monitor' }
                            }
                        ]
                    },
                    {
                        'text': 'AI引擎',
                        'i18n': 'menu.ai-engine',
                        'icon': { 'type': 'icon', 'value': 'robot' },
                        'children': [
                            {
                                'text': 'AI问答',
                                'i18n': 'menu.ai-engine.ask-data',
                                'link': '/ai-engine/ask-data',
                                'icon': { 'type': 'icon', 'value': 'message' }
                            },
                            {
                                'text': '知识库',
                                'i18n': 'menu.ai-engine.knowledge-base',
                                'link': '/ai-engine/knowledge-base',
                                'icon': { 'type': 'icon', 'value': 'database' }
                            },
                            {
                                'text': '数据源管理',
                                'i18n': 'menu.ai-engine.datasource',
                                'link': '/ai-engine/datasource',
                                'icon': { 'type': 'icon', 'value': 'api' }
                            },
                            {
                                'text': '大模型管理',
                                'i18n': 'menu.ai-engine.llmmanage',
                                'link': '/ai-engine/llmmanage',
                                'icon': { 'type': 'icon', 'value': 'deployment-unit' }
                            },
                            {
                                'text': '多模态管理',
                                'i18n': 'menu.ai-engine.multimodal',
                                'link': '/ai-engine/multimodal',
                                'icon': { 'type': 'icon', 'value': 'experiment' }
                            }
                        ]
                    }
                ]
            },
            {
                'text': '系统管理',
                'i18n': 'menu.sys',
                'group': True,
                'hideInBreadcrumb': True,
                'children': [
                    {
                        'text': '系统管理',
                        'i18n': 'menu.sys.admin',
                        'icon': { 'type': 'icon', 'value': 'setting' },
                        'children': [
                            {
                                'text': '用户管理',
                                'i18n': 'menu.sys.user',
                                'link': '/sys/user',
                                'icon': { 'type': 'icon', 'value': 'user' }
                            },
                            {
                                'text': '机构管理',
                                'i18n': 'menu.sys.org',
                                'link': '/sys/org',
                                'icon': { 'type': 'icon', 'value': 'cluster' }
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
                                'text': '工作流管理',
                                'i18n': 'menu.sys.workflow',
                                'link': '/sys/workflow',
                                'icon': { 'type': 'icon', 'value': 'cluster' }
                            },
                            {
                                'text': '消息管理',
                                'i18n': 'menu.sys.message',
                                'link': '/sys/message',
                                'icon': { 'type': 'icon', 'value': 'message' }
                            }
                        ]
                    }
                ]
            },
            {
                'text': '客服服务',
                'i18n': 'menu.customer-service',
                'group': True,
                'hideInBreadcrumb': True,
                'children': [
                    {
                        'text': '客服服务',
                        'i18n': 'menu.customer-service.main',
                        'icon': { 'type': 'icon', 'value': 'customer-service' },
                        'children': [
                            {
                                'text': '客服仪表板',
                                'i18n': 'menu.customer-service.dashboard',
                                'link': '/customer-service/dashboard',
                                'icon': { 'type': 'icon', 'value': 'dashboard' }
                            },
                            {
                                'text': '客服工作台',
                                'i18n': 'menu.customer-service.workbench',
                                'link': '/customer-service/workbench',
                                'icon': { 'type': 'icon', 'value': 'monitor' }
                            },
                            {
                                'text': '服务工单详情',
                                'i18n': 'menu.customer-service.order-detail',
                                'link': '/customer-service/order-detail',
                                'icon': { 'type': 'icon', 'value': 'file-text' }
                            }
                        ]
                    }
                ]
            }
        ]
    
    def get_default_menus(self) -> List[Dict[str, Any]]:
        """获取默认菜单（最小权限）"""
        return [
            {
                'text': '洞察魔方',
                'group': True,
                'hideInBreadcrumb': True,
                'children': [
                    {
                        'text': 'AI监控大屏',
                        'i18n': 'menu.dashboard',
                        'link': '/dashboard',
                        'icon': { 'type': 'icon', 'value': 'dashboard' }
                    }
                ]
            }
        ]

# 全局实例
_enhanced_permission_service_instance = None

def get_enhanced_permission_service_instance():
    """获取增强权限服务单例"""
    global _enhanced_permission_service_instance
    if _enhanced_permission_service_instance is None:
        _enhanced_permission_service_instance = EnhancedPermissionService()
    return _enhanced_permission_service_instance 