import { Injectable, inject } from '@angular/core';
import { _HttpClient } from '@delon/theme';
import { Observable } from 'rxjs';

// 权限实体接口
export interface Permission {
  id?: number;
  permission_code: string;
  permission_name: string;
  api_path: string;
  api_method: string;
  resource_type?: string;
  description?: string;
  status: number;
  created_at?: string;
  updated_at?: string;
  // 关联数据
  roles?: any[];
}

// 查询参数接口
export interface PermissionQuery {
  pi: number;
  ps: number;
  keyword?: string;
  status?: number;
  api_method?: string;
  resource_type?: string;
}

@Injectable({ providedIn: 'root' })
export class SysPermissionService {
  private readonly http = inject(_HttpClient);

  /**
   * 获取权限列表
   */
  getPermissions(params: Partial<PermissionQuery>): Observable<any> {
    return this.http.get('/permissions', params);
  }

  /**
   * 根据ID获取权限详情
   */
  getPermissionById(id: number): Observable<any> {
    return this.http.get(`/permissions/${id}`);
  }

  /**
   * 创建权限
   */
  createPermission(permission: Partial<Permission>): Observable<any> {
    return this.http.post('/permissions', permission);
  }

  /**
   * 更新权限信息
   */
  updatePermission(id: number, permission: Partial<Permission>): Observable<any> {
    return this.http.put(`/permissions/${id}`, permission);
  }

  /**
   * 删除权限
   */
  deletePermission(id: number): Observable<any> {
    return this.http.delete(`/permissions/${id}`);
  }

  /**
   * 获取权限树形结构
   */
  getPermissionTree(): Observable<any> {
    return this.http.get('/permissions/tree');
  }

  /**
   * 批量删除权限
   */
  batchDeletePermissions(permissionIds: number[]): Observable<any> {
    return this.http.post('/permissions/batch-delete', { permission_ids: permissionIds });
  }

  /**
   * 获取HTTP方法选项
   */
  getHttpMethodOptions(): Array<{ label: string; value: string }> {
    return [
      { label: 'GET', value: 'GET' },
      { label: 'POST', value: 'POST' },
      { label: 'PUT', value: 'PUT' },
      { label: 'DELETE', value: 'DELETE' },
      { label: 'PATCH', value: 'PATCH' }
    ];
  }

  /**
   * 获取资源类型选项
   */
  getResourceTypeOptions(): Array<{ label: string; value: string }> {
    return [
      { label: '用户管理', value: 'user' },
      { label: '角色管理', value: 'role' },
      { label: '权限管理', value: 'permission' },
      { label: '机构管理', value: 'organization' },
      { label: '系统管理', value: 'system' },
      { label: 'AI引擎', value: 'ai-engine' },
      { label: '工作空间', value: 'workspace' }
    ];
  }
}
