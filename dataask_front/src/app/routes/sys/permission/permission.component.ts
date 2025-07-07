import { ChangeDetectionStrategy, ChangeDetectorRef, Component, OnInit, ViewChild, inject } from '@angular/core';
import { Router } from '@angular/router';
import { STChange, STColumn, STComponent, STData } from '@delon/abc/st';
import { _HttpClient, SettingsService } from '@delon/theme';
import { SHARED_IMPORTS } from '@shared';
import { NzMessageService } from 'ng-zorro-antd/message';
import { NzModalService } from 'ng-zorro-antd/modal';
import { finalize } from 'rxjs';

import { SysPermissionService, Permission, PermissionQuery } from './permission.service';

@Component({
  selector: 'app-sys-permission',
  templateUrl: './permission.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: SHARED_IMPORTS
})
export class SysPermissionComponent implements OnInit {
  private readonly http = inject(_HttpClient);
  private readonly msg = inject(NzMessageService);
  private readonly modalSrv = inject(NzModalService);
  private readonly cdr = inject(ChangeDetectorRef);
  private readonly permissionService = inject(SysPermissionService);
  private readonly router = inject(Router);
  private readonly settings = inject(SettingsService);

  // 查询参数
  q: PermissionQuery = {
    pi: 1,
    ps: 10,
    keyword: '',
    status: undefined,
    api_method: '',
    resource_type: ''
  };

  // 数据和状态
  data: Permission[] = [];
  treeData: any[] = [];
  loading = false;
  selectedRows: STData[] = [];
  expandForm = false;
  isTreeView = false;

  // 选项数据
  httpMethodOptions = this.permissionService.getHttpMethodOptions();
  resourceTypeOptions = this.permissionService.getResourceTypeOptions();

  // 状态选项
  statusOptions = [
    { label: '全部', value: undefined },
    { label: '启用', value: 1 },
    { label: '禁用', value: 0 }
  ];

  @ViewChild('st', { static: true })
  st!: STComponent;

  // 当前用户信息
  get currentUser() {
    return this.settings.user;
  }

  get currentUserRoleCode() {
    return this.currentUser?.roleCode || this.currentUser?.role_code || '';
  }

  // 表格列配置
  columns: STColumn[] = [
    { title: '', index: 'key', type: 'checkbox' },
    {
      title: '权限编码',
      index: 'permission_code',
      width: 150,
      sort: true
    },
    {
      title: '权限名称',
      index: 'permission_name',
      width: 150,
      sort: true
    },
    {
      title: 'API路径',
      index: 'api_path',
      width: 200
    },
    {
      title: 'HTTP方法',
      index: 'api_method',
      width: 100,
      render: 'method',
      filter: {
        menus: this.httpMethodOptions.map(m => ({ text: m.label, value: m.value })),
        fn: (filter, record) => record.api_method === filter.value
      }
    },
    {
      title: '资源类型',
      index: 'resource_type',
      width: 120,
      format: (item: Permission) => {
        const type = this.resourceTypeOptions.find(t => t.value === item.resource_type);
        return type ? type.label : item.resource_type || '-';
      }
    },
    {
      title: '描述',
      index: 'description',
      width: 200
    },
    {
      title: '状态',
      index: 'status',
      render: 'status',
      width: 80,
      filter: {
        menus: [
          { text: '启用', value: 1 },
          { text: '禁用', value: 0 }
        ],
        fn: (filter, record) => record.status === filter.value
      }
    },
    {
      title: '创建时间',
      index: 'created_at',
      type: 'date',
      width: 150,
      sort: true
    },
    {
      title: '操作',
      width: 240,
      fixed: 'right',
      buttons: [
        {
          text: '查看',
          icon: 'eye',
          click: (item: Permission) => this.viewPermission(item)
        },
        {
          text: '编辑',
          icon: 'edit',
          click: (item: Permission) => this.editPermission(item),
          iif: () => this.canManagePermission()
        },
        {
          text: '删除',
          icon: 'delete',
          type: 'del',
          click: (item: Permission) => this.deletePermission(item),
          iif: () => this.canManagePermission()
        }
      ]
    }
  ];

  ngOnInit(): void {
    this.getData();
  }

  /**
   * 检查是否可以管理权限
   */
  canManagePermission(): boolean {
    const currentRole = this.currentUserRoleCode;
    // 只有超级管理员可以管理权限
    return currentRole === 'SUPER_ADMIN';
  }

  /**
   * 检查是否可以查看权限
   */
  canViewPermission(): boolean {
    const currentRole = this.currentUserRoleCode;
    // 超级管理员和机构管理员都可以查看权限
    return currentRole === 'SUPER_ADMIN' || currentRole === 'ORG_ADMIN';
  }

