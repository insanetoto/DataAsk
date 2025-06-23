import { Injectable, inject } from '@angular/core';
import { _HttpClient } from '@delon/theme';
import { Observable } from 'rxjs';

export interface Organization {
  id?: number;
  org_code: string;
  org_name: string;
  parent_org_code?: string;
  level_depth?: number;
  contact_person: string;
  contact_phone: string;
  contact_email: string;
  status: number;
  created_at?: string;
  updated_at?: string;
  children?: Organization[];
  parent?: Organization;
}

export interface OrganizationQuery {
  pi: number;
  ps: number;
  keyword?: string;
  status?: number;
  parent_org_code?: string;
}

@Injectable({ providedIn: 'root' })
export class SysOrgService {
  private readonly http = inject(_HttpClient);

  /**
   * 获取机构列表
   */
  getOrganizations(params: OrganizationQuery): Observable<any> {
    return this.http.get('/api/organizations', params);
  }

  /**
   * 获取机构树形结构
   */
  getOrganizationTree(rootOrgCode?: string): Observable<any> {
    const params = rootOrgCode ? { root_org_code: rootOrgCode } : {};
    return this.http.get('/api/organizations/tree', params);
  }

  /**
   * 根据ID获取机构详情
   */
  getOrganization(id: number): Observable<any> {
    return this.http.get(`/api/organizations/${id}`);
  }

  /**
   * 根据编码获取机构详情
   */
  getOrganizationByCode(orgCode: string): Observable<any> {
    return this.http.get(`/api/organizations/code/${orgCode}`);
  }

  /**
   * 创建机构
   */
  createOrganization(data: Partial<Organization>): Observable<any> {
    return this.http.post('/api/organizations', data);
  }

  /**
   * 更新机构
   */
  updateOrganization(id: number, data: Partial<Organization>): Observable<any> {
    return this.http.put(`/api/organizations/${id}`, data);
  }

  /**
   * 删除机构
   */
  deleteOrganization(id: number): Observable<any> {
    return this.http.delete(`/api/organizations/${id}`);
  }

  /**
   * 获取子机构列表
   */
  getChildren(orgCode: string): Observable<any> {
    return this.http.get(`/api/organizations/${orgCode}/children`);
  }

  /**
   * 获取上级机构链
   */
  getParents(orgCode: string): Observable<any> {
    return this.http.get(`/api/organizations/${orgCode}/parents`);
  }

  /**
   * 移动机构（更改上级机构）
   */
  moveOrganization(orgCode: string, newParentCode?: string): Observable<any> {
    return this.http.put(`/api/organizations/${orgCode}/move`, {
      new_parent_code: newParentCode
    });
  }
}
