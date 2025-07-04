import { ChangeDetectionStrategy, ChangeDetectorRef, Component, OnInit, TemplateRef, ViewChild, inject } from '@angular/core';
import { Router } from '@angular/router';
import { STChange, STColumn, STComponent, STData } from '@delon/abc/st';
import { _HttpClient, SettingsService } from '@delon/theme';
import { SHARED_IMPORTS } from '@shared';
import { NzMessageService } from 'ng-zorro-antd/message';
import { NzModalService } from 'ng-zorro-antd/modal';
import { finalize } from 'rxjs';

import { SysUserService, User, UserQuery } from './user.service';

@Component({
  selector: 'app-sys-user',
  templateUrl: './user.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: SHARED_IMPORTS
})
export class SysUserComponent implements OnInit {
  private readonly http = inject(_HttpClient);
  private readonly msg = inject(NzMessageService);
  private readonly modalSrv = inject(NzModalService);
  private readonly cdr = inject(ChangeDetectorRef);
  private readonly router = inject(Router);
  private readonly userService = inject(SysUserService);
  private readonly settings = inject(SettingsService);

  // 查询参数
  q: UserQuery = {
    pi: 1,
    ps: 10,
    keyword: '',
    status: undefined,
    org_code: '',
    role_id: undefined
  };

  // 数据和状态
  data: User[] = [];
  loading = false;
  selectedRows: STData[] = [];
  expandForm = false;

  // 表单数据
  editingUser: Partial<User> = {};
  isEditMode = false;
  modalTitle = '';

  // 选项数据
  organizationOptions: any[] = [];
  roleOptions: any[] = [];

  // 状态选项
  statusOptions = [
    { label: '全部', value: undefined },
    { label: '启用', value: 1 },
    { label: '禁用', value: 0 }
  ];

  @ViewChild('st', { static: true })
  st!: STComponent;

  @ViewChild('deleteConfirmTemplate', { static: true })
  deleteConfirmTemplate!: TemplateRef<any>;

