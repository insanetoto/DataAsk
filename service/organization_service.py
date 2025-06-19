# -*- coding: utf-8 -*-
"""
机构管理服务模块
提供机构的增删改查功能，集成Redis缓存提升性能
"""
import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from tools.database import get_database_service
from tools.redis_service import get_redis_service

logger = logging.getLogger(__name__)

class OrganizationService:
    """机构管理服务类"""
    
    def __init__(self):
        self.cache_prefix = "org:"
        self.cache_timeout = 3600  # 缓存1小时
        self.list_cache_key = "org:list"
        
    def create_organization(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建机构（支持层级结构）
        
        Args:
            data: 机构数据字典，包含parent_org_code字段用于指定上级机构
            
        Returns:
            创建结果
        """
        try:
            db_service = get_database_service()
            
            # 验证必要字段
            required_fields = ['org_code', 'org_name', 'contact_person', 'contact_phone', 'contact_email']
            for field in required_fields:
                if field not in data or not data[field].strip():
                    return {
                        'success': False,
                        'error': f'缺少必要字段: {field}'
                    }
            
            # 检查机构编码是否已存在
            existing_org = self.get_organization_by_code(data['org_code'])
            if existing_org['success'] and existing_org['data']:
                return {
                    'success': False,
                    'error': f'机构编码 {data["org_code"]} 已存在'
                }
            
            # 验证上级机构是否存在（如果指定了上级机构）
            parent_org_code = data.get('parent_org_code')
            if parent_org_code:
                parent_org_code = parent_org_code.strip()
                if parent_org_code:  # 如果不为空
                    parent_org = self.get_organization_by_code(parent_org_code)
                    if not parent_org['success'] or not parent_org['data']:
                        return {
                            'success': False,
                            'error': f'上级机构编码 {parent_org_code} 不存在'
                        }
                    
                    # 检查是否会形成循环引用
                    if parent_org_code == data['org_code']:
                        return {
                            'success': False,
                            'error': '不能将自己设置为上级机构'
                        }
                        
                    # 检查上级机构的所有上级中是否包含当前机构（防止循环）
                    parent_hierarchy = self.get_organization_parents(parent_org_code)
                    if parent_hierarchy['success']:
                        parent_codes = [org['org_code'] for org in parent_hierarchy['data']]
                        if data['org_code'] in parent_codes:
                            return {
                                'success': False,
                                'error': '不能设置为上级机构，这会形成循环引用'
                            }
                else:
                    parent_org_code = None
            else:
                parent_org_code = None
            
            # 插入数据（触发器会自动计算层级信息）
            sql = """
            INSERT INTO organizations (org_code, parent_org_code, org_name, contact_person, contact_phone, contact_email, status)
            VALUES (:org_code, :parent_org_code, :org_name, :contact_person, :contact_phone, :contact_email, :status)
            """
            
            params = {
                'org_code': data['org_code'].strip(),
                'parent_org_code': parent_org_code,
                'org_name': data['org_name'].strip(),
                'contact_person': data['contact_person'].strip(),
                'contact_phone': data['contact_phone'].strip(),
                'contact_email': data['contact_email'].strip(),
                'status': data.get('status', 1)
            }
            
            db_service.execute_update(sql, params)
            
            # 获取新创建的机构信息
            new_org = self.get_organization_by_code(data['org_code'])
            
            # 清除列表缓存
            self._clear_list_cache()
            
            logger.info(f"成功创建机构: {data['org_code']} - {data['org_name']}，上级机构: {parent_org_code or '无'}")
            
            return {
                'success': True,
                'data': new_org['data'],
                'message': '机构创建成功'
            }
            
        except Exception as e:
            logger.error(f"创建机构失败: {str(e)}")
            return {
                'success': False,
                'error': f'创建机构失败: {str(e)}'
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
            # 先检查缓存
            cache_key = f"{self.cache_prefix}id:{org_id}"
            redis_service = get_redis_service()
            cached_data = redis_service.get_cache(cache_key)
            
            if cached_data:
                logger.info(f"从缓存获取机构信息: ID={org_id}")
                return {
                    'success': True,
                    'data': json.loads(cached_data)
                }
            
            # 从数据库查询
            db_service = get_database_service()
            sql = """
            SELECT id, org_code, parent_org_code, org_name, contact_person, contact_phone, contact_email, 
                   status, level_depth, level_path, created_at, updated_at
            FROM organizations 
            WHERE id = :org_id
            """
            
            result = db_service.execute_query(sql, {'org_id': org_id})
            
            if not result:
                return {
                    'success': False,
                    'error': '机构不存在'
                }
            
            org_data = result[0]
            
            # 缓存数据
            redis_service.set_cache(cache_key, json.dumps(org_data, default=str), self.cache_timeout)
            
            return {
                'success': True,
                'data': org_data
            }
            
        except Exception as e:
            logger.error(f"根据ID获取机构信息失败: {str(e)}")
            return {
                'success': False,
                'error': f'获取机构信息失败: {str(e)}'
            }
    
    def get_organization_by_code(self, org_code: str) -> Dict[str, Any]:
        """
        根据机构编码获取机构信息
        
        Args:
            org_code: 机构编码
            
        Returns:
            机构信息
        """
        try:
            # 先检查缓存
            cache_key = f"{self.cache_prefix}code:{org_code}"
            redis_service = get_redis_service()
            cached_data = redis_service.get_cache(cache_key)
            
            if cached_data:
                logger.info(f"从缓存获取机构信息: code={org_code}")
                return {
                    'success': True,
                    'data': json.loads(cached_data)
                }
            
            # 从数据库查询
            db_service = get_database_service()
            sql = """
            SELECT id, org_code, parent_org_code, org_name, contact_person, contact_phone, contact_email, 
                   status, level_depth, level_path, created_at, updated_at
            FROM organizations 
            WHERE org_code = :org_code
            """
            
            result = db_service.execute_query(sql, {'org_code': org_code})
            
            if not result:
                return {
                    'success': True,
                    'data': None
                }
            
            org_data = result[0]
            
            # 缓存数据
            redis_service.set_cache(cache_key, json.dumps(org_data, default=str), self.cache_timeout)
            
            return {
                'success': True,
                'data': org_data
            }
            
        except Exception as e:
            logger.error(f"根据编码获取机构信息失败: {str(e)}")
            return {
                'success': False,
                'error': f'获取机构信息失败: {str(e)}'
            }
    
    def get_organizations_list(self, page: int = 1, page_size: int = 10, status: Optional[int] = None, 
                              keyword: Optional[str] = None) -> Dict[str, Any]:
        """
        获取机构列表
        
        Args:
            page: 页码
            page_size: 每页数量
            status: 状态筛选
            keyword: 关键词搜索
            
        Returns:
            机构列表和分页信息
        """
        try:
            # 生成缓存键
            cache_key = f"{self.list_cache_key}:{page}:{page_size}:{status}:{keyword or ''}"
            redis_service = get_redis_service()
            cached_data = redis_service.get_cache(cache_key)
            
            if cached_data:
                logger.info(f"从缓存获取机构列表: page={page}, page_size={page_size}")
                return {
                    'success': True,
                    'data': cached_data
                }
            
            db_service = get_database_service()
            
            # 构建查询条件
            where_conditions = []
            params = {}
            
            if status is not None:
                where_conditions.append("status = :status")
                params['status'] = status
                
            if keyword:
                where_conditions.append("(org_code LIKE :keyword OR org_name LIKE :keyword OR contact_person LIKE :keyword)")
                params['keyword'] = f'%{keyword}%'
            
            where_clause = ""
            if where_conditions:
                where_clause = "WHERE " + " AND ".join(where_conditions)
            
            # 查询总数
            count_sql = f"SELECT COUNT(*) as total FROM organizations {where_clause}"
            count_result = db_service.execute_query(count_sql, params)
            total = count_result[0]['total']
            
            # 计算分页参数
            offset = (page - 1) * page_size
            total_pages = (total + page_size - 1) // page_size
            
            # 查询数据
            params['limit'] = page_size
            params['offset'] = offset
            
            data_sql = f"""
            SELECT id, org_code, org_name, contact_person, contact_phone, contact_email, 
                   status, created_at, updated_at
            FROM organizations 
            {where_clause}
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :offset
            """
            
            data_result = db_service.execute_query(data_sql, params)
            
            result_data = {
                'list': data_result,
                'pagination': {
                    'page': page,
                    'page_size': page_size,
                    'total': total,
                    'total_pages': total_pages,
                    'has_next': page < total_pages,
                    'has_prev': page > 1
                }
            }
            
            # 缓存结果（缓存时间稍短，因为列表更新频繁）
            redis_service.set_cache(cache_key, result_data, 600)  # 10分钟
            
            return {
                'success': True,
                'data': result_data
            }
            
        except Exception as e:
            logger.error(f"获取机构列表失败: {str(e)}")
            return {
                'success': False,
                'error': f'获取机构列表失败: {str(e)}'
            }
    
    def _get_organization_by_id_without_status_check(self, org_id: int) -> Dict[str, Any]:
        """根据ID获取机构信息（不检查状态）"""
        try:
            db_service = get_database_service()
            sql = """
            SELECT id, org_code, parent_org_code, org_name, contact_person, contact_phone, contact_email, 
                   status, level_depth, level_path, created_at, updated_at
            FROM organizations 
            WHERE id = :org_id
            """
            
            result = db_service.execute_query(sql, {'org_id': org_id})
            
            if not result:
                return {
                    'success': False,
                    'error': '机构不存在'
                }
            
            org_data = result[0]
            
            return {
                'success': True,
                'data': org_data
            }
            
        except Exception as e:
            logger.error(f"根据ID获取机构信息失败: {str(e)}")
            return {
                'success': False,
                'error': f'获取机构信息失败: {str(e)}'
            }
    
    def update_organization(self, org_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """更新机构信息"""
        try:
            db_service = get_database_service()
            
            # 获取现有机构信息（不检查状态）
            current_org = self._get_organization_by_id_without_status_check(org_id)
            if not current_org['success'] or not current_org['data']:
                return {
                    'success': False,
                    'error': '机构不存在'
                }
            
            # 构建更新字段
            update_fields = []
            params = {'org_id': org_id}
            
            # 可更新字段列表
            updatable_fields = {
                'org_name': str,
                'contact_person': str,
                'contact_phone': str,
                'contact_email': str,
                'status': int
            }
            
            # 处理每个可更新字段
            for field, field_type in updatable_fields.items():
                if field in data:
                    value = data[field]
                    if isinstance(value, str):
                        value = value.strip()
                    if value is not None:
                        update_fields.append(f"{field} = :{field}")
                        params[field] = field_type(value)
            
            if not update_fields:
                return {
                    'success': False,
                    'error': '没有提供需要更新的字段'
                }
            
            # 执行更新
            sql = f"""
            UPDATE organizations 
            SET {', '.join(update_fields)}
            WHERE id = :org_id
            """
            
            db_service.execute_update(sql, params)
            
            # 清除缓存
            self._clear_organization_cache(current_org['data']['org_code'], org_id)
            self._clear_list_cache()
            
            # 获取更新后的机构信息
            updated_org = self._get_organization_by_id_without_status_check(org_id)
            
            return {
                'success': True,
                'data': updated_org['data'],
                'message': '机构信息更新成功'
            }
            
        except Exception as e:
            logger.error(f"更新机构信息失败: {str(e)}")
            return {
                'success': False,
                'error': f'更新机构信息失败: {str(e)}'
            }
    
    def delete_organization(self, org_id: int) -> Dict[str, Any]:
        """删除机构（软删除）"""
        try:
            db_service = get_database_service()
            
            # 获取机构信息（不检查状态）
            current_org = self._get_organization_by_id_without_status_check(org_id)
            if not current_org['success'] or not current_org['data']:
                return {
                    'success': False,
                    'error': '机构不存在'
                }
            
            # 检查是否有子机构
            children_sql = """
            SELECT COUNT(*) as count
            FROM organizations
            WHERE parent_org_code = :org_code AND status = 1
            """
            children_result = db_service.execute_query(children_sql, {'org_code': current_org['data']['org_code']})
            if children_result[0]['count'] > 0:
                return {
                    'success': False,
                    'error': '该机构下存在子机构，无法删除'
                }
            
            # 检查是否有用户
            users_sql = """
            SELECT COUNT(*) as count
            FROM users
            WHERE org_code = :org_code AND status = 1
            """
            users_result = db_service.execute_query(users_sql, {'org_code': current_org['data']['org_code']})
            if users_result[0]['count'] > 0:
                return {
                    'success': False,
                    'error': '该机构下存在用户，无法删除'
                }
            
            # 软删除机构（将状态设置为0）
            sql = """
            UPDATE organizations 
            SET status = 0
            WHERE id = :org_id
            """
            
            db_service.execute_update(sql, {'org_id': org_id})
            
            # 清除缓存
            self._clear_organization_cache(current_org['data']['org_code'], org_id)
            self._clear_list_cache()
            
            return {
                'success': True,
                'message': '机构删除成功'
            }
            
        except Exception as e:
            logger.error(f"删除机构失败: {str(e)}")
            return {
                'success': False,
                'error': f'删除机构失败: {str(e)}'
            }
    
    def _clear_organization_cache(self, org_code: str, org_id: int):
        """清除单个机构的缓存"""
        try:
            redis_service = get_redis_service()
            redis_service.delete_cache(f"{self.cache_prefix}code:{org_code}")
            redis_service.delete_cache(f"{self.cache_prefix}id:{org_id}")
        except Exception as e:
            logger.warning(f"清除机构缓存失败: {str(e)}")
    
    def _clear_list_cache(self):
        """清除机构列表缓存"""
        try:
            redis_service = get_redis_service()
            # 使用通配符删除所有列表缓存
            keys = redis_service.get_keys_by_pattern(f"{self.list_cache_key}:*")
            if keys:
                for key in keys:
                    redis_service.delete_cache(key)
        except Exception as e:
            logger.warning(f"清除机构列表缓存失败: {str(e)}")
    
    def get_organization_children(self, org_code: str, include_self: bool = False) -> Dict[str, Any]:
        """
        获取机构的所有子机构（递归）
        
        Args:
            org_code: 机构编码
            include_self: 是否包含自身
            
        Returns:
            子机构列表
        """
        try:
            db_service = get_database_service()
            
            # 使用存储过程获取子机构
            sql = "CALL GetOrgChildren(:org_code)"
            result = db_service.execute_query(sql, {'org_code': org_code})
            
            if not result:
                return {
                    'success': True,
                    'data': []
                }
            
            # 如果不包含自身，过滤掉根节点
            if not include_self:
                result = [org for org in result if org['org_code'] != org_code]
            
            return {
                'success': True,
                'data': result
            }
            
        except Exception as e:
            logger.error(f"获取子机构失败: {str(e)}")
            return {
                'success': False,
                'error': f'获取子机构失败: {str(e)}'
            }
    
    def get_organization_parents(self, org_code: str, include_self: bool = False) -> Dict[str, Any]:
        """
        获取机构的所有上级机构（递归）
        
        Args:
            org_code: 机构编码
            include_self: 是否包含自身
            
        Returns:
            上级机构列表
        """
        try:
            db_service = get_database_service()
            
            # 使用存储过程获取上级机构
            sql = "CALL GetOrgParents(:org_code)"
            result = db_service.execute_query(sql, {'org_code': org_code})
            
            if not result:
                return {
                    'success': True,
                    'data': []
                }
            
            # 如果不包含自身，过滤掉当前节点
            if not include_self:
                result = [org for org in result if org['org_code'] != org_code]
            
            return {
                'success': True,
                'data': result
            }
            
        except Exception as e:
            logger.error(f"获取上级机构失败: {str(e)}")
            return {
                'success': False,
                'error': f'获取上级机构失败: {str(e)}'
            }
    
    def get_organization_tree(self, root_org_code: str = None) -> Dict[str, Any]:
        """
        获取机构树结构
        
        Args:
            root_org_code: 根机构编码，如果为None则获取所有顶级机构
            
        Returns:
            机构树结构
        """
        try:
            db_service = get_database_service()
            
            if root_org_code:
                # 获取指定机构及其子机构
                result = self.get_organization_children(root_org_code, include_self=True)
                if not result['success']:
                    return result
                org_list = result['data']
            else:
                # 获取所有机构
                sql = """
                SELECT id, org_code, parent_org_code, org_name, contact_person, contact_phone, 
                       contact_email, status, level_depth, level_path, created_at, updated_at
                FROM organizations 
                ORDER BY level_path, org_code
                """
                org_list = db_service.execute_query(sql)
            
            # 构建树形结构
            tree = self._build_organization_tree(org_list, root_org_code)
            
            return {
                'success': True,
                'data': tree
            }
            
        except Exception as e:
            logger.error(f"获取机构树失败: {str(e)}")
            return {
                'success': False,
                'error': f'获取机构树失败: {str(e)}'
            }
    
    def _build_organization_tree(self, org_list: List[Dict], root_code: str = None) -> List[Dict]:
        """
        构建机构树形结构
        
        Args:
            org_list: 机构列表
            root_code: 根节点编码
            
        Returns:
            树形结构列表
        """
        # 创建机构映射
        org_map = {org['org_code']: org for org in org_list}
        
        # 为每个机构添加children字段
        for org in org_list:
            org['children'] = []
        
        # 构建父子关系
        root_nodes = []
        
        for org in org_list:
            parent_code = org['parent_org_code']
            if parent_code and parent_code in org_map:
                # 添加到父节点的children中
                org_map[parent_code]['children'].append(org)
            else:
                # 顶级节点
                if root_code is None or org['org_code'] == root_code:
                    root_nodes.append(org)
        
        # 如果指定了根节点，返回该节点的子树
        if root_code and root_code in org_map:
            return [org_map[root_code]]
        
        return root_nodes
    
    def get_organization_hierarchy_view(self, page: int = 1, page_size: int = 10, 
                                      keyword: Optional[str] = None) -> Dict[str, Any]:
        """
        获取机构层级关系视图（分页）
        
        Args:
            page: 页码
            page_size: 每页数量
            keyword: 搜索关键词
            
        Returns:
            层级关系列表
        """
        try:
            db_service = get_database_service()
            
            # 构建查询条件
            where_conditions = []
            params = {}
            
            if keyword:
                where_conditions.append("""
                    (child.org_code LIKE :keyword OR child.org_name LIKE :keyword 
                     OR parent.org_name LIKE :keyword OR child.contact_person LIKE :keyword)
                """)
                params['keyword'] = f'%{keyword}%'
            
            where_clause = ""
            if where_conditions:
                where_clause = "WHERE " + " AND ".join(where_conditions)
            
            # 查询总数
            count_sql = f"""
            SELECT COUNT(*) as total
            FROM organizations child
            LEFT JOIN organizations parent ON child.parent_org_code = parent.org_code
            {where_clause}
            """
            
            count_result = db_service.execute_query(count_sql, params)
            total = count_result[0]['total'] if count_result else 0
            
            # 查询数据
            offset = (page - 1) * page_size
            
            sql = f"""
            SELECT 
                child.id,
                child.org_code,
                child.org_name,
                child.parent_org_code,
                parent.org_name AS parent_org_name,
                child.level_depth,
                child.level_path,
                child.contact_person,
                child.contact_phone,
                child.contact_email,
                child.status,
                child.created_at,
                child.updated_at
            FROM organizations child
            LEFT JOIN organizations parent ON child.parent_org_code = parent.org_code
            {where_clause}
            ORDER BY child.level_path, child.org_code
            LIMIT :limit OFFSET :offset
            """
            
            params.update({
                'limit': page_size,
                'offset': offset
            })
            
            organizations = db_service.execute_query(sql, params)
            
            return {
                'success': True,
                'data': {
                    'organizations': organizations,
                    'pagination': {
                        'page': page,
                        'page_size': page_size,
                        'total': total,
                        'pages': (total + page_size - 1) // page_size
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"获取机构层级关系视图失败: {str(e)}")
            return {
                'success': False,
                'error': f'获取机构层级关系视图失败: {str(e)}'
            }
    
    def move_organization(self, org_code: str, new_parent_code: str = None) -> Dict[str, Any]:
        """
        移动机构到新的上级机构下
        
        Args:
            org_code: 要移动的机构编码
            new_parent_code: 新的上级机构编码，None表示移动到顶级
            
        Returns:
            移动结果
        """
        try:
            db_service = get_database_service()
            
            # 验证机构是否存在
            org_result = self.get_organization_by_code(org_code)
            if not org_result['success'] or not org_result['data']:
                return {
                    'success': False,
                    'error': f'机构 {org_code} 不存在'
                }
            
            # 验证新上级机构是否存在（如果指定了）
            if new_parent_code:
                parent_result = self.get_organization_by_code(new_parent_code)
                if not parent_result['success'] or not parent_result['data']:
                    return {
                        'success': False,
                        'error': f'上级机构 {new_parent_code} 不存在'
                    }
                
                # 检查是否会形成循环引用
                if new_parent_code == org_code:
                    return {
                        'success': False,
                        'error': '不能将机构移动到自己下面'
                    }
                
                # 检查新上级机构是否是当前机构的子机构
                children_result = self.get_organization_children(org_code)
                if children_result['success']:
                    child_codes = [child['org_code'] for child in children_result['data']]
                    if new_parent_code in child_codes:
                        return {
                            'success': False,
                            'error': '不能将机构移动到其子机构下面'
                        }
            
            # 更新机构的上级机构
            sql = """
            UPDATE organizations 
            SET parent_org_code = :new_parent_code,
                updated_at = CURRENT_TIMESTAMP
            WHERE org_code = :org_code
            """
            
            db_service.execute_update(sql, {
                'org_code': org_code,
                'new_parent_code': new_parent_code
            })
            
            # 重新计算层级信息
            self._recalculate_organization_hierarchy(org_code)
            
            # 清除缓存
            self._clear_organization_cache(org_code, org_result['data']['id'])
            self._clear_list_cache()
            
            logger.info(f"成功移动机构 {org_code} 到 {new_parent_code or '顶级'}")
            
            return {
                'success': True,
                'message': '机构移动成功'
            }
            
        except Exception as e:
            logger.error(f"移动机构失败: {str(e)}")
            return {
                'success': False,
                'error': f'移动机构失败: {str(e)}'
            }
    
    def _recalculate_organization_hierarchy(self, org_code: str):
        """
        重新计算机构层级信息
        
        Args:
            org_code: 机构编码
        """
        try:
            db_service = get_database_service()
            
            # 递归更新层级信息
            def update_org_hierarchy(code):
                # 获取当前机构信息
                org_info = self.get_organization_by_code(code)
                if not org_info['success'] or not org_info['data']:
                    return
                
                org = org_info['data']
                parent_code = org['parent_org_code']
                
                # 计算层级深度和路径
                if parent_code:
                    parent_info = self.get_organization_by_code(parent_code)
                    if parent_info['success'] and parent_info['data']:
                        parent_depth = parent_info['data']['level_depth']
                        parent_path = parent_info['data']['level_path']
                        new_depth = parent_depth + 1
                        new_path = f"{parent_path}{code}/"
                    else:
                        new_depth = 0
                        new_path = f"/{code}/"
                else:
                    new_depth = 0
                    new_path = f"/{code}/"
                
                # 更新当前机构
                update_sql = """
                UPDATE organizations 
                SET level_depth = :depth, level_path = :path
                WHERE org_code = :code
                """
                db_service.execute_update(update_sql, {
                    'depth': new_depth,
                    'path': new_path,
                    'code': code
                })
                
                # 递归更新子机构
                children_result = self.get_organization_children(code, include_self=False)
                if children_result['success']:
                    for child in children_result['data']:
                        if child['relative_depth'] == 1:  # 只更新直接子机构
                            update_org_hierarchy(child['org_code'])
            
            update_org_hierarchy(org_code)
                
        except Exception as e:
            logger.error(f"重新计算机构层级信息失败: {str(e)}")

# 全局机构服务实例
organization_service = None

def init_organization_service() -> OrganizationService:
    """初始化机构管理服务"""
    global organization_service
    organization_service = OrganizationService()
    return organization_service

def get_organization_service() -> OrganizationService:
    """获取机构管理服务实例"""
    if organization_service is None:
        return init_organization_service()
    return organization_service 