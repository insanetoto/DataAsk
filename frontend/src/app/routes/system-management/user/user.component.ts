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
  selector: 'app-user',
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
    <nz-card nzTitle="人员管理">
      <form nz-form [formGroup]="searchForm" class="search-form">
        <nz-space nzDirection="horizontal" nzSize="middle">
          <nz-form-item *nzSpaceItem>
            <nz-form-label>用户名称</nz-form-label>
            <nz-form-control>
              <input nz-input placeholder="请输入用户名称" formControlName="username" style="width: 200px;">
            </nz-form-control>
          </nz-form-item>
          <nz-form-item *nzSpaceItem>
            <nz-form-label>所属机构</nz-form-label>
            <nz-form-control>
              <nz-select formControlName="orgCode" style="width: 150px;" nzPlaceHolder="请选择机构">
                <nz-option nzValue="" nzLabel="全部"></nz-option>
                <nz-option nzValue="05" nzLabel="集团总部"></nz-option>
                <nz-option nzValue="0501" nzLabel="省公司"></nz-option>
                <nz-option nzValue="050101" nzLabel="科数部"></nz-option>
              </nz-select>
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
            新增用户
          </button>
        </nz-space>
      </form>

      <nz-table #basicTable [nzData]="userList" [nzLoading]="loading" [nzPageSize]="10" class="user-table">
        <thead>
          <tr>
            <th>用户编码</th>
            <th>用户名称</th>
            <th>所属机构</th>
            <th>角色</th>
            <th>联系电话</th>
            <th>最后登录</th>
            <th>登录次数</th>
            <th>状态</th>
            <th nzWidth="200px">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr *ngFor="let data of basicTable.data">
            <td>{{ data.user_code }}</td>
            <td>{{ data.username }}</td>
            <td>{{ data.org_name }}</td>
            <td>
              <nz-tag [nzColor]="getRoleColor(data.role_level)">
                {{ data.role_name }}
              </nz-tag>
            </td>
            <td>{{ data.phone || '-' }}</td>
            <td>{{ data.last_login_at | date:'yyyy-MM-dd HH:mm' }}</td>
            <td>{{ data.login_count }}</td>
            <td>
              <nz-tag [nzColor]="data.status === 1 ? 'green' : 'red'">
                {{ data.status === 1 ? '启用' : '禁用' }}
              </nz-tag>
            </td>
            <td>
              <nz-space nzSize="small">
                <button *nzSpaceItem nz-button nzType="link" nzSize="small" (click)="resetPassword(data)">
                  <span nz-icon nzType="key"></span>
                  重置密码
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
    .user-table {
      margin-top: 16px;
    }
    :host ::ng-deep .ant-table-thead > tr > th {
      background-color: #fafafa;
    }
  `]
})
export class UserComponent implements OnInit {
  searchForm: FormGroup;
  userList: any[] = [];
  loading = false;

  constructor(private fb: FormBuilder) {
    this.searchForm = this.fb.group({
      username: [''],
      orgCode: [''],
      status: ['']
    });
  }

  ngOnInit(): void {
    this.loadData();
  }

  loadData(): void {
    this.loading = true;
    setTimeout(() => {
      this.userList = [
        {
          id: 1,
          user_code: 'admin',
          username: '超级管理员',
          org_name: '集团总部',
          role_name: '超级系统管理员',
          role_level: 1,
          phone: '13800000000',
          last_login_at: '2025-06-17T13:06:28',
          login_count: 3,
          status: 1,
          created_at: '2025-06-17T03:43:35'
        },
        {
          id: 2,
          user_code: 'manager01',
          username: '省公司管理员',
          org_name: '省公司',
          role_name: '机构管理员',
          role_level: 2,
          phone: '13800000001',
          last_login_at: '2025-06-17T12:30:00',
          login_count: 15,
          status: 1,
          created_at: '2025-06-17T09:00:00'
        },
        {
          id: 3,
          user_code: 'user01',
          username: '科数部用户',
          org_name: '科数部',
          role_name: '普通用户',
          role_level: 3,
          phone: '13800000002',
          last_login_at: '2025-06-17T11:45:00',
          login_count: 8,
          status: 1,
          created_at: '2025-06-17T08:30:00'
        }
      ];
      this.loading = false;
    }, 1000);
  }

  getRoleColor(level: number): string {
    switch (level) {
      case 1: return 'red';
      case 2: return 'orange';
      case 3: return 'blue';
      default: return 'default';
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
    console.log('新增用户');
  }

  edit(data: any): void {
    console.log('编辑用户', data);
  }

  delete(data: any): void {
    console.log('删除用户', data);
  }

  resetPassword(data: any): void {
    console.log('重置密码', data);
  }
} 