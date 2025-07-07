import { ChangeDetectionStrategy, ChangeDetectorRef, Component, OnInit, TemplateRef, ViewChild, inject } from '@angular/core';
import { Router } from '@angular/router';
import { STChange, STColumn, STComponent, STData } from '@delon/abc/st';
import { _HttpClient, SettingsService } from '@delon/theme';
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
  private readonly router = inject(Router);
  private readonly settings = inject(SettingsService);

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

  // 权限管理数据
  editingRole: Partial<Role> = {};
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

  // 当前用户信息
  get currentUser() {
    return this.settings.user;
  }

  get currentUserRoleCode() {
    return this.currentUser?.roleCode || this.currentUser?.role_code || this.currentUser?.role?.role_code;
  }

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
      width: 260,
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
          click: (item: Role) => this.editRole(item),
          iif: (item: Role) => this.canManageRole(item)
        },
        {
          text: '权限',
          icon: 'lock',
          click: (item: Role) => this.managePermissions(item),
          iif: (item: Role) => this.canManageRole(item)
        },
        {
          text: '删除',
          icon: 'delete',
          type: 'del',
          click: (item: Role) => this.deleteRole(item),
          iif: (item: Role) => this.canManageRole(item)
        }
      ]
    }
  ];

  ngOnInit(): void {
    // 添加调试信息
    console.log('当前用户信息:', this.currentUser);
    console.log('当前用户角色编码:', this.currentUserRoleCode);
    console.log('是否可以管理角色:', this.canManageAnyRole());

    // 移除组件级别的权限检查，因为路由级别已经有权限控制
    // this.checkPermissions();
    this.getData();
    this.loadPermissionOptions();
  }

  /**
   * 检查是否可以管理任何角色
   */
  canManageAnyRole(): boolean {
    const currentRole = this.currentUserRoleCode;
    return currentRole === 'SUPER_ADMIN' || currentRole === 'ORG_ADMIN';
  }

  /**
   * 检查是否可以管理指定角色
   */
  canManageRole(role: Role): boolean {
    const currentRole = this.currentUserRoleCode;

    // 超级管理员可以管理所有角色
    if (currentRole === 'SUPER_ADMIN') {
      return true;
    }

    // 机构管理员不能管理超级管理员角色
    if (currentRole === 'ORG_ADMIN') {
      return role.role_level !== 1; // 不能管理超级管理员（role_level=1）
    }

    return false;
  }

  /**
   * 检查是否可以新增角色
   */
  canAddRole(): boolean {
    return this.canManageAnyRole();
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

          // 检查是否是权限错误
          if (error.status === 403) {
            this.msg.error('您没有权限访问角色管理');
            this.router.navigate(['/dashboard']);
            return;
          }

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
  addRole(): void {
    this.router.navigate(['/sys/role/edit/new']);
  }

  /**
   * 查看角色
   */
  viewRole(item: Role): void {
    this.router.navigate(['/sys/role/view', item.id]);
  }

  /**
   * 编辑角色
   */
  editRole(item: Role): void {
    this.router.navigate(['/sys/role/edit', item.id]);
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
