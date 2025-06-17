import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule } from '@angular/forms';
import { NzButtonModule } from 'ng-zorro-antd/button';
import { NzCardModule } from 'ng-zorro-antd/card';
import { NzFormModule } from 'ng-zorro-antd/form';
import { NzIconModule } from 'ng-zorro-antd/icon';
import { NzInputModule } from 'ng-zorro-antd/input';
import { NzSelectModule } from 'ng-zorro-antd/select';
import { NzSpaceModule } from 'ng-zorro-antd/space';
import { NzTableModule } from 'ng-zorro-antd/table';
import { NzTagModule } from 'ng-zorro-antd/tag';

@Component({
  selector: 'app-permission',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    NzButtonModule,
    NzCardModule,
    NzFormModule,
    NzIconModule,
    NzInputModule,
    NzSelectModule,
    NzSpaceModule,
    NzTableModule,
    NzTagModule
  ],
  template: `
    <nz-card nzTitle="权限管理">
      <form nz-form [formGroup]="searchForm" class="search-form">
        <nz-space nzDirection="horizontal" nzSize="middle">
          <nz-form-item *nzSpaceItem>
            <nz-form-label>权限名称</nz-form-label>
            <nz-form-control>
              <input nz-input placeholder="请输入权限名称" formControlName="permissionName" style="width: 200px;">
            </nz-form-control>
          </nz-form-item>
          <nz-form-item *nzSpaceItem>
            <nz-form-label>资源类型</nz-form-label>
            <nz-form-control>
              <nz-select formControlName="resourceType" style="width: 150px;" nzPlaceHolder="请选择类型">
                <nz-option nzValue="" nzLabel="全部"></nz-option>
                <nz-option nzValue="system" nzLabel="系统管理"></nz-option>
                <nz-option nzValue="organization" nzLabel="机构管理"></nz-option>
                <nz-option nzValue="user" nzLabel="用户管理"></nz-option>
                <nz-option nzValue="role" nzLabel="角色管理"></nz-option>
                <nz-option nzValue="ai" nzLabel="AI问答"></nz-option>
                <nz-option nzValue="database" nzLabel="数据库"></nz-option>
              </nz-select>
            </nz-form-control>
          </nz-form-item>
          <button *nzSpaceItem nz-button nzType="primary" (click)="search()">
            <span nz-icon nzType="search"></span>
            查询
          </button>
          <button *nzSpaceItem nz-button (click)="reset()">
            <span nz-icon nzType="reload"></span>
            重置
          </button>
        </nz-space>
      </form>

      <nz-table #basicTable [nzData]="permissionList" [nzLoading]="loading" [nzPageSize]="10" class="permission-table">
        <thead>
          <tr>
            <th>权限编码</th>
            <th>权限名称</th>
            <th>API路径</th>
            <th>HTTP方法</th>
            <th>资源类型</th>
            <th>描述</th>
            <th>状态</th>
            <th>创建时间</th>
          </tr>
        </thead>
        <tbody>
          <tr *ngFor="let data of basicTable.data">
            <td>{{ data.permission_code }}</td>
            <td>{{ data.permission_name }}</td>
            <td><code>{{ data.api_path }}</code></td>
            <td>
              <nz-tag [nzColor]="getMethodColor(data.api_method)">
                {{ data.api_method }}
              </nz-tag>
            </td>
            <td>
              <nz-tag [nzColor]="getResourceTypeColor(data.resource_type)">
                {{ getResourceTypeText(data.resource_type) }}
              </nz-tag>
            </td>
            <td>{{ data.description || '-' }}</td>
            <td>
              <nz-tag [nzColor]="data.status === 1 ? 'green' : 'red'">
                {{ data.status === 1 ? '启用' : '禁用' }}
              </nz-tag>
            </td>
            <td>{{ data.created_at | date:'yyyy-MM-dd HH:mm' }}</td>
          </tr>
        </tbody>
      </nz-table>
    </nz-card>
  `,
  styles: [`
    .search-form {
      background: #f5f5f5;
      padding: 16px;
      margin-bottom: 16px;
      border-radius: 6px;
    }
    .permission-table {
      margin-top: 16px;
    }
    :host ::ng-deep .ant-table-thead > tr > th {
      background-color: #fafafa;
    }
    code {
      background: #f5f5f5;
      padding: 2px 6px;
      border-radius: 3px;
      font-size: 12px;
    }
  `]
})
export class PermissionComponent implements OnInit {
  searchForm: FormGroup;
  permissionList: any[] = [];
  loading = false;

  constructor(private fb: FormBuilder) {
    this.searchForm = this.fb.group({
      permissionName: [''],
      resourceType: ['']
    });
  }

  ngOnInit(): void {
    this.loadData();
  }

  loadData(): void {
    this.loading = true;
    setTimeout(() => {
      this.permissionList = [
        {
          id: 1,
          permission_code: 'SYSTEM_HEALTH',
          permission_name: '系统健康检查',
          api_path: '/api/v1/health',
          api_method: 'GET',
          resource_type: 'system',
          description: '查看系统健康状态',
          status: 1,
          created_at: '2025-06-17T10:00:00'
        },
        {
          id: 2,
          permission_code: 'ORG_CREATE',
          permission_name: '创建机构',
          api_path: '/api/v1/organizations',
          api_method: 'POST',
          resource_type: 'organization',
          description: '创建新机构',
          status: 1,
          created_at: '2025-06-17T10:00:00'
        },
        {
          id: 3,
          permission_code: 'USER_LIST',
          permission_name: '用户列表',
          api_path: '/api/v1/users',
          api_method: 'GET',
          resource_type: 'user',
          description: '查看用户列表',
          status: 1,
          created_at: '2025-06-17T10:00:00'
        },
        {
          id: 4,
          permission_code: 'AI_ASK',
          permission_name: 'AI问答',
          api_path: '/api/v1/ask',
          api_method: 'POST',
          resource_type: 'ai',
          description: 'AI智能问答',
          status: 1,
          created_at: '2025-06-17T10:00:00'
        }
      ];
      this.loading = false;
    }, 1000);
  }

  getMethodColor(method: string): string {
    switch (method) {
      case 'GET': return 'blue';
      case 'POST': return 'green';
      case 'PUT': return 'orange';
      case 'DELETE': return 'red';
      default: return 'default';
    }
  }

  getResourceTypeColor(type: string): string {
    switch (type) {
      case 'system': return 'purple';
      case 'organization': return 'cyan';
      case 'user': return 'blue';
      case 'role': return 'orange';
      case 'ai': return 'green';
      case 'database': return 'magenta';
      default: return 'default';
    }
  }

  getResourceTypeText(type: string): string {
    switch (type) {
      case 'system': return '系统管理';
      case 'organization': return '机构管理';
      case 'user': return '用户管理';
      case 'role': return '角色管理';
      case 'ai': return 'AI问答';
      case 'database': return '数据库';
      default: return type;
    }
  }

  search(): void {
    console.log('搜索', this.searchForm.value);
    this.loadData();
  }

  reset(): void {
    this.searchForm.reset();
    this.loadData();
  }
} 