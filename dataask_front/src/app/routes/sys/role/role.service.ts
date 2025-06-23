import { Injectable, inject } from '@angular/core';
import { _HttpClient } from '@delon/theme';
import { Observable } from 'rxjs';

// 角色实体接口
export interface Role {
  id?: number;
  role_code: string;
  role_name: string;
  role_level: number;
  description?: string;
  status: number;
  created_at?: string;
  updated_at?: string;
  // 关联数据
  users?: any[];
  permissions?: any[];
}

// 查询参数接口
export interface RoleQuery {
  pi: number;
  ps: number;
  keyword?: string;
  status?: number;
  role_level?: number;
}

@Injectable({ providedIn: 'root' })
export class SysRoleService {
  private readonly http = inject(_HttpClient);

  /**
   * 获取角色列表
   */
  getRoles(params: Partial<RoleQuery>): Observable<any> {
    return this.http.get('/roles', params);
  }

  /**
   * 根据ID获取角色详情
   */
  getRoleById(id: number): Observable<any> {
    return this.http.get(`/roles/${id}`);
  }

  /**
   * 创建角色
   */
  createRole(role: Partial<Role>): Observable<any> {
    return this.http.post('/roles', role);
  }

  /**
   * 更新角色信息
   */
  updateRole(id: number, role: Partial<Role>): Observable<any> {
    return this.http.put(`/roles/${id}`, role);
  }

  /**
   * 删除角色
   */
  deleteRole(id: number): Observable<any> {
    return this.http.delete(`/roles/${id}`);
  }

  /**
   * 获取角色权限
   */
  getRolePermissions(roleId: number): Observable<any> {
    return this.http.get(`/roles/${roleId}/permissions`);
  }

  /**
   * 设置角色权限
   */
  setRolePermissions(roleId: number, permissionIds: number[]): Observable<any> {
    return this.http.post(`/roles/${roleId}/permissions`, { permission_ids: permissionIds });
  }

  /**
   * 批量删除角色
   */
  batchDeleteRoles(roleIds: number[]): Observable<any> {
    return this.http.post('/roles/batch-delete', { role_ids: roleIds });
  }

  /**
   * 获取角色等级选项
   */
  getRoleLevelOptions(): Array<{ label: string; value: number }> {
    return [
      { label: '超级管理员', value: 1 },
      { label: '机构管理员', value: 2 },
      { label: '普通用户', value: 3 }
    ];
  }
}
