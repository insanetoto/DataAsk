# -*- coding: utf-8 -*-
"""
权限系统初始化脚本
清除历史数据并重新配置整个权限体系
"""
import sys
import os
import bcrypt
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.database import get_database_service, init_database_service
from config.base_config import Config
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PermissionSystemInitializer:
    def __init__(self):
        # 初始化数据库服务
        config = Config()
        init_database_service(config)
        self.db = get_database_service()
        
    def clear_existing_data(self):
        """清除现有数据"""
        logger.info("开始清除历史数据...")
        
        # 禁用外键检查
        self.db.execute_update("SET FOREIGN_KEY_CHECKS = 0;")
        
        clear_sql = [
            "DELETE FROM role_permissions;",
            "DELETE FROM user_sessions;", 
            "DELETE FROM operation_audit;",
            "DELETE FROM sys_user_menu;",
            "DELETE FROM sys_menu;",
            "DELETE FROM users;",
            "DELETE FROM roles;",
            "DELETE FROM permissions;",
            "DELETE FROM permission_templates;",
            "DELETE FROM organizations;",
            # 清除工作流相关表
            "DELETE FROM sys_workflow;",
        ]
        
        for sql in clear_sql:
            try:
                self.db.execute_update(sql)
                logger.info(f"执行清理: {sql}")
            except Exception as e:
                logger.warning(f"清理失败: {sql}, 错误: {e}")
        
        # 重新启用外键检查
        self.db.execute_update("SET FOREIGN_KEY_CHECKS = 1;")
                
        logger.info("历史数据清除完成")
    
    def init_organizations(self):
        """初始化机构层级结构"""
        logger.info("开始初始化机构结构...")
        
        organizations = [
            {
                'org_code': '0500000000',
                'org_name': '南方电网集团',
                'parent_org_code': None,
                'level_depth': 1,
                'contact_person': '集团管理员',
                'contact_phone': '020-12345678',
                'contact_email': 'admin@csg.cn'
            },
            {
                'org_code': '0501000000', 
                'org_name': '云南电网公司',
                'parent_org_code': '0500000000',
                'level_depth': 2,
                'contact_person': '云南管理员',
                'contact_phone': '0871-12345678',
                'contact_email': 'admin@yn.csg.cn'
            },
            {
                'org_code': '0501010000',
                'org_name': '昆明供电局', 
                'parent_org_code': '0501000000',
                'level_depth': 3,
                'contact_person': '昆明管理员',
                'contact_phone': '0871-87654321',
                'contact_email': 'admin@km.yn.csg.cn'
            },
            {
                'org_code': '0501010100',
                'org_name': '昆明供电局官渡分局',
                'parent_org_code': '0501010000', 
                'level_depth': 4,
                'contact_person': '官渡管理员',
                'contact_phone': '0871-67891234',
                'contact_email': 'admin@gd.km.yn.csg.cn'
            },
            {
                'org_code': '0501010101',
                'org_name': '昆明供电局官渡分局小板桥供电所',
                'parent_org_code': '0501010100',
                'level_depth': 5,
                'contact_person': '小板桥管理员', 
                'contact_phone': '0871-56789012',
                'contact_email': 'admin@xbq.gd.km.yn.csg.cn'
            }
        ]
        
        for org in organizations:
            sql = """
                INSERT INTO organizations (
                    org_code, org_name, parent_org_code, level_depth,
                    contact_person, contact_phone, contact_email,
                    status, created_at, updated_at
                ) VALUES (
                    :org_code, :org_name, :parent_org_code, :level_depth,
                    :contact_person, :contact_phone, :contact_email,
                    1, NOW(), NOW()
                )
            """
            self.db.execute_update(sql, org)
            logger.info(f"创建机构: {org['org_name']} ({org['org_code']})")
            
        logger.info("机构结构初始化完成")
    
    def init_roles(self):
        """初始化角色"""
        logger.info("开始初始化角色...")
        
        roles = [
            {
                'role_code': 'SUPER_ADMIN',
                'role_name': '超级管理员',
                'role_level': 1,
                'data_scope': 'ALL',
                'is_system_role': 1,
                'description': '系统超级管理员，拥有所有权限'
            },
            {
                'role_code': 'ORG_ADMIN', 
                'role_name': '机构管理员',
                'role_level': 2,
                'data_scope': 'ORG',
                'is_system_role': 0,
                'description': '机构管理员，管理本机构范围内的所有资源'
            },
            {
                'role_code': 'NORMAL_USER',
                'role_name': '普通用户',
                'role_level': 3, 
                'data_scope': 'SELF',
                'is_system_role': 0,
                'description': '普通用户，只能访问个人相关数据'
            }
        ]
        
        for role in roles:
            sql = """
                INSERT INTO roles (
                    role_code, role_name, role_level, data_scope, 
                    is_system_role, status, description, created_at, updated_at
                ) VALUES (
                    :role_code, :role_name, :role_level, :data_scope,
                    :is_system_role, 1, :description, NOW(), NOW()
                )
            """
            self.db.execute_update(sql, role)
            logger.info(f"创建角色: {role['role_name']} ({role['role_code']})")
            
        logger.info("角色初始化完成")
    
    def init_permissions(self):
        """初始化权限资源"""
        logger.info("开始初始化权限资源...")
        
        permissions = [
            # 菜单权限
            ('MENU_DASHBOARD', 'MENU', '仪表盘菜单', '/dashboard', 'GET'),
            ('MENU_WORKSPACE', 'MENU', '工作台菜单', '/workspace', 'GET'),
            ('MENU_WORKSPACE_WORKBENCH', 'MENU', '个人工作台菜单', '/workspace/workbench', 'GET'),
            ('MENU_WORKSPACE_REPORT', 'MENU', '工作报表菜单', '/workspace/report', 'GET'),
            ('MENU_WORKSPACE_MONITOR', 'MENU', '系统监控菜单', '/workspace/monitor', 'GET'),
            ('MENU_AI_ENGINE', 'MENU', 'AI引擎菜单', '/ai-engine', 'GET'),
            ('MENU_AI_ENGINE_ASK_DATA', 'MENU', 'AI问答菜单', '/ai-engine/ask-data', 'GET'),
            ('MENU_AI_ENGINE_KNOWLEDGE_BASE', 'MENU', '知识库菜单', '/ai-engine/knowledge-base', 'GET'),
            ('MENU_AI_ENGINE_DATASOURCE', 'MENU', '数据源管理菜单', '/ai-engine/datasource', 'GET'),
            ('MENU_AI_ENGINE_LLMMANAGE', 'MENU', '大模型管理菜单', '/ai-engine/llmmanage', 'GET'),
            ('MENU_AI_ENGINE_MULTIMODAL', 'MENU', '多模态管理菜单', '/ai-engine/multimodal', 'GET'),
            ('MENU_SYS', 'MENU', '系统管理菜单', '/sys', 'GET'),
            ('MENU_SYS_USER', 'MENU', '用户管理菜单', '/sys/user', 'GET'),
            ('MENU_SYS_ORG', 'MENU', '机构管理菜单', '/sys/org', 'GET'),
            ('MENU_SYS_ROLE', 'MENU', '角色管理菜单', '/sys/role', 'GET'),
            ('MENU_SYS_PERMISSION', 'MENU', '权限管理菜单', '/sys/permission', 'GET'),
            ('MENU_SYS_WORKFLOW', 'MENU', '工作流管理菜单', '/sys/workflow', 'GET'),
            ('MENU_SYS_MESSAGE', 'MENU', '消息管理菜单', '/sys/message', 'GET'),
            
            # API权限
            ('USER_LIST', 'API', '用户列表查询', '/api/users', 'GET'),
            ('USER_CREATE', 'API', '用户创建', '/api/users', 'POST'),
            ('USER_UPDATE', 'API', '用户修改', '/api/users/{id}', 'PUT'),
            ('USER_DELETE', 'API', '用户删除', '/api/users/{id}', 'DELETE'),
            ('USER_VIEW', 'API', '用户详情查看', '/api/users/{id}', 'GET'),
            ('USER_RESET_PASSWORD', 'API', '重置用户密码', '/api/users/{id}/reset-password', 'PUT'),
            
            ('ORG_LIST', 'API', '机构列表查询', '/api/organizations', 'GET'),
            ('ORG_CREATE', 'API', '机构创建', '/api/organizations', 'POST'),
            ('ORG_UPDATE', 'API', '机构修改', '/api/organizations/{id}', 'PUT'),
            ('ORG_DELETE', 'API', '机构删除', '/api/organizations/{id}', 'DELETE'),
            ('ORG_VIEW', 'API', '机构详情查看', '/api/organizations/{id}', 'GET'),
            ('ORG_TREE', 'API', '机构树查询', '/api/organizations/tree', 'GET'),
            
            ('ROLE_LIST', 'API', '角色列表查询', '/api/roles', 'GET'),
            ('ROLE_CREATE', 'API', '角色创建', '/api/roles', 'POST'),
            ('ROLE_UPDATE', 'API', '角色修改', '/api/roles/{id}', 'PUT'),
            ('ROLE_DELETE', 'API', '角色删除', '/api/roles/{id}', 'DELETE'),
            ('ROLE_VIEW', 'API', '角色详情查看', '/api/roles/{id}', 'GET'),
            
            ('PERMISSION_LIST', 'API', '权限列表查询', '/api/permissions', 'GET'),
            ('PERMISSION_CREATE', 'API', '权限创建', '/api/permissions', 'POST'),
            ('PERMISSION_UPDATE', 'API', '权限修改', '/api/permissions/{id}', 'PUT'),
            ('PERMISSION_DELETE', 'API', '权限删除', '/api/permissions/{id}', 'DELETE'),
            ('PERMISSION_VIEW', 'API', '权限详情查看', '/api/permissions/{id}', 'GET'),
            
            ('WORKFLOW_LIST', 'API', '工作流列表查询', '/api/workflows', 'GET'),
            ('WORKFLOW_CREATE', 'API', '工作流创建', '/api/workflows', 'POST'),
            ('WORKFLOW_UPDATE', 'API', '工作流修改', '/api/workflows/{id}', 'PUT'),
            ('WORKFLOW_DELETE', 'API', '工作流删除', '/api/workflows/{id}', 'DELETE'),
            ('WORKFLOW_EXECUTE', 'API', '工作流执行', '/api/workflows/{id}/execute', 'POST'),
            
            ('MESSAGE_LIST', 'API', '消息列表查询', '/api/messages', 'GET'),
            ('MESSAGE_SEND', 'API', '消息发送', '/api/messages', 'POST'),
            ('MESSAGE_READ', 'API', '消息已读', '/api/messages/{id}/read', 'PUT'),
            ('MESSAGE_DELETE', 'API', '消息删除', '/api/messages/{id}', 'DELETE'),
            
            # 按钮权限
            ('BTN_USER_ADD', 'BUTTON', '用户新增按钮', '/button/user/add', 'BUTTON'),
            ('BTN_USER_EDIT', 'BUTTON', '用户编辑按钮', '/button/user/edit', 'BUTTON'),
            ('BTN_USER_DELETE', 'BUTTON', '用户删除按钮', '/button/user/delete', 'BUTTON'),
            ('BTN_USER_RESET_PWD', 'BUTTON', '重置密码按钮', '/button/user/reset-pwd', 'BUTTON'),
            ('BTN_ORG_ADD', 'BUTTON', '机构新增按钮', '/button/org/add', 'BUTTON'),
            ('BTN_ORG_EDIT', 'BUTTON', '机构编辑按钮', '/button/org/edit', 'BUTTON'),
            ('BTN_ORG_DELETE', 'BUTTON', '机构删除按钮', '/button/org/delete', 'BUTTON'),
            ('BTN_ROLE_ADD', 'BUTTON', '角色新增按钮', '/button/role/add', 'BUTTON'),
            ('BTN_ROLE_EDIT', 'BUTTON', '角色编辑按钮', '/button/role/edit', 'BUTTON'),
            ('BTN_ROLE_DELETE', 'BUTTON', '角色删除按钮', '/button/role/delete', 'BUTTON'),
        ]
        
        for perm_code, perm_type, perm_name, api_path, api_method in permissions:
            sql = """
                INSERT INTO permissions (
                    permission_code, permission_type, permission_name,
                    api_path, api_method, status, created_at, updated_at
                ) VALUES (
                    :permission_code, :permission_type, :permission_name,
                    :api_path, :api_method, 1, NOW(), NOW()
                )
            """
            self.db.execute_update(sql, {
                'permission_code': perm_code,
                'permission_type': perm_type,
                'permission_name': perm_name,
                'api_path': api_path,
                'api_method': api_method
            })
            
        logger.info(f"权限资源初始化完成，共创建 {len(permissions)} 个权限")
    
    def init_permission_templates(self):
        """初始化权限模板"""
        logger.info("开始初始化权限模板...")
        
        # 超级管理员权限模板（拥有所有权限）
        super_admin_permissions = self.db.execute_query(
            "SELECT permission_code, permission_type FROM permissions"
        )
        
        for perm in super_admin_permissions:
            sql = """
                INSERT INTO permission_templates (
                    role_level, permission_code, permission_type,
                    created_at
                ) VALUES (1, :permission_code, :permission_type, NOW())
            """
            self.db.execute_update(sql, perm)
        
        # 机构管理员权限模板（除超级管理相关外的所有权限）
        org_admin_permissions = [
            # 菜单权限
            'MENU_DASHBOARD', 'MENU_WORKSPACE', 'MENU_WORKSPACE_WORKBENCH', 
            'MENU_WORKSPACE_REPORT', 'MENU_WORKSPACE_MONITOR',
            'MENU_AI_ENGINE', 'MENU_AI_ENGINE_ASK_DATA', 'MENU_AI_ENGINE_KNOWLEDGE_BASE',
            'MENU_AI_ENGINE_DATASOURCE', 'MENU_AI_ENGINE_LLMMANAGE', 'MENU_AI_ENGINE_MULTIMODAL',
            'MENU_SYS', 'MENU_SYS_USER', 'MENU_SYS_ORG', 'MENU_SYS_ROLE',
            'MENU_SYS_WORKFLOW', 'MENU_SYS_MESSAGE',
            
            # API权限
            'USER_LIST', 'USER_CREATE', 'USER_UPDATE', 'USER_DELETE', 'USER_VIEW',
            'ORG_LIST', 'ORG_CREATE', 'ORG_UPDATE', 'ORG_DELETE', 'ORG_VIEW', 'ORG_TREE',
            'ROLE_LIST', 'ROLE_VIEW', 'WORKFLOW_LIST', 'WORKFLOW_CREATE', 'WORKFLOW_UPDATE',
            'WORKFLOW_DELETE', 'WORKFLOW_EXECUTE', 'MESSAGE_LIST', 'MESSAGE_SEND',
            'MESSAGE_READ', 'MESSAGE_DELETE',
            
            # 按钮权限
            'BTN_USER_ADD', 'BTN_USER_EDIT', 'BTN_USER_DELETE', 'BTN_USER_RESET_PWD',
            'BTN_ORG_ADD', 'BTN_ORG_EDIT', 'BTN_ORG_DELETE'
        ]
        
        for perm_code in org_admin_permissions:
            perm_type_result = self.db.execute_query(
                "SELECT permission_type FROM permissions WHERE permission_code = :code",
                {'code': perm_code}
            )
            if perm_type_result:
                sql = """
                    INSERT INTO permission_templates (
                        role_level, permission_code, permission_type,
                        created_at
                    ) VALUES (2, :permission_code, :permission_type, NOW())
                """
                self.db.execute_update(sql, {
                    'permission_code': perm_code,
                    'permission_type': perm_type_result[0]['permission_type']
                })
        
        # 普通用户权限模板（基础查看权限）
        normal_user_permissions = [
            'MENU_DASHBOARD', 'MENU_WORKSPACE', 'MENU_WORKSPACE_WORKBENCH',
            'MENU_AI_ENGINE', 'MENU_AI_ENGINE_ASK_DATA',
            'USER_VIEW', 'MESSAGE_LIST', 'MESSAGE_READ'
        ]
        
        for perm_code in normal_user_permissions:
            perm_type_result = self.db.execute_query(
                "SELECT permission_type FROM permissions WHERE permission_code = :code",
                {'code': perm_code}
            )
            if perm_type_result:
                sql = """
                    INSERT INTO permission_templates (
                        role_level, permission_code, permission_type,
                        created_at
                    ) VALUES (3, :permission_code, :permission_type, NOW())
                """
                self.db.execute_update(sql, {
                    'permission_code': perm_code,
                    'permission_type': perm_type_result[0]['permission_type']
                })
        
        logger.info("权限模板初始化完成")
    
    def create_users(self):
        """创建管理员用户"""
        logger.info("开始创建管理员用户...")
        
        users = [
            {
                'user_code': 'SUPER_ADMIN_001',
                'username': 'SuperAdmin',
                'password': 'superadmin',
                'org_code': '0500000000',  # 南方电网集团
                'role_code': 'SUPER_ADMIN',
                'phone': '13800000000',
                'address': '广州市天河区'
            },
            {
                'user_code': 'ORG_ADMIN_CSG',
                'username': 'admin_csg', 
                'password': 'admin123',
                'org_code': '0500000000',
                'role_code': 'ORG_ADMIN',
                'phone': '13800000001',
                'address': '广州市天河区南方电网大厦'
            },
            {
                'user_code': 'ORG_ADMIN_YN',
                'username': 'admin_yn_csg',
                'password': 'admin123',
                'org_code': '0501000000',
                'role_code': 'ORG_ADMIN',
                'phone': '13800000002', 
                'address': '昆明市五华区云南电网大厦'
            },
            {
                'user_code': 'ORG_ADMIN_KM',
                'username': 'admin_km_yn_csg',
                'password': 'admin123',
                'org_code': '0501010000',
                'role_code': 'ORG_ADMIN',
                'phone': '13800000003',
                'address': '昆明市西山区昆明供电局'
            },
            {
                'user_code': 'ORG_ADMIN_GD',
                'username': 'admin_gd_km_yn_csg', 
                'password': 'admin123',
                'org_code': '0501010100',
                'role_code': 'ORG_ADMIN',
                'phone': '13800000004',
                'address': '昆明市官渡区官渡分局'
            },
            {
                'user_code': 'ORG_ADMIN_XBQ',
                'username': 'admin_xbq_gd_km_yn_csg',
                'password': 'admin123',
                'org_code': '0501010101',
                'role_code': 'ORG_ADMIN',
                'phone': '13800000005',
                'address': '昆明市官渡区小板桥供电所'
            }
        ]
        
        for user_data in users:
            # 获取角色ID
            role_result = self.db.execute_query(
                "SELECT id FROM roles WHERE role_code = :role_code",
                {'role_code': user_data['role_code']}
            )
            
            if not role_result:
                logger.error(f"角色 {user_data['role_code']} 不存在")
                continue
                
            role_id = role_result[0]['id']
            
            # 加密密码
            password_hash = bcrypt.hashpw(
                user_data['password'].encode('utf-8'), 
                bcrypt.gensalt()
            ).decode('utf-8')
            
            sql = """
                INSERT INTO users (
                    user_code, username, password_hash, org_code, role_id,
                    phone, address, status, created_at, updated_at
                ) VALUES (
                    :user_code, :username, :password_hash, :org_code, :role_id,
                    :phone, :address, 1, NOW(), NOW()
                )
            """
            
            self.db.execute_update(sql, {
                'user_code': user_data['user_code'],
                'username': user_data['username'],
                'password_hash': password_hash,
                'org_code': user_data['org_code'],
                'role_id': role_id,
                'phone': user_data['phone'],
                'address': user_data['address']
            })
            
            logger.info(f"创建用户: {user_data['username']} ({user_data['user_code']})")
        
        logger.info("管理员用户创建完成")
    
    def assign_role_permissions(self):
        """分配角色权限"""
        logger.info("开始分配角色权限...")
        
        # 获取所有角色
        roles = self.db.execute_query("SELECT id, role_level FROM roles")
        
        for role in roles:
            role_id = role['id']
            role_level = role['role_level']
            
            # 根据角色级别获取权限模板
            permissions = self.db.execute_query(
                "SELECT permission_code FROM permission_templates WHERE role_level = :level",
                {'level': role_level}
            )
            
            for perm in permissions:
                # 获取权限ID
                perm_result = self.db.execute_query(
                    "SELECT id FROM permissions WHERE permission_code = :code",
                    {'code': perm['permission_code']}
                )
                
                if perm_result:
                    perm_id = perm_result[0]['id']
                    
                    sql = """
                        INSERT INTO role_permissions (
                            role_id, permission_id, created_at
                        ) VALUES (:role_id, :permission_id, NOW())
                    """
                    self.db.execute_update(sql, {
                        'role_id': role_id,
                        'permission_id': perm_id
                    })
            
            logger.info(f"角色 {role_id} 权限分配完成，共分配 {len(permissions)} 个权限")
        
        logger.info("角色权限分配完成")
    
    def init_menu_system(self):
        """初始化菜单系统"""
        logger.info("开始初始化菜单系统...")
        
        menus = [
            {
                'menu_code': 'DASHBOARD',
                'menu_name': 'AI监控大屏',
                'menu_type': 'M',
                'parent_id': None,
                'route_path': '/dashboard',
                'component': None,
                'icon': 'anticon-dashboard',
                'order_num': 1
            },
            {
                'menu_code': 'WORKSPACE',
                'menu_name': '工作台',
                'menu_type': 'M',
                'parent_id': None,
                'route_path': '/workspace',
                'component': None,
                'icon': 'anticon-appstore',
                'order_num': 2
            },
            {
                'menu_code': 'WORKSPACE_WORKBENCH',
                'menu_name': '个人工作台',
                'menu_type': 'M',
                'parent_id': 2,  # 工作台的子菜单
                'route_path': '/workspace/workbench',
                'component': None,
                'icon': None,
                'order_num': 21
            },
            {
                'menu_code': 'WORKSPACE_REPORT',
                'menu_name': '工作报表',
                'menu_type': 'M',
                'parent_id': 2,
                'route_path': '/workspace/report',
                'component': None,
                'icon': None,
                'order_num': 22
            },
            {
                'menu_code': 'WORKSPACE_MONITOR',
                'menu_name': '系统监控',
                'menu_type': 'M',
                'parent_id': 2,
                'route_path': '/workspace/monitor',
                'component': None,
                'icon': None,
                'order_num': 23
            },
            {
                'menu_code': 'AI_ENGINE',
                'menu_name': 'AI引擎',
                'menu_type': 'M',
                'parent_id': None,
                'route_path': '/ai-engine',
                'component': None,
                'icon': 'anticon-robot',
                'order_num': 3
            },
            {
                'menu_code': 'AI_ENGINE_ASK_DATA',
                'menu_name': 'AI问答',
                'menu_type': 'M',
                'parent_id': 6,
                'route_path': '/ai-engine/ask-data',
                'component': None,
                'icon': None,
                'order_num': 31
            },
            {
                'menu_code': 'AI_ENGINE_KNOWLEDGE_BASE',
                'menu_name': '知识库',
                'menu_type': 'M',
                'parent_id': 6,
                'route_path': '/ai-engine/knowledge-base',
                'component': None,
                'icon': None,
                'order_num': 32
            },
            {
                'menu_code': 'AI_ENGINE_DATASOURCE',
                'menu_name': '数据源管理',
                'menu_type': 'M',
                'parent_id': 6,
                'route_path': '/ai-engine/datasource',
                'component': None,
                'icon': None,
                'order_num': 33
            },
            {
                'menu_code': 'AI_ENGINE_LLMMANAGE',
                'menu_name': '大模型管理',
                'menu_type': 'M',
                'parent_id': 6,
                'route_path': '/ai-engine/llmmanage',
                'component': None,
                'icon': None,
                'order_num': 34
            },
            {
                'menu_code': 'AI_ENGINE_MULTIMODAL',
                'menu_name': '多模态管理',
                'menu_type': 'M',
                'parent_id': 6,
                'route_path': '/ai-engine/multimodal',
                'component': None,
                'icon': None,
                'order_num': 35
            },
            {
                'menu_code': 'SYS',
                'menu_name': '系统管理',
                'menu_type': 'M',
                'parent_id': None,
                'route_path': '/sys',
                'component': None,
                'icon': 'anticon-setting',
                'order_num': 4
            },
            {
                'menu_code': 'SYS_USER',
                'menu_name': '用户管理',
                'menu_type': 'M',
                'parent_id': 12,
                'route_path': '/sys/user',
                'component': None,
                'icon': None,
                'order_num': 41
            },
            {
                'menu_code': 'SYS_ORG',
                'menu_name': '机构管理',
                'menu_type': 'M',
                'parent_id': 12,
                'route_path': '/sys/org',
                'component': None,
                'icon': None,
                'order_num': 42
            },
            {
                'menu_code': 'SYS_ROLE',
                'menu_name': '角色管理',
                'menu_type': 'M',
                'parent_id': 12,
                'route_path': '/sys/role',
                'component': None,
                'icon': None,
                'order_num': 43
            },
            {
                'menu_code': 'SYS_PERMISSION',
                'menu_name': '权限管理',
                'menu_type': 'M',
                'parent_id': 12,
                'route_path': '/sys/permission',
                'component': None,
                'icon': None,
                'order_num': 44
            },
            {
                'menu_code': 'SYS_WORKFLOW',
                'menu_name': '工作流管理',
                'menu_type': 'M',
                'parent_id': 12,
                'route_path': '/sys/workflow',
                'component': None,
                'icon': None,
                'order_num': 45
            },
            {
                'menu_code': 'SYS_MESSAGE',
                'menu_name': '消息管理',
                'menu_type': 'M',
                'parent_id': 12,
                'route_path': '/sys/message',
                'component': None,
                'icon': None,
                'order_num': 46
            }
        ]
        
        # 先创建菜单
        for menu in menus:
            sql = """
                INSERT INTO sys_menu (
                    name, type, parent_id, path, component,
                    icon, order_num, status, perms, create_time, update_time
                ) VALUES (
                    :menu_name, :menu_type, :parent_id, :route_path, :component,
                    :icon, :order_num, 1, :menu_code, NOW(), NOW()
                )
            """
            self.db.execute_update(sql, {
                'menu_code': menu['menu_code'],
                'menu_name': menu['menu_name'],
                'menu_type': menu['menu_type'],
                'parent_id': menu['parent_id'],
                'route_path': menu['route_path'],
                'component': menu['component'],
                'icon': menu['icon'],
                'order_num': menu['order_num']
            })
        
        # 为超级管理员和机构管理员分配所有菜单
        users = self.db.execute_query("""
            SELECT u.id, r.role_code 
            FROM users u 
            JOIN roles r ON u.role_id = r.id 
            WHERE r.role_code IN ('SUPER_ADMIN', 'ORG_ADMIN')
        """)
        
        menu_ids = self.db.execute_query("SELECT id FROM sys_menu")
        
        for user in users:
            for menu in menu_ids:
                sql = """
                    INSERT INTO sys_user_menu (user_id, menu_id)
                    VALUES (:user_id, :menu_id)
                """
                self.db.execute_update(sql, {
                    'user_id': user['id'],
                    'menu_id': menu['id']
                })
        
        logger.info("菜单系统初始化完成")
    
    def run_initialization(self):
        """运行完整的初始化流程"""
        try:
            logger.info("=== 开始权限系统全新初始化 ===")
            
            # 1. 清除历史数据
            self.clear_existing_data()
            
            # 2. 初始化机构结构
            self.init_organizations()
            
            # 3. 初始化角色
            self.init_roles()
            
            # 4. 初始化权限资源
            self.init_permissions()
            
            # 5. 初始化权限模板
            self.init_permission_templates()
            
            # 6. 创建管理员用户
            self.create_users()
            
            # 7. 分配角色权限
            self.assign_role_permissions()
            
            # 8. 初始化菜单系统
            self.init_menu_system()
            
            logger.info("=== 权限系统初始化完成 ===")
            
            # 输出用户信息
            self.print_user_info()
            
        except Exception as e:
            logger.error(f"初始化失败: {str(e)}")
            raise
    
    def print_user_info(self):
        """打印用户信息"""
        logger.info("\n=== 创建的用户信息 ===")
        users = self.db.execute_query("""
            SELECT u.username, u.user_code, r.role_name, o.org_name, u.phone
            FROM users u
            JOIN roles r ON u.role_id = r.id 
            JOIN organizations o ON u.org_code = o.org_code
            ORDER BY r.role_level, o.org_code
        """)
        
        for user in users:
            logger.info(f"用户名: {user['username']}")
            logger.info(f"  编码: {user['user_code']}")
            logger.info(f"  角色: {user['role_name']}")
            logger.info(f"  机构: {user['org_name']}")
            logger.info(f"  电话: {user['phone']}")
            logger.info("  ---")

if __name__ == "__main__":
    initializer = PermissionSystemInitializer()
    initializer.run_initialization() 