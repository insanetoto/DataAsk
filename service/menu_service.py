#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import Dict, Any, List, Optional
from tools.database import DatabaseService, get_database_service
from sqlalchemy import text

class MenuService:
    """菜单服务
    
    负责处理系统菜单相关的业务逻辑
    """
    
    def __init__(self, db_service: Optional[DatabaseService] = None):
        """
        初始化菜单服务
        
        Args:
            db_service: 数据库服务实例，如果不提供则使用全局实例
        """
        self.db_service = db_service or get_database_service()
    
    def get_user_menus(self, user_id: int) -> Dict[str, Any]:
        """获取用户菜单列表"""
        try:
            # 查询用户的菜单
            with self.db_service.get_session() as session:
                result = session.execute(
                    text("""
                    SELECT DISTINCT 
                        m.id,
                        m.parent_id,
                        m.name,
                        m.path,
                        m.component,
                        m.type,
                        m.icon,
                        m.order_num,
                        m.perms,
                        m.is_frame,
                        m.visible,
                        m.status
                    FROM sys_menu m
                    INNER JOIN sys_user_menu um ON m.id = um.menu_id
                    WHERE um.user_id = :user_id AND m.status = 1 AND m.visible = 1
                    ORDER BY m.parent_id, m.order_num
                    """),
                    {"user_id": user_id}
                )
                
                # 将行转换为字典
                menus = []
                for row in result:
                    menu_dict = {}
                    for key in row._mapping.keys():
                        menu_dict[key] = getattr(row, key)
                    menus.append(menu_dict)
                
                if not menus:
                    return {
                        'success': False,
                        'error': '未找到用户菜单'
                    }
                
                # 构建菜单树
                menu_tree = self._build_menu_tree(menus)
                
                return {
                    'success': True,
                    'data': menu_tree
                }
        except Exception as e:
            return {
                'success': False,
                'error': f'获取用户菜单失败: {str(e)}'
            }
    
    def _build_menu_tree(self, menus: List[Dict[str, Any]], parent_id: int = 0) -> List[Dict[str, Any]]:
        """构建菜单树结构"""
        tree = []
        for menu in menus:
            if menu['parent_id'] == parent_id:
                children = self._build_menu_tree(menus, menu['id'])
                menu_item = {
                    'id': menu['id'],
                    'name': menu['name'],
                    'path': menu['path'],
                    'component': menu['component'],
                    'type': menu['type'],
                    'icon': menu['icon'],
                    'orderNum': menu['order_num'],
                    'perms': menu['perms'],
                    'isFrame': bool(menu['is_frame']),
                    'visible': bool(menu['visible'])
                }
                if children:
                    menu_item['children'] = children
                tree.append(menu_item)
        return tree

def get_menu_service():
    """获取菜单服务实例"""
    return MenuService() 