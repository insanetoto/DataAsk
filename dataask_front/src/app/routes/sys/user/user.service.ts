import { Injectable, inject } from '@angular/core';
import { _HttpClient } from '@delon/theme';
import { Observable } from 'rxjs';

// 用户实体接口
export interface User {
  id?: number;
  org_code: string;
  user_code: string;
  username: string;
  password_hash?: string;
  phone?: string;
  address?: string;
  role_id: number;
  last_login_at?: string;
  login_count?: number;
  status: number;
  created_at?: string;
  updated_at?: string;
  // 关联数据字段
  org_name?: string;
  role_code?: string;
  organization?: any;
  role?: any;
}

// 查询参数接口
export interface UserQuery {
  pi: number;
  ps: number;
  keyword?: string;
  status?: number;
  org_code?: string;
  role_id?: number;
}

@Injectable({ providedIn: 'root' })
export class SysUserService {
  private readonly http = inject(_HttpClient);

  // 暴露http客户端供子组件使用
  get httpClient() {
    return this.http;
  }

  /**
   * 获取用户列表
   */
  getUsers(params: Partial<UserQuery>): Observable<any> {
    return this.http.get('/users', params);
  }

  /**
   * 根据ID获取用户详情
   */
  getUserById(id: number): Observable<any> {
    return this.http.get(`/users/${id}`);
  }

  /**
   * 创建用户
   */
  createUser(user: Partial<User>): Observable<any> {
    return this.http.post('/users', user);
  }

  /**
   * 更新用户信息
   */
  updateUser(id: number, user: Partial<User>): Observable<any> {
    return this.http.put(`/users/${id}`, user);
  }

  /**
   * 删除用户
   */
  deleteUser(id: number): Observable<any> {
    return this.http.delete(`/users/${id}`);
  }

  /**
   * 获取用户角色
   */
  getUserRoles(userId: number): Observable<any> {
    return this.http.get(`/users/${userId}/roles`);
  }

  /**
   * 设置用户角色
   */
  setUserRoles(userId: number, roleIds: number[]): Observable<any> {
    return this.http.post(`/users/${userId}/roles`, { role_ids: roleIds });
  }

  /**
   * 获取用户权限
   */
  getUserPermissions(userId: number): Observable<any> {
    return this.http.get(`/users/${userId}/permissions`);
  }

  /**
   * 重置用户密码
   */
  resetPassword(userId: number, newPassword: string): Observable<any> {
    return this.http.put(`/users/${userId}/password`, { password: newPassword });
  }

  /**
   * 批量删除用户
   */
  batchDeleteUsers(userIds: number[]): Observable<any> {
    return this.http.post('/users/batch-delete', { user_ids: userIds });
  }

  /**
   * 导出用户数据
   */
  exportUsers(params: Partial<UserQuery>): Observable<any> {
    return this.http.get('/users/export', params);
  }
}
