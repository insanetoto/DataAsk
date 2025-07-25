"""
菜单服务模块
提供菜单管理相关的业务逻辑
"""
import logging
from typing import Dict, Any, List, Optional
from tools.database import get_database_service
from tools.exceptions import (
    ValidationException, BusinessException,
    DatabaseException
)

logger = logging.getLogger(__name__)

class MenuService:
    """菜单服务类"""
    
    def __init__(self):
        self.db = get_database_service()
    
    def get_user_menus(self, user_id: int) -> Dict[str, Any]:
        """
        获取用户的菜单列表
        
        Args:
            user_id: 用户ID
        
        Returns:
            Dict:
                success: 是否成功
                data: 菜单列表数据
                error: 错误信息
        """
        try:
            # 获取用户的菜单
            menu_sql = """
                SELECT DISTINCT m.*
                FROM sys_menu m
                INNER JOIN sys_user_menu um ON m.id = um.menu_id
                WHERE um.user_id = :user_id
                AND m.status = 1
                ORDER BY m.order_num
            """
            menus = self.db.execute_query(menu_sql, {'user_id': user_id})
            
            # 构建树形结构
            menu_map = {menu['id']: dict(menu, children=[]) for menu in menus}
            tree = []
            
            for menu in menus:
                # 转换为前端需要的格式，适配数据库字段名，移除国际化支持
                menu_item = {
                    'text': menu['name'],  # 直接使用数据库中的中文名称
                    'group': menu['type'] == 'M' and menu.get('parent_id') is None,  # M表示菜单，顶级菜单设为group
                    'hideInBreadcrumb': False,
                    'children': [],
                }
                
                # 如果有路径，设置链接
                if menu.get('path'):
                    menu_item['link'] = menu['path']
                
                # 如果有图标，设置图标
                if menu.get('icon') and menu['icon'] != '#':
                    # 转换anticon-前缀的图标格式
                    icon_value = menu['icon'].replace('anticon-', '') if menu['icon'].startswith('anticon-') else menu['icon']
                    menu_item['icon'] = {'type': 'icon', 'value': icon_value}
                
                parent_id = menu['parent_id']
                if parent_id and parent_id in menu_map:
                    if 'children' not in menu_map[parent_id]:
                        menu_map[parent_id]['children'] = []
                    menu_map[parent_id]['children'].append(menu_item)
                else:
                    tree.append(menu_item)
            
            return {
                'success': True,
                'data': tree,
                'error': None
            }
            
        except Exception as e:
            logger.error(f"获取用户菜单失败: {str(e)}")
            return {
                'success': False,
                'data': None,
                'error': str(e)
            }
    
    def get_menus_list(
        self,
        page: int = 1,
        page_size: int = 10,
        keyword: str = '',
        status: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        获取菜单列表
        
        Args:
            page: 页码
            page_size: 每页数量
            keyword: 搜索关键词
            status: 菜单状态
        
        Returns:
            菜单列表数据
        """
        try:
            # 构建查询条件
            conditions = []
            params = {}
            
            if keyword:
                conditions.append("(menu_code LIKE :keyword_code OR menu_name LIKE :keyword_name)")
                params['keyword_code'] = f"%{keyword}%"
                params['keyword_name'] = f"%{keyword}%"
            
            if status is not None:
                conditions.append("status = :status")
                params['status'] = status
            
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            
            # 计算分页
            offset = (page - 1) * page_size
            params['limit'] = page_size
            params['offset'] = offset
            
            # 查询总数
            count_sql = f"SELECT COUNT(*) as total FROM sys_menu WHERE {where_clause}"
            total_result = self.db.execute_query(count_sql, params)
            total = total_result[0]['total'] if total_result else 0
            
            # 查询数据
            sql = f"""
                SELECT m.*, p.menu_name as parent_name
                FROM sys_menu m
                LEFT JOIN sys_menu p ON m.parent_id = p.id
                WHERE {where_clause}
                ORDER BY m.order_num, m.created_at DESC
                LIMIT :limit OFFSET :offset
            """
            
            menus = self.db.execute_query(sql, params)
            
            return {
                'list': menus,
                'total': total,
                'page': page,
                'page_size': page_size
            }
            
        except Exception as e:
            logger.error(f"获取菜单列表失败: {str(e)}")
            raise DatabaseException("获取菜单列表失败")
    
    def get_menu_by_id(self, menu_id: int) -> Dict[str, Any]:
        """
        根据ID获取菜单信息
        
        Args:
            menu_id: 菜单ID
        
        Returns:
            菜单信息
        """
        try:
            sql = """
                SELECT m.*, p.menu_name as parent_name
                FROM sys_menu m
                LEFT JOIN sys_menu p ON m.parent_id = p.id
                WHERE m.id = :menu_id
            """
            menu_results = self.db.execute_query(sql, {'menu_id': menu_id})
            
            if not menu_results:
                raise BusinessException("菜单不存在")
            
            return menu_results[0]
            
        except BusinessException:
            raise
        except Exception as e:
            logger.error(f"获取菜单信息失败: {str(e)}")
            raise DatabaseException("获取菜单信息失败")
    
    def get_menu_by_code(self, menu_code: str) -> Dict[str, Any]:
        """
        根据编码获取菜单信息
        
        Args:
            menu_code: 菜单编码
        
        Returns:
            菜单信息
        """
        try:
            sql = """
                SELECT m.*, p.menu_name as parent_name
                FROM sys_menu m
                LEFT JOIN sys_menu p ON m.parent_id = p.id
                WHERE m.menu_code = :menu_code
            """
            menu_results = self.db.execute_query(sql, {'menu_code': menu_code})
            
            if not menu_results:
                raise BusinessException("菜单不存在")
            
            return menu_results[0]
            
        except BusinessException:
            raise
        except Exception as e:
            logger.error(f"获取菜单信息失败: {str(e)}")
            raise DatabaseException("获取菜单信息失败")
    
    def create_menu(self, menu_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建菜单
        
        Args:
            menu_data: 菜单数据
        
        Returns:
            创建的菜单信息
        """
        try:
            # 验证必要字段
            required_fields = ['menu_name', 'menu_code', 'menu_type']
            for field in required_fields:
                if not menu_data.get(field):
                    raise ValidationException(f"缺少必要字段: {field}")
            
            # 检查菜单编码是否已存在
            if self.check_menu_code_exists(menu_data['menu_code']):
                raise BusinessException("菜单编码已存在")
            
            # 检查父菜单是否存在
            if menu_data.get('parent_id'):
                parent_menu = self.get_menu_by_id(menu_data['parent_id'])
                if not parent_menu:
                    raise BusinessException("父菜单不存在")
            
            # 插入数据
            sql = """
                INSERT INTO sys_menu (
                    menu_code, menu_name, menu_type, parent_id,
                    route_path, component, icon, order_num,
                    status, remark, created_by
                ) VALUES (
                    :menu_code, :menu_name, :menu_type, :parent_id,
                    :route_path, :component, :icon, :order_num,
                    :status, :remark, :created_by
                )
            """
            params = {
                'menu_code': menu_data['menu_code'],
                'menu_name': menu_data['menu_name'],
                'menu_type': menu_data['menu_type'],
                'parent_id': menu_data.get('parent_id'),
                'route_path': menu_data.get('route_path'),
                'component': menu_data.get('component'),
                'icon': menu_data.get('icon'),
                'order_num': menu_data.get('sort_order', 0),
                'status': menu_data.get('status', 1),
                'remark': menu_data.get('remark'),
                'created_by': menu_data.get('created_by')
            }
            
            menu_id = self.db.execute_update(sql, params)
            
            # 返回创建的菜单信息
            return self.get_menu_by_id(menu_id)
            
        except (ValidationException, BusinessException):
            raise
        except Exception as e:
            logger.error(f"创建菜单失败: {str(e)}")
            raise DatabaseException("创建菜单失败")
    
    def update_menu(self, menu_id: int, menu_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        更新菜单信息
        
        Args:
            menu_id: 菜单ID
            menu_data: 菜单数据
        
        Returns:
            更新后的菜单信息
        """
        try:
            # 检查菜单是否存在
            existing_menu = self.get_menu_by_id(menu_id)
            if not existing_menu:
                raise BusinessException("菜单不存在")
            
            # 如果更新菜单编码,检查是否已存在
            if 'menu_code' in menu_data and menu_data['menu_code'] != existing_menu['menu_code']:
                if self.check_menu_code_exists(menu_data['menu_code']):
                    raise BusinessException("菜单编码已存在")
            
            # 检查父菜单是否存在
            if menu_data.get('parent_id'):
                parent_menu = self.get_menu_by_id(menu_data['parent_id'])
                if not parent_menu:
                    raise BusinessException("父菜单不存在")
                # 检查是否会形成循环引用
                if self.would_create_cycle(existing_menu['id'], menu_data['parent_id']):
                    raise BusinessException("不能将菜单设置为其子菜单的父菜单")
            
            # 构建更新SQL
            update_fields = []
            params = {}
            for key, value in menu_data.items():
                if key not in ['id', 'created_at', 'created_by']:
                    update_fields.append(f"{key} = :{key}")
                    params[key] = value
            
            if not update_fields:
                raise ValidationException("没有需要更新的字段")
            
            sql = f"""
                UPDATE sys_menu
                SET {', '.join(update_fields)}
                WHERE id = :menu_id
            """
            params['menu_id'] = menu_id
            
            self.db.execute_update(sql, params)
            
            # 返回更新后的菜单信息
            return self.get_menu_by_id(menu_id)
            
        except (ValidationException, BusinessException):
            raise
        except Exception as e:
            logger.error(f"更新菜单失败: {str(e)}")
            raise DatabaseException("更新菜单失败")
    
    def delete_menu(self, menu_id: int) -> bool:
        """
        删除菜单
        
        Args:
            menu_id: 菜单ID
        
        Returns:
            是否删除成功
        """
        try:
            # 检查菜单是否存在
            menu = self.get_menu_by_id(menu_id)
            if not menu:
                raise BusinessException("菜单不存在")
            
            # 检查是否有子菜单
            if self.has_children(menu_id):
                raise BusinessException("该菜单下存在子菜单,不能删除")
            
            # 执行删除
            sql = "DELETE FROM sys_menu WHERE id = :menu_id"
            self.db.execute_update(sql, {'menu_id': menu_id})
            
            return True
            
        except BusinessException:
            raise
        except Exception as e:
            logger.error(f"删除菜单失败: {str(e)}")
            raise DatabaseException("删除菜单失败")
    
    def get_menu_tree(self, root_menu_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        获取菜单树形结构
        
        Args:
            root_menu_id: 根菜单ID,为None时返回全部
        
        Returns:
            菜单树形数据
        """
        try:
            # 获取所有菜单
            sql = "SELECT * FROM sys_menu WHERE status = 1"
            params = {}
            if root_menu_id:
                sql += " AND (id = :root_id OR parent_id = :root_id)"
                params['root_id'] = root_menu_id
            
            menus = self.db.execute_query(sql, params)
            
            # 构建树形结构
            menu_map = {menu['id']: dict(menu, children=[]) for menu in menus}
            tree = []
            
            for menu in menus:
                parent_id = menu['parent_id']
                if parent_id and parent_id in menu_map:
                    menu_map[parent_id]['children'].append(menu_map[menu['id']])
                else:
                    tree.append(menu_map[menu['id']])
            
            return tree
            
        except Exception as e:
            logger.error(f"获取菜单树失败: {str(e)}")
            raise DatabaseException("获取菜单树失败")
    
    def check_menu_code_exists(self, menu_code: str) -> bool:
        """检查菜单编码是否已存在"""
        sql = "SELECT COUNT(*) as count FROM sys_menu WHERE menu_code = :menu_code"
        result = self.db.execute_query(sql, {'menu_code': menu_code})
        return result[0]['count'] > 0
    
    def has_children(self, menu_id: int) -> bool:
        """检查是否有子菜单"""
        sql = "SELECT COUNT(*) as count FROM sys_menu WHERE parent_id = :menu_id"
        result = self.db.execute_query(sql, {'menu_id': menu_id})
        return result[0]['count'] > 0
    
    def would_create_cycle(self, menu_id: int, new_parent_id: int) -> bool:
        """检查是否会形成循环引用"""
        current = new_parent_id
        while current:
            if current == menu_id:
                return True
            parent = self.get_menu_by_id(current)
            current = parent['parent_id'] if parent else None
        return False

# 菜单服务单例
_menu_service = None

def get_menu_service_instance() -> MenuService:
    """获取菜单服务实例"""
    global _menu_service
    if _menu_service is None:
        _menu_service = MenuService()
    return _menu_service 