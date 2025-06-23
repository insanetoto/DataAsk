import { ChangeDetectionStrategy, ChangeDetectorRef, Component, OnInit, TemplateRef, ViewChild, inject } from '@angular/core';
import { STChange, STColumn, STComponent, STData } from '@delon/abc/st';
import { _HttpClient } from '@delon/theme';
import { SHARED_IMPORTS } from '@shared';
import { NzMessageService } from 'ng-zorro-antd/message';
import { NzModalService } from 'ng-zorro-antd/modal';
import { finalize } from 'rxjs';

import { SysRoleService, Role, RoleQuery } from './role.service';

@Component({
  selector: 'app-sys-role',
  templateUrl: './role.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: SHARED_IMPORTS
})
export class SysRoleComponent implements OnInit {
  private readonly http = inject(_HttpClient);
  private readonly msg = inject(NzMessageService);
  private readonly modalSrv = inject(NzModalService);
  private readonly cdr = inject(ChangeDetectorRef);
  private readonly roleService = inject(SysRoleService);

  // 查询参数
  q: RoleQuery = {
    pi: 1,
    ps: 10,
    keyword: '',
    status: undefined,
    role_level: undefined
  };

  // 数据和状态
  data: Role[] = [];
  loading = false;
  selectedRows: STData[] = [];
  expandForm = false;

  // 表单数据
  editingRole: Partial<Role> = {};
  isEditMode = false;
  modalTitle = '';

  // 选项数据

