import { ChangeDetectionStrategy, ChangeDetectorRef, Component, OnInit, TemplateRef, ViewChild, inject } from '@angular/core';
import { STChange, STColumn, STComponent, STData } from '@delon/abc/st';
import { _HttpClient } from '@delon/theme';
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

  // 表单数据
  editingPermission: Partial<Permission> = {};
  isEditMode = false;
  modalTitle = '';

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
          click: (item: Permission) => this.editPermission(item)
        },
        {
          text: '删除',
          icon: 'delete',
          type: 'del',
          click: (item: Permission) => this.deletePermission(item)
        }
      ]
    }
  ];

  ngOnInit(): void {
    this.getData();
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
  addPermission(tpl: TemplateRef<unknown>): void {
    this.editingPermission = {
      status: 1,
      api_method: 'GET'
    };
    this.isEditMode = false;
    this.modalTitle = '新增权限';
    this.showModal(tpl);
  }

  /**
   * 查看权限
   */
  viewPermission(item: Permission): void {
    this.editingPermission = { ...item };
    this.isEditMode = false;
    this.modalTitle = '查看权限';
    this.msg.info(`查看权限: ${item.permission_name}`);
  }

  /**
   * 编辑权限
   */
  editPermission(item: Permission, tpl?: TemplateRef<unknown>): void {
    this.editingPermission = { ...item };
    this.isEditMode = true;
    this.modalTitle = '编辑权限';
    if (tpl) {
      this.showModal(tpl);
    }
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
            if (res.code === 200 || res.success === true) {
              this.msg.success('删除成功');
              this.getData();
            } else {
              this.msg.error(res.message || res.error || '删除失败');
            }
          },
          error: () => {
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
            if (res.code === 200 || res.success === true) {
              this.msg.success('批量删除成功');
              this.getData();
              this.st.clearCheck();
            } else {
              this.msg.error(res.message || res.error || '批量删除失败');
            }
          },
          error: () => {
            this.msg.error('批量删除失败');
          }
        });
      }
    });
  }

  /**
   * 显示模态框
   */
  showModal(tpl: TemplateRef<unknown>): void {
    this.modalSrv.create({
      nzTitle: this.modalTitle,
      nzContent: tpl,
      nzWidth: 600,
      nzOnOk: () => {
        return this.savePermission();
      }
    });
  }

  /**
   * 保存权限
   */
  savePermission(): Promise<boolean> {
    return new Promise(resolve => {
      // 表单验证
      if (
        !this.editingPermission.permission_code ||
        !this.editingPermission.permission_name ||
        !this.editingPermission.api_path ||
        !this.editingPermission.api_method
      ) {
        this.msg.error('请填写完整信息');
        resolve(false);
        return;
      }

      const request = this.isEditMode
        ? this.permissionService.updatePermission(this.editingPermission.id!, this.editingPermission)
        : this.permissionService.createPermission(this.editingPermission);

      request.subscribe({
        next: res => {
          if (res.code === 200 || res.success === true) {
            this.msg.success(this.isEditMode ? '更新成功' : '创建成功');
            this.getData();
            resolve(true);
          } else {
            this.msg.error(res.message || res.error || '保存失败');
            resolve(false);
          }
        },
        error: () => {
          this.msg.error('保存失败');
          resolve(false);
        }
      });
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
