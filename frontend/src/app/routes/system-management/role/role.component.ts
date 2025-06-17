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
  selector: 'app-role',
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
    <nz-card nzTitle="角色管理">
      <form nz-form [formGroup]="searchForm" class="search-form">
        <nz-space nzDirection="horizontal" nzSize="middle">
          <nz-form-item *nzSpaceItem>
            <nz-form-label>角色名称</nz-form-label>
            <nz-form-control>
              <input nz-input placeholder="请输入角色名称" formControlName="roleName" style="width: 200px;">
            </nz-form-control>
          </nz-form-item>
          <nz-form-item *nzSpaceItem>
            <nz-form-label>状态</nz-form-label>
            <nz-form-control>
              <nz-select formControlName="status" style="width: 120px;" nzPlaceHolder="请选择状态">
                <nz-option nzValue="" nzLabel="全部"></nz-option>
                <nz-option nzValue="1" nzLabel="启用"></nz-option>
                <nz-option nzValue="0" nzLabel="禁用"></nz-option>
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
          <button *nzSpaceItem nz-button nzType="primary" (click)="add()">
            <span nz-icon nzType="plus"></span>
            新增角色
          </button>
        </nz-space>
      </form>

      <nz-table #basicTable [nzData]="roleList" [nzLoading]="loading" [nzPageSize]="10" class="role-table">
        <thead>
          <tr>
            <th>角色编码</th>
            <th>角色名称</th>
            <th>角色等级</th>
            <th>所属机构</th>
            <th>描述</th>
            <th>状态</th>
            <th>创建时间</th>
            <th nzWidth="200px">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr *ngFor="let data of basicTable.data">
            <td>{{ data.role_code }}</td>
            <td>{{ data.role_name }}</td>
            <td>
              <nz-tag [nzColor]="getRoleLevelColor(data.role_level)">
                {{ getRoleLevelText(data.role_level) }}
              </nz-tag>
            </td>
            <td>{{ data.org_name || '-' }}</td>
            <td>{{ data.description || '-' }}</td>
            <td>
              <nz-tag [nzColor]="data.status === 1 ? 'green' : 'red'">
                {{ data.status === 1 ? '启用' : '禁用' }}
              </nz-tag>
            </td>
            <td>{{ data.created_at | date:'yyyy-MM-dd HH:mm' }}</td>
            <td>
              <nz-space nzSize="small">
                <button *nzSpaceItem nz-button nzType="link" nzSize="small" (click)="setPermissions(data)">
                  <span nz-icon nzType="setting"></span>
                  设置权限
                </button>
                <button *nzSpaceItem nz-button nzType="link" nzSize="small" (click)="edit(data)">
                  <span nz-icon nzType="edit"></span>
                  编辑
                </button>
                <button *nzSpaceItem nz-button nzType="link" nzSize="small" nzDanger (click)="delete(data)">
                  <span nz-icon nzType="delete"></span>
                  删除
                </button>
              </nz-space>
            </td>
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
    .role-table {
      margin-top: 16px;
    }
    :host ::ng-deep .ant-table-thead > tr > th {
      background-color: #fafafa;
    }
  `]
})
export class RoleComponent implements OnInit {
  searchForm: FormGroup;
  roleList: any[] = [];
  loading = false;

  constructor(private fb: FormBuilder) {
    this.searchForm = this.fb.group({
      roleName: [''],
      status: ['']
    });
  }

  ngOnInit(): void {
    this.loadData();
  }

  loadData(): void {
    this.loading = true;
    setTimeout(() => {
      this.roleList = [
        {
          id: 1,
          role_code: 'SUPER_ADMIN',
          role_name: '超级系统管理员',
          role_level: 1,
          org_name: '集团总部',
          description: '系统最高管理员，拥有所有权限',
          status: 1,
          created_at: '2025-06-17T10:00:00'
        },
        {
          id: 2,
          role_code: 'ORG_ADMIN',
          role_name: '机构管理员',
          role_level: 2,
          org_name: '省公司',
          description: '机构管理员，管理本机构用户和数据',
          status: 1,
          created_at: '2025-06-17T10:30:00'
        },
        {
          id: 3,
          role_code: 'NORMAL_USER',
          role_name: '普通用户',
          role_level: 3,
          org_name: '科数部',
          description: '普通用户，具有基本查询权限',
          status: 1,
          created_at: '2025-06-17T11:00:00'
        }
      ];
      this.loading = false;
    }, 1000);
  }

  getRoleLevelColor(level: number): string {
    switch (level) {
      case 1: return 'red';
      case 2: return 'orange';
      case 3: return 'blue';
      default: return 'default';
    }
  }

  getRoleLevelText(level: number): string {
    switch (level) {
      case 1: return '超级管理员';
      case 2: return '机构管理员';
      case 3: return '普通用户';
      default: return '未知';
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

  add(): void {
    console.log('新增角色');
  }

  edit(data: any): void {
    console.log('编辑角色', data);
  }

  delete(data: any): void {
    console.log('删除角色', data);
  }

  setPermissions(data: any): void {
    console.log('设置权限', data);
  }
} 