  roleLevelOptions = this.roleService.getRoleLevelOptions();
  permissionOptions: any[] = [];
  selectedPermissions: number[] = [];

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
      title: '角色编码',
      index: 'role_code',
      width: 120,
      sort: true
    },
    {
      title: '角色名称',
      index: 'role_name',
      width: 150,
      sort: true
    },
    {
      title: '角色等级',
      index: 'role_level',
      width: 120,
      format: (item: Role) => {
        const level = this.roleLevelOptions.find(l => l.value === item.role_level);
        return level ? level.label : '-';
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
      width: 320,
      fixed: 'right',
      buttons: [
        {
          text: '查看',
          icon: 'eye',
          click: (item: Role) => this.viewRole(item)
        },
        {
          text: '编辑',
          icon: 'edit',
          click: (item: Role) => this.editRole(item)
        },
        {
          text: '权限',
          icon: 'lock',
          click: (item: Role) => this.managePermissions(item)
        },
        {
          text: '删除',
          icon: 'delete',
          type: 'del',
          click: (item: Role) => this.deleteRole(item)
        }
      ]
    }
  ];

  ngOnInit(): void {
    this.getData();
    this.loadPermissionOptions();
  }

  /**
   * 获取角色列表数据
   */
  getData(): void {
    this.loading = true;
    const params = {
      pi: this.q.pi,
      ps: this.q.ps,
      keyword: this.q.keyword || '',
      status: this.q.status,
      role_level: this.q.role_level
    };

    this.roleService
      .getRoles(params)
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
            this.msg.error(res.message || '获取角色数据失败');
            this.data = [];
          }
        },
        error: error => {
          console.error('获取角色数据失败:', error);

          // 检查是否是被HTTP拦截器误判的成功响应
          if (error.status === 200 && error.ok && error.body) {
            if (error.body.success === true || error.body.code === 200) {
              this.data = error.body.data?.list || error.body.data?.items || error.body.data || [];
              return;
            }
          }

          this.msg.error('获取角色数据失败');
          this.data = [];
        }
      });
  }

  /**
   * 加载权限选项
   */
  loadPermissionOptions(): void {
    this.http.get('/permissions', { pi: 1, ps: 1000, status: 1 }).subscribe({
      next: res => {
        if (res.code === 200 || res.success === true) {
          this.permissionOptions = res.data?.list || res.data?.items || res.data || [];
        }
      },
      error: error => {
        console.error('加载权限选项失败:', error);

        if (error.status === 200 && error.ok && error.body) {
          if (error.body.success === true || error.body.code === 200) {
            this.permissionOptions = error.body.data?.list || error.body.data?.items || error.body.data || [];
          }
        }
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
   * 新增角色
   */
  addRole(tpl: TemplateRef<unknown>): void {
    this.editingRole = {
      status: 1,
      role_level: 3
    };
    this.isEditMode = false;
    this.modalTitle = '新增角色';
    this.showModal(tpl);
  }

  /**
   * 查看角色
   */
  viewRole(item: Role): void {
    this.editingRole = { ...item };
    this.isEditMode = false;
    this.modalTitle = '查看角色';
    this.msg.info(`查看角色: ${item.role_name}`);
  }

  /**
   * 编辑角色
   */
  editRole(item: Role, tpl?: TemplateRef<unknown>): void {
    this.editingRole = { ...item };
    this.isEditMode = true;
    this.modalTitle = '编辑角色';
    if (tpl) {
      this.showModal(tpl);
    }
  }

  /**
   * 删除角色
   */
  deleteRole(item: Role): void {
    this.modalSrv.confirm({
      nzTitle: '确认删除',
      nzContent: `确定要删除角色 "${item.role_name}" 吗？`,
      nzOnOk: () => {
        return this.roleService.deleteRole(item.id!).subscribe({
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
   * 管理权限
   */
  managePermissions(item: Role, tpl?: TemplateRef<unknown>): void {
    this.editingRole = { ...item };
    this.modalTitle = `管理权限 - ${item.role_name}`;

    // 加载角色当前权限
    this.roleService.getRolePermissions(item.id!).subscribe({
      next: res => {
        if (res.code === 200 || res.success === true) {
          this.selectedPermissions = (res.data || []).map((p: any) => p.id);
        }
      },
      error: error => {
        console.error('获取角色权限失败:', error);

        if (error.status === 200 && error.ok && error.body) {
          if (error.body.success === true || error.body.code === 200) {
            this.selectedPermissions = (error.body.data || []).map((p: any) => p.id);
          }
        }
      }
    });

    if (tpl) {
      this.showPermissionModal(tpl);
    }
  }

  /**
   * 批量删除
   */
  batchDelete(): void {
    if (this.selectedRows.length === 0) {
      this.msg.warning('请选择要删除的角色');
      return;
    }

    this.modalSrv.confirm({
      nzTitle: '确认批量删除',
      nzContent: `确定要删除选中的 ${this.selectedRows.length} 个角色吗？`,
      nzOnOk: () => {
        const roleIds = this.selectedRows.map(row => row['id']);
        return this.roleService.batchDeleteRoles(roleIds).subscribe({
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
        return this.saveRole();
      }
    });
  }

  /**
   * 显示权限管理模态框
   */
  showPermissionModal(tpl: TemplateRef<unknown>): void {
    this.modalSrv.create({
      nzTitle: this.modalTitle,
      nzContent: tpl,
      nzWidth: 800,
      nzOnOk: () => {
        return this.savePermissions();
      }
    });
  }

  /**
   * 保存角色
   */
  saveRole(): Promise<boolean> {
    return new Promise(resolve => {
      // 表单验证
      if (!this.editingRole.role_code || !this.editingRole.role_name || !this.editingRole.role_level) {
        this.msg.error('请填写完整信息');
        resolve(false);
        return;
      }

      const request = this.isEditMode
        ? this.roleService.updateRole(this.editingRole.id!, this.editingRole)
        : this.roleService.createRole(this.editingRole);

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
   * 保存权限
   */
  savePermissions(): Promise<boolean> {
    return new Promise(resolve => {
      this.roleService.setRolePermissions(this.editingRole.id!, this.selectedPermissions).subscribe({
        next: res => {
          if (res.code === 200 || res.success === true) {
            this.msg.success('权限设置成功');
            resolve(true);
          } else {
            this.msg.error(res.message || res.error || '权限设置失败');
            resolve(false);
          }
        },
        error: () => {
          this.msg.error('权限设置失败');
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
      role_level: undefined
    };
    this.getData();
  }
}