  // 表格列配置
  columns: STColumn[] = [
    { title: '', index: 'key', type: 'checkbox' },
    {
      title: '用户编码',
      index: 'user_code',
      width: 120,
      sort: true
    },
    {
      title: '用户名称',
      index: 'username',
      width: 150,
      sort: true
    },
    {
      title: '所属机构',
      index: 'org_code',
      width: 150,
      format: (item: User) => {
        // 优先使用organization对象中的org_name，然后尝试org_name字段，最后显示org_code
        return (item as any).organization?.org_name || (item as any).org_name || item.org_code || '-';
      }
    },
    {
      title: '角色',
      index: 'role_id',
      width: 160,
      format: (item: User) => {
        // 优先使用role对象中的role_name，然后尝试role_name字段，最后使用role_code映射
        return (
          (item as any).role?.role_name ||
          (item as any).role_name ||
          this.getRoleNameByCode((item as any).role_code) ||
          this.getRoleNameByCode((item as any).role?.role_code) ||
          '-'
        );
      }
    },
    {
      title: '联系电话',
      index: 'phone',
      width: 120
    },
    {
      title: '登录次数',
      index: 'login_count',
      width: 100,
      type: 'number'
    },
    {
      title: '最后登录',
      index: 'last_login_at',
      type: 'date',
      width: 150,
      sort: true
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
          click: (item: User) => this.viewUser(item),
          iif: (item: User) => this.canManageUser(item)
        },
        {
          text: '编辑',
          icon: 'edit',
          click: (item: User) => this.editUser(item),
          iif: (item: User) => this.canManageUser(item)
        },
        {
          text: '重置密码',
          icon: 'lock',
          click: (item: User) => this.resetPassword(item),
          iif: (item: User) => this.canManageUser(item)
        },
        {
          text: '删除',
          icon: 'delete',
          click: (item: User) => this.deleteUser(item),
          iif: (item: User) => this.canDeleteUser(item)
        }
      ]
    }
  ];

  ngOnInit(): void {
    this.initializePermissions();
    this.getData();
    this.loadOrganizationOptions();
    this.loadRoleOptions();
  }

  /**
   * 初始化权限控制
   */
  private initializePermissions(): void {
    const currentUser = this.settings.user;
    if (!currentUser) return;

    const roleCode = currentUser.roleCode || currentUser.role_code || currentUser.role?.role_code;

    // 如果是机构管理员，自动设置机构过滤条件
    if (roleCode === 'ORG_ADMIN') {
      const orgCode = currentUser.orgCode || currentUser.org_code || currentUser.organization?.org_code;
      if (orgCode) {
        this.q.org_code = orgCode;
      }
    }
  }

  /**
   * 根据角色编码获取角色名称
   */
  getRoleNameByCode(roleCode: string): string {
    const roleMap: Record<string, string> = {
      SUPER_ADMIN: '超级系统管理员',
      ORG_ADMIN: '机构管理员',
      NORMAL_USER: '普通用户'
    };
    return roleMap[roleCode] || roleCode || '-';
  }

  /**
   * 检查是否可以管理指定用户
   */
  canManageUser(user: User): boolean {
    const currentUser = this.settings.user;
    if (!currentUser) return false;

    const roleCode = currentUser.roleCode || currentUser.role_code || currentUser.role?.role_code;

    // 超级管理员可以管理所有用户
    if (roleCode === 'SUPER_ADMIN') {
      return true;
    }

    // 机构管理员只能管理同机构用户
    if (roleCode === 'ORG_ADMIN') {
      const currentOrgCode = currentUser.orgCode || currentUser.org_code || currentUser.organization?.org_code;
      const targetOrgCode = user.org_code || (user as any).organization?.org_code;
      return currentOrgCode === targetOrgCode;
    }

    return false;
  }

  /**
   * 检查是否可以删除指定用户
   */
  canDeleteUser(user: User): boolean {
    const currentUser = this.settings.user;
    if (!currentUser) return false;

    // 不能删除自己
    if (currentUser.id === user.id) {
      return false;
    }

    return this.canManageUser(user);
  }

  /**
   * 检查是否可以新增用户
   */
  canAddUser(): boolean {
    const currentUser = this.settings.user;
    if (!currentUser) return false;

    const roleCode = currentUser.roleCode || currentUser.role_code || currentUser.role?.role_code;

    // 超级管理员和机构管理员都可以新增用户
    return roleCode === 'SUPER_ADMIN' || roleCode === 'ORG_ADMIN';
  }

  /**
   * 检查是否是机构管理员且机构固定
   */
  isOrgAdminWithFixedOrg(): boolean {
    const currentUser = this.settings.user;
    if (!currentUser) return false;

    const roleCode = currentUser.roleCode || currentUser.role_code || currentUser.role?.role_code;

    // 机构管理员的机构选择应该被禁用，因为他们只能管理自己的机构
    return roleCode === 'ORG_ADMIN';
  }

  /**
   * 获取用户列表数据
   */
  getData(forceRefresh = false): void {
    this.loading = true;

    // 权限控制：机构管理员只能查看本机构用户
    let orgCode = this.q.org_code || '';
    const currentUser = this.settings.user;
    if (currentUser) {
      const roleCode = currentUser.roleCode || currentUser.role_code || currentUser.role?.role_code;
      if (roleCode === 'ORG_ADMIN') {
        // 机构管理员强制使用自己的机构代码
        const currentOrgCode = currentUser.orgCode || currentUser.org_code || currentUser.organization?.org_code;
        if (currentOrgCode) {
          orgCode = currentOrgCode;
        }
      }
    }

    const params: any = {
      pi: this.q.pi,
      ps: this.q.ps,
      keyword: this.q.keyword || '',
      status: this.q.status,
      org_code: orgCode,
      role_id: this.q.role_id
    };

    // 添加强制刷新参数，跳过缓存
    if (forceRefresh) {
      params._t = Date.now();
    }

    this.userService
      .getUsers(params)
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
            this.msg.error(res.message || '获取用户数据失败');
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

          this.msg.error('获取用户数据失败');
          this.data = [];
        }
      });
  }

  /**
   * 加载机构选项
   */
  loadOrganizationOptions(): void {
    this.http.get('/organizations', { pi: 1, ps: 1000, status: 1 }).subscribe({
      next: res => {
        if (res.code === 200 || res.success === true) {
          this.organizationOptions = res.data?.list || res.data?.items || res.data || [];
        }
      },
      error: error => {
        if (error.status === 200 && error.ok && error.body) {
          if (error.body.success === true || error.body.code === 200) {
            this.organizationOptions = error.body.data?.list || error.body.data?.items || error.body.data || [];
          }
        }
      }
    });
  }

  /**
   * 加载角色选项
   */
  loadRoleOptions(): void {
    this.http.get('/roles', { pi: 1, ps: 1000, status: 1 }).subscribe({
      next: res => {
        if (res.code === 200 || res.success === true) {
          this.roleOptions = res.data?.list || res.data?.items || res.data || [];
        }
      },
      error: error => {
        if (error.status === 200 && error.ok && error.body) {
          if (error.body.success === true || error.body.code === 200) {
            this.roleOptions = error.body.data?.list || error.body.data?.items || error.body.data || [];
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
   * 新增用户
   */
  addUser(tpl: TemplateRef<unknown>): void {
    this.editingUser = {
      status: 1
    };
    this.isEditMode = false;
    this.modalTitle = '新增用户';
    this.showModal(tpl);
  }

  /**
   * 查看用户
   */
  viewUser(item: User): void {
    // 跳转到用户详情页面
    this.router.navigate(['/sys/user/view', item.id]);
  }

  /**
   * 编辑用户
   */
  editUser(item: User): void {
    // 跳转到用户编辑页面
    this.router.navigate(['/sys/user/edit', item.id]);
  }

  /**
   * 删除用户
   */
  deleteUser(item: User): void {
    // 创建自定义确认对话框，提供停用和删除两个选项
    this.modalSrv.confirm({
      nzTitle: '用户操作选择',
      nzContent: `
        <div>
          <p>请选择对用户 "<strong>${item.username}</strong>" 的操作：</p>
          <div style="margin-top: 16px;">
            <p><strong>停用：</strong>将用户状态设置为停用，用户无法登录但数据保留</p>
            <p><strong>删除：</strong>永久删除用户数据，此操作无法撤销</p>
          </div>
        </div>
      `,
      nzOkText: '停用用户',
      nzOkType: 'primary',
      nzCancelText: '删除用户',
      nzOnOk: () => {
        // 停用用户
        return this.disableUser(item);
      },
      nzOnCancel: () => {
        // 删除用户 - 需要二次确认
        this.confirmDeleteUser(item);
      },
      nzWidth: 500
    });
  }

  /**
   * 停用用户
   */
  private disableUser(item: User): Promise<boolean> {
    return new Promise(resolve => {
      // 只传递需要更新的字段
      const updateData = {
        status: 0 // 0表示停用
      };

      this.userService.updateUser(item.id!, updateData).subscribe({
        next: res => {
          if (res.code === 200 || res.success === true) {
            this.msg.success('用户已停用');
            // 立即更新本地数据状态
            const userIndex = this.data.findIndex(u => u.id === item.id);
            if (userIndex !== -1) {
              this.data[userIndex] = { ...this.data[userIndex], status: 0 };
            }
            // 强制刷新数据，确保与服务器同步
            this.getData(true);
            resolve(true);
          } else {
            this.msg.error(res.message || res.error || '停用失败');
            resolve(false);
          }
        },
        error: () => {
          this.msg.error('停用失败');
          resolve(false);
        }
      });
    });
  }

  // 用于删除确认的用户名输入值
  deleteConfirmUsername = '';
  // 当前要删除的用户
  currentDeletingUser: User | null = null;

  /**
   * 确认删除用户（二次确认）
   */
  private confirmDeleteUser(item: User): void {
    // 重置输入值
    this.deleteConfirmUsername = '';
    this.currentDeletingUser = item;

    // 使用模板引用创建模态框
    const modal = this.modalSrv.create({
      nzTitle: '确认永久删除',
      nzContent: this.deleteConfirmTemplate,
      nzOkText: '永久删除',
      nzCancelText: '取消',
      nzOkType: 'primary',
      nzOkDanger: true,
      nzWidth: 600,
      nzOnOk: () => {
        if (this.deleteConfirmUsername.trim() === item.username) {
          return this.permanentDeleteUser(item);
        } else {
          this.msg.error('用户名输入不正确，删除操作已取消');
          return false;
        }
      }
    });

    // 模态框打开后聚焦到输入框
    modal.afterOpen.subscribe(() => {
      setTimeout(() => {
        const confirmInput = document.querySelector('#deleteConfirmInput') as HTMLInputElement;
        if (confirmInput) {
          confirmInput.focus();
        }
      }, 100);
    });
  }

  /**
   * 永久删除用户
   */
  private permanentDeleteUser(item: User): Promise<boolean> {
    return new Promise(resolve => {
      this.userService.deleteUser(item.id!).subscribe({
        next: res => {
          if (res.code === 200 || res.success === true) {
            this.msg.success('用户已永久删除');
            // 立即从本地数据中移除
            this.data = this.data.filter(u => u.id !== item.id);
            // 强制刷新数据，确保与服务器同步
            this.getData(true);
            resolve(true);
          } else {
            this.msg.error(res.message || res.error || '删除失败');
            resolve(false);
          }
        },
        error: () => {
          this.msg.error('删除失败');
          resolve(false);
        }
      });
    });
  }

  /**
   * 重置密码
   */
  resetPassword(item: User): void {
    // 直接跳转到重置密码页面，ACL已经在按钮级别进行了权限控制
    this.router.navigate(['/sys/user/reset-password', item.id]);
  }

  /**
   * 批量删除
   */
  batchDelete(): void {
    if (this.selectedRows.length === 0) {
      this.msg.warning('请选择要删除的用户');
      return;
    }

    this.modalSrv.confirm({
      nzTitle: '确认批量删除',
      nzContent: `确定要删除选中的 ${this.selectedRows.length} 个用户吗？`,
      nzOnOk: () => {
        const userIds = this.selectedRows.map(row => row['id']);
        return this.userService.batchDeleteUsers(userIds).subscribe({
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
        return this.saveUser();
      }
    });
  }

  /**
   * 保存用户
   */
  saveUser(): Promise<boolean> {
    return new Promise(resolve => {
      // 表单验证
      if (!this.editingUser.user_code || !this.editingUser.username || !this.editingUser.org_code || !this.editingUser.role_id) {
        this.msg.error('请填写完整信息');
        resolve(false);
        return;
      }

      const request = this.isEditMode
        ? this.userService.updateUser(this.editingUser.id!, this.editingUser)
        : this.userService.createUser(this.editingUser);

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
      org_code: '',
      role_id: undefined
    };
    this.getData();
  }
}
