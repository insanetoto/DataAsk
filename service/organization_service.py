# -*- coding: utf-8 -*-
"""
机构服务模块
提供机构管理相关的业务逻辑
"""
import logging
from typing import Dict, Any, List, Optional
from tools.database import get_database_service
from tools.exceptions import (
    ValidationException, BusinessException,
    DatabaseException
)

logger = logging.getLogger(__name__)

class OrganizationService:
    """机构服务类"""
    
    def __init__(self):
        self.db = get_database_service()
    
    def get_organizations_list(
        self,
        page: int = 1,
        page_size: int = 10,
        keyword: str = '',
        status: Optional[int] = None,
        parent_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取机构列表（支持数据范围过滤）
        
        Args:
            page: 页码
            page_size: 每页数量
            keyword: 搜索关键词
            status: 机构状态
            parent_code: 父机构编码
            
        Returns:
            机构列表数据
        """
        try:
            # 构建查询条件
            conditions = []
            params = {}
            
            if keyword:
                conditions.append("(o.org_code LIKE :keyword OR o.org_name LIKE :keyword)")
                params['keyword'] = f"%{keyword}%"
            
            if status is not None:
                conditions.append("o.status = :status")
                params['status'] = status
            
            if parent_code:
                conditions.append("o.parent_org_code = :parent_code")
                params['parent_code'] = parent_code
            
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            
            # 基础查询SQL
            base_sql = f"""
                SELECT o.id, o.org_code, o.org_name, o.parent_org_code, 
                       o.level_depth, o.contact_person, o.contact_phone, 
                       o.contact_email, o.status, o.created_at, o.updated_at,
                       p.org_name as parent_name
                FROM organizations o
                LEFT JOIN organizations p ON o.parent_org_code = p.org_code
                WHERE {where_clause}
            """
            
            # 应用数据范围过滤
            from flask import g
            filtered_sql = base_sql
            if hasattr(g, 'user_acl_info') and g.user_acl_info:
                from service.enhanced_permission_service import get_enhanced_permission_service_instance
                permission_service = get_enhanced_permission_service_instance()
                filtered_sql = permission_service.apply_data_scope_filter(base_sql, g.user_acl_info, 'o')
            
            # 计算分页
            offset = (page - 1) * page_size
            params['limit'] = page_size
            params['offset'] = offset
            
            # 查询总数
            count_sql = f"SELECT COUNT(*) as total FROM ({filtered_sql}) as filtered_orgs"
            total_result = self.db.execute_query(count_sql, params)
            total = total_result[0]['total'] if total_result else 0
            
            # 查询数据
            data_sql = f"""
                {filtered_sql}
                ORDER BY o.created_at DESC
                LIMIT :limit OFFSET :offset
            """
            
            organizations = self.db.execute_query(data_sql, params)
            
            return {
                'success': True,
                'data': {
                    'list': organizations,
                    'total': total,
                    'page': page,
                    'page_size': page_size
                },
                'error': None
            }
            
        except Exception as e:
            logger.error(f"获取机构列表失败: {str(e)}")
            return {
                'success': False,
                'data': None,
                'error': str(e)
            }
    
    def get_organization_by_id(self, org_id: int) -> Dict[str, Any]:
        """
        根据ID获取机构信息
        
        Args:
            org_id: 机构ID
            
        Returns:
            机构信息
        """
        try:
            sql = """
                SELECT o.*, p.org_name as parent_name
                FROM organizations o
                LEFT JOIN organizations p ON o.parent_code = p.org_code
                WHERE o.id = ?
            """
            org = self.db.fetch_one(sql, [org_id])
            
            if not org:
                raise BusinessException("机构不存在")
            
            return org
            
        except BusinessException:
            raise
        except Exception as e:
            logger.error(f"获取机构信息失败: {str(e)}")
            raise DatabaseException("获取机构信息失败")
    
    def get_organization_by_code(self, org_code: str) -> Dict[str, Any]:
        """
        根据编码获取机构信息
        
        Args:
            org_code: 机构编码
            
        Returns:
            机构信息
        """
        try:
            sql = """
                SELECT o.*, p.org_name as parent_name
                FROM organizations o
                LEFT JOIN organizations p ON o.parent_code = p.org_code
                WHERE o.org_code = ?
            """
            org = self.db.fetch_one(sql, [org_code])
            
            if not org:
                raise BusinessException("机构不存在")
            
            return org
            
        except BusinessException:
            raise
        except Exception as e:
            logger.error(f"获取机构信息失败: {str(e)}")
            raise DatabaseException("获取机构信息失败")
    
    def create_organization(self, org_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建机构
        
        Args:
            org_data: 机构数据
            
        Returns:
            创建的机构信息
        """
        try:
            # 验证必要字段
            required_fields = ['org_name', 'org_type']
            for field in required_fields:
                if not org_data.get(field):
                    raise ValidationException(f"缺少必要字段: {field}")
            
            # 生成机构编码
            org_data['org_code'] = self.generate_org_code(org_data.get('parent_code'))
            
            # 检查父机构是否存在
            if org_data.get('parent_code'):
                parent_org = self.get_organization_by_code(org_data['parent_code'])
                if not parent_org:
                    raise BusinessException("父机构不存在")
            
            # 插入数据
            sql = """
                INSERT INTO organizations (
                    org_code, org_name, org_type, parent_code,
                    status, sort_order, remark, created_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = [
                org_data['org_code'],
                org_data['org_name'],
                org_data['org_type'],
                org_data.get('parent_code'),
                org_data.get('status', 1),
                org_data.get('sort_order', 0),
                org_data.get('remark'),
                org_data.get('created_by')
            ]
            
            org_id = self.db.execute(sql, params)
            
            # 返回创建的机构信息
            return self.get_organization_by_id(org_id)
            
        except (ValidationException, BusinessException):
            raise
        except Exception as e:
            logger.error(f"创建机构失败: {str(e)}")
            raise DatabaseException("创建机构失败")
    
    def update_organization(self, org_id: int, org_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        更新机构信息
        
        Args:
            org_id: 机构ID
            org_data: 机构数据
            
        Returns:
            更新后的机构信息
        """
        try:
            # 检查机构是否存在
            existing_org = self.get_organization_by_id(org_id)
            if not existing_org:
                raise BusinessException("机构不存在")
            
            # 检查父机构是否存在
            if org_data.get('parent_code'):
                parent_org = self.get_organization_by_code(org_data['parent_code'])
                if not parent_org:
                    raise BusinessException("父机构不存在")
                # 检查是否形成循环引用
                if self.would_create_cycle(existing_org['org_code'], org_data['parent_code']):
                    raise BusinessException("不能将机构设置为其下级机构的子机构")
            
            # 构建更新SQL
            update_fields = []
            params = []
            for key, value in org_data.items():
                if key not in ['id', 'org_code', 'created_at', 'created_by']:
                    update_fields.append(f"{key} = ?")
                    params.append(value)
            
            if not update_fields:
                raise ValidationException("没有需要更新的字段")
            
            sql = f"""
                UPDATE organizations
                SET {', '.join(update_fields)}
                WHERE id = ?
            """
            params.append(org_id)
            
            self.db.execute(sql, params)
            
            # 返回更新后的机构信息
            return self.get_organization_by_id(org_id)
            
        except (ValidationException, BusinessException):
            raise
        except Exception as e:
            logger.error(f"更新机构失败: {str(e)}")
            raise DatabaseException("更新机构失败")
    
    def delete_organization(self, org_id: int) -> bool:
        """
        删除机构
        
        Args:
            org_id: 机构ID
            
        Returns:
            是否删除成功
        """
        try:
            # 检查机构是否存在
            org = self.get_organization_by_id(org_id)
            if not org:
                raise BusinessException("机构不存在")
            
            # 检查是否有子机构
            if self.has_children(org['org_code']):
                raise BusinessException("该机构下存在子机构,不能删除")
            
            # 检查是否有关联用户
            if self.has_users(org['org_code']):
                raise BusinessException("该机构下存在用户,不能删除")
            
            # 执行删除
            sql = "DELETE FROM organizations WHERE id = ?"
            self.db.execute(sql, [org_id])
            
            return True
            
        except BusinessException:
            raise
        except Exception as e:
            logger.error(f"删除机构失败: {str(e)}")
            raise DatabaseException("删除机构失败")
    
    def get_organization_tree(self, root_org_code: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取机构树形结构
        
        Args:
            root_org_code: 根机构编码,为None时返回全部
            
        Returns:
            机构树形数据
        """
        try:
            # 获取所有机构
            sql = "SELECT * FROM organizations WHERE status = 1"
            if root_org_code:
                sql += " AND (org_code = ? OR parent_code = ?)"
                orgs = self.db.fetch_all(sql, [root_org_code, root_org_code])
            else:
                orgs = self.db.fetch_all(sql)
            
            # 构建树形结构
            org_map = {org['org_code']: dict(org, children=[]) for org in orgs}
            tree = []
            
            for org in orgs:
                parent_code = org['parent_code']
                if parent_code and parent_code in org_map:
                    org_map[parent_code]['children'].append(org_map[org['org_code']])
                else:
                    tree.append(org_map[org['org_code']])
            
            return tree
            
        except Exception as e:
            logger.error(f"获取机构树失败: {str(e)}")
            raise DatabaseException("获取机构树失败")
    
    def generate_org_code(self, parent_code: Optional[str] = None) -> str:
        """
        生成机构编码
        
        Args:
            parent_code: 父机构编码
            
        Returns:
            新的机构编码
        """
        try:
            if parent_code:
                # 获取同级最大编码
                sql = "SELECT MAX(org_code) as max_code FROM organizations WHERE parent_code = ?"
                result = self.db.fetch_one(sql, [parent_code])
                if result['max_code']:
                    current_num = int(result['max_code'][-3:])
                    return f"{parent_code}{(current_num + 1):03d}"
                return f"{parent_code}001"
            else:
                # 获取顶级机构最大编码
                sql = "SELECT MAX(org_code) as max_code FROM organizations WHERE LENGTH(org_code) = 3"
                result = self.db.fetch_one(sql)
                if result['max_code']:
                    current_num = int(result['max_code'])
                    return f"{(current_num + 1):03d}"
                return "001"
            
        except Exception as e:
            logger.error(f"生成机构编码失败: {str(e)}")
            raise DatabaseException("生成机构编码失败")
    
    def has_children(self, org_code: str) -> bool:
        """检查是否有子机构"""
        sql = "SELECT COUNT(*) as count FROM organizations WHERE parent_code = ?"
        result = self.db.fetch_one(sql, [org_code])
        return result['count'] > 0
    
    def has_users(self, org_code: str) -> bool:
        """检查是否有关联用户"""
        sql = "SELECT COUNT(*) as count FROM users WHERE org_code = ?"
        result = self.db.fetch_one(sql, [org_code])
        return result['count'] > 0
    
    def would_create_cycle(self, org_code: str, new_parent_code: str) -> bool:
        """检查是否会形成循环引用"""
        current = new_parent_code
        while current:
            if current == org_code:
                return True
            parent = self.get_organization_by_code(current)
            current = parent['parent_code'] if parent else None
        return False

# 机构服务单例
_organization_service = None

def get_organization_service_instance() -> OrganizationService:
    """获取机构服务实例"""
    global _organization_service
    if _organization_service is None:
        _organization_service = OrganizationService()
    return _organization_service 