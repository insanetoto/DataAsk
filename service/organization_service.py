# -*- coding: utf-8 -*-
"""
机构管理服务模块
提供机构的增删改查功能，集成Redis缓存提升性能
"""
import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from tools.database import DatabaseService, get_database_service
from tools.redis_service import RedisService, get_redis_service
from tools.di_container import DIContainer

logger = logging.getLogger(__name__)

class OrganizationService:
    """机构管理服务类"""
    
    def __init__(self, redis_service: RedisService = None, db_service: DatabaseService = None):
        self.cache_prefix = "org:"
        self.cache_timeout = 3600  # 缓存1小时
        self.list_cache_key = "org:list"
        self.redis = redis_service
        self.db_service = db_service
        
        if not self.redis:
            raise RuntimeError("Redis服务未初始化")
        if not self.db_service:
            raise RuntimeError("数据库服务未初始化")
        
    def _generate_org_code(self, parent_org_code: str = None) -> str:
        """
        自动生成机构编码
        
        规则：
        1. 机构编码最多10位，每两位为1级，从00开始编码
        2. 如果没有上级机构，生成顶级机构编码（如00, 01, 02...）
        3. 如果有上级机构，在上级机构编码基础上增加两位（如0501, 0502...）
        
        Args:
            parent_org_code: 上级机构编码
            
        Returns:
            生成的机构编码
        """
        try:
            if not parent_org_code:
                # 生成顶级机构编码
                sql = """
                SELECT org_code FROM organizations 
                WHERE parent_org_code IS NULL 
                ORDER BY org_code DESC 
                LIMIT 1
                """
                result = self.db_service.execute_query(sql, {})
                
                if not result:
                    # 没有任何顶级机构，从00开始
                    return "00"
                
                last_code = result[0]['org_code']
                
                # 确保是两位的顶级编码
                if len(last_code) == 2 and last_code.isdigit():
                    next_num = int(last_code) + 1
                    if next_num > 99:
                        raise ValueError("顶级机构编码已达上限(99)")
                    return f"{next_num:02d}"
                else:
                    # 如果存在的编码不是标准格式，从00开始
                    return "00"
            
            else:
                # 检查上级机构编码长度是否合法
                if len(parent_org_code) >= 10:
                    raise ValueError("上级机构层级已达最大深度，无法创建下级机构")
                
                if len(parent_org_code) % 2 != 0:
                    raise ValueError("上级机构编码格式不正确")
                
                # 生成下级机构编码
                sql = """
                SELECT org_code FROM organizations 
                WHERE parent_org_code = :parent_org_code 
                ORDER BY org_code DESC 
                LIMIT 1
                """
                result = self.db_service.execute_query(sql, {'parent_org_code': parent_org_code})
                
                if not result:
                    # 该上级机构下没有子机构，从00开始
                    return parent_org_code + "00"
                
                last_code = result[0]['org_code']
                
                # 提取最后两位作为序号
                if len(last_code) > len(parent_org_code):
                    last_suffix = last_code[len(parent_org_code):]
                    if len(last_suffix) >= 2 and last_suffix[:2].isdigit():
                        next_num = int(last_suffix[:2]) + 1
                        if next_num > 99:
                            raise ValueError(f"机构 {parent_org_code} 的下级机构编码已达上限(99)")
                        return parent_org_code + f"{next_num:02d}"
                
                # 如果无法解析，从00开始
                return parent_org_code + "00"
                
        except Exception as e:
            logger.error(f"生成机构编码失败: {str(e)}")
            raise ValueError(f"生成机构编码失败: {str(e)}")
    
    def _calculate_level_depth(self, parent_org_code: str = None) -> int:
        """
        计算机构层级深度
        
        Args:
            parent_org_code: 上级机构编码
            
        Returns:
            层级深度
        """
        if not parent_org_code:
            return 0
        
        try:
            # 获取上级机构的层级深度
            sql = "SELECT level_depth FROM organizations WHERE org_code = :parent_org_code"
            result = self.db_service.execute_query(sql, {'parent_org_code': parent_org_code})
            
            if result:
                return result[0]['level_depth'] + 1
            else:
                # 如果找不到上级机构，默认为顶级机构
                return 0
        except Exception as e:
            logger.error(f"计算层级深度失败: {str(e)}")
            return 0
    
    def _calculate_level_path(self, parent_org_code: str = None, org_code: str = None) -> str:
        """
        计算机构层级路径
        
        Args:
            parent_org_code: 上级机构编码
            org_code: 当前机构编码
            
        Returns:
            层级路径
        """
        if not parent_org_code:
            return f'/{org_code}/'
        
        try:
            # 获取上级机构的层级路径
            sql = "SELECT level_path FROM organizations WHERE org_code = :parent_org_code"
            result = self.db_service.execute_query(sql, {'parent_org_code': parent_org_code})
            
            if result and result[0]['level_path']:
                parent_path = result[0]['level_path']
                return f'{parent_path}{org_code}/'
            else:
                # 如果找不到上级机构路径，默认为顶级路径
                return f'/{org_code}/'
        except Exception as e:
            logger.error(f"计算层级路径失败: {str(e)}")
            return f'/{org_code}/'
    
    def create_organization(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建机构
        
        Args:
            data: 机构数据，包含 org_name, contact_person, contact_phone, contact_email 等
                 可选包含 org_code（如果不提供则自动生成）, parent_org_code, status
            
        Returns:
            创建结果
        """
        try:
            # 验证必填字段
            required_fields = ['org_name', 'contact_person', 'contact_phone', 'contact_email']
            for field in required_fields:
                if not data.get(field):
                    return {
                        'success': False,
                        'error': f'缺少必填字段: {field}'
                    }
            
            # 处理机构编码
            if 'org_code' not in data or not data['org_code'] or data['org_code'].strip() == '':
                # 自动生成机构编码
                parent_org_code = data.get('parent_org_code')
                if parent_org_code and parent_org_code.strip() == '':
                    parent_org_code = None
                
                try:
                    generated_code = self._generate_org_code(parent_org_code)
                    data['org_code'] = generated_code
                    logger.info(f"自动生成机构编码: {generated_code}，上级机构: {parent_org_code or '无'}")
                except ValueError as e:
                    return {
                        'success': False,
                        'error': str(e)
                    }
            else:
                # 验证手动输入的机构编码
                org_code = data['org_code'].strip()
                if len(org_code) > 10:
                    return {
                        'success': False,
                        'error': '机构编码长度不能超过10位'
                    }
                
                # 检查编码是否已存在
                existing_org = self.get_organization_by_code(org_code)
                if existing_org['success'] and existing_org['data']:
                    return {
                        'success': False,
                        'error': f'机构编码 {org_code} 已存在'
                    }
                
                data['org_code'] = org_code
            
            # 验证上级机构（如果指定了的话）
            parent_org_code = data.get('parent_org_code')
            if parent_org_code and parent_org_code.strip():
                parent_org_code = parent_org_code.strip()
                
                # 检查上级机构是否存在
                parent_org = self.get_organization_by_code(parent_org_code)
                if not parent_org['success'] or not parent_org['data']:
                    return {
                        'success': False,
                        'error': f'上级机构 {parent_org_code} 不存在'
                    }
                
                # 检查是否会形成循环引用
                if parent_org_code == data['org_code']:
                    return {
                        'success': False,
                        'error': '不能设置为上级机构，这会形成循环引用'
                    }
            else:
                parent_org_code = None
            
            # 计算层级信息
            level_depth = self._calculate_level_depth(parent_org_code)
            level_path = self._calculate_level_path(parent_org_code, data['org_code'])
            
            # 插入数据（包含计算的层级信息）
            sql = """
            INSERT INTO organizations (org_code, parent_org_code, org_name, contact_person, contact_phone, contact_email, status, level_depth, level_path)
            VALUES (:org_code, :parent_org_code, :org_name, :contact_person, :contact_phone, :contact_email, :status, :level_depth, :level_path)
            """
            
            params = {
                'org_code': data['org_code'],
                'parent_org_code': parent_org_code,
                'org_name': data['org_name'].strip(),
                'contact_person': data['contact_person'].strip(),
                'contact_phone': data['contact_phone'].strip(),
                'contact_email': data['contact_email'].strip(),
                'status': data.get('status', 1),
                'level_depth': level_depth,
                'level_path': level_path
            }
            
            self.db_service.execute_update(sql, params)
            
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
            cached_data = self.redis.get_cache(cache_key)
            
            if cached_data:
        
                # cached_data 已经是字典对象，不需要再json.loads
                org_data = cached_data if isinstance(cached_data, dict) else json.loads(cached_data)
                return {
                    'success': True,
                    'data': org_data
                }
            
            # 从数据库查询
            sql = """
            SELECT id, org_code, parent_org_code, org_name, contact_person, contact_phone, contact_email, 
                   status, level_depth, level_path, created_at, updated_at
            FROM organizations 
            WHERE id = :org_id
            """
            
            result = self.db_service.execute_query(sql, {'org_id': org_id})
            
            if not result:
                return {
                    'success': False,
                    'error': '机构不存在'
                }
            
            org_data = result[0]
            
            # 缓存数据
            self.redis.set_cache(cache_key, json.dumps(org_data, default=str), self.cache_timeout)
            
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
            cached_data = self.redis.get_cache(cache_key)
            
            if cached_data:
        
                # cached_data 已经是字典对象，不需要再json.loads
                org_data = cached_data if isinstance(cached_data, dict) else json.loads(cached_data)
                return {
                    'success': True,
                    'data': org_data
                }
            
            # 从数据库查询
            sql = """
            SELECT id, org_code, parent_org_code, org_name, contact_person, contact_phone, contact_email, 
                   status, level_depth, level_path, created_at, updated_at
            FROM organizations 
            WHERE org_code = :org_code
            """
            
            result = self.db_service.execute_query(sql, {'org_code': org_code})
            
            if not result:
                return {
                    'success': True,
                    'data': None
                }
            
            org_data = result[0]
            
            # 缓存数据
            self.redis.set_cache(cache_key, json.dumps(org_data, default=str), self.cache_timeout)
            
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
            cached_data = self.redis.get_cache(cache_key)
            
            if cached_data:
        
                return {
                    'success': True,
                    'data': cached_data
                }
            
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
            count_result = self.db_service.execute_query(count_sql, params)
            total = count_result[0]['total']
            
            # 计算分页参数
            offset = (page - 1) * page_size
            total_pages = (total + page_size - 1) // page_size
            
            # 查询数据
            params['limit'] = page_size
            params['offset'] = offset
            
            data_sql = f"""
            SELECT id, org_code, org_name, parent_org_code, level_depth, contact_person, contact_phone, contact_email, 
                   status, created_at, updated_at
            FROM organizations 
            {where_clause}
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :offset
            """
            
            data_result = self.db_service.execute_query(data_sql, params)
            
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
            self.redis.set_cache(cache_key, result_data, 600)  # 10分钟
            
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
            sql = """
            SELECT id, org_code, parent_org_code, org_name, contact_person, contact_phone, contact_email, 
                   status, level_depth, level_path, created_at, updated_at
            FROM organizations 
            WHERE id = :org_id
            """
            
            result = self.db_service.execute_query(sql, {'org_id': org_id})
            
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
            
            self.db_service.execute_update(sql, params)
            
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
            # 获取机构信息（不检查状态）
            current_org = self._get_organization_by_id_without_status_check(org_id)
            if not current_org['success'] or not current_org['data']:
                return {
                    'success': False,
                    'error': '机构不存在'
                }
            
            # 检查是否有子机构
            children_sql = """
            SELECT org_code, org_name
            FROM organizations
            WHERE parent_org_code = :org_code AND status = 1
            """
            children_result = self.db_service.execute_query(children_sql, {'org_code': current_org['data']['org_code']})
            if children_result:
                child_names = [f"{child['org_name']}({child['org_code']})" for child in children_result[:3]]
                child_display = "、".join(child_names)
                if len(children_result) > 3:
                    child_display += f"等{len(children_result)}个子机构"
                return {
                    'success': False,
                    'error': f'该机构下存在子机构：{child_display}，请先删除子机构后再删除该机构'
                }
            
            # 检查是否有用户
            users_sql = """
            SELECT username, user_code
            FROM users
            WHERE org_code = :org_code AND status = 1
            """
            users_result = self.db_service.execute_query(users_sql, {'org_code': current_org['data']['org_code']})
            if users_result:
                user_names = [f"{user['username']}({user['user_code']})" for user in users_result[:3]]
                user_display = "、".join(user_names)
                if len(users_result) > 3:
                    user_display += f"等{len(users_result)}个用户"
                return {
                    'success': False,
                    'error': f'该机构下存在用户：{user_display}，请先转移或删除用户后再删除该机构'
                }
            
            # 软删除机构（将状态设置为0）
            sql = """
            UPDATE organizations 
            SET status = 0
            WHERE id = :org_id
            """
            
            self.db_service.execute_update(sql, {'org_id': org_id})
            
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
            self.redis.delete_cache(f"{self.cache_prefix}code:{org_code}")
            self.redis.delete_cache(f"{self.cache_prefix}id:{org_id}")
        except Exception as e:
            logger.warning(f"清除机构缓存失败: {str(e)}")
    
    def _clear_list_cache(self):
        """清除机构列表缓存"""
        try:
            # 使用通配符删除所有列表缓存
            keys = self.redis.get_keys_by_pattern(f"{self.list_cache_key}:*")
            if keys:
                for key in keys:
                    self.redis.delete_cache(key)
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
            # 首先获取当前机构信息
            current_org = self.get_organization_by_code(org_code)
            if not current_org['success'] or not current_org['data']:
                return {
                    'success': False,
                    'error': f'机构 {org_code} 不存在'
                }
            
            # 使用level_path字段获取所有子机构
            current_path = current_org['data']['level_path']
            
            # 查询以当前机构路径开头的所有机构（即所有子机构）
            sql = """
            SELECT id, org_code, parent_org_code, org_name, contact_person, contact_phone, 
                   contact_email, status, level_depth, level_path, created_at, updated_at
            FROM organizations 
            WHERE level_path LIKE :path_pattern AND status = 1
            ORDER BY level_depth, org_code
            """
            
            # 路径模式：查找以当前路径开头的所有机构
            path_pattern = f"{current_path}%"
            result = self.db_service.execute_query(sql, {'path_pattern': path_pattern})
            
            if not result:
                return {
                    'success': True,
                    'data': []
                }
            
            # 如果不包含自身，过滤掉当前机构
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
            # 首先获取当前机构信息
            current_org = self.get_organization_by_code(org_code)
            if not current_org['success'] or not current_org['data']:
                return {
                    'success': False,
                    'error': f'机构 {org_code} 不存在'
                }
            
            # 使用level_path字段获取所有上级机构
            current_path = current_org['data']['level_path']
            
            # 解析路径，获取所有上级机构编码
            # level_path 格式如: /0501/050101/050102/
            path_parts = [part for part in current_path.split('/') if part]
            
            if not path_parts:
                return {
                    'success': True,
                    'data': []
                }
            
            # 构建查询条件：获取路径中的所有机构
            parent_codes = path_parts[:-1] if not include_self else path_parts
            
            if not parent_codes:
                return {
                    'success': True,
                    'data': []
                }
            
            # 查询所有上级机构
            placeholders = ','.join([f':code_{i}' for i in range(len(parent_codes))])
            sql = f"""
            SELECT id, org_code, parent_org_code, org_name, contact_person, contact_phone, 
                   contact_email, status, level_depth, level_path, created_at, updated_at
            FROM organizations 
            WHERE org_code IN ({placeholders}) AND status = 1
            ORDER BY level_depth
            """
            
            params = {f'code_{i}': code for i, code in enumerate(parent_codes)}
            result = self.db_service.execute_query(sql, params)
            
            return {
                'success': True,
                'data': result or []
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
            # 获取所有机构
            sql = """
            SELECT id, org_code, parent_org_code, org_name, contact_person, contact_phone, 
                   contact_email, status, level_depth, level_path, created_at, updated_at
            FROM organizations 
            ORDER BY level_path, org_code
            """
            org_list = self.db_service.execute_query(sql)
            
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
            
            count_result = self.db_service.execute_query(count_sql, params)
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
            
            organizations = self.db_service.execute_query(sql, params)
            
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
            
            self.db_service.execute_update(sql, {
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
                self.db_service.execute_update(update_sql, {
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

def get_organization_service_instance() -> OrganizationService:
    """
    获取OrganizationService实例的工厂函数
    """
    from tools.redis_service import get_redis_service
    from tools.database import get_database_service
    
    redis_service = get_redis_service()
    db_service = get_database_service()
    return OrganizationService(redis_service=redis_service, db_service=db_service)

def get_organization_service() -> OrganizationService:
    """
    获取OrganizationService的单例实例
    """
    # 简化版本，直接返回新实例
    return get_organization_service_instance() 