  /**
   * 获取权限列表数据
   */
  getData(): void {
    this.loading = true;
    const params = {
      pi: this.q.pi,
      ps: this.q.ps,
      keyword: this.q.keyword || '',
      status: this.q.status,
      api_method: this.q.api_method || '',
      resource_type: this.q.resource_type || ''
    };

    this.permissionService
      .getPermissions(params)
      .pipe(
        finalize(() => {
          this.loading = false;
          this.cdr.detectChanges();
        })
      )
      .subscribe({
        next: res => {
          if (res.code === 200 || res.success === true) {
            this.data = res.data?.list || res.data?.items || res.data || [];
          } else {
            this.msg.error(res.message || '获取权限数据失败');
            this.data = [];
          }
        },
        error: error => {
          // 检查是否是被HTTP拦截器误判的成功响应
          if (error.status === 200 && error.ok && error.body) {
            if (error.body.success === true || error.body.code === 200) {
              this.data = error.body.data?.list || error.body.data?.items || error.body.data || [];
              return;
            }
          }

          this.msg.error('获取权限数据失败');
          this.data = [];
        }
      });
  }

  /**
   * 获取权限树形数据
   */
  getTreeData(): void {
    this.loading = true;
    this.permissionService
      .getPermissionTree()
      .pipe(
        finalize(() => {
          this.loading = false;
          this.cdr.detectChanges();
        })
      )
      .subscribe({
        next: res => {
          if (res.code === 200 || res.success === true) {
            this.treeData = res.data || [];
          } else {
            this.msg.error(res.message || '获取树形数据失败');
            this.treeData = [];
          }
        },
        error: error => {
          // 检查是否是被HTTP拦截器误判的成功响应
          if (error.status === 200 && error.ok && error.body) {
            if (error.body.success === true || error.body.code === 200) {
              this.treeData = error.body.data || [];
              return;
            }
          }

          this.msg.error('获取树形数据失败');
          this.treeData = [];
        }
      });
  }

  /**
   * 表格变化事件
   */
  stChange(e: STChange): void {
    switch (e.type) {
      case 'checkbox':
        this.selectedRows = e.checkbox!;
        this.cdr.detectChanges();
        break;
      case 'filter':
        this.getData();
        break;
      case 'sort':
        this.getData();
        break;
      case 'pi':
        this.q.pi = e.pi!;
        this.getData();
        break;
      case 'ps':
        this.q.ps = e.ps!;
        this.getData();
        break;
    }
  }

  /**
   * 切换视图模式
   */
  toggleView(): void {
    this.isTreeView = !this.isTreeView;
    if (this.isTreeView) {
      this.getTreeData();
    } else {
      this.getData();
    }
  }

  /**
   * 新增权限
   */
  addPermission(): void {
    this.router.navigate(['/sys/permission/edit/new']);
  }

  /**
   * 查看权限
   */
  viewPermission(item: Permission): void {
    this.router.navigate(['/sys/permission/view', item.id]);
  }

  /**
   * 编辑权限
   */
  editPermission(item: Permission): void {
    this.router.navigate(['/sys/permission/edit', item.id]);
  }

  /**
   * 删除权限
   */
  deletePermission(item: Permission): void {
    this.modalSrv.confirm({
      nzTitle: '确认删除',
      nzContent: `确定要删除权限 "${item.permission_name}" 吗？`,
      nzOnOk: () => {
        return this.permissionService.deletePermission(item.id!).subscribe({
          next: res => {
            // 兼容不同的响应格式
            if (res.code === 200 || res.success === true || res.message === '权限删除成功') {
              this.msg.success(res.message || '删除成功');
              this.getData();
            } else {
              this.msg.error(res.message || res.error || '删除失败');
            }
          },
          error: error => {
            console.error('删除权限失败:', error);
            // 检查是否是被HTTP拦截器误判的成功响应
            if (error.status === 200 && error.ok && error.body) {
              if (error.body.success === true || error.body.code === 200 || error.body.message === '权限删除成功') {
                this.msg.success(error.body.message || '删除成功');
                this.getData();
                return;
              }
            }
            this.msg.error('删除失败');
          }
        });
      }
    });
  }

  /**
   * 批量删除
   */
  batchDelete(): void {
    if (this.selectedRows.length === 0) {
      this.msg.warning('请选择要删除的权限');
      return;
    }

    this.modalSrv.confirm({
      nzTitle: '确认批量删除',
      nzContent: `确定要删除选中的 ${this.selectedRows.length} 个权限吗？`,
      nzOnOk: () => {
        const permissionIds = this.selectedRows.map(row => row['id']);
        return this.permissionService.batchDeletePermissions(permissionIds).subscribe({
          next: res => {
            // 兼容不同的响应格式
            if (res.code === 200 || res.success === true || res.message?.includes('删除成功')) {
              this.msg.success(res.message || '批量删除成功');
              this.getData();
              this.st.clearCheck();
            } else {
              this.msg.error(res.message || res.error || '批量删除失败');
            }
          },
          error: error => {
            console.error('批量删除权限失败:', error);
            // 检查是否是被HTTP拦截器误判的成功响应
            if (error.status === 200 && error.ok && error.body) {
              if (error.body.success === true || error.body.code === 200 || error.body.message?.includes('删除成功')) {
                this.msg.success(error.body.message || '批量删除成功');
                this.getData();
                this.st.clearCheck();
                return;
              }
            }
            this.msg.error('批量删除失败');
          }
        });
      }
    });
  }

  /**
   * 重置搜索
   */
  reset(): void {
    this.q = {
      pi: 1,
      ps: 10,
      keyword: '',
      status: undefined,
      api_method: '',
      resource_type: ''
    };
    this.getData();
  }
}
